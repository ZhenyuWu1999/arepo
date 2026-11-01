# Cuillin handoff: recover the Morton Blob run provenance

2026-11-01 (Europe/London) - Codex (GPT-6), with Zhenyu Wu; local Mac.

**Next priority: look for Morton's original Blob snapshots, run-specific code
and Figure 20 analysis on Cuillin.** A recovered physical-time/plot-coordinate
pair and the actual analysis script can test the clock hypothesis directly.
Agreement after an arbitrary time rescaling does not identify its cause.

This is a planned evidence-recovery task. No Cuillin connection, file search,
build or simulation is performed while writing this handoff. The existence
and location of the original publication artifacts on Cuillin are unverified.
The local checkout is `feature/3d-moving-mesh`, starting at `c92f0b5`; the
downloaded native runs retain source `35ecccd` provenance. This publication
contains plotting/analysis and documentation changes, not a new hydro method.

## Current evidence

| Item | Established evidence | Limit |
| --- | --- | --- |
| Current Blob runs | N/lumped RK2, static 32^3 random nodes, 140 initial cloud nodes; equal/hierarchy, eight MPI ranks; both finish 1.5 t_cr = 3 t_cc | These are the previously downloaded runs, not an audit of later COSMA campaigns |
| Saved-state checks | 31 states per run; normalized extensive conservation <=8.430e-14 equal and <=3.681e-14 hierarchy; positive states and fixed median duals | Saved states do not supply a fresh audit of all omitted native stages |
| Current hierarchy comparison | Endpoint relative volume-weighted density L1 difference 8.265e-6; nearly identical cloud-mass histories | The current lifetime gap is present with equal steps too |
| Available predecessor | Local `/Users/zhenyuwu/rdsolver`, source `adfbe55586fc`; analytic BLOB state agrees on the current nodes, and initial spatial N residuals agree on all 221713 current tetrahedra to the recorded tolerance | This does not recover the publication run's points, mesh, binary or settings |
| Short update control | Four current native RK2 steps agree with an independent Heun update at roundoff | It does not establish long-time equivalence with the publication's N1 run |
| Published comparison | Twenty vector-path vertices digitized from the red 32^3 N1 curve in Figure 20; original axis and tick calibration checked | Curve coordinates are not original snapshot measurements |
| Cloud criterion | rho>0.64*rho_cloud,0 AND T<0.9*T_wind,0, inherited from Agertz; native extensive masses and initial selected-mass normalization | Eulerian selected gas, without a material tracer; the temperature cut removes no extra nodes in these 62 saved states |
| LDA | The earlier downloaded LDA runs fail raw negative-pressure checks and have no evolved saved states | They are not a completed counterpart to the N1 mass comparison |

Details remain in [the independent analysis](RD_3D_BLOB_COSMA_ANALYSIS_20261020.md),
[the N1 diagnosis](RD_3D_BLOB_N1_DIAGNOSIS_20261020.md), and shared-log entries
21--25 and 27--34. Native moving 3D remains unfinished; the provenance task
does not alter the mesh/hierarchy/MPI development priorities.

## Selected figures and clock status

The latest two Blob figures are in
`dev_log/figures/rd_3d_blob_reference_20261022_v4/`:

- Hierarchical N/RK2 density slices at the actual z=5 plane, with P1-Z
  tetrahedral reconstruction and approximately 0, 1, 2, 3 t_cc.
- One mass panel with four curves: current equal/hierarchy, the original
  digitized Morton coordinate x_p multiplied by 1.6*2, and x_p multiplied
  by 1.6. The latter has the user-requested label
  `Morton with artificial halt timescale`. It is an artificial half-timescale
  display, not a corrected physical clock. There are no fitted parameters.

The definitions used in the records are

```
t_cc = R_cloud*sqrt(chi)/v_wind             # radius-based figure clock
t_cr = 2*R_cloud*sqrt(chi)/v_wind = 2*t_cc  # Morton equation 54
t_KH = 1.6*t_cr = 3.2*t_cc                # stated Figure 20 clock
```

