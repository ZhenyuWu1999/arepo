#!/usr/bin/env python3
"""Element-level test of the LDA F1 mass matrix at mesh-relative stagnation.

This test is deliberately independent of the AREPO executable.  It reproduces
the two-dimensional Euler K_i^+ and K_i^- matrices from
src/hydro/residual_distribution_solver.c for a uniform state on an equilateral
triangle.  It then compares three definitions of the F1 temporal contribution:

  pseudoinverse:
      T_i = -K_i^+ (S^-)^dagger b

  null-space completion:
      T_i = -K_i^+ (S^-)^dagger b
            + (b - S^- (S^-)^dagger b) / 3

  fully lumped:
      T_i = dU_i / 3

Here the triangle area and dt are set to one and

      b = (dU_0 + dU_1 + dU_2) / 3.

The script also approaches stagnation from several directions with an
invertible S^- and checks whether the composite LDA matrices

      beta_i = -K_i^+ (S^-)^-1

have a bounded, direction-independent limit.

Run:

    python3 tests/rd/test_lda_f1_rank_deficiency.py

No AREPO build or input data is required.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


GAMMA = 1.4
GAMMA_MINUS1 = GAMMA - 1.0

# Unit outward normals of an equilateral triangle.  Equal edge lengths are
# sufficient because only the closure sum_i |e_i| n_i = 0 is required here.
NORMALS = np.array(
    [
        [1.0, 0.0],
        [-0.5, 0.5 * math.sqrt(3.0)],
        [-0.5, -0.5 * math.sqrt(3.0)],
    ],
    dtype=float,
)
EDGE_MAGNITUDES = np.ones(3, dtype=float)


@dataclass
class SplitMatrices:
    kplus: np.ndarray
    kminus: np.ndarray

    @property
    def splus(self) -> np.ndarray:
        return np.sum(self.kplus, axis=0)

    @property
    def sminus(self) -> np.ndarray:
        return np.sum(self.kminus, axis=0)


def _one_k_matrix(
    normal: np.ndarray,
    magnitude: float,
    eigenvalues: np.ndarray,
    velocity: np.ndarray,
    sound_speed: float,
    enthalpy: float,
) -> np.ndarray:
    """Port the K-matrix formula used by residual_distribution_solver.c."""

    nx, ny = normal
    velx_avg, vely_avg = velocity
    vel_dot_n = float(velocity @ normal)

    velx_c = velx_avg / sound_speed
    vely_c = vely_avg / sound_speed
    h_c = enthalpy / sound_speed
    alpha = GAMMA_MINUS1 * (velx_avg**2 + vely_avg**2) / 2.0
    alpha_c = alpha / sound_speed

    value1, value2, value3, _value4 = eigenvalues
    value12 = (value1 - value2) / 2.0
    value123 = (value1 + value2 - 2.0 * value3) / 2.0

    matrix = np.empty((4, 4), dtype=float)
    half_mag = 0.5 * magnitude

    matrix[0, 0] = half_mag * (
        alpha_c * value123 / sound_speed
        - vel_dot_n * value12 / sound_speed
        + value3
    )
    matrix[0, 1] = half_mag * (
        -GAMMA_MINUS1 * velx_c * value123 / sound_speed
        + nx * value12 / sound_speed
    )
    matrix[0, 2] = half_mag * (
        -GAMMA_MINUS1 * vely_c * value123 / sound_speed
        + ny * value12 / sound_speed
    )
    matrix[0, 3] = half_mag * (
        GAMMA_MINUS1 * value123 / (sound_speed * sound_speed)
    )

    matrix[1, 0] = half_mag * (
        (alpha_c * velx_c - vel_dot_n * nx) * value123
        + (alpha_c * nx - velx_c * vel_dot_n) * value12
    )
    matrix[1, 1] = half_mag * (
        (nx * nx - GAMMA_MINUS1 * velx_c * velx_c) * value123
        - (GAMMA - 2.0) * velx_c * nx * value12
        + value3
    )
    matrix[1, 2] = half_mag * (
        (nx * ny - GAMMA_MINUS1 * velx_c * vely_c) * value123
        + (velx_c * ny - GAMMA_MINUS1 * vely_c * nx) * value12
    )
    matrix[1, 3] = half_mag * (
        GAMMA_MINUS1 * velx_c * value123 / sound_speed
        + GAMMA_MINUS1 * nx * value12 / sound_speed
    )

    matrix[2, 0] = half_mag * (
        (alpha_c * vely_c - vel_dot_n * ny) * value123
        + (alpha_c * ny - vely_c * vel_dot_n) * value12
    )
    matrix[2, 1] = half_mag * (
        (nx * ny - GAMMA_MINUS1 * velx_c * vely_c) * value123
        + (vely_c * nx - GAMMA_MINUS1 * velx_c * ny) * value12
    )
    matrix[2, 2] = half_mag * (
        (ny * ny - GAMMA_MINUS1 * vely_c * vely_c) * value123
        - (GAMMA - 2.0) * vely_c * ny * value12
        + value3
    )
    matrix[2, 3] = half_mag * (
        GAMMA_MINUS1 * vely_c * value123 / sound_speed
        + GAMMA_MINUS1 * ny * value12 / sound_speed
    )

    matrix[3, 0] = half_mag * (
        (alpha_c * h_c - vel_dot_n * vel_dot_n) * value123
        + vel_dot_n * (alpha_c - h_c) * value12
    )
    matrix[3, 1] = half_mag * (
        (vel_dot_n * nx - velx_avg - alpha_c * velx_c) * value123
        + (h_c * nx - GAMMA_MINUS1 * velx_c * vel_dot_n) * value12
    )
    matrix[3, 2] = half_mag * (
        (vel_dot_n * ny - vely_avg - alpha_c * vely_c) * value123
        + (h_c * ny - GAMMA_MINUS1 * vely_c * vel_dot_n) * value12
    )
    matrix[3, 3] = half_mag * (
        GAMMA_MINUS1 * h_c * value123 / sound_speed
        + GAMMA_MINUS1 * vel_dot_n * value12 / sound_speed
        + value3
    )

    return matrix


def build_split_matrices(
    fluid_velocity: np.ndarray,
    relative_velocity: np.ndarray,
    density: float = 1.0,
    pressure: float = 1.0,
) -> SplitMatrices:
    """Build K_i^+/- while the mesh moves at u_mesh = u - u_relative."""

    sound_speed = math.sqrt(GAMMA * pressure / density)
    enthalpy = (
        GAMMA * pressure / (GAMMA_MINUS1 * density)
        + 0.5 * float(fluid_velocity @ fluid_velocity)
    )
    mesh_velocity = fluid_velocity - relative_velocity

    kplus = np.empty((3, 4, 4), dtype=float)
    kminus = np.empty((3, 4, 4), dtype=float)

    for vertex, (normal, magnitude) in enumerate(
        zip(NORMALS, EDGE_MAGNITUDES, strict=True)
    ):
        fluid_normal_velocity = float(fluid_velocity @ normal)
        mesh_normal_velocity = float(mesh_velocity @ normal)
        relative_normal_velocity = fluid_normal_velocity - mesh_normal_velocity
        eigenvalues = np.array(
            [
                relative_normal_velocity + sound_speed,
                relative_normal_velocity - sound_speed,
                relative_normal_velocity,
                relative_normal_velocity,
            ]
        )

        kplus[vertex] = _one_k_matrix(
            normal,
            magnitude,
            np.maximum(eigenvalues, 0.0),
            fluid_velocity,
            sound_speed,
            enthalpy,
        )
        kminus[vertex] = _one_k_matrix(
            normal,
            magnitude,
            np.minimum(eigenvalues, 0.0),
            fluid_velocity,
            sound_speed,
            enthalpy,
        )

    return SplitMatrices(kplus=kplus, kminus=kminus)


def svd_pseudoinverse(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray, int]:
    """Moore-Penrose inverse with an explicit machine-precision rank rule."""

    left, singular_values, right_t = np.linalg.svd(matrix, full_matrices=False)
    tolerance = (
        np.finfo(float).eps
        * max(matrix.shape)
        * singular_values[0]
    )
    keep = singular_values > tolerance
    inverse_values = np.zeros_like(singular_values)
    inverse_values[keep] = 1.0 / singular_values[keep]
    pseudoinverse = (right_t.T * inverse_values) @ left.T
    return pseudoinverse, singular_values, int(np.count_nonzero(keep))


def lda_distribution(
    split: SplitMatrices,
    target: np.ndarray,
    inverse: np.ndarray,
) -> np.ndarray:
    """Return T_i = -K_i^+ inverse(S^-) target."""

    solution = inverse @ target
    return np.array([-matrix @ solution for matrix in split.kplus])


def relative_conservation_defect(
    contributions: np.ndarray,
    target: np.ndarray,
) -> float:
    scale = max(np.linalg.norm(target), np.finfo(float).tiny)
    return float(np.linalg.norm(np.sum(contributions, axis=0) - target) / scale)


def make_test_increment(
    stagnant_sminus: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Construct dU with both range and left-null-space content."""

    left, _singular_values, _right_t = np.linalg.svd(
        stagnant_sminus, full_matrices=True
    )
    left_null = left[:, -1]

    seed = np.array([0.7, -0.2, 0.4, -0.5])
    range_part = stagnant_sminus @ seed
    range_part /= np.linalg.norm(range_part)
    target = range_part + 0.5 * left_null

    variation = np.array([0.11, -0.07, 0.04, 0.09])
    increments = np.array(
        [
            target + variation,
            target - variation,
            target,
        ]
    )
    assert np.allclose(np.mean(increments, axis=0), target)
    return increments, target, left_null


