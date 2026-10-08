# Independent review of Claude's HLLC-RD Sedov work

Author: Codex, 2026-10-01. Requested by Zhenyu Wu. No thesis or solver edits.

## Assessment

The archived Sedov improvement is reproducible. The low-order spatial operator
is an HLLC finite-volume fluctuation split on median-dual segments, embedded in
the existing ALE-RD geometry/time-update infrastructure. It belongs to the broad
RD framework, but is not the N/LDA multidimensional-upwind construction. It is
not evidence that the N/LDA distributions now survive this strong blast.

This distinction is substantive, not determined by whether the implementation
loops over triangles or faces. Under `RD_RUSANOV_LOW_ORDER` plus
`RD_LOW_ORDER_HLLC`, the stage loop calls `rd_hllc_residual` and skips the
Roe/K-matrix assembly in the `#else` branch (current solver around lines4499–4531).
The `N_SCHEME` configuration flag therefore does not make these results N-scheme
results. Spatial first order is retained despite the two RK stages.

## What was checked

Archive: `../../local_runs/hllc_rd_review_20261001_v1/`.

- Independently reread 40 HDF5 snapshots for eight RD/MMFV cases. All hashes
  match the saved metadata; the sampled densities, pressures, masses and
  internal energies are positive. Recomputed total mass/energy, radial-bin
  density peaks, core density and pressure match the original table.
- Verified the HLLC campaign's source tar, its three archived binaries/configs
  and its recorded IC/parameter hashes. The production root binary was not used.
- Reran the existing 4000-case C-kernel test with the actual archived HLLC header
  and the subsequently corrected test normals. Conservation defect 1.64e-16,
  independent HLLC comparison 1.06e-12, Galilean covariance 2.93e-12, relative
  to the test flux scale. CFL-limited forward states remained admissible;
  uniform and stationary-contact checks passed. These are kernel tests, not a
  moving-connectivity theorem or a new native hydrodynamic run.
- The current header differs from the tested native source by the later,
  separate `rd_hllc_gauss_edge_split` function for the experimental blend. The
  low-order pair and element kernels are unchanged. The full current solver
  differs and was not assumed to be the frozen native source.
- Inspected the profile plot and the eight-run density-map comparison.
- Native budget components were summed from the two moving HLLC run logs.

The bundled Python could run the NumPy-only kernel test but lacks h5py.
Snapshot analysis used the existing `21cmfast` environment; a Python-version
compatibility change to the review script's hashing routine was required.
Neither issue was a solver/test failure.

## Recomputed comparison

Same nominal Sedov setup: 128² initial points, unit periodic box, gamma5/3,
p0=1e-6, thermal injection E=1, 21 heated points, t=.05. The RD initial data
are shared by HLLC/Rusanov. FV uses Voronoi-volume energy normalization and
cell-centre sampling, so the cross-method comparison is not a strict
flux-only ablation. All methods use global adaptive timesteps; their actual
step sequences differ.

| Method | Number-mean radial density peak | Area-mean core density, r<.05 | Core samples | Mass drift | Energy drift |
|---|---:|---:|---:|---:|---:|
| Moving Rusanov RD | 2.428023 | .197703 | 3 | −.239707% | −2.414700% |
| Moving HLLC split | 2.979900 | .027639 | 4 | −.328961% | +.698093% |
| Static HLLC split | 2.327823 | .030868 | 130 | roundoff | roundoff |
| Moving MMFV, first order | 3.098843 | .027557 | 4 | roundoff | roundoff |
| Moving MMFV, second order | 3.302425 | .029976 | 4 | roundoff | roundoff |

Single-point moving HLLC also completes: density peak2.998906, core density
.003264 (one sample), mass drift−.335283%, energy drift−1.606341%.

The peak increase and reduced core mixing are clear. Core values are supported
by very few moving nodes, so matching to three decimals is not evidence of
high-precision continuum-core accuracy. A finite heated mass also differs from
the point-injection similarity solution. The entropy argument provides a useful
interpretation of that plateau, rather than an exact test of the point-source
limit at this one resolution.

## RD versus FV classification

For inward triangle normals n_i and triangle-mean mesh velocity w_T, define

    nu_ij = (n_j - n_i)/6,
    G(U) = F(U) - U tensor w_T,
    phi_i^T = sum_(j != i) [H_HLLC(U_i,U_j;nu_ij) - G(U_i).nu_ij].

Antisymmetry of the numerical flux and sum_(j!=i)nu_ij=−n_i/2 give

    sum_i phi_i^T = (1/2) sum_i G(U_i).n_i = Phi^T.

This is a legitimate conservative distribution of a nodally interpolated flux
residual. Abgrall's primary paper explicitly constructs median-dual FV in RD
form in §4.1, Eqs23–24:
https://arxiv.org/html/1708.03108v3#S4.SS1

The reverse representation also exists for general RD, so having *some* flux
form does not by itself disqualify a multidimensional RD method. Here the
distinguishing fact is that the actual construction uses only two states for
each directional Riemann solve, and bypasses the element characteristic
distribution used by N/LDA. The triangle total being conservative does not
restore the strict multidimensional-upwind property.

