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


def write_manifest(paths: list[Path]) -> None:
    lines = [f"{checksum(p)}  {p.name}\n" for p in sorted(paths, key=lambda p: p.name)]
    MANIFEST.write_text("".join(lines))
    print(f"\nwrote {MANIFEST.name} with {len(lines)} entries")


def verify() -> int:
    if not MANIFEST.exists():
        print(f"{MANIFEST.name} is absent; run without --verify first")
        return 1
    failures = 0
    for line in MANIFEST.read_text().splitlines():
        expected, name = line.split()
        path = HERE / name
        if not path.exists():
            print(f"  MISSING  {name}")
            failures += 1
        elif checksum(path) != expected:
            print(f"  MISMATCH {name}")
            failures += 1
        else:
            print(f"  ok       {name}")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verify", action="store_true",
                        help="checksum the files on disk against the manifest")
    args = parser.parse_args()

    if args.verify:
        return verify()

    print("regenerating moving-mesh RD initial conditions")
    write_manifest(generate())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
