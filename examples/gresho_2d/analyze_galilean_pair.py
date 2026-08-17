#!/usr/bin/env python3
"""Compare boosted Gresho snapshots after undoing the uniform translation."""

import argparse

import h5py
import numpy as np


FIELDS = ("Coordinates", "Velocities", "Density", "Pressure", "InternalEnergy", "Masses", "Volume")


def load(path, boost):
    with h5py.File(path, "r") as handle:
        gas = handle["PartType0"]
        time = float(np.atleast_1d(handle["Header"].attrs["Time"])[0])
        fields = {name: np.asarray(gas[name], dtype=np.float64) for name in FIELDS}
        order = np.argsort(np.asarray(gas["ParticleIDs"]))

    fields = {name: value[order] for name, value in fields.items()}
    fields["Coordinates"][:, 0] = (fields["Coordinates"][:, 0] - boost * time) % 1.0
    fields["Velocities"][:, 0] -= boost
    return time, fields


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("reference")
    parser.add_argument("candidate")
    parser.add_argument("--boost", type=float, required=True)
    args = parser.parse_args()

    reference_time, reference = load(args.reference, 0.0)
    candidate_time, candidate = load(args.candidate, args.boost)
    if candidate_time != reference_time:
        raise SystemExit(f"snapshot times differ: {reference_time} != {candidate_time}")

    print(f"time={reference_time:.17g} boost={args.boost:.17g}")
    for name in FIELDS:
        delta = candidate[name] - reference[name]
        if name == "Coordinates":
            delta = (delta + 0.5) % 1.0 - 0.5
        absolute = np.abs(delta)
        print(f"{name:14s} L1={absolute.mean():.9e} Linf={absolute.max():.9e}")


if __name__ == "__main__":
    main()
