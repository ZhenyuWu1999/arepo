# Riemann numerical fluxes as median-dual residual distribution

Date: 2026-10-01. Author: Codex. User request: locate earlier literature supporting
HLLC (or another Riemann solver) in RD and draw an explanatory figure in the
geometric spirit of thesis Figure 3.2. No thesis or solver edits.

## Verified primary references

1. H. Deconinck and M. Ricchiuto (2017), *Residual Distribution Schemes:
   Foundations and Analysis*, Encyclopedia of Computational Mechanics, second
   edition. DOI: https://doi.org/10.1002/9781119176817.ecm2054 .
   Author-hosted PDF: https://team.inria.fr/cardamom/files/2019/10/deconinck-ricchiuto2017.pdf .
   **Section 4.1**, printed pages 13–14, equations (55)–(59), explains finite-volume
   schemes in fluctuation-splitting form. It explicitly uses the median dual,
   subtracts the same-state physical flux, and derives the element sum for a
   linearly interpolated nodal flux. The illustrative dissipation matrix includes
   Roe's absolute-value matrix. Equation (59) is explicitly labelled FV–RD for
   scalar advection. This is the closest reference already used in the thesis.
   The older locally cached text has this discussion in **section 3.6.1**; do not
   give that section number for the verified 2017 second-edition PDF.
2. R. Abgrall (2018; arXiv preprint 2017), *Some Remarks About Conservation for
   Residual Distribution Schemes*, Computational Methods in Applied Mathematics
   18(3), 327–351. DOI: https://doi.org/10.1515/cmam-2017-0056 .
   Open author text: https://arxiv.org/html/1708.03108v3#S4.SS1 .
   Section 4.1, equations (23)–(24), gives the general finite-volume-to-RD
   construction used below. It requires consistency and conservative orientation
   of the numerical flux for these algebraic statements, not a specific solver.
   Section 4.2 treats the converse direction and is not needed to justify this
   specific two-state construction.
3. G. Hu, R. Li and T. Tang (2010), *A robust high-order residual distribution type
   scheme for steady Euler equations on unstructured grids*, Journal of
   Computational Physics 229, 1681–1697. DOI: https://doi.org/10.1016/j.jcp.2009.11.002 .
   Author-hosted PDF: https://www.math.hkbu.edu.hk/~ttang/Papers/HuLiTang10a.pdf .
   Section 2, immediately after equation (5), explicitly states that HLLC flux is
   used in their simulations. This is a genuine HLLC + RD-type precedent, but it
   is cell-centred, high-order reconstructed, steady Euler with a Newton-type
   nonlinear solve. It is **not** evidence for an identical vertex-centred,
   median-dual, moving-mesh Sedov algorithm. The broader literature statement in
   the preceding review should therefore not be read as absence of all HLLC/RD
   literature; the present search found this qualified example.

## Geometry, fluxes, and residuals

First consider a static triangle T with three nodal states U_i. Let n_i denote
its inward, edge-length-weighted opposite-edge normal. The median-dual subcell
S_i intersect T is bounded by node i, the midpoints of its adjacent edges, and
centroid G. For the internal segment Gamma_ij from midpoint m_ij to G, the
normal scaled by its length, directed from subcell i to j, is

    nu_ij = (n_j - n_i)/6,
    nu_ji = -nu_ij,
    sum_(j != i) nu_ij = -n_i/2.

Use a numerical Riemann flux integrated over this segment:

    H_ij = |Gamma_ij| fhat_(nu_hat_ij)(U_i, U_j).

It must obey consistency H(U,U;nu) = F(U).nu and conservative orientation
H(U_j,U_i;-nu) = -H(U_i,U_j;nu). HLLC, HLL, Roe or Rusanov can be used when
implemented with these properties. Define the two assigned fluctuations:

    D_ij^(i) = H_ij - F(U_i).nu_ij,
    D_ij^(j) = F(U_j).nu_ij - H_ij.

These are not just +H and -H. They measure the change from the physical flux
associated with each endpoint state. For equal states both vanish. Geometrically,
the subtracted terms also account for the physical flux on the two outer
half-edges of the median-dual subcell. Thus each element contribution can be
viewed as the balance on that closed subcell.

