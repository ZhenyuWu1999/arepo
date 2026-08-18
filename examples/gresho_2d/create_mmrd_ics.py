#!/usr/bin/env python3

"""Regenerate every initial condition used by the moving-mesh RD campaign.

The runs recorded in `dev_log/RD_DEVELOPMENT_LOG_2.md` sections 10 and 15 to 21
depend on HDF5 initial conditions that are too large to track in git. Without a
committed generator a fresh checkout cannot reproduce any of those numbers,
which is the reproducibility gap raised in section 14.2 and carried as P3 since
section 15.5. This script closes it: everything is deterministic, and
`--verify` checks what is on disk against the recorded manifest.

Two families:

*Self-contained.* The jittered lattices are built here from a fixed seed, so
they need nothing else:

    IC_smoothjit48, IC_smoothjit96       resolution pair, seed 20260811
    IC_ens{48,96}_{1..4}                 ensemble, seed 20260811 + 1000*k

*Derived.* These reuse the generator positions of an existing Gresho initial
condition and overwrite only the fluid state, so that a comparison against the
Gresho runs varies the state and not the point set:

    IC_freestream_{random,glass}48       uniform state, uniform advection
    IC_smooth_{random,glass}48           smooth periodic state

Their base files come from `create.py` in this directory. If a base is missing
the script says so and skips that entry rather than inventing a point set.

    python create_mmrd_ics.py            # write everything that can be written
    python create_mmrd_ics.py --verify   # checksum what is on disk
"""

from __future__ import annotations

import argparse
import hashlib
import platform
import shutil
import sys
from pathlib import Path

import h5py
import numpy as np

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "MMRD_ICS.sha256"

GAMMA = 5.0 / 3.0
BOX = 1.0
JITTER = 0.4          # fraction of the cell size, identical at every resolution
BASE_SEED = 20260811

# free stream: uniform state carried at an angle that is not lattice aligned
FS_RHO, FS_PRESSURE, FS_VELOCITY = 1.0, 1.0, (1.0, 0.5)

# Galilean-invariance test: the Gresho vortex carried at three times its own
# peak azimuthal velocity, which is bulk Mach 1.0 against this vortex's sound
# speed. A static mesh must advect the vortex across cells and scatters the
# profile; a mesh moving with the flow should reproduce the unboosted result.
GRESHO_BOOST = 3.0

# Boost sequence and resolutions for the quantitative Galilean study of log
# section 25. All members share their generator lattice at a given resolution,
# so a comparison across boosts varies only the velocity frame.
GRESHO_BOOSTS = (0.0, 1.0, 3.0, 10.0)
GRESHO_RESOLUTIONS = (48, 96)

# Yee isentropic vortex, for order measurement. Gresho's velocity profile is
# only C^0 and caps the observed order near 1.6, so it cannot decide whether a
# residual is second order. Yee is smooth and is an exact steady solution in its
# own frame, so at boost zero any deviation is pure scheme error. Constants
# match Analysis/yee_boost/yee_boost_common.py, against which volume 1's LDA
# order of 1.879 was measured; note gamma differs from the Gresho cases.
YEE_BOX = 10.0
YEE_GAMMA = 1.4
YEE_BETA = 5.0
YEE_T_INFINITY = 1.0
YEE_RESOLUTIONS = (32, 64, 128)

# Discontinuous tier of the form-selection campaign. Both use gamma = 1.4.
# The Sod tube is periodic with two interfaces, at x = L/4 and x = 3L/4, which is
# the arrangement volume 1 used; the KH contact is given a finite transition
# width so that the initial data is resolved and a positivity failure at t = 0
# does not pre-empt the comparison the campaign is for.
SHOCK_GAMMA = 1.4
KH_TRANSITION = 0.025

