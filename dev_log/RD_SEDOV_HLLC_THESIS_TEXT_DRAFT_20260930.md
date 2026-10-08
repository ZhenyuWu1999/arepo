# Draft thesis text: HLLC-RD and the moving-mesh Sedov test (for review; not in the thesis)

Author: Claude Code (Opus 5.5), 2026-09-30, at the user's request. The user will
review this draft before any thesis edit. It describes the edge-HLLC
distribution (`RD_LOW_ORDER_HLLC`, [report](RD_SEDOV_HLLC_LOW_ORDER_20260930.md)).
It explains how the distribution differs from AREPO's Riemann-solver finite
volume update and how it is an RD (fluctuation-splitting) scheme.

Citation keys are those already present in the thesis bibliography:
`Toro1994`, `Deconinck_Residual_2017`, `Arpaia_ALE_2015`, `Springel_Pur_2010`,
`Schaller_SWIFT_2024`, `Borrow_SPHENIX_2022`. `Einfeldt1991` (JCP 92, 273) would
be a new entry. Labels in angle brackets are placeholders.

---

```latex
\subsubsection{Sedov blast wave}
\label{section:ALE_RD_sedov}

The Sedov blast wave tests the response of the solver to a strong shock
expanding into a cold medium, with a hot and rarefied interior. We use the
two-dimensional setup of the SWIFT example: a periodic unit square sampled by a
$128^2$ glass, $\rho=1$, $\mathbf v=0$, background pressure $p_0=10^{-6}$ and
$\gamma=5/3$. An energy $E=1$ is added as thermal energy to the 21 vertices
nearest to the centre, and the solution is evolved to $t=0.05$, when the
analytic shock radius is $0.258$. All mesh-based calculations use a common
adaptive timestep with $C_{\mathrm{CFL}}=0.1$.

With this energy injection, both the N and LDA schemes fail within the first
steps, when the stage update produces a negative pressure or mass near the
hot vertices. The N scheme completes only if the energy is spread over the
130 vertices within a radius $0.05$, and only on a static mesh. Both
distributions are built on the Roe-linearised residual. Linearised Riemann
solvers are known not to preserve positivity near low densities
\citep{Einfeldt1991}, and LDA is not positive by construction
(Section~<\ref{section:RD_schemes}>).

For this test we therefore use a first-order, positivity-preserving
distribution based on the HLLC approximate Riemann solver \citep{Toro1994}.
The element residual is the ALE residual of
Equation~<\ref{eq:ALE_RD_baseline_contour_integral}> with the nodal flux
interpolation,
\begin{equation}
 \widetilde\Phi^T
 =\frac12\sum_{j\in T}\mathbf G(\mathbf U_j)\cdot\mathbf n_j ,
 \qquad
 \mathbf G(\mathbf U)=\boldsymbol{\mathcal F}(\mathbf U)
   -\mathbf U\otimes\overline{\boldsymbol\sigma}_T ,
\end{equation}
where $\mathbf n_j$ are the inward nodal normals of the midpoint triangle.
Inside each triangle, the three segments joining the edge midpoints to the
centroid separate the parts of $T$ that belong to the median dual cells of
its three vertices (Figure~<\ref{fig:RD_geometry_2D}>). For two vertices $i$ and
$j$ of $T$, the segment between their parts has the scaled normal
\begin{equation}
 \boldsymbol\nu_{ij}^T=\frac{\mathbf n_j-\mathbf n_i}{6},
 \qquad
 \sum_{j\in T,\,j\neq i}\boldsymbol\nu_{ij}^T=-\frac{\mathbf n_i}{2},
\end{equation}
which points from $i$ to $j$ and whose magnitude is the segment length. The
element residual is distributed as
\begin{equation}
 \phi_i^T=\sum_{j\in T,\,j\neq i}
 \left[\mathbf H\!\left(\mathbf U_i,\mathbf U_j;\boldsymbol\nu_{ij}^T\right)
 -\mathbf G(\mathbf U_i)\cdot\boldsymbol\nu_{ij}^T\right],
 \label{eq:ALE_RD_HLLC_distribution}
\end{equation}
where $\mathbf H$ is the HLLC numerical flux through a segment moving with
$\overline{\boldsymbol\sigma}_T$. It is evaluated in the frame moving with
$\overline{\boldsymbol\sigma}_T$ and transformed back to the laboratory frame.
Because the numerical flux is conservative,
$\mathbf H(\mathbf U_j,\mathbf U_i;-\boldsymbol\nu)
=-\mathbf H(\mathbf U_i,\mathbf U_j;\boldsymbol\nu)$, the numerical fluxes
cancel in pairs within the element, and
$\sum_{i\in T}\phi_i^T=\widetilde\Phi^T$. The nodal residuals are therefore a
conservative split of the element residual. They are integrated with the same
two RK stages, lumped temporal mass and modified dual area as the N scheme
(Section~<\ref{section:ALE_RD_equal_timestep}>).

Although this distribution uses a Riemann solver, it is not the
finite-volume update of AREPO.

\begin{itemize}
 \item \textbf{AREPO MMFV.} AREPO solves one Riemann problem on every Voronoi
 face, with states reconstructed and extrapolated to the face, and exchanges
 the resulting flux between the two Voronoi cells.
 \item \textbf{Loop and states.} Here the loop runs over the Delaunay
 triangles, as for all RD schemes in this chapter. Each triangle uses only its
 three nodal states.
 \item \textbf{Role of the Riemann problem.} A one-dimensional Riemann problem
 is solved on each of the three median-dual segments inside the triangle. It
 serves only to decide how the element residual is shared: the left- and
 right-going fluctuations of the HLLC solution, $A^-\Delta\mathbf U$ and
 $A^+\Delta\mathbf U$, go to the two vertices of the segment.
 \item \textbf{Relation to RD.} This is the fluctuation-splitting form of a
 first-order finite-volume scheme on the median dual mesh
 \citep{Deconinck_Residual_2017}. In one dimension it reduces to the
 fluctuation splitting of Roe's solver that introduced RD in
 Section~<\ref{section:RD_1D}>.
 \item \textbf{Geometry.} Each Delaunay edge is visited by its two triangles.
 Each treats half of the median dual face with its own element velocity
 $\overline{\boldsymbol\sigma}_T$. The median dual face passes through the
 triangle centroids, whereas the Voronoi face of AREPO passes through the
 circumcentres. The two coincide only for equilateral triangles.
 \item \textbf{Order and upwinding.} Like the Rusanov distribution of
 Section~<\ref{section:RD_schemes}>, and unlike N and LDA, this distribution is
 not multidimensional upwind. It is first-order accurate in space.
\end{itemize}

The split has two properties that matter for the blast wave.

\begin{itemize}
 \item \textbf{Positivity.} Each pair contribution in
 Equation~\ref{eq:ALE_RD_HLLC_distribution} is a one-sided average of the HLLC
 Riemann fan. A forward-Euler stage is therefore a convex combination of
 admissible states if
 \begin{equation}
  \Delta t\sum_{T\ni i}\sum_{j\in T,\,j\neq i}
  |\boldsymbol\nu_{ij}^T|\,s_{ij}\le|\overline S_i^{n+1/2}|,
 \end{equation}
 where $s_{ij}$ is the largest HLLC wave speed of the pair, provided the HLLC
 intermediate states are themselves admissible. The implementation checks
 these states, the stage CFL condition and the convex weights of the corrector
 at every stage, and applies no density or pressure floor.
 \item \textbf{Contact preservation.} HLLC resolves the contact wave. If the
 vertices of a triangle move with the gas and have equal pressure, the residual
 vanishes, and no density is exchanged between them. On a quasi-Lagrangian mesh
 this avoids the diffusion of the hot, rarefied interior produced by a Rusanov
 or Lax--Friedrichs distribution, whose dissipation scales with the sound
 speed for every component.
\end{itemize}

Figure~<\ref{fig:ALE_RD_sedov_hllc}> compares HLLC-RD on static and moving
meshes with AREPO MMFV \citep{Springel_Pur_2010} and SWIFT with SPHENIX
\citep{Schaller_SWIFT_2024,Borrow_SPHENIX_2022}, all with the same glass and
the same 21 heated particles.

\begin{itemize}
 \item \textbf{Moving HLLC-RD.} It follows the analytic shock position and
 profile. Its radially binned density peak is 2.98 (maximum 3.41), and its
 central density is 0.028, similar to MMFV (0.030).
 \item \textbf{Static HLLC-RD.} The shock is much broader: the binned peak is
 2.33. This reflects the advantage of the moving mesh even at first order.
 \item \textbf{Difference from MMFV.} The remaining difference from MMFV
 (binned peak 3.30, maximum 3.97) is mainly due to the first-order spatial
 accuracy of HLLC-RD. First-order MMFV gives a peak of 3.10 and the same
 central density 0.028.
 \item \textbf{Central pressure.} It is 1.71 on the moving mesh, compared
 with the analytic 1.61. A similar excess (1.67) occurs in first-order MMFV.
 \item \textbf{Conservation.} On the static mesh, mass and energy are
 conserved to round-off. On the moving mesh they change by $-0.33\%$ and
 $+0.70\%$, because of the connectivity changes discussed in
 Section~<\ref{section:ALE_RD_ongoing_work}>.
\end{itemize}

The central density does not approach the analytic point-source value
$\rho\to0$. The heated vertices carry a finite entropy
$K_{\mathrm{inj}}=p_{\mathrm{hot}}/\rho_0^{\gamma}$, and the gas near the
centre is this injected gas after adiabatic expansion to the central pressure,
$\rho_{\mathrm c}\simeq(p_{\mathrm c}/K_{\mathrm{inj}})^{1/\gamma}\approx0.031$.
MMFV (0.030) and moving HLLC-RD (0.028) retain this state, whereas a Rusanov
distribution raises the central density to about 0.2 by numerical mixing.

Figure~<\ref{fig:ALE_RD_sedov_n_hllc}> shows the injection over 130 vertices,
the only case in which the N scheme completes.

\begin{itemize}
 \item \textbf{Static meshes.} The radially binned profiles of N and HLLC-RD
 are almost identical: density peaks 2.30 and 2.32, central pressures 1.56
 and 1.55. This is expected for two first-order upwind distributions on the
 same mesh.
 \item \textbf{Scatter.} The N solution is much noisier. The detrended
 radial-velocity RMS in $0.05<r<0.22$ is 0.19, against 0.024 for HLLC-RD, and
 interior densities reach 0.65.
 \item \textbf{Moving mesh.} With this injection, N fails on the moving mesh,
 whereas HLLC-RD completes and sharpens the shock (binned peak 2.94).
 \item \textbf{Core bubble.} The heated gas remains a nearly uniform bubble,
 $\rho\approx0.09$ out to $r\approx0.14$. This agrees with the adiabatic
 estimate 0.097 for this injection.
\end{itemize}
```

---

Numbers are from `../local_runs/sedov_hllc_20260930_v1/` (HLLC), `sedov_mmfv_20260929_v1`
(MMFV), `sedov_mmfv_first_order_20260930_v1` (first-order MMFV) and
`swift_sedov_default_20260929_v1` (SWIFT). Preview figures:

* `../local_runs/sedov_hllc_20260930_v1/analysis/thesis_preview/hllc_sedov_thesis_preview.png` (21 vertices)
* `../local_runs/sedov_hllc_disk005_20260930_v1/analysis/thesis_preview/hllc_n_sedov_disk005_preview.png` (130 vertices, with N)

The 130-vertex HLLC runs reuse the frozen HLLC binaries (`run_hllc_disk005.py`).
The static N run is the archived `sedov_2d_20260929_v1/runs/disk005_N_static_lab`.