def exact_stagnation_test(fluid_velocity: np.ndarray) -> dict[str, np.ndarray | float]:
    split = build_split_matrices(fluid_velocity, np.zeros(2))
    closure_defect = np.linalg.norm(split.splus + split.sminus, ord=np.inf)
    assert closure_defect < 2.0e-14

    pseudoinverse, singular_values, rank = svd_pseudoinverse(split.sminus)
    increments, target, left_null = make_test_increment(split.sminus)

    pseudo = lda_distribution(split, target, pseudoinverse)
    projected = split.sminus @ pseudoinverse @ target
    remainder = target - projected
    completed = pseudo + remainder[np.newaxis, :] / 3.0
    lumped = increments / 3.0

    pseudo_defect = relative_conservation_defect(pseudo, target)
    completed_defect = relative_conservation_defect(completed, target)
    lumped_defect = relative_conservation_defect(lumped, target)

    assert rank == 3
    assert pseudo_defect > 1.0e-2
    assert completed_defect < 2.0e-14
    assert lumped_defect < 2.0e-14

    return {
        "split": split,
        "increments": increments,
        "target": target,
        "left_null": left_null,
        "singular_values": singular_values,
        "rank": float(rank),
        "pseudo": pseudo,
        "completed": completed,
        "lumped": lumped,
        "pseudo_defect": pseudo_defect,
        "completed_defect": completed_defect,
        "lumped_defect": lumped_defect,
        "remainder_fraction": float(
            np.linalg.norm(remainder) / np.linalg.norm(target)
        ),
        "closure_defect": float(closure_defect),
    }


