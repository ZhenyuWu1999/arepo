# Thesis final-version audit — 2026-10-02

Author: Codex. User request: review major scientific issues in Chapters 3–4, verify references (especially Chapters 1, 3, 4), and scan the whole thesis for red text and unresolved comments. **The thesis was not edited.**

## Scope

- Thesis repository: /Users/zhenyuwu/Desktop/MyThesis/Zhenyu-PhDThesis.
- Reviewed HEAD: **5d31697**, finalize Chapter 5. Tracked files were clean before and after review. No pull, commit or push.
- Read Chapters 3 and 4, checked principal derivations against cited papers and current implementation/baseline notes, and scanned all thesis TeX sources and chapter bibliographies.
- Bibliography: 365 stored entries, 345 distinct cited keys in the thesis; Chapters 1, 3, 4 cite 206 distinct entries (171, 36, 25 per chapter). Of the 206, 164 resolved directly through Crossref DOI metadata; 38 have no DOI, and four require non-Crossref sources. Books, reports, theses, arXiv records and exceptional matches were checked separately. Fuzzy title similarity alone was not accepted as proof of identity.
- No new full thesis compilation or native hydro runs. The counterexample below is an independent element-level algebra check.
- Reproducibility files: ../local_runs/thesis_final_audit_codex_20261002_v1/. The inventory.json source hashes were unchanged at the end of the audit.

## 1. Important mathematical limitation: singular LDA with the G3 residual

Locations: chapter4/chapter4.tex, lines 530, 838–848, 971–973.

Chapter 3's nullspace argument for the Roe-linearized residual does not by itself justify replacing its right-hand side with an arbitrary contour residual. Chapter 4 uses G3 integration of the flux of the P1 conservative state, retains Roe distribution matrices, and describes a pseudoinverse for singular inflow matrices.

Let \(S=\mathbf S^-=\sum_i\mathbf K_i^-\). Since \(\sum_i\mathbf K_i^+=-S\), the stated distribution gives

\[
 \sum_i\widetilde\phi_i
 =-\sum_i\mathbf K_i^+S^\dagger\widetilde\Phi_{G3}
 =SS^\dagger\widetilde\Phi_{G3}.
\]

This equals the desired total only when \(\widetilde\Phi_{G3}\in\operatorname{Range}S\). It is automatic for a full-rank matrix, but **not automatic for a singular matrix**. The F1 temporal lumped fallback described at line 973 does not restore a missing component of the spatial residual.

### Explicit counterexample

Use the static-mesh limit, triangle vertices \((0,0),(1,0),(0,1)\), \(\gamma=1.4\), and positive nodal states

\[
 \rho_i=p_i=1,\qquad
 \mathbf v_0=(1,0),\quad \mathbf v_1=(-1,1),\quad \mathbf v_2=(0,-1).
\]

The Roe mean velocity is zero, \(\bar H=25/6\), and \(\operatorname{rank}S=3\). Its range requires \(\Phi_E=\bar H\Phi_\rho\). Direct edge integration gives

\[
 \widetilde\Phi_{G3}=(-1.5,\;0.1,\;0,\;-6.45)^T,\qquad
 \Phi_E-\bar H\Phi_\rho=-0.2.
\]

Density is constant along each edge, so the flux here is polynomial and G3 integrates it exactly. This is not quadrature round-off. Raw pseudoinverse distribution instead sums to approximately

\[
 (-1.5453857791,\;0.1,\;0,\;-6.4391074130)^T.
\]

Code and output: check_rank.py and rank_result.json in the audit directory. Current native source confirms spatial range completion exists only in an opt-in path: src/hydro/residual_distribution_solver.c, lines 1353–1375 and 5320–5360, guarded by RD_LDA_COMMON_BETA. The normal mixed-stage baseline is not that option. Its conservation diagnostic can expose the defect; it is not an automatic repair.

