# 4.2 follow-up: singular residuals, Arpaia §6, and the requested wording edit

2026-09-26; Codex; requested by Zhenyu. This supplements the earlier
[4.2 review](RD_THESIS_42_MATH_REVIEW_20260926.md), without replacing its historical record.

## 1. What the pseudoinverse does to Roe and Gauss targets

Compare the spatial LDA distributions on identical states, common Roe matrices,
geometry and mesh velocity. Let K_i denote the ALE matrices in this section,
S^-=sum K_i^-, P=S^-(S^-)^dagger, and D_i=-K_i^+(S^-)^dagger.
The exact split identity gives

\[
\sum_i D_i\Phi=P\Phi.
\]

The inverse is replaced by the *same* pseudoinverse for both targets. The essential
difference is the right-hand side, not the choice among multiple compatible solutions.

For the pure characteristic target Phi_char=sum K_i Uhat_i, the common physical
Roe system at exact mesh-relative stagnation supplies a compatible RHS. Hence
P Phi_char=Phi_char. An intermediate solution need not be unique, but K_i^+
annihilates the common kernel, so the distributed residuals are unique.

The independent nonlinear P1-U contour Phi_G need not belong to the same range.
When it does not, the pseudoinverse provides a least-squares solution and drops
(I-P)Phi_G from the sum of the nodal residuals. Accurate quadrature does not
establish compatibility with a separately averaged Jacobian.

If Phi_G=Phi_char+deltaPhi, then

\[
\phi_{i,G}=\phi_{i,char}+D_i\delta\Phi,
\qquad
\sum_i\phi_{i,G}=\Phi_{char}+P\delta\Phi.
\]

Thus the projected contour is **not generally the Roe residual**: the part of
deltaPhi inside the range remains. Full rank gives P=I for either target.
Exact-rank algebra is distinct from floating-point rank selection; near-singular
Roe solves can still incur rank-threshold/cancellation errors.

### Matched example

Use the prior review's triangle (0,0),(1,0),(0,1), gamma=7/5, sigma=0,
rho=p=1 and velocities (1,0),(0,1),(-1,-1). Hbar=25/6 and rank(S^-)=3.

| Quantity | rho residual | x-momentum | y-momentum | energy |
| --- | ---: | ---: | ---: | ---: |
| Pure Roe target | -1 | 0 | 1/14 | -25/6 |
| Sum after its LDA pseudoinverse | -1 | roundoff | 1/14 | -25/6 |
| G3 target | -1 | 0 | 1/10 | -257/60 |
| Sum after its LDA pseudoinverse | -1.02647503782 | roundoff | 0.1 | -4.27697932426 |

G3 is exact in this constant-density example because the edge flux has degree
at most three. The target's left-null component is -7/60; this is not quadrature
or roundoff error. The Roe sum defect is 8.88e-16, the Gauss sum defect 0.0264750.
This is one independent element calculation, not a hydro accuracy comparison.

### Essential qualification for the current *moving* Roe residual

The current Roe split has an additional vector

\[
\Phi_{Roe}=\Phi_{char}+C_T,\qquad
C_T=-\int_T\sigma_h\cdot\nabla(U_h-\widehat U_h)\,dA.
\]

Compatibility of Phi_char does **not** imply compatibility of C_T. Therefore it
would be wrong to generalize the prior Chapter 3 statement into “moving Roe is
always compatible, only Gauss can be incompatible.”

In the current N reference, solve S^- Uhat_in=sum K_j^- Uhat_j, then add C_T/3
to each node. That explicit correction is outside the pseudoinverse and recovers
the total Phi_char+C_T if the characteristic inflow solve is compatible.

In the legacy LDA/Roe option, the whole corrected target is the LDA RHS; its
nodal sum is P(Phi_char+C_T), so a component of C_T may be lost. This also has
an explicit counterexample: boost the above fluid by b=(0,1) and translate the
mesh with sigma=b. Relative Roe velocity remains zero. Here

\[
C_T=(0,0,0,-1/14)^T.
\]

The pure ALE characteristic LDA sum still closes to 8.88e-16, while sending the
corrected Roe total through LDA produces a maximum defect 0.0169578623. The
current N distribution, with C_T/3 added afterwards, closes to 1.05e-15.
This is not evidence that changing the production residual is warranted.

Source checks in `src/hydro/residual_distribution_solver.c`:

- 4596–4602 assemble the mesh correction into the Roe target;
- 4731 supplies Phi as the LDA RHS, and 5051 uses the rank-revealing solve;
- 5099–5149 construct/check the LDA sum;
- 5188–5208 add C_T/3 directly to N contributions;
- 5213 onward separately reconcile the experimental N/contour option.

The current moving LDA reference has no general spatial complement. Its A2
check detects a failure; it does not repair it. The static common-beta optional
completion is a different configuration. F1 temporal RHS compatibility is a
separate issue for either spatial residual; its rank-deficient lumped fallback
does not repair an incompatible spatial target. Changing internal coordinates
cannot turn an exactly inconsistent linear system into a consistent one.

