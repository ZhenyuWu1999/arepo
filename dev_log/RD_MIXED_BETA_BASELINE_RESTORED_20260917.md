# Mixed-stage static LDA/F1 baseline restored — 2026-09-17

Author: Codex. User decision: restore the former stage-dependent method as the
baseline; retain common opening beta_n as an explicit comparison and describe
the limited error comparison in Chapter 4. This supersedes log3 §73's default
choice, while preserving its implementation and evidence as an opt-in trial.

## Method and options

The opening spatial contribution uses beta_n; the closing spatial contribution
and F1 temporal term use beta_*. Hierarchical closing matrices use predicted
stage-live states and unchanged frozen states. No flag is required for this
baseline. RD_LDA_MIXED_STAGE_BETA remains a compatible explicit selection.
RD_LDA_COMMON_OPENING_BETA selects common opening beta_n for the standard static
LDA/F1 path. The two flags are mutually exclusive. Common-beta singular spatial
range completion remains inside that opt-in path; temporal rank-deficient
lumped fallback is retained. N, B, moving geometry and rate-Heun are unaffected.
Root Config is unchanged. Restoration does not establish second-order time
accuracy or equivalence between hierarchy and finest-bin equal timesteps.

## Native replay evidence

Frozen source, separate configurations/build directories/binaries/outputs,
MPI rank4, OMP_NUM_THREADS=1 and OPENBLAS_NUM_THREADS=1. KH uses the previous
static glass2304/Gauss3 setup to t2; Yee is the previous advected glass2304 case
to t1. Each saved state is sorted by ID before comparison; IDs, coordinates,
conserved states, timebins, dual areas, pressure and time match exactly.

| New case | Archived reference | Exact snapshots |
|---|---|---:|
| kh_default_internal | beta_kh_mixed_equal | 11 |
| kh_default_hier | beta_kh_mixed_hier | 11 |
| yee_t1_internal | beta_yee_mixed_equal | 5 |
| yee_t1_common | beta_yee_equal | 5 |

All cases finish, with positive stored density/pressure and conservation gates
passing unchanged. make check_rd passes all four scripts. These are regression
checks, not a new convergence study. Prior current-Gauss Yee weighted density
L1 differs by about 0.183% between mixed and common beta_n; the Chapter 4 wording
is restricted to measured errors in the tests considered. Earlier common
beta_* evidence is explicitly identified as earlier Yee tests. Paardekooper's
common beta_n convention is supported by the existing source/paper audit, not
cited as direct support for our mixed-stage choice.

## Thesis and figure

Only chapter4.tex and a new mixed-baseline KH figure were installed. The126
tracked-file checks preserve all files apart from Chapter 4, including Chapters
1–3, bibliography, FV/comparison and MPI text. No formula underbraces.
Full thesis compilation: 245 pages, zero unresolved references. Review pages
166–171 (printed143–148) rendered and checked individually. KH restores the old
4-rank mixed data and uses the requested Delta E/E0 [10^-16] axis. Data remain
at round-off; curve appearance is not evidence of improved physical accuracy.
The prepared 2-rank common-beta figure was not installed and remains archived.

Workspace archive: local_runs/restore_mixed_baseline_20260917_v1/ includes
before files, baseline_only.patch, frozen source/config/header/binary provenance,
build/run logs, exact-state analysis, figure data, thesis patch, compile/QA and
delivery records. Native source tar SHA256: af2bd74ea3830839ad2f55fc53b111f82750a4c2af55dc8e44ae60bd2d71ffe3.
Branch develop_pureC_RD; base adc424b with pre-existing work preserved.
No commit or push.
