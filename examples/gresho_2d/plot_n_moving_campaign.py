#!/usr/bin/env python3
"""Plot the focused moving-mesh N campaign with the mathematical form labelled."""

from __future__ import annotations

import argparse
from pathlib import Path

import h5py
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
from matplotlib.ticker import NullFormatter
import numpy as np


FORM = (
    "Moving-mesh ALE–RD N  |  Arpaia modified-midpoint mass  |  "
    "P¹(U) contour total  |  element frame b_T = σ̄_T"
)
FORMULA = (
    "Φᵀ = ½ Σⱼ [F(Uⱼ)·nⱼ − (σ̄_T·nⱼ)Uⱼ]   |   "
    "φᵢ = φᵢᴺ + (Φᵀ − Σⱼφⱼᴺ)/3"
)
SWITCHES = (
    "N_SCHEME · RD_ALE_EQUALSTEP · RD_ALE_CONTOUR_RESIDUAL · "
    "RD_ELEMENT_COMOVING_FRAME · RD_ALE_CFL_TIMESTEP"
)
LDA_YEE = np.array([2.290109722e-3, 7.356192296e-4, 2.252200434e-4])


def load_snapshot(path: Path) -> tuple[float, dict[str, np.ndarray]]:
    with h5py.File(path, "r") as handle:
        gas = handle["PartType0"]
        fields = {
            name: np.asarray(gas[name], dtype=np.float64)
            for name in (
                "Coordinates",
                "Velocities",
                "Density",
                "Pressure",
                "InternalEnergy",
                "Masses",
                "Volume",
                "ParticleIDs",
            )
        }
        time = float(np.atleast_1d(handle["Header"].attrs["Time"])[0])
    order = np.argsort(fields["ParticleIDs"])
    return time, {name: value[order] for name, value in fields.items()}


def add_form_labels(fig: plt.Figure) -> None:
    fig.text(0.5, 0.064, FORM, ha="center", va="bottom", fontsize=9.3, weight="semibold")
    fig.text(0.5, 0.039, FORMULA, ha="center", va="bottom", fontsize=8.5)
    fig.text(0.5, 0.017, SWITCHES, ha="center", va="bottom", fontsize=7.8, color="#4a5568")


def save(fig: plt.Figure, output: Path, stem: str) -> None:
    fig.savefig(output / f"{stem}.png", dpi=220, bbox_inches="tight")
    fig.savefig(output / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)


def gresho_fields(root: Path) -> dict[int, tuple[float, np.ndarray, np.ndarray, np.ndarray]]:
    result = {}
    for boost in (0, 3, 10):
        time, data = load_snapshot(root / "long" / f"output_gresho_b{boost}" / "snap_001.hdf5")
        pos = data["Coordinates"].copy()
        vel = data["Velocities"].copy()
        pos[:, 0] = (pos[:, 0] - boost * time) % 1.0
        vel[:, 0] -= boost
        dx = pos[:, 0] - 0.5
        dy = pos[:, 1] - 0.5
        radius = np.hypot(dx, dy)
        vphi = (-vel[:, 0] * dy + vel[:, 1] * dx) / np.maximum(radius, 1e-300)
        result[boost] = (time, radius, vphi, data["Volume"])
    return result


def exact_gresho(radius: np.ndarray) -> np.ndarray:
    return np.where(radius < 0.2, 5.0 * radius, np.where(radius < 0.4, 2.0 - 5.0 * radius, 0.0))


def bin_profile(x: np.ndarray, value: np.ndarray, weight: np.ndarray, edges: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    index = np.clip(np.searchsorted(edges, x, side="right") - 1, 0, len(edges) - 2)
    numerator = np.bincount(index, weights=value * weight, minlength=len(edges) - 1)
    denominator = np.bincount(index, weights=weight, minlength=len(edges) - 1)
    profile = np.divide(numerator, denominator, out=np.full_like(numerator, np.nan), where=denominator > 0)
    return 0.5 * (edges[1:] + edges[:-1]), profile


def plot_gresho(root: Path, output: Path) -> dict[int, float]:
    runs = gresho_fields(root)
    exact_r = np.linspace(0.0, 0.5, 600)
    colors = {0: "#2463a6", 3: "#db7b2b", 10: "#20866a"}

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8))
    ax = axes[0]
    ax.plot(exact_r, exact_gresho(exact_r), color="black", lw=2.1, label="exact")
    errors = {}
    for boost, (_, radius, vphi, volume) in runs.items():
        ax.scatter(radius, vphi, s=5, alpha=0.22, color=colors[boost], edgecolors="none",
                   label=f"boost {boost}")
        errors[boost] = float(np.average(np.abs(vphi - exact_gresho(radius)), weights=volume))
    ax.set(xlim=(0, 0.5), ylim=(-0.08, 1.08), xlabel="radius", ylabel=r"$v_\phi$",
           title=r"Gresho profile at $t=1$, $n=48$")
    ax.grid(alpha=0.18)
    ax.legend(frameon=False, ncol=2)

    ax = axes[1]
    _, r0, v0, _ = runs[0]
    for boost in (3, 10):
        _, _, vb, _ = runs[boost]
        delta = np.maximum(np.abs(vb - v0), 1e-18)
        ax.scatter(r0, delta, s=5, alpha=0.28, color=colors[boost], edgecolors="none",
                   label=f"|boost {boost} − boost 0|")
    ax.set(xlim=(0, 0.5), yscale="log", xlabel="radius", ylabel=r"$|\Delta v_\phi|$",
           title="Particle-ID Galilean difference")
    ax.grid(alpha=0.18, which="both")
    ax.legend(frameon=False)
    fig.suptitle("Long Gresho boost test", fontsize=15, weight="bold")
    fig.tight_layout(rect=(0, 0.12, 1, 0.94))
    add_form_labels(fig)
    save(fig, output, "n-moving-gresho-boosts")
    return errors