def approach_stagnation_test(
    fluid_velocity: np.ndarray,
    target: np.ndarray,
    exact_completed: np.ndarray,
    exact_lumped: np.ndarray,
) -> None:
    directions = [
        ("0 deg", np.array([1.0, 0.0])),
        ("37 deg", np.array([math.cos(math.radians(37)), math.sin(math.radians(37))])),
        ("143 deg", np.array([math.cos(math.radians(143)), math.sin(math.radians(143))])),
    ]
    magnitudes = [1.0e-2, 1.0e-4, 1.0e-6, 1.0e-8, 1.0e-10, 1.0e-12]

    print("\nNear-stagnation full-rank composite beta test")
    print(
        "relative_u  direction  rank       cond(S-)   conservation"
        "   ||T-T_null||   ||T-T_lumped||      ||beta||"
    )

    beta_by_magnitude: dict[float, list[np.ndarray]] = {}
    distribution_by_magnitude: dict[float, list[np.ndarray]] = {}

    for magnitude in magnitudes:
        for direction_name, direction in directions:
            split = build_split_matrices(
                fluid_velocity, magnitude * direction
            )
            closure_defect = np.linalg.norm(
                split.splus + split.sminus, ord=np.inf
            )
            assert closure_defect < 2.0e-14

            singular_values = np.linalg.svd(
                split.sminus, compute_uv=False
            )
            rank = int(np.linalg.matrix_rank(split.sminus))
            condition = float(singular_values[0] / singular_values[-1])
            beta = np.array(
                [
                    np.linalg.solve(split.sminus.T, -matrix.T).T
                    for matrix in split.kplus
                ]
            )
            contributions = np.einsum("ijk,k->ij", beta, target)
            defect = relative_conservation_defect(contributions, target)

            print(
                f"{magnitude:10.1e}  {direction_name:>9s}"
                f"  {rank:4d}  {condition:14.6e}"
                f"  {defect:13.6e}"
                f"  {np.linalg.norm(contributions - exact_completed):13.6e}"
                f"  {np.linalg.norm(contributions - exact_lumped):15.6e}"
                f"  {np.linalg.norm(beta):12.6e}"
            )

            beta_by_magnitude.setdefault(magnitude, []).append(beta)
            distribution_by_magnitude.setdefault(magnitude, []).append(
                contributions
            )

    print("\nMaximum difference between approach directions")
    print("relative_u     beta matrices     beta_i * target")
    reliable_beta_spread = None
    for magnitude in magnitudes:
        beta_values = beta_by_magnitude[magnitude]
        distribution_values = distribution_by_magnitude[magnitude]
        beta_spread = max(
            np.linalg.norm(beta_values[i] - beta_values[j])
            for i in range(len(beta_values))
            for j in range(i)
        )
        contribution_spread = max(
            np.linalg.norm(distribution_values[i] - distribution_values[j])
            for i in range(len(distribution_values))
            for j in range(i)
        )
        print(
            f"{magnitude:10.1e}    {beta_spread:13.6e}"
            f"    {contribution_spread:15.6e}"
        )
        if magnitude == 1.0e-8:
            reliable_beta_spread = beta_spread

    # The directional difference is already O(1) at 1e-8, where the direct
    # solves still conserve to much better than 1e-6 in both test cases.  It is
    # therefore not an artefact of the 1e-12 condition number.
    assert reliable_beta_spread is not None
    assert reliable_beta_spread > 1.0e-1


