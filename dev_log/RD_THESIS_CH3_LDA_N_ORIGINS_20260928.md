# Chapter 3 restoration and early LDA/N references

Author: Codex. Date: 2026-09-28.

## User correction and completed restoration

The user clarified that the K-matrix request was an element-by-element check,
not a request for additional prose. The Distribution Schemes request was for
original LDA/N references, not a new paragraph citing reviews and later
astrophysical applications. The user explicitly requested restoring both areas.

Both areas now match the pre-edit text, including the original red TODO markers.
The restoration was checked against thesis HEAD 06c9647 as well as the previous
backup. The CGAL/Fabri2000 change is retained. No newly researched citation has
been inserted into the thesis; the following are research findings/recommendations.

The previous symbolic/native audit remains valid: all 16 explicit K entries
were correct and remain unchanged. No further solver testing was needed.
Chapter 4 SHA256 remains
`6626102fdc87c5a6e25f38319003e78ddcf50b1c7a610c4fde3de59ceb1011a8`.

## Source trail and confidence

### N: earliest report and later journal reference

- P. L. Roe (1987), *Linear advection schemes on triangular meshes*,
  CoA Report 8720, Cranfield Institute of Technology, November 1987.
  The report itself was not obtained. Its metadata and relationship to N are
  corroborated by Roe's own 1990 report, the 1993 paper below, and Roe's
  first-person historical account. Do not say the 1987 original was read.
- P. L. Roe (1990), *“Optimum” upwind advection on a triangular mesh*,
  ICASE Report 90-75 / NASA CR-187459. Full original report retrieved from
  [NASA NTRS](https://ntrs.nasa.gov/citations/19910000937), including its N
  construction and reference [1] to the 1987 report.
- P. L. Roe and D. Sidilkover (1992), *Optimum Positive Linear Schemes for
  Advection in Two and Three Dimensions*, SIAM Journal on Numerical Analysis
  29(6), 1542–1568, [doi:10.1137/0729089](https://doi.org/10.1137/0729089).
  Appropriate standard journal reference for the optimal positive scalar
  advection scheme. The thesis already contains the key `Roe_Optimum_1992`.
  Publisher metadata/abstract/references were checked; the full 1992 article
  was not retrieved in this task.

### LDA: early direct citation and an accessible early paper

- R. Struijs, H. Deconinck and P. L. Roe (1991), *Fluctuation splitting schemes
  for the 2D Euler equations*, VKI Lecture Series 1991-01, Computational Fluid
  Dynamics, February 18–22, 1991; also catalogued as VKI PP 1991-11.
  Metadata verified in the [official VKI publication list, PDF page 33](https://www.vki.ac.be/download/people/publications/publi_deconinck.pdf).
  The original lecture notes were not retrieved. This is a defensible early
  direct citation for LDA, rather than a claim that LDA was certainly invented
  for the first time in 1991.
- H. Deconinck, H. Paillère, R. Struijs and P. L. Roe (1993),
  *Multidimensional upwind schemes based on fluctuation-splitting for systems
  of conservation laws*, Computational Mechanics 11, 323–340,
  [doi:10.1007/BF00350091](https://doi.org/10.1007/BF00350091).
  Full text read through the University of Michigan author repository.
  Section 3.1, printed p.327, equation (23), explicitly attributes the
  Low Diffusion A name to Struijs et al. (1991). The same section attributes
  the scalar N discussion to Roe (1987) and Struijs et al. (1991).
  This is a useful early, accessible journal treatment of both scalar schemes.
  It is a different paper from the 1993 Computers & Fluids Roe-linearization
  article already in the thesis bibliography.

The earlier Deconinck/Ricchiuto review locally available traces both N and LDA
ideas to Roe's 1987 report. Since the 1987 original could not be inspected, the
more conservative recommendation is to distinguish the early common background
from the explicitly documented LDA name/formula citation in 1991/1993. No
categorical claim that 1991 is the first-ever LDA publication is justified here.

### Matrix/system N is a separate extension

E. van der Weide and H. Deconinck (1996), *Positive matrix distribution schemes
for hyperbolic systems*, in *Computational Fluid Dynamics '96*, Wiley,
pp.747–753. Abgrall and Barth's original 2002 research article explicitly
attributes the system N extension to this work (abstract and §5):
[author full text](https://www.math.u-bordeaux.fr/~rabgrall/mes_papiers/SISC_24_3_2002.pdf),
[publisher DOI](https://doi.org/10.1137/S106482750138592X).
The 1996 original was not retrieved; this attribution is verified from the
later primary research article. Early scalar citations alone should not be
presented as proof of authorship of every matrix formula in Chapter 3.

## Recommended minimal eventual thesis edit

Keep the existing prose. Add citations at the first N/LDA definition:
N: Roe/Sidilkover1992, optionally Roe1987 for historical priority;
LDA: Struijs/Deconinck/Roe1991, with Deconinck et al.1993 as an accessible
early journal source. If documenting the matrix N extension specifically,
add van der Weide/Deconinck1996. These are proposals, not edits already made.

## Build and artifacts

Archive: `../../local_runs/thesis_ch3_origins_20260928_105952/`.
Full 247-page thesis rebuilt with XeLaTeX/BibTeX/xdvipdfmx; no undefined
citations/references or LaTeX errors. Existing Chapter 1 BibTeX warnings
(`sept`, missing journal for Zwicky1933) remain outside scope. Printed pp.115–117
rendered and visually checked. Original TODO markers are intentionally present
because the user requested restoring the original text.

Final PDF: `output/pdf/thesis_chapter3_restored.pdf` within the archive.
SHA256: `55ac3e625f96c54696a3eb7bf11d76fef78d6430a98b35be680b7341f953d48d`.
The thesis's `master.pdf` and generated `master.bbl` are refreshed.
No commit/push, Overleaf write, solver change or COSMA operation.
