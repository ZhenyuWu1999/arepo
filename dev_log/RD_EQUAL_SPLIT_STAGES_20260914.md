# Static equal RK2 across the two AREPO hydro hooks

Date: 2026-09-14. Author: Codex (GPT-6). Requested by Zhenyu as the first
implementation step following the Chapter 4 structure review.

## Result and scope

Implemented opt-in `RD_RK2_SPLIT_STAGES` for static, non-comoving, source-free
N/LDA with `FORCE_EQUAL_TIMESTEPS` and standard `RD_RK2_TOTAL_RESIDUAL`.
The first main-loop hydro hook executes the predictor; the second executes
the corrector, using the same two hook locations as static hierarchy.

The trial Config is
[Config_RD_RK2_LDA_GAUSS3_EQUAL_SPLIT.sh](../examples/yee_2d/Config_RD_RK2_LDA_GAUSS3_EQUAL_SPLIT.sh).
The named September 13 equal reference and repository-default Config remain
available unchanged. The option is registered in `Template-Config.sh`.

All 24 final native cases completed (30 process launches, including resumes).
At the same MPI rank count, matched Yee, uniform, Sod, N and smooth KH final
four-component conservative-density states are identical to their unsplit
controls. MPI, hierarchy-degeneration and remapping comparisons are at
roundoff. This establishes a tested scheduling refactor for the stated static
scope; it does not establish a runtime speedup or change F1 accuracy.

## Why moving the call is sufficient only with explicit stage lifetime

Let `U_i^n` be the initial nodal conservative-density vector, `U_i^*` the
predictor, `|S_i|` the static median-dual area, and `Q_i=|S_i|U_i` the extensive
conserved vector. Define `delta U_i=U_i^*-U_i^n` as the predictor increment.
The spatial residual and F1 temporal correction are unchanged.

At the first hook the code saves `U_i^n` in `SphP.RD_Ustage0`, executes the
existing full-step predictor sweep and its MPI increment exchange, leaving
`Q_i=|S_i|U_i^*`. Primitive fields still represent the initial stage. At the
second hook it invokes the existing corrector preparation: form `delta U_i`
from the saved initial state and predicted Q, recover predictor primitives,
apply the existing local half-increment, exchange primitives and `RD_dU`,
then execute the original F1 corrector sweep.

The split path retains the predictor's `DualArea` for the corrector. Temporary
element indices, ownership lists and normals are reconstructed at each call;
no pointer or triangle-indexed stage cache survives across the main loop.
Node records can therefore be reordered or moved to a different rank between
stages. Static geometry and an autonomous hydro residual make the change in
the global evaluation time immaterial for the tested configurations.

Equal and hierarchy now share the stage-call interface and hook positions.
Equal still uses its original full-step GL/F1 assembly, while hierarchy uses
its existing interval ledger and weights. This refactor does not enable
hierarchy machinery or its frozen-node policy in equal runs. It therefore
does not alter the fixed-mesh F1 hierarchy limitation discussed in log3 §40.

The internal guard `RD_RK2_INTERNAL_LOOP` was renamed to `RD_RK2_EQUALSTEP`:
it selects the equal-step algebra, which now may execute one sweep per call.
Unsplit builds still perform the same two or four passes in one invocation.

## Restart and migration handling

`All.RD_EqualStepEnd` is zero at a completed step, otherwise the integer
endpoint of the pending corrector. A predictor refuses an unconsumed stage;
a corrector requires a matching endpoint. The actual new vertex bins are
reduced across ranks when opening a step: `All.HighestActiveTimeBin` still
describes the previous synchronization just after timestep selection, so it
cannot supply the new step's width.

AREPO's binary restart serializes both `All` and complete `SphP` records.
The previous comment saying `RD_Ustage0`/`RD_dU` were excluded from restart
IO was incorrect and is corrected. These fields are excluded from snapshots.
No extra MPI stage payload is needed: domain migration already carries SphP.

A checkpoint between hooks resumes directly at its pending corrector. The
final restart has a closed stage, so extending a completed run begins a new
predictor. Integer-timebase rescaling also rescales the pending endpoint.
After static restart mesh construction, the split path rebuilds timebin
lists and marks active bins again after restoring real particle bins.

That last operation fixes a failure found by the new extension test. Mesh
construction temporarily places nodes in an all-active bin and rebuilds
linked lists. Previously the run setup restored P[].TimeBinHydro without
restoring those lists. After TimeMax rescaling, the lists could still refer
to the old larger bin, selecting a wrong next synchronization. The new stage
endpoint assertion caught this before another hydro update. The repair is
confined to the new split path.

Binary restarts must use a compatible build/configuration; adding the stage
marker changes the `All` layout for split builds. The old hierarchy restart
restriction is unchanged. Snapshot restart begins a fresh complete step and
does not represent an open RK stage.

## Native evidence

Final archive:
`/Users/zhenyuwu/arepo_rd/local_runs/equal_split_stages_20260914_v2`.
The working source was frozen before compilation from base
`5f3db112c8487ce9f597e4c0f8c5e99c2e04531c` plus the saved source patch:

- source patch SHA256:
  `67d22fd4d3c1646f81a9bf4f9ebdb9f0222c1de176360f6a7284a0d6e9f2f7a9`