For a Roe flux without an entropy modification, the same split is the familiar
A_nu^- (U_j-U_i) and A_nu^+ (U_j-U_i), where the Roe matrix includes the segment
length and satisfies the flux-difference identity. HLLC supplies its own
fluctuations; it is not thereby identical to the Roe solver.

Adding the two sides eliminates H:

    D_ij^(i) + D_ij^(j) = [F(U_j)-F(U_i)].nu_ij.

Adding the two contributions reaching each node defines phi_i^T. Adding all
three nodal residuals, with the geometrical identity above, gives

    sum_i phi_i^T = -sum_i F(U_i).sum_(j != i) nu_ij
                 = (1/2) sum_i F(U_i).n_i = Phi^T.

Specifically Phi^T = integral_(boundary T) F_h.n_out ds, where
F_h = sum_i psi_i F(U_i). For nonlinear Euler this nodal-flux interpolant is
not generally F(sum_i psi_i U_i). The equality does not claim that the
trapezoidal physical flux equals an exact nonlinear contour integral or a
Gauss-contour RD residual. The code's optional Gauss correction for blending
is a separate operation.

Assembling over a full static median cell recovers the finite-volume update:

    |S_i| dU_i/dt = -sum_(T containing i) phi_i^T.

The subtracted same-state flux sums to zero around a complete closed median
cell. Physical boundary contributions require the usual boundary treatment.
The flux-to-fluctuation rewriting alone does not establish positivity, high
order, entropy stability, or the N/LDA multidimensional-upwind property.

For the present ALE spatial operator the analogous identity uses
G_T(U)=F(U)-U tensor w_T, with the same triangle velocity used throughout
its pair fluxes and physical flux subtraction. This identifies the spatial
operator in rd_hllc.h; it does not prove the complete moving-time update or
connectivity-change conservation. Triangle mean velocity need not be the
exact normal velocity of every moving median-dual segment.

## Standalone figure and validation

Archive: `../../local_runs/riemann_rd_schematic_20261001_v1/` from this report.

- `plot_riemann_to_rd.py`: original Matplotlib vector drawing.
- `output/pdf/riemann_flux_to_rd.pdf`: one-page vector figure.
- `output/pdf/riemann_flux_to_rd.png`: 200 dpi inline version of the same figure.
- `output/pdf/riemann_flux_to_rd.svg`: editable vector version.
- `geometry_check.json`: inward normals, internal normals, identity check.
- `sources/deconinck_ricchiuto2017.pdf` and `.txt`: verified 2017 author-hosted copy.
- `tmp/pdfs/riemann_flux_to_rd_render.png`: rendered PDF used for visual QA.

Thesis Figure 3.2 was inspected: it has LDA and N two-target geometrical panels,
not the preceding dual-cell geometry figure. The new original drawing keeps
its triangle-and-assignment-arrow explanation, but does not label fixed inflow
or downstream vertices for HLLC. Blue/orange arrows show residual assignment,
not physical flow directions or the signs of vector fluctuations. Other pairs
are shown faintly to explain assembly.

Checked inward-normal closure, correct i-to-j orientation, segment length,
perpendicularity, and the residual identity using arbitrary vector-valued
fluxes and conservative pair fluxes. Maximum absolute sum error: 8.88e-16.
This is an algebra/diagram check, not a numerical-hydrodynamics validation.
PDF rendered with pdftoppm and visually inspected after spacing corrections.
Bundled Python lacks Matplotlib; used the existing 21cmfast environment with
OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=1. No new dependency installation,
no new hydrodynamic run, no thesis edits, no commit or push.

## Follow-up: wave splitting and the nodal update

User asked how the internal split actually connects to the Riemann solver and
changes a vertex state. Clarification: both H_ij and F_i.nu_ij are integrated
normal fluxes; their essential difference is the two-state Riemann numerical
flux versus the single-state physical flux. H_ij is not obtained by integrating
the original continuous P1 interpolation F(U_h) across the internal segment.
The low-order construction sets up a local two-state problem on the median dual.

For a conservative HLLC fan, define W_L=U_*L-U_i,
W_*=U_*R-U_*L, W_R=U_j-U_*R, with speeds S_L,S_*,S_R.
In static, consistently oriented coordinates,

    D_i = ell sum_p min(S_p,0) W_p,
    D_j = ell sum_p max(S_p,0) W_p.

