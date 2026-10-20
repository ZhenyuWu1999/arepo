#!/usr/bin/env python3
"""Generate the deterministic Morton-inspired 3D Blob IC without AREPO imports."""
import argparse
from pathlib import Path

import h5py
import numpy as np

BOX = 10.
GAMMA = 5/3
WIND = 1.5*4.1
TCR = 2*np.sqrt(10)/WIND


def make_ic(path, n=32, seed=68315):
    if n < 2:
        raise ValueError('n must be at least two')
    count = n**3
    x = np.random.default_rng(seed).uniform(0, BOX, (count, 3))
    cloud = np.linalg.norm(x-[2.5, 5., 5.], axis=1) < 1.
    rho = np.where(cloud, 100., 10.)
    v = np.full_like(x, 1e-7)
    v[:, 0] = np.where(cloud, 1e-8, WIND)
    counts = np.array([count, 0, 0, 0, 0, 0], dtype=np.uint32)
    attrs = dict(NumPart_ThisFile=counts, NumPart_Total=counts,
        NumPart_Total_HighWord=np.zeros(6, np.uint32), MassTable=np.zeros(6),
        Time=0., Redshift=0., BoxSize=BOX, NumFilesPerSnapshot=1,
        Omega0=0., OmegaB=0., OmegaLambda=0., HubbleParam=1., Flag_Sfr=0,
        Flag_Cooling=0, Flag_StellarAge=0, Flag_Metals=0, Flag_Feedback=0,
        Flag_DoublePrecision=1)
    # Exclusive creation protects archived ICs. Masses stores input density.
    with h5py.File(path, 'x') as f:
        h = f.create_group('Header')
        for key, value in attrs.items():
            h.attrs[key] = value
        gas = f.create_group('PartType0')
        for key, value in dict(Coordinates=x, Velocities=v, Masses=rho,
                InternalEnergy=100/((GAMMA-1)*rho),
                ParticleIDs=np.arange(1, count+1, dtype=np.uint64)).items():
            gas.create_dataset(key, data=value)
    return int(cloud.sum())


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('output', type=Path)
    p.add_argument('--n', type=int, default=32)
    p.add_argument('--seed', type=int, default=68315)
    a = p.parse_args()
    clouds = make_ic(a.output, a.n, a.seed)
    print(f'{a.output}: {a.n**3} nodes, {clouds} cloud nodes; t_cr={TCR:.17g}')
