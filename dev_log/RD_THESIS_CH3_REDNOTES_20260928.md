# Chapter 3 red-note resolution: references and K normalisation

2026-09-27/28. Author: Codex. The user explicitly authorized Chapter3 edits
to resolve its remaining red notes, add distribution-scheme and CGAL
references, recheck the K matrix, and compile a PDF for review.

Thesis repository: `/Users/zhenyuwu/Desktop/MyThesis/Zhenyu-PhDThesis`,
main at06c9647 after the preceding Overleaf sync. Work archive:
`../../local_runs/thesis_ch3_rednotes_20260927_235021/`.
Original Chapter3 text/bibliography, Chapter4 and full PDF are backed up;
all tracked-file hashes and the original working-tree status are recorded.

## Text and references

Exactly three red TODOs were present in Chapter3. All are resolved:

- Distribution Schemes now attributes the presentation to Deconinck and
  Ricchiuto2017, Csik et al.2002, Paardekooper2017 and Morton et al.2023.
  The N definition also cites Roe and Sidilkover1992 and the review.
- CGAL is expanded to Computational Geometry Algorithms Library, with
  `Fabri_CGAL_2000` added to `chapter3bib.bib`. This cites the library's
  design paper, without assigning an unverified CGAL release to the old code.
- The K-normalisation TODO is replaced with an explicit relation between
  the edge-length-weighted normal and the unit normal, and the corresponding
  eigenvalue scaling. The existing16 matrix entries are unchanged.

Sources checked:

- [Deconinck and Ricchiuto2017 publisher record](https://onlinelibrary.wiley.com/doi/abs/10.1002/9781119176817.ecm2054).
- Local primary Csik2002 paper at
  `/Users/zhenyuwu/Desktop/PhD/Reading/CFD/RD_important_papers/[2002 Csik].pdf`;
  title, authors, volume179, pages286--312 and DOI10.1006/jcph.2002.7057 checked.
- Local earlier Deconinck/Ricchiuto review, including its Roe/Sidilkover1992
  reference. Text extracts are archived under `sources/`; this earlier
  review is distinguished from the2017 edition whose metadata was checked.
- [CGAL official bibliography](https://www.cgal.org/publications/Biblio/cgal_publications.html)
  lists Fabri, Giezeman, Kettner, Schirra and Schonherr2000, Software: Practice
  and Experience30(11),1167--1202. The DOI was checked against the publisher
  record:10.1002/1097-024X(200009)30:11<1167::AID-SPE337>3.0.CO;2-B.

## Matrix audit

The thesis normal n_i points inward and has length equal to the opposite
edge. Write n_i=ell_i*n_hat_i, with unit n_hat_i. Then

    K_i = (n_x A_x + n_y A_y)/2
        = ell_i * (n_hat_x A_x + n_hat_y A_y)/2.

The16 entries already in the thesis equal half the normal contraction of
the Euler flux Jacobians. There is no missing edge length or extra factor
of two. Its eigenvalues are ell_i/2 times u dot n_hat_i minus c, twice
u dot n_hat_i, and u dot n_hat_i plus c.

Read-only implementation checks:

- AREPO `src/mesh/voronoi/voronoi.c:triangle_get_normals_area` builds the
  inward edge normals, stores their magnitudes, then normalizes them.
- AREPO `src/hydro/residual_distribution_solver.c` uses unit-normal wave
  speeds and multiplies every K/K+/K- entry by0.5*Mag. Both the main static
  assembly and `rd_build_characteristic_matrices` follow this convention.
- The original local standalone implementation,
  `/Users/zhenyuwu/Desktop/RD/src/triangle2D.h`, also uses
  NORMAL=PERP/MAG and0.5*MAG in both assembly stages.

`audit_k_matrix.py` independently differentiates the conserved Euler fluxes
symbolically: all16 differences from the displayed matrix simplify to zero.
It also extracts and compiles the unchanged native characteristic-builder
function and compares against the formula and independent spectral
projectors on160 random triangles, for gamma1.4 and5/3, including zero
velocity:480 nodal matrices. Scaled maximum full-matrix error1.06e-14,
split errors2.40e-14, normal-convention equivalence5.30e-16, eigenvalue
error1.45e-13; all below the1e-10 audit threshold. Split sums and zero
element sums are also checked. This is an algebra/normalisation audit, not
a new hydrodynamic run or a3D implementation validation.

## Build handling

Use XeLaTeX/TeX Live2025. All include-output subdirectories must exist in
the isolated build directory. The initial automated attempt stopped because
some were absent; a subsequent incremental invocation merely converted
the incomplete stale XDV. Neither output was delivered.

A full forced rebuild then exposed another out-of-tree build issue: the
root's old master.bbl took precedence over the new bibliography, leaving
the new CGAL reference and a previously synced Chapter2 citation unresolved.
Running BibTeX in the isolated build directory, with BIBINPUTS/BSTINPUTS
pointing to the thesis, and giving that build directory first priority in
TEXINPUTS for subsequent XeLaTeX passes resolves both without editing
Chapter2. The PDF converter must run from the thesis directory so its
relative figure paths resolve. Final build and visual checks are recorded
in the archive's `verification.json`.

Only Chapter3 source/bibliography are intentionally edited. Chapter4,
including Overleaf4.3.1 and local Yee4.3.2, matches its pre-task hash.
No production solver changes, simulations, Git commit/push or Overleaf write.

## Final artifact

Full thesis PDF:247 pages; no compile errors, unresolved citations or
unresolved cross-references. Printed pages115--117 and123 contain the
main edits; Fabri appears in the bibliography on198. Final rendered pages
114--117,123 and198 were checked. The normal-definition paragraph and its
equation are kept together; the matrix and citations are legible, with no
clipping or overlap in the edited regions. Existing unrelated overfull boxes
and minor package/BibTeX warnings remain outside the edited scope.

Deliverable: `output/pdf/thesis_chapter3_review.pdf`, SHA256
`c7524c853196453271f7611d399996ae29bc4d4a3c93847280a4f98a42703407`.
The thesis folder's `master.pdf` and generated `master.bbl` were also
refreshed. The only tracked thesis changes introduced by this task are
`chapter3/chapter3.tex` and `chapter3/chapter3bib.bib`; the pre-existing
Chapter4 working-tree changes are preserved exactly.