def run_case(label: str, fluid_velocity: np.ndarray) -> None:
    print(f"\n{'=' * 78}\n{label}: fluid velocity = {fluid_velocity}")
    result = exact_stagnation_test(fluid_velocity)

    print("\nExact mesh-relative stagnation")
    print(f"  singular values of S-       : {result['singular_values']}")
    print(f"  numerical rank              : {int(result['rank'])}")
    print(f"  ||S+ + S-||_inf             : {result['closure_defect']:.6e}")
    print(f"  target outside range(S-)    : {result['remainder_fraction']:.6e}")
    print(f"  pseudoinverse defect        : {result['pseudo_defect']:.6e}")
    print(f"  null-completion defect      : {result['completed_defect']:.6e}")
    print(f"  fully-lumped defect         : {result['lumped_defect']:.6e}")
    print(
        "  ||null-completion-lumped||  : "
        f"{np.linalg.norm(result['completed'] - result['lumped']):.6e}"
    )

    approach_stagnation_test(
        fluid_velocity,
        result["target"],
        result["completed"],
        result["lumped"],
    )


def main() -> None:
    np.set_printoptions(precision=6, suppress=False)
    run_case("zero background velocity", np.array([0.0, 0.0]))
    run_case("boosted/moving-mesh background", np.array([1.0, 0.3]))
    print("\nPASS: all algebraic conservation and rank assertions succeeded.")


if __name__ == "__main__":
    main()
