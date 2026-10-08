# Literature search: finite-volume schemes used as residual distribution

Author: Claude Code (Opus 5.5), 2026-10-01, at the request of Zhenyu Wu.
Question: is there earlier work, with results, on schemes that use a
finite-volume (FV) flux as an RD distribution, as our HLLC-RD does?

Method: web search plus reading of the accessible texts. Directly read: the
verified Deconinck & Ricchiuto (2017) copy, Paardekooper (2017), Guzik & Groth
(2008) and Hu, Li & Tang (2010). Barsukow et al. (2025) and Abgrall (2018)
were read through the arXiv/ar5iv HTML. Items marked *(abstract)* were checked
only from the abstract or publisher page. No thesis or solver edits; no runs.

## 1. Short answer

* **The FV ⇔ RD identity is well established in theory.** One-dimensional Roe
  fluctuation splitting (Roe 1982, thesis §3.2.1) generalises to multiple
  dimensions as follows.
  * Paillère (1995) and Deconinck & Ricchiuto (2017, §4.1): median-dual FV
    written as RD.
  * Abgrall (2018, §4.1): general flux ⇔ RD construction.
  * Barsukow, Ciallella, Ricchiuto & Torlo (2025, Prop. 6): multidimensional
    FV with corner fluxes is equivalent to RD.
* **Few published *numerical results* use an FV flux as the RD distribution
  on triangles.**
  * The original example is Paillère's upwind FV-RD scheme for scalar advection
    (DR2017 Eq. 59). The review states that it is:
    * positive under its CFL bound;
    * not linearity preserving;
    * first order in practice;
    * more dissipative and more restrictive in Δt than N (citing Paillère 1995).
  * The recent example with Euler results is Barsukow et al. (2025). It covers
    a circular Sod problem and KH, but uses Cartesian meshes, genuinely
    multidimensional corner fluxes and a focus on stationarity preservation.
* **I found no published median-dual HLLC (or other approximate Riemann
  solver) FV-RD on triangles, for Euler, moving meshes or Sedov.** Hu, Li &
  Tang (2010) use HLLC in an "RD-type" steady solver. However, they state that
  it differs from traditional RD by solving the system with Newton "rather
  than through residual distribution": it is a cell-centred reconstructed
  scheme, so it is not a direct precedent. This is a search result, not a
  proof of absence.
* **Comparisons of RD (N, LDA, LN, B) with separate FV codes are more
  common.** The relevant shock result is Paardekooper (2017): on a cylindrical
  blast, the N scheme is "almost indistinguishable" from a structured-grid HLL
  FV code.

## 2. Theory: FV written as RD (or RD as fluxes)

| Reference | What it shows | Results? |
|---|---|---|
| Roe (1982), "Fluctuations and signals" | 1D upwind FV as fluctuation splitting | 1D; basis of thesis §3.2.1 |
| Paillère (1995), PhD thesis VKI/ULB; Paillère, Deconinck & van der Weide (1997, VKI LS 1997-02) | Upwind median-dual FV-RD for advection (later DR2017 Eq. 59); RD as an "alternative for FV and FE" | Results in the thesis (not accessed online) |
| Deconinck & Ricchiuto (2017), §4.1, Eqs. 55–60 | Median-dual FV with any consistent conservative flux ⇒ RD residuals φ_i=Σ[H−F_i·ν_ij], element sum = P1 flux residual. Upwind FV-RD: LED, positivity bound (60), not LP, first order observed. N has the lowest dissipation among first-order schemes and larger Δt bounds than upwind-FV-RD and Rusanov (citing Paillère 1995) | Their Euler examples compare **LN** with a **separate cell-centred 2nd-order Roe FV** (Barth–Jespersen limiter, RK2). LN is sharper on double Mach and on a shock–shock interaction. No Euler run of FV-RD itself |
| Abgrall (2018, CMAM 18:327; arXiv 1708.03108), §4.1, Eqs. 23–24 | FV residual Φ_σ^K = Σ_{γ⊂∂(C_σ∩K)} f̂(u_σ,u⁻); every known scheme has a flux form | Theory only |
| Abgrall & Ricchiuto (2021/2022; arXiv 2109.08491) *(abstract)* | RD as a generalisation of Roe's flux in fluctuation form; local/global fluxes | Review chapter |
| Abgrall, Maire & Ricchiuto (2025; arXiv 2509.25967) *(abstract)* | Common conservation framework for FV fluxes and element residuals, Eulerian and Lagrangian | Theory only |
| Barsukow, Ciallella, Ricchiuto & Torlo (2025; arXiv 2506.21700), §4.5, Prop. 6 | "the multidimensional finite volume global flux method with piecewise constant data is equivalent to the Residual Distribution scheme" with corner-conservative fluctuations (also averaged-flux and SUPG-stabilised variants) | **Yes.** Acoustics; Euler (isentropic vortex, low Mach, circular Sod, KH); shallow water. Cartesian meshes. Better than standard FV for stationary/near-stationary states |
| Ricchiuto, Rubino, Witteveen & Deconinck (2003), ASTAR workshop *(title only)* | 1D two-fluid RD and its relation to Godunov FV | 1D proceedings |
| Sidilkover & Roe (1995), ICASE 95-10 *(abstract)* | Unifies control-volume (structured) and fluctuation-splitting advection schemes | Scalar |
| Wood & Kleb (1999, JCP 153:353) *(abstract)* | 1D equivalence; 2D comparison of FS and FV diffusion | Scalar advection–diffusion: FS less artificial diffusion; 29× speed-up to a given accuracy |
| Kuzmin (2026; arXiv 2602.02095) *(abstract)* | Element-based convex limiting (FCT, MCL) for FE interpreted as RD | Review |

## 3. Results comparing RD with (separate) FV codes

