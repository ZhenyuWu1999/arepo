#!/usr/bin/env python3
"""Non-uniform element test of N + contour Galilean covariance.

This is an algebraic regression for the combination enabled by
RD_ELEMENT_COMOVING_FRAME.  It deliberately uses three different positive
Euler states, a non-zero mesh velocity and a frame velocity unrelated to
either of them.  The test checks, in order,

  K_i'            = G K_i G^-1,
  U_in'           = G U_in,
  phi_i^{N prime} = G phi_i^N,
  Phi_contour'    = G Phi_contour,

and the same covariance after reconciling N with the contour total by
distributing (Phi_contour - sum_i phi_i^N)/3.

Run directly or through:

    make check_rd
"""

from __future__ import annotations

import numpy as np

from test_lda_f1_rank_deficiency import (
    EDGE_MAGNITUDES,
    GAMMA,
    NORMALS,
    SplitMatrices,
    build_split_matrices,
)


def galilean_matrix(frame_velocity: np.ndarray) -> np.ndarray:
    bx, by = frame_velocity
    return np.array(
        [
            [1.0, 0.0, 0.0, 0.0],
            [-bx, 1.0, 0.0, 0.0],
            [-by, 0.0, 1.0, 0.0],
            [0.5 * float(frame_velocity @ frame_velocity), -bx, -by, 1.0],
        ]
    )


def conservative_state(
    density: float,
    velocity: np.ndarray,
    pressure: float,
) -> np.ndarray:
    energy = pressure / (GAMMA - 1.0) + 0.5 * density * float(velocity @ velocity)
    return np.array(
        [density, density * velocity[0], density * velocity[1], energy]
    )


def n_distribution(
    split: SplitMatrices,
    states: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    inflow_rhs = sum(
        (matrix @ state for matrix, state in zip(split.kminus, states, strict=True)),
        start=np.zeros(4),
    )
    inflow = np.linalg.solve(split.sminus, inflow_rhs)
    residuals = np.array(
        [
            matrix @ (state - inflow)
            for matrix, state in zip(split.kplus, states, strict=True)
        ]
    )
    return inflow, residuals


def contour_residual(
    states: np.ndarray,
    pressures: np.ndarray,
    mesh_velocity: np.ndarray,
) -> np.ndarray:
    total = np.zeros(4)
    for state, pressure, normal, magnitude in zip(
        states, pressures, NORMALS, EDGE_MAGNITUDES, strict=True
    ):
        density = state[0]
        velocity = state[1:3] / density
        normal_velocity = float(velocity @ normal)
        physical = np.array(
            [
                density * normal_velocity,
                state[1] * normal_velocity + pressure * normal[0],
                state[2] * normal_velocity + pressure * normal[1],
                (state[3] + pressure) * normal_velocity,
            ]
        )
        ale = physical - float(mesh_velocity @ normal) * state
        total += 0.5 * magnitude * ale
    return total


def reconcile_with_contour(
    residuals: np.ndarray,
    contour_total: np.ndarray,
) -> np.ndarray:
    return residuals + (contour_total - np.sum(residuals, axis=0)) / 3.0


def max_abs(value: np.ndarray) -> float:
    return float(np.max(np.abs(value)))


def main() -> None:
    characteristic_velocity = np.array([0.72, -0.13])
    mesh_velocity = np.array([0.20, -0.05])
    relative_velocity = characteristic_velocity - mesh_velocity
    frame_velocity = np.array([1.70, -0.40])

    densities = np.array([1.10, 0.85, 1.25])
    velocities = np.array([[0.90, -0.10], [0.55, -0.35], [0.80, 0.05]])
    pressures = np.array([0.95, 1.20, 0.80])
    states = np.array(
        [
            conservative_state(density, velocity, pressure)
            for density, velocity, pressure in zip(
                densities, velocities, pressures, strict=True
            )
        ]
    )

    transform = galilean_matrix(frame_velocity)
    inverse = galilean_matrix(-frame_velocity)
    shifted_states = np.einsum("ab,ib->ia", transform, states)

    lab = build_split_matrices(
        characteristic_velocity,
        relative_velocity,
    )
    shifted = build_split_matrices(
        characteristic_velocity - frame_velocity,
        relative_velocity,
    )

    expected_kplus = np.einsum(
        "ab,ibc,cd->iad", transform, lab.kplus, inverse
    )
    expected_kminus = np.einsum(
        "ab,ibc,cd->iad", transform, lab.kminus, inverse
    )
    np.testing.assert_allclose(shifted.kplus, expected_kplus, rtol=5e-13, atol=5e-13)
    np.testing.assert_allclose(shifted.kminus, expected_kminus, rtol=5e-13, atol=5e-13)

    inflow_lab, raw_lab = n_distribution(lab, states)
    inflow_shifted, raw_shifted = n_distribution(shifted, shifted_states)
    expected_inflow = transform @ inflow_lab
    expected_raw = np.einsum("ab,ib->ia", transform, raw_lab)
    np.testing.assert_allclose(
        inflow_shifted, expected_inflow, rtol=2e-12, atol=2e-12
    )
    np.testing.assert_allclose(raw_shifted, expected_raw, rtol=2e-12, atol=2e-12)

    contour_lab = contour_residual(states, pressures, mesh_velocity)
    contour_shifted = contour_residual(
        shifted_states,
        pressures,
        mesh_velocity - frame_velocity,
    )
    expected_contour = transform @ contour_lab
    np.testing.assert_allclose(
        contour_shifted, expected_contour, rtol=2e-12, atol=2e-12
    )

    corrected_lab = reconcile_with_contour(raw_lab, contour_lab)
    corrected_shifted = reconcile_with_contour(raw_shifted, contour_shifted)
    expected_corrected = np.einsum("ab,ib->ia", transform, corrected_lab)
    np.testing.assert_allclose(
        corrected_shifted, expected_corrected, rtol=3e-12, atol=3e-12
    )
    np.testing.assert_allclose(
        np.sum(corrected_lab, axis=0), contour_lab, rtol=1e-13, atol=1e-13
    )
    np.testing.assert_allclose(
        np.sum(corrected_shifted, axis=0),
        contour_shifted,
        rtol=1e-13,
        atol=1e-13,
    )

    correction_norm = float(
        np.linalg.norm(contour_lab - np.sum(raw_lab, axis=0))
    )
    assert np.linalg.norm(contour_lab) > 1.0e-3
    assert correction_norm > 1.0e-3

    print("N frame covariance defects")
    print(f"  K+ similarity       : {max_abs(shifted.kplus - expected_kplus):.6e}")
    print(f"  K- similarity       : {max_abs(shifted.kminus - expected_kminus):.6e}")
    print(f"  inflow state        : {max_abs(inflow_shifted - expected_inflow):.6e}")
    print(f"  raw N distribution  : {max_abs(raw_shifted - expected_raw):.6e}")
    print(f"  contour total       : {max_abs(contour_shifted - expected_contour):.6e}")
    print(
        "  reconciled N        : "
        f"{max_abs(corrected_shifted - expected_corrected):.6e}"
    )
    print(f"  non-zero correction : {correction_norm:.6e}")
    print("PASS: non-uniform N + contour residual is Galilean covariant.")


if __name__ == "__main__":
    main()