## 2. What Arpaia §6 does and does not provide

Primary source: Arpaia, Ricchiuto & Abgrall, J. Sci. Comput. 63 (2015), 502–547,
DOI 10.1007/s10915-014-9910-5. The local final journal PDF is authoritative for
the equation/page numbers here. The online author-posted research-report version
was also checked; its equation numbering differs.

The user's clarification is correct: the detailed ALE derivation in §§2–4 is
mostly scalar. The earlier reply was too brief about the distinction between
the completeness of the PDE system and the completeness of its derivation.

- §6, Equations 87–88 (printed p.524), specifies rho, rho*u, rho*v, rho*E,
  the nonlinear Euler fluxes including pressure and enthalpy flux, and the
  ideal-gas closure continued on p.533. This is the full compressible ideal-gas
  Euler system, not linear acoustics, passive advection or isentropic Euler.
- §6.1, pp.533–534, gives a short *formal extension*: scalar residuals become
  vectors, inflow parameters become characteristic matrices, positive/negative
  splits use eigendecomposition, and nonlinear limiting/blending uses
  characteristic components. It refers implementation detail to refs.14,24,35,36.
  It does not rederive all moving-Euler formulas in Roe parameter-vector notation.
- §6.2 is an implemented Euler calculation, with a smooth vortex, a nonlinear
  two-dimensional Riemann problem, and a Mach-3 moving-wall wind tunnel. The
  latter two contain shocks/contact or shock-expansion interactions. Simplicity
  of a test setup does not turn its governing Euler system into scalar equations.
- §7 explicitly leaves rigorous positivity analysis open even for the scalar
  scheme. The paper therefore should not be cited as a complete system-level
  positivity/stability proof for our particular implementation.

### Comparison with our construction

| Aspect | Arpaia paper | Current thesis/reference |
| --- | --- | --- |
| PDE | Full 2D compressible perfect-gas Euler in §6 | Same physical system within the gas-only, non-cosmological scope |
| Derivation detail | Scalar ALE/RK construction, then brief characteristic-matrix extension | Explicit U, Z, Uhat distinction and the mesh-transport correction for the mixed Roe/P1-U representation |
| Spatial total | §3.3.1 explicitly permits direct contour integration or an exact mean-Jacobian linearization | Explicit N/Roe+correction and LDA/G3 conservative-state contour choices |
| What §6 specifies about reconstruction | It does not spell out enough to identify its Euler contour quadrature, Roe parameter averaging and mesh correction with ours | These interpolation and integration choices are written out |
| Time/geometric construction | Midpoint geometry, modified dual area, F1, global/selective lumping | The selected Arpaia global-lumped two-stage structure; mixed-stage beta and singular temporal fallback are implementation choices requiring their own validation |
| Mesh motion | First two Euler tests prescribe sinusoidal deformation; wall case uses Laplace smoothing driven by boundary motion | AREPO generator velocities, flow following and regularization, with Delaunay connectivity rebuilt |
| Connectivity | Continuous deformation of the triangulation in this construction | Changed connectivity plus endpoint storage requires additional accounting |
| Singular matrices | No explicit pseudoinverse/range/fallback treatment found in §6 | Explicit rank-revealing solves, spatial assertion, separate F1 temporal fallback |

Crucially, contour integration is not absent from Arpaia's framework. Its §3.3.1
lists it explicitly, so “Arpaia=Roe, ours=Gauss” cannot be asserted from §6.
The defensible difference is the specificity and choices of the Euler construction,
the mesh regime and the AREPO implementation, not whether Euler was solved at all.

Suggested interpretation for the thesis introduction (not installed): the main
derivation is presented for scalar conservation laws, and its extension to the
Euler system is described briefly using characteristic matrices and existing RD
literature. Our work specifies the choices needed for the selected AREPO scheme.
The phrase “instead of the complete Euler equations” still does not express that
distinction accurately.

## 3. Authorized wording change

Replaced the one occurrence in chapter4.tex line454:

`the geometric source term is absorbed into the median dual cell.`

with

`the geometric source term is absorbed into the modified dual-area coefficient.`

Only this phrase was changed; all other source bytes are preserved. The other
128 tracked/snapshotted files including master.pdf retain their hashes. No other
thesis prose, singular-matrix discussion or Scope subsection was edited.
No compile was run for this plain-text substitution; no equations, labels or
LaTeX commands changed. No commit/push/Overleaf sync or hydro runs.

Archive: `../local_runs/chapter4_2_followup_20260926_v1/`, containing exact
before/after text, patch, hashes, installation check, independent matched-residual
calculation and JSON results. Journal pages 534,535,537,539,543 were additionally
rendered and inspected, supplementing the previous review's pages 519–521,524,533.