# Resolutions per discontinuous family. The Sod tube gained 128 when section 8
# of `dev_log/RD_ALE_FORM_SELECTION.md` stress-tested the robustness premise
# across the mesh as well as the Courant number, and that run turned out to
# carry the whole partial retraction. It was originally produced by editing
# this loop rather than through the generator, so it sat outside the manifest
# until log section 34.1 found it; the resolution is a parameter now so that
# cannot recur.
SHOCK_RESOLUTIONS = {"sod": (64, 128), "kh": (64,)}


def smooth_state(xy: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """A C-infinity periodic state.

    Gresho is unsuitable for measuring the ALE conservation defect because its
    azimuthal velocity is piecewise linear, so grad^2 U is singular at r=0.2 and
    r=0.4 and dominates any scaling measurement. This state has no such feature.
    """
    k = 2.0 * np.pi / BOX
    rho = 1.0 + 0.3 * np.sin(k * xy[:, 0]) * np.cos(k * xy[:, 1])
    vx = 0.6 + 0.2 * np.sin(k * xy[:, 1])
    vy = 0.4 + 0.2 * np.sin(k * xy[:, 0])
    return rho, vx, vy


def gresho_state(xy: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """The standard Gresho vortex: density one, and a triangular v_phi(r).

    v_phi peaks at 1.0 at r = 0.2 and the sound speed is about 2.9, so a bulk
    boost of 3 is three times the vortex's own peak velocity at Mach 1.
    """
    dx = xy[:, 0] - 0.5 * BOX
    dy = xy[:, 1] - 0.5 * BOX
    r = np.hypot(dx, dy)
    safe = np.maximum(r, 1e-300)

    vphi = np.where(r < 0.2, 5.0 * r, np.where(r < 0.4, 2.0 - 5.0 * r, 0.0))
    pressure = np.where(r < 0.2, 5.0 + 12.5 * r ** 2,
                        np.where(r < 0.4,
                                 9.0 + 12.5 * r ** 2 - 20.0 * r + 4.0 * np.log(5.0 * safe),
                                 3.0 + 4.0 * np.log(2.0)))
    rho = np.ones_like(r)
    return rho, -vphi * dy / safe, vphi * dx / safe, pressure


def yee_state(xy: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    dx = xy[:, 0] - 0.5 * YEE_BOX
    dy = xy[:, 1] - 0.5 * YEE_BOX
    dx -= YEE_BOX * np.round(dx / YEE_BOX)
    dy -= YEE_BOX * np.round(dy / YEE_BOX)
    r2 = dx * dx + dy * dy

    temperature = YEE_T_INFINITY - ((YEE_GAMMA - 1.0) * YEE_BETA ** 2
                                    / (8.0 * np.pi ** 2 * YEE_GAMMA) * np.exp(1.0 - r2))
    rho = temperature ** (1.0 / (YEE_GAMMA - 1.0))
    pressure = rho * temperature
    factor = 0.5 * YEE_BETA / np.pi * np.exp(0.5 * (1.0 - r2))
    return rho, -dy * factor, dx * factor, pressure


def sod_state(xy: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    left = (xy[:, 0] > 0.25 * BOX) & (xy[:, 0] < 0.75 * BOX)
    rho = np.where(left, 1.0, 0.125)
    pressure = np.where(left, 1.0, 0.1)
    return rho, np.zeros(len(xy)), np.zeros(len(xy)), pressure


def kh_state(xy: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    y = xy[:, 1] / BOX
    w = KH_TRANSITION
    band = 0.5 * (np.tanh((y - 0.25) / w) - np.tanh((y - 0.75) / w))
    rho = 1.0 + band
    vx = -0.5 + band
    vy = 0.1 * np.sin(4.0 * np.pi * xy[:, 0] / BOX)
    return rho, vx, vy, np.full(len(xy), 2.5)


def write_ic(path: Path, xy: np.ndarray, rho: np.ndarray, vx: np.ndarray,
             vy: np.ndarray, pressure: np.ndarray | float) -> None:
    n = len(xy)
    with h5py.File(path, "w") as f:
        header = f.create_group("Header")
        scalars = dict(BoxSize=BOX, Flag_Cooling=0, Flag_DoublePrecision=1,
                       Flag_Feedback=0, Flag_Metals=0, Flag_Sfr=0,
                       Flag_StellarAge=0, HubbleParam=1.0, NumFilesPerSnapshot=1,
                       Omega0=0.0, OmegaB=0.0, OmegaLambda=0.0, Redshift=0.0,
                       Time=0.0)
        for key, value in scalars.items():
            header.attrs[key] = value
        header.attrs["MassTable"] = np.zeros(6, dtype=np.int32)
        for key in ("NumPart_ThisFile", "NumPart_Total"):
            counts = np.zeros(6, dtype=np.int32)
            counts[0] = n
            header.attrs[key] = counts
        header.attrs["NumPart_Total_HighWord"] = np.zeros(6, dtype=np.int32)

        gas = f.create_group("PartType0")
        coordinates = np.zeros((n, 3))
        coordinates[:, :2] = xy
        gas.create_dataset("Coordinates", data=coordinates)
        velocities = np.zeros((n, 3))
        velocities[:, 0] = vx
        velocities[:, 1] = vy
        gas.create_dataset("Velocities", data=velocities)
        # READ_MASS_AS_DENSITY_IN_INPUT: this field is the density
        gas.create_dataset("Masses", data=rho)
        gas.create_dataset("InternalEnergy",
                           data=np.broadcast_to(pressure, rho.shape) / ((GAMMA - 1.0) * rho))
        gas.create_dataset("ParticleIDs", data=np.arange(1, n + 1, dtype=np.int32))


def jittered_lattice(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    h = BOX / n
    centres = (np.arange(n) + 0.5) * h
    gx, gy = np.meshgrid(centres, centres, indexing="ij")
    xy = np.column_stack([gx.ravel(), gy.ravel()])
    xy = xy + (rng.random(xy.shape) - 0.5) * JITTER * h
    return xy % BOX


def derive_from(base: Path, target: Path, state: str) -> bool:
    """Copy a base initial condition and overwrite only its fluid state."""
    if not base.exists():
        print(f"  skip {target.name}: base {base.name} is absent; run create.py first")
        return False
    shutil.copyfile(base, target)
    with h5py.File(target, "r+") as f:
        gas = f["PartType0"]
        xy = np.asarray(gas["Coordinates"][:, :2], dtype=np.float64)
        if state == "freestream":
            rho = np.full(len(xy), FS_RHO)
            vx = np.full(len(xy), FS_VELOCITY[0])
            vy = np.full(len(xy), FS_VELOCITY[1])
            pressure = FS_PRESSURE
        else:
            rho, vx, vy = smooth_state(xy)
            pressure = 1.0
        gas["Masses"][:] = rho
        gas["InternalEnergy"][:] = np.broadcast_to(pressure, rho.shape) / ((GAMMA - 1.0) * rho)
        velocities = np.zeros((len(xy), 3))
        velocities[:, 0] = vx
        velocities[:, 1] = vy
        gas["Velocities"][:] = velocities
    print(f"  wrote {target.name} (from {base.name}, {state})")
    return True


def generate() -> list[Path]:
    written: list[Path] = []

    for n in (48, 96):
        xy = jittered_lattice(n, BASE_SEED)
        rho, vx, vy = smooth_state(xy)
        path = HERE / f"IC_smoothjit{n}.hdf5"
        write_ic(path, xy, rho, vx, vy, 1.0)
        written.append(path)
        print(f"  wrote {path.name} (jittered lattice, n={n}, seed {BASE_SEED})")

    for n in (48, 96):
        for member in (1, 2, 3, 4):
            seed = BASE_SEED + 1000 * member
            xy = jittered_lattice(n, seed)
            rho, vx, vy = smooth_state(xy)
            path = HERE / f"IC_ens{n}_{member}.hdf5"
            write_ic(path, xy, rho, vx, vy, 1.0)
            written.append(path)
            print(f"  wrote {path.name} (ensemble member {member}, seed {seed})")

    for n in GRESHO_RESOLUTIONS:
        xy = jittered_lattice(n, BASE_SEED)
        rho, vx, vy, pressure = gresho_state(xy)
        for boost in GRESHO_BOOSTS:
            path = HERE / f"IC_greshojit{n}_b{boost:g}.hdf5"
            write_ic(path, xy, rho, vx + boost, vy, pressure)
            written.append(path)
            print(f"  wrote {path.name} (Gresho, n={n}, boost {boost:g})")

    for n in YEE_RESOLUTIONS:
        rng = np.random.default_rng(BASE_SEED)
        h = YEE_BOX / n
        centres = (np.arange(n) + 0.5) * h
        gx, gy = np.meshgrid(centres, centres, indexing="ij")
        xy = np.column_stack([gx.ravel(), gy.ravel()])
        xy = (xy + (rng.random(xy.shape) - 0.5) * JITTER * h) % YEE_BOX
        rho, vx, vy, pressure = yee_state(xy)
        path = HERE / f"IC_yeejit{n}.hdf5"
        n_part = len(xy)
        with h5py.File(path, "w") as f:
            header = f.create_group("Header")
            for key, value in dict(BoxSize=YEE_BOX, Flag_Cooling=0, Flag_DoublePrecision=1,
                                   Flag_Feedback=0, Flag_Metals=0, Flag_Sfr=0, Flag_StellarAge=0,
                                   HubbleParam=1.0, NumFilesPerSnapshot=1, Omega0=0.0, OmegaB=0.0,
                                   OmegaLambda=0.0, Redshift=0.0, Time=0.0).items():
                header.attrs[key] = value
            header.attrs["MassTable"] = np.zeros(6, dtype=np.int32)
            for key in ("NumPart_ThisFile", "NumPart_Total"):
                counts = np.zeros(6, dtype=np.int32); counts[0] = n_part
                header.attrs[key] = counts
            header.attrs["NumPart_Total_HighWord"] = np.zeros(6, dtype=np.int32)
            gas = f.create_group("PartType0")
            coordinates = np.zeros((n_part, 3)); coordinates[:, :2] = xy
            gas.create_dataset("Coordinates", data=coordinates)
            velocities = np.zeros((n_part, 3)); velocities[:, 0] = vx; velocities[:, 1] = vy
            gas.create_dataset("Velocities", data=velocities)
            gas.create_dataset("Masses", data=rho)
            gas.create_dataset("InternalEnergy", data=pressure / ((YEE_GAMMA - 1.0) * rho))
            gas.create_dataset("ParticleIDs", data=np.arange(1, n_part + 1, dtype=np.int32))
        written.append(path)
        print(f"  wrote {path.name} (Yee vortex, n={n}, box {YEE_BOX:g}, gamma {YEE_GAMMA})")

    shock_cases = [(name, state, n)
                   for name, state in (("sod", sod_state), ("kh", kh_state))
                   for n in SHOCK_RESOLUTIONS[name]]
    for name, state, n in shock_cases:
        xy = jittered_lattice(n, BASE_SEED)
        rho, vx, vy, pressure = state(xy)
        path = HERE / f"IC_{name}jit{n}.hdf5"
        n_part = len(xy)
        with h5py.File(path, "w") as f:
            header = f.create_group("Header")
            for key, value in dict(BoxSize=BOX, Flag_Cooling=0, Flag_DoublePrecision=1,
                                   Flag_Feedback=0, Flag_Metals=0, Flag_Sfr=0, Flag_StellarAge=0,
                                   HubbleParam=1.0, NumFilesPerSnapshot=1, Omega0=0.0, OmegaB=0.0,
                                   OmegaLambda=0.0, Redshift=0.0, Time=0.0).items():
                header.attrs[key] = value
            header.attrs["MassTable"] = np.zeros(6, dtype=np.int32)
            for key in ("NumPart_ThisFile", "NumPart_Total"):
                counts = np.zeros(6, dtype=np.int32); counts[0] = n_part
                header.attrs[key] = counts
            header.attrs["NumPart_Total_HighWord"] = np.zeros(6, dtype=np.int32)
            gas = f.create_group("PartType0")
            coordinates = np.zeros((n_part, 3)); coordinates[:, :2] = xy
            gas.create_dataset("Coordinates", data=coordinates)
            velocities = np.zeros((n_part, 3)); velocities[:, 0] = vx; velocities[:, 1] = vy
            gas.create_dataset("Velocities", data=velocities)
            gas.create_dataset("Masses", data=rho)
            gas.create_dataset("InternalEnergy", data=pressure / ((SHOCK_GAMMA - 1.0) * rho))
            gas.create_dataset("ParticleIDs", data=np.arange(1, n_part + 1, dtype=np.int32))
        written.append(path)
        print(f"  wrote {path.name} ({name}, n={n}, gamma {SHOCK_GAMMA})")

    for family in ("random48", "glass48"):
        base = HERE / f"IC_gresho_v0_{family}.hdf5"
        target = HERE / f"IC_gresho_boost{GRESHO_BOOST:g}_{family}.hdf5"
        if base.exists():
            shutil.copyfile(base, target)
            with h5py.File(target, "r+") as f:
                velocities = np.asarray(f["PartType0/Velocities"][:])
                velocities[:, 0] += GRESHO_BOOST
                f["PartType0/Velocities"][:] = velocities
            written.append(target)
            print(f"  wrote {target.name} (Gresho boosted by {GRESHO_BOOST:g} in x)")
        else:
            print(f"  skip {target.name}: base {base.name} is absent; run create.py first")

    for family in ("random48", "glass48"):
        base = HERE / f"IC_gresho_v0_{family}.hdf5"
        for state, prefix in (("freestream", "IC_freestream"), ("smooth", "IC_smooth")):
            suffix = family if state == "freestream" else family.replace("48", "48")
            target = HERE / f"{prefix}_{suffix}.hdf5"
            if derive_from(base, target, state):
                written.append(target)

    return written


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def environment_stamp() -> str:
    """Record the main environment inputs that can change the output bytes.

    Any family whose state is built from transcendental functions -- Yee, KH and
    Gresho all are -- is reproducible only for a fixed numpy; the last bit of
    exp, sin and tanh is not specified across versions or SIMD paths. Families
    built from arithmetic and comparisons alone, such as the Sod tube, are
    reproducible across a wider range of environments, although HDF5 encoding
    can still change.  This stamp is diagnostic, not a portability guarantee:
    CPU-specific SIMD/libm choices may differ even when these values match.
    """
    return (
        f"python {platform.python_version()}, numpy {np.__version__}, "
        f"h5py {h5py.__version__}, hdf5 {h5py.version.hdf5_version}, "
        f"platform {platform.system()}/{platform.machine()}"
    )


def write_manifest(paths: list[Path]) -> None:
    header = [
        "# initial conditions for the moving-mesh RD campaign\n",
        f"# generated by {Path(__file__).name} under {environment_stamp()}\n",
        "# see environment_stamp() on why a version change moves some checksums\n",
    ]
    lines = [f"{checksum(p)}  {p.name}\n" for p in sorted(paths, key=lambda p: p.name)]
    MANIFEST.write_text("".join(header + lines))
    print(f"\nwrote {MANIFEST.name} with {len(lines)} entries")


def read_manifest(path: Path) -> tuple[dict[str, str], list[str]]:
    """Read one checksum manifest and retain its diagnostic comment lines."""

    entries: dict[str, str] = {}
    comments: list[str] = []
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            comments.append(line)
            continue
        fields = line.split()
        if len(fields) != 2:
            raise ValueError(f"{path.name}:{line_number}: expected SHA256 and filename")
        expected, name = fields
        if name in entries and entries[name] != expected:
            raise ValueError(f"{path.name}:{line_number}: conflicting checksum for {name}")
        entries[name] = expected
    return entries, comments


def verify() -> int:
    """Verify every local IC manifest and reject unmanifested IC files."""

    manifests = sorted(HERE.glob("*_ICS.sha256"))
    if not manifests:
        print(f"no *_ICS.sha256 manifests found in {HERE}")
        return 1

    failures = 0
    known: dict[str, tuple[str, list[str]]] = {}
    for manifest in manifests:
        try:
            entries, comments = read_manifest(manifest)
        except ValueError as error:
            print(f"  INVALID  {error}")
            failures += 1
            continue

        for line in comments:
            if "generated by" in line and " under " in line:
                recorded = line.split(" under ", 1)[-1].strip()
                current = environment_stamp()
                if recorded != current:
                    print(f"  note     {manifest.name} was written under {recorded};"
                          f" this is {current}")

        for name, expected in entries.items():
            if name in known:
                previous, sources = known[name]
                if previous != expected:
                    print(
                        f"  CONFLICT {name}: {sources[-1]} has {previous}, "
                        f"{manifest.name} has {expected}"
                    )
                    failures += 1
                elif manifest.name not in sources:
                    sources.append(manifest.name)
            else:
                known[name] = (expected, [manifest.name])

    for name, (expected, _sources) in sorted(known.items()):
        path = HERE / name
        if not path.exists():
            print(f"  MISSING  {name}")
            failures += 1
        elif checksum(path) != expected:
            print(f"  MISMATCH {name}")
            failures += 1
        else:
            print(f"  ok       {name}")

    # Git deliberately ignores these large binaries, so a one-way manifest
    # check would hide exactly the omission the manifest is meant to expose.
    # Every IC in this directory must be named by at least one tracked manifest.
    for path in sorted(HERE.glob("IC_*.hdf5")):
        if path.name not in known:
            print(f"  UNMANIFESTED {path.name}")
            failures += 1

    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verify", action="store_true",
                        help="checksum the files on disk against the manifest")
    parser.add_argument("--force", action="store_true",
                        help="overwrite initial conditions that already exist")
    parser.add_argument("--update-manifest", action="store_true",
                        help="replace MMRD_ICS.sha256 after a complete intentional regeneration")
    args = parser.parse_args()

    if args.verify:
        return verify()

    # Overwriting in place is how the campaign lost the byte identity of eight
    # initial conditions on 2026-08-17: this script rewrites every family, and
    # the ones built from transcendental functions came back with different
    # last bits under a newer numpy. The originals were not recoverable. A run
    # that regenerates must now say so explicitly.
    try:
        managed_names, _comments = read_manifest(MANIFEST)
    except (FileNotFoundError, ValueError) as error:
        print(f"cannot determine managed IC names from {MANIFEST}: {error}")
        return 1
    existing = sorted(name for name in managed_names if (HERE / name).exists())
    if existing and not args.force:
        print(f"{len(existing)} initial conditions already exist in {HERE}.")
        print("Re-running overwrites them, and their exact bytes cannot be")
        print("recovered if this environment differs from the one that wrote")
        print("them. Use --verify to check them, or --force to rewrite.")
        return 1

    print("regenerating moving-mesh RD initial conditions")
    written = generate()
    if args.update_manifest:
        written_names = {path.name for path in written}
        missing = sorted(set(managed_names) - written_names)
        if missing:
            print("refusing to replace the manifest after an incomplete generation:")
            for name in missing:
                print(f"  not written {name}")
            return 1
        write_manifest(written)
    else:
        print(f"\nkept the recorded manifest {MANIFEST.name};"
              " pass --update-manifest to replace it intentionally")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