def plot_sod(root: Path, output: Path) -> None:
    t0, initial = load_snapshot(root / "output_sod" / "snap_000.hdf5")
    time, final = load_snapshot(root / "output_sod" / "snap_001.hdf5")
    edges = np.linspace(0.0, 1.0, 257)
    panels = (
        ("Density", r"$\rho$"),
        ("Velocities", r"$v_x$"),
        ("Pressure", r"$p$"),
    )
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.2), sharex=True)
    for ax, (field, ylabel) in zip(axes, panels):
        init_value = initial[field][:, 0] if field == "Velocities" else initial[field]
        final_value = final[field][:, 0] if field == "Velocities" else final[field]
        xi, yi = bin_profile(initial["Coordinates"][:, 0], init_value, initial["Volume"], edges)
        xf, yf = bin_profile(final["Coordinates"][:, 0], final_value, final["Volume"], edges)
        ax.plot(xi, yi, color="#8b95a5", lw=1.2, ls="--", label=f"initial, t={t0:g}")
        ax.scatter(final["Coordinates"][:, 0], final_value, s=2, alpha=0.08,
                   color="#2463a6", edgecolors="none")
        ax.plot(xf, yf, color="#2463a6", lw=1.6, label=f"N solution, t={time:g}")
        ax.set(xlabel="x", ylabel=ylabel)
        ax.grid(alpha=0.18)
    axes[0].legend(frameon=False)
    fig.suptitle("Periodic Sod tube: positive completion through 4667 edge flips",
                 fontsize=15, weight="bold")
    fig.tight_layout(rect=(0, 0.12, 1, 0.92))
    add_form_labels(fig)
    save(fig, output, "n-moving-sod")


def periodic_triangulation(x: np.ndarray, y: np.ndarray) -> mtri.Triangulation:
    tri = mtri.Triangulation(x, y)
    triangles = tri.triangles
    dx = np.ptp(x[triangles], axis=1)
    dy = np.ptp(y[triangles], axis=1)
    tri.set_mask((dx > 0.15) | (dy > 0.15))
    return tri


def plot_kh(root: Path, output: Path) -> None:
    time, data = load_snapshot(root / "long" / "output_kh" / "snap_001.hdf5")
    x = data["Coordinates"][:, 0]
    y = data["Coordinates"][:, 1]
    tri = periodic_triangulation(x, y)
    fields = ((data["Density"], r"density $\rho$", "viridis"),
              (data["Velocities"][:, 1], r"vertical velocity $v_y$", "coolwarm"))
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.8))
    for ax, (value, title, cmap) in zip(axes, fields):
        artist = ax.tripcolor(tri, value, shading="gouraud", cmap=cmap)
        fig.colorbar(artist, ax=ax, shrink=0.84)
        ax.set(aspect="equal", xlim=(0, 1), ylim=(0, 1), xlabel="x", ylabel="y", title=title)
    fig.suptitle(fr"Kelvin–Helmholtz at $t={time:g}$, $n=64$", fontsize=15, weight="bold")
    fig.tight_layout(rect=(0, 0.12, 1, 0.92))
    add_form_labels(fig)
    save(fig, output, "n-moving-kh")


def yee_density_error(path: Path) -> float:
    _, data = load_snapshot(path)
    x = data["Coordinates"]
    dx = x[:, 0] - 5.0
    dy = x[:, 1] - 5.0
    dx -= 10.0 * np.round(dx / 10.0)
    dy -= 10.0 * np.round(dy / 10.0)
    r2 = dx * dx + dy * dy
    gamma = 1.4
    temperature = 1.0 - ((gamma - 1.0) * 25.0 / (8.0 * np.pi**2 * gamma) * np.exp(1.0 - r2))
    exact = temperature ** (1.0 / (gamma - 1.0))
    return float(np.average(np.abs(data["Density"] - exact), weights=data["Volume"]))