**Implication:** Chapter 4's unconditional element-conservation statement needs a rank/range qualification and a description of the actual spatial treatment if arbitrary singular G3 cases are claimed. Chapter 3's compatible Roe nullspace proof can remain. This counterexample does not establish that any plotted native run encounters this state or quantify its run-level error. A spatial range-completion formula is an algorithmic choice requiring validation, not a thesis wording fix to silently claim as implemented.

## 2. Important literature correction: existing ALE-RD Euler implementations

Location: chapter4/chapter4.tex, line 300.

The paragraph says the Arpaia papers mainly concern scalar laws or simplified Euler equations rather than the complete Euler equations, and starts by saying there is no detailed moving-mesh RD implementation. This is inaccurate.

Arpaia, Ricchiuto & Abgrall (2015), An ALE Formulation for Explicit Runge–Kutta Residual Distribution, explicitly treats the perfect-gas compressible Euler system in Section 6. Section 6.1 (printed p. 533) describes matrix upwind parameters and eigenvalue splitting; Section 6.2 includes Euler tests. Referring to earlier work for some details does not make these “simplified Euler equations”.

Primary source: [published paper](https://doi.org/10.1007/s10915-014-9910-5). The locally stored full paper was read; extracted text is arpaia_ale.txt in the audit directory.

In the same paragraph, Colombo & Re (2022) describe collapse/expansion of the **local affected patch**, including connectivity changes such as edge swaps, not collapse of the entire triangulation. Their method explicitly treats Euler equations with local mesh adaptation. See [author-posted paper, especially Section 3](https://arxiv.org/abs/2204.11668).

The contribution can still be presented as implementing and extending RD in AREPO, with its particular moving Delaunay geometry, solver coupling and scheduling requirements. It should not be justified by absence of previous full-Euler ALE-RD work.

## 3. Accuracy claims: separate time integration from spatial convergence

Locations: chapter3/chapter3.tex, lines 1194–1229 and 1376; also Chapter 4's hierarchy discussion.

The lumped N update reduces to Heun, as stated. The general LDA/F1 corrector has a different mass action and cannot inherit an unconditional “second-order time integration” claim just because it has two stages. The chapter conclusion currently makes that unqualified claim.

The project's [static baseline](RD_STATIC_BASELINE_CHAPTER4.md), Section 4, records fixed-h temporal self-convergence near first order for the standard two-pass GL/F1 path. It also explains that the frozen-star hierarchy modifies the leading operator rather than merely rescheduling the equal-step method. The [2026-09-17 restoration](RD_MIXED_BETA_BASELINE_RESTORED_20260917.md) retains the mixed-stage baseline and explicitly does not establish second-order temporal accuracy.

For the ordinary two-pass corrector, with assembled lumped area matrix \(M_L\), F1 mass \(M\), \(v=-M_L^{-1}R\), and \(C=M_L^{-1}M\), its leading rate is \((2I-C)v\); \(M=M_L\) is the special Heun case. Two-stage form alone supplies no proof of time order for general F1.

Suggested scope: call it the two-stage RK-RD construction, retain measured smooth-flow spatial/joint convergence, and avoid asserting separately proven fixed-grid temporal order 2 for every scheme. This does not refute published RK-RD space-time accuracy results or the thesis plots. No new time-convergence study was run in this audit.

## 4. Secondary scientific qualifications

- Chapter 4, lines 987, 996, 1031: boosted tests show reduced advection error and approximately boost-independent behaviour in the tested cases. They do not prove exact discrete Galilean invariance for arbitrary boosts. No extra AREPO comparison is needed to qualify the wording.
- Chapter 4, line 1075: describing the fixed-connectivity Lagrangian staggered method of Abgrall et al. (2020) as unable to be used for astrophysical simulations is too broad. Its immediate applicability to the present AREPO implementation is the relevant limitation.
- Chapter 4, line 4: “significantly increase the performance” is ambiguous without timing/scaling measurements. Distinguish numerical capability from demonstrated speedup.
- Moving HLLC-RD Sedov remains a useful preliminary result, correctly identified as first order. Earlier archived checks report finite drift: the 21-hot-point run has about −0.33% mass and +0.70% energy; the one-hot-point run about −1.61% energy, unlike the static round-off result. Those budgets do not isolate edge flips from every other contribution. Section 4.3.3 already declares conservation work incomplete. These previously discussed limitations do not require expanding the thesis into a new validation chapter.
- Chapter 3's closed dual-normal identity assumes an interior or periodic node; physical-boundary contributions need separate treatment. N positivity statements should retain their assumptions rather than promote a scalar monotonicity argument into an unconditional Euler positivity guarantee.

No new major sign/factor error was identified in the Roe K construction, compatible zero-velocity nullspace argument, median-dual FV-RD construction, mean-mesh-velocity ALE identity, or midpoint GCL derivation. FV-RD as a finite-volume construction written in RD form is defensible; it should not be advertised as multidimensional upwinding.

## 5. Bibliography

No fabricated reference or duplicate work was identified in the checked Chapters 1/3/4 bibliography. Across all 365 stored records there are no duplicate keys, normalized exact titles, DOIs, arXiv identifiers or ISBNs. Near-title matches were examined and are distinct publications, e.g. Planck 2015/2018, Hafen 2019/2020 and different Enzo papers. There are no missing cited keys.

| Entry and source location | Finding | Verified information |
|---|---|---|
| Campoli_ShockFitting_2017, chapter4/chapter4bib.bib:13 | Pages incorrectly 95–116. | **113–129**, per [publisher's contents](https://link.springer.com/book/10.1007/978-3-319-68427-7). DOI remains 10.1007/978-3-319-68427-7_5. |
| van2006upwind, chapter1/chapter1bib-simulation.bib:1004 | Mixes 2006 with the 16th AIAA CFD conference and paper number 3559. | Choose the **2003** conference paper, DOI 10.2514/6.2003-3559, or the **2006 journal article**, Communications in Computational Physics **1(2), 192–206**. [Publisher's journal record](https://global-sci.org/index.php/cicp/article/view/5409). |
| Zier_Lumina_2026, chapter1/chapter1bib-simulation.bib:539 | “Submitted to MNRAS” is outdated. | The [current arXiv record](https://arxiv.org/abs/2605.15310) says **Accepted by MNRAS**. Definitive journal volume/article metadata was not verified; do not invent it. |
| Abgrall_Residual_2002, chapter3/chapter3bib.bib:120 | Year convention merits checking, not a false-reference diagnosis. | The [official issue](https://epubs.siam.org/doi/10.1137/S106482750138592X) is January **2003**, whereas copyright and many later citations use **2002**. Title, authors, volume and pages match. |

Previously corrected Bromm & Loeb (2003) and Begelman et al. (2006) DOIs, and the Inria research-report classification of arpaia2015mesh, are now correct. Wu et al. (2026) is already the published entry: MNRAS **551(2), stag1461**, DOI [10.1093/mnras/stag1461](https://doi.org/10.1093/mnras/stag1461); current Crossref metadata agrees. Morton (2021) is confirmed by the University of Edinburgh's DataCite record, DOI 10.7488/era/1086.

The older log's “no arXiv-only references” should not be carried forward as a description of the current bibliography: the Lumina entry still uses its arXiv record. This is a publication-status update, not evidence of a fictitious reference.

## 6. Red text, comments and source references

- No active \sk, \zw, \red, \adg, TODO or FIXME comment found in the thesis body.
- Three old comments remain in %-commented lines in chapter2/chapter2.tex:18, :271, :504. They do not appear in the PDF.
- master.tex:44–47 defines comment commands but does not create an unresolved comment. Red syntax highlighting in customisations.sty is not a review annotation.
- Source scan found no undefined references, duplicate labels, empty citations/references or missing bibliography keys. This is a source check, not a new LaTeX build.

The thesis remains unchanged. Highest priorities are the singular G3/LDA qualification, correcting the Arpaia/Colombo literature paragraph, and removing the unqualified time-order claim; bibliography fixes are small.