- frozen source tar SHA256:
  `36e534ca5ed2c57ddc2572c5a39a2f4208c73e4dc985349ce283c25c201c0d81`

Every tested source file was checked against the final working copy. Each of
eight configurations has a separate build directory, executable, generated
header, Config, build log, binary checksum and linkage record. Both
`OMP_NUM_THREADS=1` and `OPENBLAS_NUM_THREADS=1` were set. The earlier
`943f7ae` archive is an independent reference; its solver source matches
the current base source before this refactor.

The numerical runner is [check_equal_split_stages.py](../tests/rd/check_equal_split_stages.py).
It preserves failures and original checkpoint files. Final `campaign.json`,
`summary.json` and per-run logs contain the full case list and parameters.
The final runner, including the two additional restart gates, is archived as
`check_equal_split_stages_final.py`; those additions did not change C source.

All tests use 2-D static periodic glass meshes and gamma=1.4. Main LDA tests
use Gauss3/F1; N controls use the original Roe/lumped path. Short Yee is
48² (2304 nodes), box10, t=.125, cap1/256; the extended controls reach t=.25.
The longer Yee case is 96² (9216 nodes), box10, t=1, cap1/512.
Smooth KH is glass48 (2304 nodes), box1, t=2, matching the September
13 IC and output history. Sod is the archived periodic double tube through
t=.08, full128² (16384 nodes), box1 and effective single-tube Nx=64. IC hashes and actual
particle fields are retained; the `nx64` filename is not a full-box64² claim.

Comparisons sort by ParticleID and use
`U=(rho, rho*vx, rho*vy, rho*(utherm+|v|²/2))`. Listed differences are the
maximum absolute component difference, not an analytic-error norm.

| Comparison | max absolute difference in U |
|---|---:|
| Split vs internal, Yee48, 4 ranks | 0 |
| Split vs internal, uniform, 4 ranks | 0 |
| Split vs internal, Sod, 4 ranks | 0 |
| Split vs internal, N Yee, 4 ranks | 0 |
| Split vs internal with repeated domain reconstruction | 0 |
| Split vs archived equal, KH t=2, each of 1/4 ranks | 0 |
| Split vs archived equal, Yee96 t=1, 4 ranks | 0 |
| Split 1 vs 4 ranks, Yee48 | 8.88e-15 |
| Split 2 vs 4 ranks, Yee48 | 7.55e-15 |
| Hierarchy with equal bins vs split equal, 4 ranks | 1.29e-14 |
| Hierarchy forced2:1 vs archived forced2:1, 4 ranks | 0 |
| Stop after predictor and resume, 1/4 ranks | 0 |
| Stop/resume with domain reconstruction | 0 |
| Resume after changing the domain partition | 6.66e-15 |
| Extend completed restart from t=.125 to .25 vs continuous run | 0 |
| Extend pending-stage restart to t=.25 vs continuous run | 0 |

The remapping test changes only allowed restart parameters, MultipleDomains
2→4 and TopNodeFactor4→8. Its first resumed decomposition moves **1,155 of
2,304 nodes before the saved predictor's corrector**. Ordinary repeated
decomposition alone settled to zero transfers after initialization; it is
not presented as evidence of repeated physical migration.

Saved states have positive density and pressure, unchanged coordinates,
uniform-state preservation and matching compared timebins. The largest
sampled normalized global conservation defect over all cases is7.50e-15
(the Sod control and its identical split result). Each extensive total is
assembled with the median-dual area; mass and momentum changes are normalized
by initial total mass, energy changes by initial total energy. The final
comparison threshold is1e-11, unchanged across the campaign.

`make check_rd` passed the three existing algebra checks. Native builds ran
the option checks and retained RD_DEBUG_ASSERTS. Raw single-run times are
recorded for provenance, not used to claim performance improvement.

## Preserved attempts and remaining boundaries

- Initial campaign setup had an incorrect archived Sod case name; it failed
  before compilation/simulation and is preserved under
  `equal_split_stages_20260914_setup_attempt1`.
- The first MPI launch was denied loopback socket binding by the sandbox,
  before hydro initialization. Its output is preserved in
  `equal_split_stages_20260914/runs/yee_split_r1/sandbox_launch_failure`;
  authorized local execution outside that restriction succeeded.
- The first native implementation passed ordinary, pending-restart and
  physics gates but failed completed-run extension at the new endpoint
  assertion. Full v1 source/build/run evidence remains under
  `equal_split_stages_20260914`. The linked-list fix was frozen and all main
  cases rerun in v2, which passed all final gates.

B needs old triangle-stage distributions; four-pass rate-Heun and moving
geometry have different stage-lifetime requirements. They retain their
existing internal-loop paths and are rejected with the split option.
Gravity, cooling, refinement and stage-altering diagnostics are also outside
this opt-in implementation. No moving-mesh or cosmological validation is
claimed. Two calls rebuild element classification twice and introduce an
endpoint/bin check; this is a control-flow improvement, not an established
speed optimization.

Zhenyu also clarified the later timestep figure: bins belong to nodes;
triangles execute at the finest incident-node frequency; frozen nodes
passively receive conserved increments without refreshing their stage
state at that frequency. No timestep-figure or thesis edit was made during
this code-first task.