For R=1, chi=10 and v_wind=6.15, these are respectively
0.5141914894582731, 1.0283829789165462 and 1.645412766266474 in code time.
Current output ends at 1.5425744683748193 = 0.9375*t_KH. The current equal-run
half-mass time is about 0.404206*t_cr, while the traced reference half-mass
coordinate is about 0.706769 in its published t/t_KH label. The printed
definitions are self-consistent, but that alone cannot verify the original
figure-generation chain. The earlier fitting exercise is archived history;
Zhenyu explicitly declines fitted factors as meaningful evidence.

## What to find on Cuillin

Begin with a bounded, read-only inventory of Zhenyu's accessible source,
analysis and run archives. Historical leads are `/home/zwu/rdsolver/` and
`/home/zwu/Hydro_data_analysis/`; confirm their existence and symlink targets
on Cuillin rather than assuming the Mac or historical layout applies. Look
for alternate source copies, paper-era Git refs and untracked analysis files,
not only the current repository. The Mac's available Git history lacks the
Figure 20 cloud-mass plotter. Inventory filenames/sizes first, before reading
large snapshot collections. Shared/group archive locations must be established
from accessible project records; do not assume access to another user's home.

Recover and record these artifacts together:

1. **Original run outputs:** preferably start with the 32^3 N1 case. Preserve
   several original snapshots including the initial state, physical-time
   headers, run log, output schedule and any cloud-mass tables. Do not infer
   physical time from snapshot index times an assumed output interval.
2. **Actual source/build:** run-specific source revision and local diff,
   constants/header, compiler/build records and binary checksum if available.
   Verify N scheme, FIRST_ORDER/time integration, DRIFT/JUMP or other scheduling,
   CFL, floors/repairs and boundary settings. A current template is not proof
   of a publication binary's flags.
3. **Figure 20 analysis:** script/notebook, data arrays and saved figure source
   for the correct red 32^3 N1 trace. Check physical units and every time
   multiplication/division, including any duplicated preprocessing step.
4. **Original IC/mesh:** coordinate file and tetrahedral connectivity or
   generator/triangulation recipe, RNG implementation/seed, actual cloud-node
   count, median duals, domain, radius and center. Matching a seed number is
   insufficient across different generators or precomputed coordinate files.
5. **Mass selection/weights:** initial cloud and wind reference quantities,
   temperature convention, inequalities, extensive mass versus density,
   median-dual/other quadrature and initial normalization. Reproduce the exact
   published diagnostic before comparing alternate cuts.

For each candidate, record execution host/date, original path, sizes, source
revision/diff and checksums for the selected files. Distinguish a related test
or later code copy from an artifact demonstrably used for the paper. Preserve
originals; keep large snapshots and binaries outside Git. Commit compact
inventories/provenance and independently recomputed diagnostics.

## Checks that can resolve the discrepancy

First pair several nonzero original physical times T with their actual
Figure 20 plotted coordinates x_p. Using the recovered IC parameters, compute
`a = x_p / (T/t_cr)` and inspect the analysis path. The stated KH conversion
gives a=1/1.6; an unconverted crushing-time axis gives a=1; multiplication
instead of division gives a=1.6. Also check radius/diameter factors and code
units directly. Use actual paired samples, not a coefficient chosen to align
the two mass-decay curves.

Then recompute selected cloud mass from the original snapshots with the
original weights and the stated criterion, and reproduce the published curve
without fitting. Compare analytic primitive states and actual point/mesh
realizations separately. If the clock and diagnostic are verified but the
gap persists, stage a controlled original N1/current N-RK2 comparison with
the same IC/mesh, measured timestep and admissibility checks. Separate time
integration, timestep sensitivity, point sampling and spatial representation
before attributing the result to extra numerical dissipation in the port.

Completion of the recovery stage means a documented source-to-run-to-plot
chain, or a precise inventory of what remains missing. Lightweight inventory
can use the login node; compilation, substantial snapshot analysis and any
new simulation must use Cuillin compute resources under the existing rules.
No new campaign or original-data discovery is claimed by this handoff.