def plot_yee(root: Path, output: Path) -> tuple[np.ndarray, np.ndarray]:
    resolution = np.array([32, 64, 128])
    n_error = np.array([
        yee_density_error(root / f"output_yee_n{n}" / "snap_001.hdf5") for n in resolution
    ])
    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    ax.loglog(resolution, n_error, "o-", lw=2, ms=6, color="#2463a6", label="N")
    ax.loglog(resolution, LDA_YEE, "s-", lw=2, ms=6, color="#db7b2b", label="LDA reference")
    ax.loglog(resolution, n_error[0] * (resolution[0] / resolution), ls=":", color="#4a5568",
              label=r"$O(h)$ guide")
    for x, y in zip(resolution, n_error):
        ax.annotate(f"{y:.2e}", (x, y), xytext=(5, 6), textcoords="offset points", fontsize=8)
    ax.set(xlabel="cells per dimension", ylabel=r"volume-weighted density $L_1$",
           title="Yee vortex at t=1")
    ax.set_xticks(resolution, labels=[str(n) for n in resolution])
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.grid(alpha=0.2, which="both")
    ax.legend(frameon=False)
    fig.suptitle("Smooth-flow accuracy: N is the robust first-order control",
                 fontsize=14, weight="bold")
    fig.tight_layout(rect=(0, 0.12, 1, 0.92))
    add_form_labels(fig)
    save(fig, output, "n-moving-yee-convergence")
    return resolution, n_error


def plot_summary(root: Path, output: Path, gresho_error: dict[int, float],
                 resolution: np.ndarray, n_error: np.ndarray) -> None:
    runs = gresho_fields(root)
    _, sod = load_snapshot(root / "output_sod" / "snap_001.hdf5")
    kh_time, kh = load_snapshot(root / "long" / "output_kh" / "snap_001.hdf5")
    fig, axes = plt.subplots(2, 2, figsize=(12.2, 9.2))

    exact_r = np.linspace(0, 0.5, 500)
    axes[0, 0].plot(exact_r, exact_gresho(exact_r), color="black", lw=2, label="exact")
    for boost, color in zip((0, 3, 10), ("#2463a6", "#db7b2b", "#20866a")):
        _, radius, vphi, _ = runs[boost]
        axes[0, 0].scatter(radius, vphi, s=4, alpha=0.18, color=color, edgecolors="none",
                           label=f"b={boost}, L1={gresho_error[boost]:.3e}")
    axes[0, 0].set(xlim=(0, 0.5), ylim=(-0.08, 1.08), xlabel="radius", ylabel=r"$v_\phi$",
                   title="Gresho, t=1")
    axes[0, 0].legend(frameon=False, fontsize=8)

    edges = np.linspace(0, 1, 257)
    xc, rho = bin_profile(sod["Coordinates"][:, 0], sod["Density"], sod["Volume"], edges)
    axes[0, 1].scatter(sod["Coordinates"][:, 0], sod["Density"], s=2, alpha=0.06,
                       color="#2463a6", edgecolors="none")
    axes[0, 1].plot(xc, rho, color="#2463a6", lw=1.8)
    axes[0, 1].set(xlabel="x", ylabel=r"$\rho$", title="Sod, t=0.2")

    tri = periodic_triangulation(kh["Coordinates"][:, 0], kh["Coordinates"][:, 1])
    image = axes[1, 0].tripcolor(tri, kh["Density"], shading="gouraud", cmap="viridis")
    fig.colorbar(image, ax=axes[1, 0], shrink=0.78)
    axes[1, 0].set(aspect="equal", xlim=(0, 1), ylim=(0, 1), xlabel="x", ylabel="y",
                   title=fr"KH density, t={kh_time:g}")

    axes[1, 1].loglog(resolution, n_error, "o-", color="#2463a6", lw=2, label="N")
    axes[1, 1].loglog(resolution, LDA_YEE, "s-", color="#db7b2b", lw=2, label="LDA reference")
    axes[1, 1].set_xticks(resolution, labels=[str(n) for n in resolution])
    axes[1, 1].xaxis.set_minor_formatter(NullFormatter())
    axes[1, 1].set(xlabel="cells per dimension", ylabel=r"density $L_1$",
                   title="Yee convergence, t=1")
    axes[1, 1].legend(frameon=False)
    for ax in axes.flat:
        ax.grid(alpha=0.16)
    fig.suptitle("Moving-mesh N: long-run solution quality", fontsize=17, weight="bold")
    fig.tight_layout(rect=(0, 0.12, 1, 0.94))
    add_form_labels(fig)
    save(fig, output, "n-moving-summary")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, help="campaign archive root")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    output = (args.output_dir or root / "figures").resolve()
    output.mkdir(parents=True, exist_ok=True)

    gresho_error = plot_gresho(root, output)
    plot_sod(root, output)
    plot_kh(root, output)
    resolution, n_error = plot_yee(root, output)
    plot_summary(root, output, gresho_error, resolution, n_error)
    print(f"wrote figures to {output}")


if __name__ == "__main__":
    main()