| Reference | Comparison | Main finding |
|---|---|---|
| Paardekooper (2017, MNRAS 469:4306; arXiv 1705.02028) | astrix N/B/Bx on triangles vs dimensionally split Roe and HLLC (rodeo), plus HLL | 1D: first-order N, Roe and HLLC almost identical. **Noh**: Roe/HLLC show a carbuncle; less diffusive blended schemes "either fail on this problem, or need backup fluxes produced by the N scheme"; L1 errors of N, max-blend and HLL "very comparable". **Cylindrical blast** (p0=1e−6, γ=5/3): "The N scheme produces results that are almost indistinguishable from those obtained with the HLL scheme"; B larger errors. Vortex: B/Bx far better than Roe/HLLC |
| Deconinck & Ricchiuto (2017), Figs. 15, 17 | LN vs cell-centred 2nd-order Roe FV, same unstructured mesh | LN sharper shocks and contact |
| Guzik & Groth (2008, IJCFD 22:61) | LDA, LN/PSI, blended vs cell-centred FV | Scalar: RD "far superior to the FV method, both in smooth regions and in the presence of discontinuities". Supersonic Euler agrees; difficulties for subsonic cylinder and transonic Ringleb |
| Chizari & Ismail (2015, Bull. Malays. Math. Sci. Soc.) *(abstract)* | RD vs cell-vertex FV on skewed triangles | FV order deteriorates on non-uniformly skewed grids; first-order RD slightly better |
| Pavan, Ata & Hervouet (2015, Environ. Earth Sci. 74:7337) *(abstract)* | RD vs 2nd-order FV for pollutant transport (Telemac-2D) | Grid regularity relative to streamlines changes behaviour |
| Morton, Khochfar & Wu (2023) | RD N/LDA/blend Sedov | LDA unstable, blend favours N (already cited in the thesis) |

## 4. Riemann-solver or edge-based low-order schemes in the RD/FE context

* **Hu, Li & Tang (2010, JCP 229:1681).**
  * Uses HLLC fluxes (Jacobians by numerical differentiation).
  * Cell-centred quadratic WENO reconstruction, steady Euler, Newton–multigrid.
  * It differs from traditional RD "only in the last step, namely the
    nonlinear system is solved directly by the Newton type method rather
    than through residual distribution".
  * This corrects Codex §201's description of it as a "genuine HLLC + RD
    precedent": it is RD-type only in a loose, steady-residual sense.
* **Rusanov/Lax–Friedrichs RD** (DR2017 Eq. 71; Abgrall & Mezine 2003;
  Abgrall 2006; Abgrall, Bacigaluppi & Tokareva 2019 MOOD fallback).
  * This is the RD community's standard robust first-order scheme.
  * It is the central element split Φ/3 plus a scalar element dissipation,
    not the median-dual FV split. Our old `RD_RUSANOV_LOW_ORDER` belongs to
    this family.
* **Guermond & Popov (2016, SINUM); Guermond, Popov & Saavedra (2020, ALE).**
  * P1 continuous FE with lumped mass and graph viscosity, using the maximum
    wave speed of each edge's local Riemann problem.
  * This gives an invariant-domain (positive) first-order edge-based scheme;
    Noh, Leblanc and others are tested.
  * Kuzmin (2026) relates element-based convex limiting to RD. This is the
    closest robust Riemann-based relative of HLLC-RD, but it is not described
    as FV-RD.

## 5. Implications for the thesis text

* The thesis already cites DR2017 §4.1 as the main support; that remains
  appropriate.
* Possible additions, not made:
  * Paillère (1995), for the original upwind FV-RD scheme.
  * Barsukow et al. (2025), for a recent equivalence with Euler results.
  * Paardekooper (2017), for N ≈ HLL on a cylindrical blast. This is a
    comparison with a separate FV code, not FV-as-RD.
* The novelty can be stated as an application: HLLC median-dual FV-RD
  embedded in the Arpaia ALE-RD scheme on a reconnecting moving Delaunay
  mesh, applied to Sedov. It should not be claimed as a new scheme family.

## Sources

* Deconinck & Ricchiuto 2017: https://team.inria.fr/cardamom/files/2019/10/deconinck-ricchiuto2017.pdf (local verified copy in `../../local_runs/riemann_rd_schematic_20261001_v1/sources/`)
* Abgrall 2018: https://arxiv.org/abs/1708.03108 ; https://www.degruyterbrill.com/document/doi/10.1515/cmam-2017-0056/html
* Barsukow et al. 2025: https://arxiv.org/abs/2506.21700 (HTML v2 §4.5)
* Abgrall & Ricchiuto 2021: https://arxiv.org/abs/2109.08491
* Abgrall, Maire & Ricchiuto 2025: https://arxiv.org/abs/2509.25967
* Kuzmin 2026: https://arxiv.org/abs/2602.02095
* Paardekooper 2017: https://arxiv.org/abs/1705.02028
* Guzik & Groth 2008: http://arrow.utias.utoronto.ca/~groth/publications/IJCFD-2008-guzik.pdf
* Chizari & Ismail 2015: https://link.springer.com/article/10.1007/s40840-015-0292-0
* Wood & Kleb 1999: https://www.sciencedirect.com/science/article/abs/pii/S0021999199962812
* Sidilkover & Roe 1995: https://ntrs.nasa.gov/api/citations/19950017045/downloads/19950017045.pdf
* Pavan, Ata & Hervouet 2015: https://link.springer.com/article/10.1007/s12665-015-4760-5
* Hu, Li & Tang 2010: https://www.math.hkbu.edu.hk/~ttang/Papers/HuLiTang10a.pdf
* Abgrall, Öffner & Ranocha 2022 (entropy correction for RD/DG, background): https://arxiv.org/abs/1908.04556
