# COSMA results imported for continued local work

2026-09-27. Author: Codex, following Zhenyu's request to commit the local work,
integrate COSMA changes, and continue subsequent experiments on the Mac.

## Local archive and Git integration

- Local pre-integration base: `94cd37a` on `develop_pureC_RD`.
- Local commit `e3ec73b` preserves 44 existing files: log3 through section125,
  Chapter4 reviews, main-loop/MPI/hierarchical figures and their diagnostic tools.
  Production solver files and default configurations are unchanged.
- Initial fetch and direct GitHub head lookup still returned `94cd37a` for this
  branch. No newer COSMA commit appeared on the other published branches.
  A read-only SSH check could not authenticate. Zhenyu subsequently confirmed
  that the COSMA work has not yet been committed and explicitly deferred its
  integration. Continue local work; do not wait for or initiate that merge.

## Copied results and provenance

The user copied the comparison output to
`../../cosma_runs/yee_n_boost10_20260926/comparison_latest/`.
The current figures are `combined_convergence.{png,pdf}` and
`vortex_profiles.{png,pdf}`; the profile figure uses the renderer in
`profile_style_v2/`. The prior profile figures remain in
`before_profile_style_v2/`. No copied file has been modified or relocated.

[COSMA_RESULT_IMPORT_20260927.json](COSMA_RESULT_IMPORT_20260927.json) records
all copied-file hashes and the independent checks. The convergence/profile
figures, report, comparison JSON and both renderer versions match their
supplied verification hashes. The JSON contains16 completed science cases:
N and LDA, static laboratory frame and moving element co-moving frame,
Nx=48/96/192/384, boost(10,0), t=1 and one MPI rank. These runs do not replace
the laboratory-frame reference formulation in the thesis.

The final errors use numerical mass weights. All eight reported convergence
orders were independently reproduced by equal-weight log-log fits to the four
stored error values. This checks the copied summary, not the original numerical
errors: raw snapshots, binaries, Configs and job/gate logs are absent from this
copy. The report's12 successful gates remain a statement of the originating
campaign until its full provenance is available. Treat the results as joint
space/time refinement; do not mix them with earlier area-weighted norms.

## Working environment after handoff

Future experiments return to the local Apple-Silicon Mac. COSMA is not required
for the next phase. Use the existing `LocalMac` build with Homebrew OpenBLAS,
with both `OMP_NUM_THREADS=1` and `OPENBLAS_NUM_THREADS=1`. Keep source,
Config, build directory, executable and output provenance separate for each
new run; do not run Linux COSMA binaries on macOS. Current equal-step moving
RD remains one MPI rank. The old stopped Mac campaigns are historical and
must not be silently restarted. This handoff launches no new hydro case.