An independent compiled probe illustrates this. On triangle(0,0),(1,0),(0,1),
use rho=(1,1,3), v=(1,0), p=1 and a static mesh. This is a stationary entropy
gradient transverse to the flow; total element residual is zero. The HLLC
density residuals are approximately(0,−1/3,+1/3). Scalar advection coefficients
are k=(−1/2,+1/2,0); the zero-k vertex still receives an entropy-wave residual,
unlike the N/LDA distribution for this configuration. This shows transverse
numerical diffusion and failure of linearity preservation here. It does not
contradict membership in the broad RD family, nor imply that all other RD
schemes preserve every stationary linear field.

For a static mesh, assembling this spatial operator gives the median-dual
vertex-centred FV flux balance. For a moving mesh the code retains its own
triangle-mean velocity, modified divisor, RK stages and connectivity treatment;
it is not identical to an arbitrary standard moving-control-volume FV update,
and certainly not to AREPO's reconstructed Voronoi-face update.

Suggested description:

> An HLLC-based, spatially first-order finite-volume residual distribution on
> the median dual mesh, integrated within the ALE-RD framework.

## Statements to tighten in Claude's account

1. **Remaining difference is not proved to be solely spatial order.** The
   summary at lines362–365 attributes the remaining gap to second-order MMFV
   entirely to order. The first-order MMFV control supports order as an
   important contributor, but geometry, mesh motion, reconstruction, timesteps
   and conservation treatment also differ. Use “consistent with a substantial
   contribution from first-order spatial dissipation”.

2. **Global conservation is still not established.** Local sum_i phi_i=Phi
   and successful positivity checks are real, but neither cancels the moving
   representation/geometry defects. The 21-point and single-point energy
   drifts differ in sign; HLLC does not generally fix the budget.

   Summed native energy components (initial E≈1):

   | Injection | temporary_change | finish rebase_change | endpoint_change |
   |---|---:|---:|---:|
   | 21 | +.00690507 | +.000075875 | +.00698094 |
   | 1 | −.01621934 | +.000155913 | −.01606343 |

   The finish conversion is a small net contribution. However the logged
   `temporary_change` is final temporary total minus the old physical total;
   it includes preparation and stage updates. It is not a measurement of
   edge flips alone. A separate patch/flip accounting or controlled repair
   comparison is needed to quantify that attribution. The topology mechanism
   remains a well-motivated explanation, not isolated by this table.

3. **Averaging labels must be specific.** Summary§5.1 combines
   “binned/mass-weighted” in one heading. The original quoted peaks use
   unweighted means in radial bins of width.005. Recomputed mass-weighted peaks
   are2.982195 for HLLC,3.090429 for MMFV1 and3.289389 for MMFV2, versus the
   number-weighted2.979900,3.098843,3.302425. Core density is total selected
   mass/selected area, i.e. area-weighted density. The `core_rows` docstring
   incorrectly calls this mass-weighted; the numerical calculation is correct.

4. **Do not present HLLC as Roe in one dimension.** The thesis draft at
   lines95–99 says it reduces to the fluctuation splitting of Roe's solver.
   It retains the same general fluctuation-splitting form, but its actual
   one-dimensional numerical flux is HLLC, not Roe. Similarly A±DeltaU should
   not silently be identified with the previously defined Roe spectral
   matrices. HLLC fluctuations can instead be denoted D− and D+.

5. **The failed LDA run was Gauss3/F1.** The thesis draft's statement that
   both failed schemes used the Roe-linearised residual is too broad. The
   pilot report specifies N/Roe/lumped and LDA/Gauss3/F1. LDA still uses Roe
   characteristic weights, but that does not make its Gauss3 contour residual
   the Roe residual or establish a single cause of failure.

6. **Positivity and contact qualifications matter.** The kernel checks both
   HLLC star states and aborts if they are inadmissible; stage admissibility
   is conditional on the verified CFL/convex weights. For the zero contact
   residual statement one needs common fluid velocity equal to w_T and common
   pressure. Merely having each vertex follow its own, differing fluid velocity
   is insufficient. The present experiment supports robustness on these blasts,
   not unconditional positivity/conservation for arbitrary moving meshes.

7. **Faceting remains causally unresolved.** Similar RD faceting for1,21,130
   hot nodes and a rounder first-order MMFV front show that low order/injection
   size alone do not explain it. They do not eliminate all interactions with
   injection shape or mesh sampling. SWIFT faceting without flips likewise
   prevents assigning every polygonal pattern to edge flips.

## Recommendation for the thesis

The result is useful evidence that the framework accepts an alternative
low-order distribution capable of completing strong shocks with less mixing
than scalar Rusanov. It can be presented transparently as an FV-derived
extension or a prospective low-order part of a limited high-order scheme.
It should not be used as the Sedov validation of the N/LDA algorithms introduced
earlier, as proof of their multidimensional advantage, or as a claim that the
experimental LDA/HLLC blend is already successful.

The existing N/LDA vortex results retain their meaning. The HLLC result supports
the extensibility of the framework, while its moving conservation and mature
high-order blending remain separate work. No thesis insertion was performed.