The waves propagating into the i/j side determine its fluctuation. This is the
standard wave-propagation representation of conservative Riemann solvers:
https://www.clawpack.org/v5.9.x/wp_algorithms.html . It does not imply a fixed
Roe matrix for HLLC. A static forward-Euler illustration of nodal assembly is

    U_i^(n+1) = U_i^n - dt/|S_i| sum_(T containing i) phi_i^T,
    phi_i^T = sum_(j in T, j != i) D_ij^(i).

For scalar advection with alpha=a.nu_ij>0 and exact upwind flux H=alpha*u_i,
D_i=0, D_j=alpha*(u_j-u_i). The contribution of this interface alone is
Delta u_j=dt*alpha/|S_j|*(u_i-u_j), with no contribution to u_i.
Other interfaces still contribute to both nodes. This supplies an elementary
interpretation of the downstream state moving towards the upstream state.
HLLC's acoustic and contact waves can instead affect both sides of a pair.
The formula above illustrates the static spatial operator, not the full native
ALE lumped-RK2 update with changing geometric coefficients.

On a complete closed static median cell the subtracted same-state fluxes sum
to zero, recovering the FV update. Therefore conservation of the triangular
total alone does not identify the Riemann solver: changing H by delta H adds
+delta H to D_i and -delta H to D_j while leaving the element sum unchanged.
No thesis or solver edits, no additional numerical runs.

## Direct comparison with the 2017 review

User asked whether Deconinck–Ricchiuto2017 can be the theoretical justification
for Claude's implementation. Yes, specifically for the **spatial FV–RD
construction**. In the static limit the current low-order operator instantiates
the same median-dual geometry, same-state flux subtraction and conservative
nodal residual assembly, not merely a visually similar analogy.

The key reference is section4.1: geometric identity(55), the unnumbered general
flux-subtraction formula immediately following it, and the element sum after
(57). Equations(56)–(57) illustrate a central-flux/dissipation-matrix family;
the code evaluates HLLC fluctuations directly and need not construct that
matrix or identify HLLC with the Roe example. The implementation's matching
lines are rd_hllc.h:133–191, especially 173–184. Substituting w_T=0 gives the
static construction. Triangle-mean velocity is supplied by the caller in
residual_distribution_solver.c around4495–4507.

Differences and their citation implications:

- The review's derivation is presented using scalar notation and followed by
  a scalar upwind example; it explicitly states that the analogy extends to
  nonlinear problems and systems. Four-component Euler therefore preserves
  the algebraic construction. Scalar LED/positivity/energy-norm stability
  conclusions are not an automatic proof of Euler density/internal-energy
  positivity or entropy stability.
- HLLC is our chosen two-state flux; the review does not present this particular
  HLLC implementation. Cite the review for FV–RD and HLLC literature for the
  approximate Riemann solver. No claim of reproducing a published HLLC–ALE–RD
  algorithm is needed.
- This section's fixed-mesh semidiscrete correspondence does not specify our
  triangle-mean moving-frame flux, ALE geometric weights, lumped RK2 stages,
  or Delaunay flips. The element identity persists with a common G_T, but full
  moving-grid budget conservation requires the separate geometry/time/topology
  reasoning and numerical evidence. The review as a whole also discusses
  time-dependent methods and mentions ALE; do not describe the entire review
  as scalar-only or as having no moving-grid discussion.
- Both constructions use the nodal-flux/trapezoidal element total. The present
  HLLC branch remains spatially first order and does not inherit N/LDA's strict
  multidimensional-upwind or linearity-preserving properties.

Suggested short thesis description (discussion draft, not inserted):

"Following the finite-volume residual-distribution construction described by
Deconinck & Ricchiuto (2017), we evaluate HLLC numerical fluxes across the
internal median-dual interfaces of each triangle and distribute the associated
fluctuations to its vertices. The resulting nodal residuals sum to the element
residual. We incorporate this spatial discretisation into the ALE time-integration
framework described above."

Add one sentence distinguishing pairwise Riemann upwinding from N/LDA if the
surrounding thesis text otherwise suggests their multidimensional property
carries over. This attribution is sufficient to ground the construction without
a lengthy new derivation; a short definition and element-sum identity make the
application transparent. No thesis/solver changes or new tests in this follow-up.
