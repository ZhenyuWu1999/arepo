#!/usr/bin/env python3
"""Algebraic regression for the experimental ALE shear eigenvalue floor.

The test is independent of the AREPO executable.  It ports the exact
projector correction from residual_distribution_solver.c and falsifies its
operator identities on random positive Euler states and random triangles.
"""

from __future__ import annotations

import math

import numpy as np

from test_lda_f1_rank_deficiency import GAMMA, GAMMA_MINUS1, SplitMatrices, _one_k_matrix
from test_n_frame_covariance import galilean_matrix


EPSILON = 0.45


def random_triangle(rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    while True:
        points = rng.uniform(-1.0, 1.0, size=(3, 2))
        first = points[1] - points[0]
        second = points[2] - points[0]
        signed_twice_area = float(first[0] * second[1] - first[1] * second[0])
        if abs(signed_twice_area) > 0.05:
            break
    if signed_twice_area < 0.0:
        points[[1, 2]] = points[[2, 1]]

    edge_pairs = ((1, 2), (2, 0), (0, 1))
    normals = np.empty((3, 2))
    magnitudes = np.empty(3)
    for index, (left, right) in enumerate(edge_pairs):
        edge = points[right] - points[left]
        magnitude = float(np.linalg.norm(edge))
        normals[index] = np.array([edge[1], -edge[0]]) / magnitude
        magnitudes[index] = magnitude

    np.testing.assert_allclose(
        np.sum(magnitudes[:, None] * normals, axis=0), 0.0, atol=2.0e-14
    )
    return normals, magnitudes


def build_split(
    velocity: np.ndarray,
    relative_velocity: np.ndarray,
    density: float,
    pressure: float,
    normals: np.ndarray,
    magnitudes: np.ndarray,
) -> tuple[SplitMatrices, float, float]:
    sound_speed = math.sqrt(GAMMA * pressure / density)
    enthalpy = (
        GAMMA * pressure / (GAMMA_MINUS1 * density)
        + 0.5 * float(velocity @ velocity)
    )
    kplus = np.empty((3, 4, 4))
    kminus = np.empty((3, 4, 4))
    for vertex, (normal, magnitude) in enumerate(
        zip(normals, magnitudes, strict=True)
    ):
        relative_normal = float(relative_velocity @ normal)
        eigenvalues = np.array(
            [
                relative_normal + sound_speed,
                relative_normal - sound_speed,
                relative_normal,
                relative_normal,
            ]
        )
        kplus[vertex] = _one_k_matrix(
            normal,
            magnitude,
            np.maximum(eigenvalues, 0.0),
            velocity,
            sound_speed,
            enthalpy,
        )
        kminus[vertex] = _one_k_matrix(
            normal,
            magnitude,
            np.minimum(eigenvalues, 0.0),
            velocity,
            sound_speed,
            enthalpy,
        )
    return SplitMatrices(kplus=kplus, kminus=kminus), sound_speed, enthalpy


def apply_floor(
    split: SplitMatrices,
    velocity: np.ndarray,
    relative_velocity: np.ndarray,
    sound_speed: float,
    normals: np.ndarray,
    magnitudes: np.ndarray,
) -> SplitMatrices:
    kplus = split.kplus.copy()
    kminus = split.kminus.copy()
    floor_speed = EPSILON * sound_speed
    if np.linalg.norm(relative_velocity) >= floor_speed:
        return SplitMatrices(kplus=kplus, kminus=kminus)

    for vertex, (normal, magnitude) in enumerate(
        zip(normals, magnitudes, strict=True)
    ):
        relative_normal = float(relative_velocity @ normal)
        deficit = floor_speed - abs(relative_normal)
        if deficit <= 0.0:
            continue
        tangent = np.array([-normal[1], normal[0]])
        velocity_tangent = float(velocity @ tangent)
        right = np.array([0.0, tangent[0], tangent[1], velocity_tangent])
        left = np.array([-velocity_tangent, tangent[0], tangent[1], 0.0])
        correction = 0.25 * magnitude * deficit * np.outer(right, left)
        kplus[vertex] += correction
        kminus[vertex] -= correction
    return SplitMatrices(kplus=kplus, kminus=kminus)


def conservative_state(density: float, velocity: np.ndarray, pressure: float) -> np.ndarray:
    energy = pressure / GAMMA_MINUS1 + 0.5 * density * float(velocity @ velocity)
    return np.array([density, density * velocity[0], density * velocity[1], energy])


def pressure(state: np.ndarray) -> float:
    return GAMMA_MINUS1 * (
        state[3] - 0.5 * float(state[1:3] @ state[1:3]) / state[0]
    )


def check_one_case(
    velocity: np.ndarray,
    relative_velocity: np.ndarray,
    density: float,
    gas_pressure: float,
    normals: np.ndarray,
    magnitudes: np.ndarray,
) -> tuple[float, float, float]:
    base, sound_speed, enthalpy = build_split(
        velocity, relative_velocity, density, gas_pressure, normals, magnitudes
    )
    modified = apply_floor(
        base, velocity, relative_velocity, sound_speed, normals, magnitudes
    )

    full_scale = max(
        1.0, float(np.max(np.abs(base.kplus))), float(np.max(np.abs(base.kminus)))
    )
    full_defect = float(
        np.max(
            np.abs(
                (modified.kplus + modified.kminus)
                - (base.kplus + base.kminus)
            )
        )
    ) / full_scale
    eigenvalue_defect = 0.0
    projector_defect = 0.0

    for vertex, (normal, magnitude) in enumerate(
        zip(normals, magnitudes, strict=True)
    ):
        tangent = np.array([-normal[1], normal[0]])
        velocity_normal = float(velocity @ normal)
        velocity_tangent = float(velocity @ tangent)
        right_s = np.array([0.0, tangent[0], tangent[1], velocity_tangent])
        left_s = np.array([-velocity_tangent, tangent[0], tangent[1], 0.0])
        projector = np.outer(right_s, left_s)

        q2 = float(velocity @ velocity)
        right_e = np.array([1.0, velocity[0], velocity[1], 0.5 * q2])
        right_plus = np.array(
            [
                1.0,
                velocity[0] + sound_speed * normal[0],
                velocity[1] + sound_speed * normal[1],
                enthalpy + sound_speed * velocity_normal,
            ]
        )
        right_minus = np.array(
            [
                1.0,
                velocity[0] - sound_speed * normal[0],
                velocity[1] - sound_speed * normal[1],
                enthalpy - sound_speed * velocity_normal,
            ]
        )
        projector_scale = max(1.0, float(np.max(np.abs(projector))))
        projector_defect = max(
            projector_defect,
            float(np.max(np.abs(projector @ projector - projector)))
            / projector_scale,
            float(np.max(np.abs(projector @ right_e)))
            / max(
                1.0,
                projector_scale * float(np.max(np.abs(right_e))),
            ),
            float(np.max(np.abs(projector @ right_plus)))
            / max(
                1.0,
                projector_scale * float(np.max(np.abs(right_plus))),
            ),
            float(np.max(np.abs(projector @ right_minus)))
            / max(
                1.0,
                projector_scale * float(np.max(np.abs(right_minus))),
            ),
            abs(float(left_s @ right_s) - 1.0)
            / max(1.0, float(np.linalg.norm(left_s) * np.linalg.norm(right_s))),
        )

        relative_normal = float(relative_velocity @ normal)
        modulus = max(abs(relative_normal), EPSILON * sound_speed)
        expected_plus = 0.5 * (relative_normal + modulus)
        expected_minus = 0.5 * (relative_normal - modulus)
        scale = 0.5 * magnitude
        actual_plus = float(left_s @ modified.kplus[vertex] @ right_s) / scale
        actual_minus = float(left_s @ modified.kminus[vertex] @ right_s) / scale
        eigenvalue_defect = max(
            eigenvalue_defect,
            abs(actual_plus - expected_plus),
            abs(actual_minus - expected_minus),
        )

        shear_positive = expected_plus
        acoustic_bound = sound_speed + abs(relative_normal)
        assert shear_positive <= acoustic_bound + 5.0e-15 * sound_speed

    state = conservative_state(density, velocity, gas_pressure)
    assert state[0] > 0.0 and pressure(state) > 0.0
    return full_defect, eigenvalue_defect, projector_defect


def main() -> None:
    rng = np.random.default_rng(20260823)
    maxima = np.zeros(3)
    for _ in range(1000):
        normals, magnitudes = random_triangle(rng)
        density = 10.0 ** rng.uniform(-2.0, 2.0)
        gas_pressure = 10.0 ** rng.uniform(-2.0, 2.0)
        sound_speed = math.sqrt(GAMMA * gas_pressure / density)
        velocity = rng.normal(0.0, 3.0 * sound_speed, size=2)
        angle = rng.uniform(0.0, 2.0 * math.pi)
        relative_speed = rng.uniform(0.0, 0.999 * EPSILON * sound_speed)
        relative_velocity = relative_speed * np.array([math.cos(angle), math.sin(angle)])
        maxima = np.maximum(
            maxima,
            check_one_case(
                velocity,
                relative_velocity,
                density,
                gas_pressure,
                normals,
                magnitudes,
            ),
        )

        inactive_relative = 1.01 * EPSILON * sound_speed * np.array(
            [math.cos(angle), math.sin(angle)]
        )
        base, cs, _ = build_split(
            velocity,
            inactive_relative,
            density,
            gas_pressure,
            normals,
            magnitudes,
        )
        inactive = apply_floor(
            base, velocity, inactive_relative, cs, normals, magnitudes
        )
        np.testing.assert_array_equal(inactive.kplus, base.kplus)
        np.testing.assert_array_equal(inactive.kminus, base.kminus)

    normals, magnitudes = random_triangle(rng)
    density, gas_pressure = 0.73, 1.21
    sound_speed = math.sqrt(GAMMA * gas_pressure / density)
    velocity = np.array([2.1, -0.7])
    relative_velocity = np.array([0.12, -0.08]) * sound_speed
    base, cs, _ = build_split(
        velocity, relative_velocity, density, gas_pressure, normals, magnitudes
    )
    modified = apply_floor(
        base, velocity, relative_velocity, cs, normals, magnitudes
    )
    boost = np.array([7.0, -3.0])
    transform = galilean_matrix(boost)
    inverse = galilean_matrix(-boost)
    shifted_base, shifted_cs, _ = build_split(
        velocity - boost,
        relative_velocity,
        density,
        gas_pressure,
        normals,
        magnitudes,
    )
    shifted = apply_floor(
        shifted_base,
        velocity - boost,
        relative_velocity,
        shifted_cs,
        normals,
        magnitudes,
    )
    expected_plus = np.einsum("ab,ibc,cd->iad", transform, modified.kplus, inverse)
    expected_minus = np.einsum("ab,ibc,cd->iad", transform, modified.kminus, inverse)
    covariance_defect = max(
        float(np.max(np.abs(shifted.kplus - expected_plus))),
        float(np.max(np.abs(shifted.kminus - expected_minus))),
    )
    np.testing.assert_allclose(shifted.kplus, expected_plus, rtol=2.0e-12, atol=2.0e-12)
    np.testing.assert_allclose(shifted.kminus, expected_minus, rtol=2.0e-12, atol=2.0e-12)

    assert maxima[0] < 5.0e-12
    assert maxima[1] < 2.0e-10
    assert maxima[2] < 2.0e-10
    print("ALE shear-floor random-triangle defects")
    print(f"  K+ + K- conservation : {maxima[0]:.6e}")
    print(f"  shear split spectrum : {maxima[1]:.6e}")
    print(f"  projector identities : {maxima[2]:.6e}")
    print(f"  Galilean covariance  : {covariance_defect:.6e}")
    print("  CFL                   : modified shear lambda+ is bounded by c+|w_n|")
    print("PASS: 1000 positive states/random triangles satisfy the operator checks.")


if __name__ == "__main__":
    main()
