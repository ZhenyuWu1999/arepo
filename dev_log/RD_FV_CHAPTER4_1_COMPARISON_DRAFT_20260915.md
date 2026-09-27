# Chapter 4.1: numerical properties of FV and RD

2026-09-15 · Revised by Codex following Zhenyu's review.
**Updated in Chapter 4.1.1 after Zhenyu's comparison-prose draft at thesis
commit b013be7. The former computational-elements row is now separated into
fluid-state storage, control volume and flux/residual evaluation.**

## Table inserted in the thesis

**Caption:** Comparison of the numerical ingredients of the two-dimensional
AREPO-FV and RD discretisations. Storage, control volumes and flux or residual
evaluation are distinguished explicitly. Second-order accuracy refers to
spatial accuracy for smooth solutions.

| Property / numerical role | AREPO-FV | RD |
| --- | --- | --- |
| Fluid-state storage | One record per mesh-generating point (Delaunay vertex / Voronoi generator): `P[i]` and `SphP[i]` | Same (the thesis merges these two cells) |
| Control volume | Voronoi cell | Median dual cell |
| Flux / residual evaluation | Flux exchange across Voronoi faces | Residual of each Delaunay triangle distributed to its vertices |
| Solution representation | Cell averages with piecewise-linear reconstruction | Nodal states with continuous $P^1$ basis functions |
| Conservation | Shared interface fluxes applied with opposite signs | Conservative distribution of each element residual to its vertices |
| Upwinding | Face-normal Riemann solvers | Multidimensional characteristic residual distribution |
| Second-order spatial accuracy | Linear spatial reconstruction | $P^1$ basis functions combined with the linearity-preserving LDA scheme |
| Positivity / oscillation control* | Slope limiting | N scheme |
| Accuracy–robustness balance | Nonlinear slope limiting according to local smoothness | Nonlinear blending of N and LDA residuals (B scheme) |

**Table notes:**

- Second-order accuracy refers to spatial accuracy for smooth solutions with
  a suitable consistent discretisation. Linear basis functions alone do not
  establish the order of an RD scheme; the residual distribution also matters.
- *The positivity row identifies stabilising ingredients. Slope limiting or
  the N scheme alone does not establish unconditional density and pressure
  positivity for the Euler equations. The scalar N scheme is positive under
  its CFL restriction; Euler admissibility must be assessed for the complete
  method.*

## Editorial recommendations

Conservation, upwinding and the accuracy–robustness balance complement the
requested accuracy and positivity comparison. The last row introduces the B
scheme and explains how RD combines the roles of N and LDA. It describes the
purpose of blending, without asserting that every blend guarantees both
second-order accuracy and positivity.

The solution-representation row gives a short orientation; it can be omitted
if the surrounding paragraph already defines cell averages and nodal values.
Use **Second-order spatial accuracy**, rather than an unqualified
**Second-order accuracy**. No temporal-order claim is made by this table.

The three geometric/storage rows distinguish the shared record index from
the numerical meaning of that record and the objects used to evaluate its
update. The shared mesh point is a **Delaunay vertex**, or **Voronoi
generator**, rather than the generally distinct Voronoi cell centroid.
Mass is stored in `P[i].Mass`, with momentum, energy and hydrodynamic
primitives in `SphP[i]`; `SphP[i]` alone is therefore not the complete state
storage. RD's median-dual weight is the sum of one third of each incident
triangle area, and is generally different from the Voronoi cell area.
Time integration, hierarchical timesteps,
inactive-node handling, MPI and mesh motion remain outside this table. The earlier implementation-focused draft is archived at
`../../local_runs/rd_fv_property_table_20260915_v1/previous_comparison_draft.md`.

Avoid separate rows claiming universally lower diffusion, faster execution,
entropy stability or exact angular-momentum conservation: these would need
method-specific evidence. The LDA/N diffusion contrast is already reflected
in the accuracy–robustness row. Likewise, face-normal Riemann solves do not
imply that the complete AREPO-FV update is dimensionally split.

## Basis for the comparison

- Existing Chapter 3: nodal interpolation; N-scheme scalar positivity and its
  timestep restriction; LDA linearity preservation; nonlinear blending; the
  discussion preceding the Yee convergence test.
- [Original FV/RD comparison](AREPO_FV_RD_comparison.md), Sections 1.1 and 3.3.
- [Springel (2010), Section 3.1](https://arxiv.org/pdf/0901.4107): linear
  reconstruction and slope limiting. The described limiter bounds
  reconstructed face values but is not claimed to enforce strict TVD.
- [Pakmor et al. (2016), Section 4](https://arxiv.org/pdf/1503.00562):
  the importance of gradient estimation on irregular meshes. Its existing
  bibliography key is `Pakmor_Improving_2016`; no bibliography edit was needed.
- Current native storage: `src/hydro/residual_distribution_solver.c`,
  `rd_ale_q_from_particle` (line 1671), `rd_rk2_save_stage0` (line 3448),
  and the median-area accumulation (line 3072). FV's distinct centroid is
  used in `src/mesh/voronoi/voronoi_gradients_lsf.c` (line 206).
- [Morton et al. (2023), Section 2.2.3](https://academic.oup.com/mnras/article/518/3/4401/6847219):
  conservation, multidimensional distribution, LDA, N and nonlinear blending.
- [Current implementation qualifications](RD_STATIC_BASELINE_CHAPTER4.md):
  keep empirical convergence and Euler positivity claims separate from the
  conceptual roles in the table.

The initial seven-row table and subsection structure were inserted on
2026-09-15 (log3 §57). Zhenyu subsequently committed a revised flowchart at
6777107 and the comparison-prose draft at b013be7, renaming Section 4.1 to
“Static Mesh RD in AREPO”. The current edit (log3 §60) completes only the
comparison prose and expands the table to nine rows. It explains shared
storage, distinct control-volume weights, local conservation and upwinding,
and the roles of reconstruction/LDA, slope limiting/N and nonlinear B
blending. The user's AREPO introduction remains their draft, including its
project-list placeholder; the flowchart, efficiency subsection and all later
material are preserved byte for byte.

Initial insertion source and validation archive:
`../../local_runs/thesis_section41_table_20260915_v1/`.

Current completion archive:
`../../local_runs/thesis_comparison_completion_20260915_v1/`.
It holds the original and proposed Chapter 4, the previous version of this
report, tracked-file hash manifests, the exact patch and an isolated full
XeLaTeX build (exit 0, 237 pages). Table 4.1 is on page 141; the unchanged
landscape Figure 4.1 is on page 142. The six-page review PDF covers pages
138--143 and was rendered and inspected. There are no unresolved references
or new overfull boxes in the comparison section; unrelated existing warnings
remain. Only `chapter4/chapter4.tex` changed among 124 tracked thesis files.
No solver or configuration change; no commit or push.
