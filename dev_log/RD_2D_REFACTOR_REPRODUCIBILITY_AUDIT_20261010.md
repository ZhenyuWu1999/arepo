# Independent audit of the 2D reproducibility finding

Author: Codex, 2026-10-10. User asked to inspect Claude's review and the loss
of machine-error-level reproduction in some 2D results. Reviewed HEAD
`5e013f3`, including [Claude's review](RD_3D_INTEGRATION_CLAUDE_REVIEW_20261010.md)
§4. This audit changes documentation only. Numerical ablations below use a
separate frozen source tree; the repository solver is unchanged.

## Finding confirmed, with a narrower scope than all historical results

Claude's main finding is correct: the shared K extraction in `dd7a31b` does
not preserve the long-time floating-point trajectory of the two tested moving
LDA/B cases. The earlier Codex gates covered **static N/LDA and moving N** at
t=.015625; they did not cover moving LDA/B. Their small differences were real
but cannot establish long-time compatibility for these other paths.

I independently read and compared every saved snapshot by particle ID. The
comparison uses Claude's frozen old `e1b1aa9` and new `632a401` results. The
entire Git `src/` tree is identical between `e1b1aa9` and the pre-integration
Codex baseline `4b40f75`. Configs match the no-lazy, mode-1, equal-step baseline;
paired parameter files differ only in OutputDir. This is a Yee vortex in the
periodic 10×10 box, gamma=1.4, boost (1,0), 2304 glass nodes, CFL=.2, actual
dt=1/256, 256 steps to t=1. Both replay/ablation thread limits are one.

| Scheme | max matched-ID density difference, t=.25 | t=.5 | t=.75 | t=1 |
| --- | --- | --- | --- | --- |
| LDA | 9.326e-15 | 9.789e-12 | 1.048e-6 | 1.323e-6 |
| B | 5.218e-15 | 4.594e-12 | 4.530e-7 | 6.453e-5 |

At t=1 the largest componentwise coordinate differences are 1.471e-5 (LDA)
and 6.607e-5 (B); pressure differences are 1.871e-6 and 9.367e-5. These are
**matched-ID state/trajectory differences**, not Eulerian field differences at
identical coordinates. They establish failure of exact trajectory reproduction
without requiring interpolation between the now different meshes.

Both runs retain round-off-level global conservation. The largest absolute
old/new difference among mass, two momenta and energy over the saved snapshots
is 1.422e-14. Each run's maximum total drift, normalized by
`max(|Q_component(0)|, M(0))`, is at most 1.447e-16 for these Yee cases.
Conservation constrains totals, not the per-node spatial distribution, so it
does not imply machine-level agreement of the solution.

Area-weighted L1 errors evaluated at **each run's own coordinates** also
reproduce Claude's values. Their relative old→new changes are:

| Scheme | density L1 | velocity L1 | pressure L1 |
| --- | --- | --- | --- |
| LDA | +1.112e-7 | −7.883e-7 | +1.230e-7 |
| B | −3.863e-7 | +8.672e-6 | +2.013e-6 |

The comparable error norms support little change in accuracy for these two
runs. They do not prove that the difference is harmless for every longer
integration, resolution, hierarchy or shock. In particular, `1e-6–1e-4` is
an observed range in these cases, **not** a general reproducibility bound for
all pre-`dd7a31b` archives.

## Controlled experiments localize the change to K construction

I ran four additional native simulations, all to t=1 with the same Configs,
ICs and physical parameters:

1. Replay the exact new LDA and B binaries, checking their archived SHA-256
   before use. Every saved particle dataset, including coordinates and all
   state fields, is **byte-identical after ID sorting** to Claude's new runs.
   Same-binary reproducibility therefore holds in this tested environment.
2. Freeze the current source, restore only the two original 2D K construction
   blocks from `4b40f75`, and build separate LDA/B binaries. Keep the new
   dimension header, shared LU/SVD, state module and all other new code.
   Every saved particle dataset is **byte-identical after ID sorting** to
   Claude's old runs, at all five snapshots through t=1.

This isolates the observed regression to the K construction extraction,
rather than the five-component storage or RK-state refactor. The underlying
K formulas have independent algebraic checks; the shared implementation
changes the floating-point evaluation path and these small changes grow in
the coupled moving-mesh evolution. The experiment does not isolate a specific
instruction/FMA or one off-diagonal entry, so Claude's more specific
off-diagonal attribution remains a hypothesis. Likewise the snapshots show
amplification, but do not establish a mathematical exponential growth law.

The ablation is diagnostic, not a production fix: it restores the original
inline blocks inside the frozen main file. A modular compatibility fix must
be separately built and checked; moving the same expressions into a different
function can itself change compiler evaluation. No shared kernel was replaced
in the working repository during this audit.

## Further qualifications and next gate

- The timestep sequences and per-step logged flip counts match. LDA has 123
  steps containing flips and 249 cavities; B has 119 such steps and 244
  cavities. The `123/119` numbers in the review count steps, not cavities.
  Logged LU/SVD/rank histograms also match at every step. The logs do not
  record complete cavity vertex identities, so matching summaries alone
  cannot prove identical connectivity at every step.
- Claude's HLLC Sedov21 old/new saved particle datasets are byte-identical
  through t=.005. This control bypasses K. It is not evidence that all HLLC
  campaigns or other schemes are universally unaffected.
- The new 3D correctness evidence is separate from this old/new 2D
  compatibility issue. This audit did not repeat the 3D experiments.
- Prefer retaining an explicitly tested 2D compatibility arithmetic path
  within the modular design before further changes obscure the baseline.
  Add these 256-step moving LDA/B comparisons to refactor gates, including
  fields, coordinates, own-coordinate analytic errors, totals and event
  diagnostics. Exact reproduction, conservation and physical accuracy are
  distinct acceptance criteria; do not relax a reproduction assertion to
  `1e-4` merely to pass it.

Evidence: `../local_runs/codex_claude_3d_review_20261010_v1/` contains
`audit.py`, `audit.json`, the four-run `controlled.py` and `controlled/`
campaign, exact source patch and hashes, Configs, generated headers, binaries,
linkage, IC/parameter hashes, logs and snapshots. `verify_particles.py` and
`particle_bitwise_checks.json` check the entire stored particle record.
Original reference binaries/headers were copied with hash verification into
`reference_artifacts/` to preserve evidence outside Claude's temporary folder.
