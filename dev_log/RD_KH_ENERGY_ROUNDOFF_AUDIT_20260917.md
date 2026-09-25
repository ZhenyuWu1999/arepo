# KH rerun: opposite signs of equal and hierarchical energy changes

Author: Codex. Date: 2026-09-17. Requested by Zhenyu Wu after the common-beta
default change and the Chapter 4 KH figure update.

## Result

The opposite signs at four MPI ranks reproduce exactly. They are also
present in the **stored extensive conserved energy**, so attributing the
main trend to snapshot reconstruction would be inaccurate. Reconstruction
and postprocessing arithmetic contribute only a few 1e-18 in this experiment.
The measured drift already exists in the floating-point evolution.

Changing to two ranks makes the equal-step endpoint positive. The sign is
therefore not an intrinsic energy-loss property of equal stepping. The
evidence supports round-off accumulation with configuration-dependent bias,
not physical heating/cooling or a meaningful difference in total-energy
conservation accuracy. It does not identify the contribution of every
individual floating-point operation; no assertion is made that hierarchical
energy must always increase for other inputs or longer integrations.

At t=2, using the raw stored energy and 100-digit decimal accumulation:

| MPI ranks | Equal: delta E/E0 | Hierarchical: delta E/E0 |
|---:|---:|---:|
| 1 | -7.1779437276e-17 | +3.8556969600e-16 |
| 2 | +4.4094047546e-17 | +2.4153814406e-16 |
| 4 | -2.2418413147e-16 | +2.9096669353e-16 |

E0 is approximately 6.422490635665968. One representable binary64 step at
this total-energy scale is 1.3829189797e-16 relative to E0. Thus these drifts
are only a few such units after roughly two thousand finest substeps.
IEEE binary64 machine epsilon itself is 2.22044604925e-16. These units
describe scale; they are not a theorem that every accumulated error is
bounded by one machine epsilon.

## Controlled reruns and data path

Archive: `/Users/zhenyuwu/arepo_rd/local_runs/kh_roundoff_audit_20260917_v1/`.

Six reruns use the exact archived common-beta equal/hierarchy binaries at
1, 2 and 4 ranks. All original 44 saved snapshots at ranks1/4 match the
previous archive **bit for bit in every PartType0 field and output time**,
after sorting by ID. Rank2 is an additional controlled comparison. No IC
or method was changed to obtain a different sign.

The setup is unchanged: static periodic unit-square glass with2304 nodes;
smooth KH density1--2, vx=-.5--.5, tanh layer width .025 at y=.25/.75;
vy=.1 sin(4 pi x), p=2.5, gamma=1.4, Gauss3 P1-U LDA/F1 common beta_n;
CFL .3; equal dt1/1024, natural hierarchy dt1/1024 and1/512; t=0--2 in
code units, eleven saved states. All hierarchical outputs are shared
synchronization points and contain bins18/19. No F1 rank-lumped fallback
occurs in any of these KH runs.

The reference source archive SHA256 is
`2ca8059f1e5de15b2d02889bbbff26e9ef31c1dc0e4bd350372268ac27bf4c06`.
Configurations, executable hashes, linkage and source provenance were
copied from the final common-beta campaign. Each case has a fresh output
directory. Existing outputs were preserved. Native MPI requires local
socket permission; runs used OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=1, with
no more than eight computation processes concurrently.

Six additional runs use a frozen diagnostic copy of the same source.
Only `src/io/io.c` changes: immediately on a normal snapshot request,
each rank writes ID, SphP.Energy, mass, momentum and primitive fields to
a separate file, using hexadecimal `%a` to preserve every bit. There is
no diagnostic MPI reduction and no change to the hydrodynamic update.
All66 diagnostic snapshots match the corresponding uninstrumented reruns
exactly in every field, demonstrating noninterference for this experiment.
All12 new native runs complete with their existing assertions enabled.

The diagnostic source, its one-file patch, two separate builds, generated
headers, binary hashes and per-rank dumps are retained under `diagnostic/`.
`prepare_diagnostic.py`, `analyze.py`, `plot.py`, `analysis.json` and
`energy_audit.csv` reproduce the audit. The production solver and thesis
were not edited by this follow-up.

## Separating the three contributions

Define Q(t)=sum_i SphP[i].Energy from the exact saved doubles. Define R(t)
as sum_i m_i[u_i+|v_i|^2/2] evaluated from the saved primitive doubles with
100-digit Decimal arithmetic. Define F(t) as the exact sum of the individual
energies reconstructed by the original float64 NumPy expression.

Then, with one common normalization Q(0),

\[
\frac{F(t)-F(0)}{Q(0)}=
\frac{Q(t)-Q(0)}{Q(0)}+
\frac{[R(t)-Q(t)]-[R(0)-Q(0)]}{Q(0)}+
\frac{[F(t)-R(t)]-[F(0)-R(0)]}{Q(0)}.
\]

These are respectively evolution drift, primitive reconstruction/conversion
error, and float64 postprocessing arithmetic. The decomposition closes to
better than1e-29 after conversion of its terms to binary64.

For four ranks at t=2:

| Contribution | Equal | Hierarchical |
|---|---:|---:|
| Stored-energy drift | -2.2418413147e-16 | +2.9096669353e-16 |
| Primitive conversion | -1.3976223988e-18 | -7.0160919683e-19 |
| Reconstruction arithmetic | +2.2754518293e-18 | +1.1742865825e-18 |
| Original plot diagnostic | -2.2330630204e-16 | +2.9143937092e-16 |

Ordinary global summation can introduce substantially larger errors than
these two small reconstruction terms. For example, Python's sequential
sum of the same four-rank equal reconstructed energies, followed by total
subtraction, gives +1.1063e-15 at t=2 instead of the original -2.2331e-16.
The original figure used compensated sums of per-node differences, so it
did not suffer from that particular sequential-summation artefact. Reversing
its curve merely by choosing a different summation algorithm would not
improve the underlying simulation.

## Interpretation and plotting

A floating-point update has the form

\[
\widehat Q_i^{\,new}=\operatorname{fl}(\widehat Q_i+\widehat{\delta Q_i}).
\]

Even where the exact residual balances, finite-precision residual evaluation,
stage-variable conversions and adding increments to Q leave small errors.
Equal and hierarchy evaluate different stage states and deposit increments
in different sequences; MPI repartitions the local and received contributions.
Their rounding errors need not have the same sign or behave as independent,
zero-mean samples. A smooth-looking signed bias at a few 1e-16 is therefore
compatible with a conservative discrete method. The rank2 sign reversal is
a direct check that the equal-step negative drift is not invariant.

This audit does not distinguish which individual stage operation dominates
the raw stored-energy drift, and is not a new convergence study, efficiency
measurement, or long-time bound. Numerical diffusion of KH can redistribute
kinetic and internal energy while total energy remains conserved; the sign
of this total-energy diagnostic cannot measure that diffusion.

The new signed comparison figure shows every tested rank count, with
snapshot reconstruction above and stored energy below on identical axes.
It retains the positive and negative directions rather than selecting runs
that look less biased. For a thesis conservation diagnostic, direct stored
energy is the more direct quantity, with compensated or higher-precision
global summation. The existing thesis figure is numerically reproduced;
changing it is not required to correct a plotting error. No thesis edit or
Git commit/push was made during this audit.
