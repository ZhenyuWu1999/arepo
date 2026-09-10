# Moving RD: representation choices and the cost of fitting them into AREPO

> **Scope update, 2026-09-09 (user decision):** the native-FV/corner-RD route
> is parked as possible future work. Its existing Python algebra checks are
> the stopping point; the prototype sequence below is an earlier proposal,
> not the current work plan. The thesis-facing development priority remains
> P1 RD + conservative topology transfer + hierarchical timesteps. See
> `RD_P1_patch_synchronization_20260909.md` for the next bounded investigation.

Date: 2026-09-09. Baseline: `75c3d6ac65b8edce2741a372fc9507dacf22151e`.
Scope: mathematical design and source-level implementation assessment, following
the user's questions about macro synchronization, alternatives to remapping,
and the requirement to build on the existing AREPO project.
Conservation statements concern periodic/source-free Euler totals; boundary
fluxes and physical source terms would enter the balance separately.

This extends `RD_topology_hierarchy_conservation_20260909.md`. No production
solver or thesis file was changed. The new test is a representation/scalar
algebra discriminator, not a new Euler solver. The proposed Voronoi corner
route is not implemented in AREPO.

## 1. Decision: separate existence, representation, and implementation cost

A common macrostep does provide a place to close all hierarchical ledgers.
It does **not** make intermediate topology changes invisible. There are two
different operations that should not be conflated:

- keep the current fine-event topology updates, then add a correction at the
  macro endpoint;
- integrate on a deliberately fixed hydrodynamic connectivity during the
  macrostep, and remap only at its endpoint.

Only the latter avoids intermediate triangle birth/death by construction.
The previous audit gave a conditional conservative design of that kind. It
proves that the combination is not mathematically impossible, but does not
prove that this is the cheapest or best-performing AREPO implementation.

The user's concern about elegance identifies a real structural issue. The
current nodal P1 field changes its basis discontinuously at a flip. Some
representation transfer is unavoidable if its physical integral is to be
preserved for general nodal data. A method may express that transfer as a
projection, a geometric flux or a space-time jump condition; renaming it does
not eliminate the change in representation.

There is a different design: store true Voronoi cell averages, while using
RD-derived multidimensional upwinding to define numerical fluxes. That changes
the method, but can reuse much of AREPO's native FV infrastructure. It deserves
a bounded feasibility prototype before committing to a large persistent
P1-topology/LTS rewrite. It is not a reason to discard the existing RD work or
to assume a new method will automatically retain its results.

## 2. A concrete obstruction for the present P1 representation

Take the unit square with vertices A, B, C, D in counterclockwise order.
At the exact cocircular configuration, either diagonal is Delaunay. The
integrals of the four nodal P1 hat functions within the square are

\[
 m^{AC}=(1/3,1/6,1/3,1/6),\qquad
 m^{BD}=(1/6,1/3,1/6,1/3).
\]

Keeping the four nodal values therefore changes the represented integral by

\[
 \Delta I=\frac{U_B+U_D-U_A-U_C}{6}.
\tag{1}
\]

For nodal scalar values (2,1,1,1), the jump is -1/6. No improvement in locating
the flip time, MPI reduction or timestep size can make (1) vanish for these
fixed data. Exterior basis contributions cancel in a complete flip patch.
Affine data satisfy the appropriate moment identity and have no such defect.

The obstruction is stronger than a choice of lumping: the old and new P1
interpolants are generally different functions in the square. A generic
piecewise affine function with a gradient jump on AC cannot also be represented
by the four-node P1 space with its only internal edge on BD. Preserving the
entire old field exactly requires additional representation information;
preserving just its conservative integral is possible with the local map in
the preceding audit. Smooth-field transfer errors can be spatially small;
an under-resolved discontinuity need not have a small correction.

For the same four generators, the true Voronoi areas clipped to the square
are (1/4,1/4,1/4,1/4), independent of the chosen Delaunay diagonal. Perturb
C to (1,1+epsilon). As epsilon crosses zero, the P1 coefficients have distinct
one-sided limits, while the true Voronoi areas have a common limit. This is
a geometric comparison, not an assertion that point values and cell averages
represent the same approximation.

`tests/rd/audit_voronoi_corner_flux_algebra.py` checks this using half-plane
clipping. For epsilon=1e-8, the largest difference between the +epsilon and
-epsilon P1 masses is `0.16666667`; the corresponding Voronoi difference is
`5.00e-9`. The illustration is retained at
`/Users/zhenyuwu/arepo_rd/local_runs/topology_alternatives_20260909/representation_jump.png`.

This continuity is also the geometric property emphasized in Springel's
AREPO paper, §2.3: a disappearing Delaunay adjacency corresponds to a
Voronoi face shrinking to zero. It eliminates a finite instantaneous volume
transfer for a generic flip, not all finite-step geometry/quadrature errors.
[Springel, AREPO paper](https://arxiv.org/abs/0901.4107).

## 3. What waiting for the macrostep can and cannot accomplish

If two histories share the same initial and final meshes but flip at different
times, they generally have different transport histories. For a linearized
semidiscrete example, let L_A and L_B be old/new transport operators and T the
same-time transfer. A flip at tau within [0,H] gives

\[
 U(H)=\exp[(H-\tau)L_B]\,T\,\exp[\tau L_A]U(0).
\tag{2}
\]

An endpoint-only procedure sees neither tau nor the missing integrals.
It cannot reconstruct (2) in general. A scalar correction can restore one
global sum, but does not reconstruct the omitted momentum/energy distribution
or physical transport. An old-to-final mass difference also need not encode
the sequence of noncommuting intermediate transfers.

If the hydrodynamic connectivity is deliberately held fixed, the intended
operator instead becomes T exp(H L_A), schematically. That is a different,
well-defined algorithm. Under the assumptions in the preceding audit
(valid persistent elements, compatible clocks and traces, conservative
fixed-connectivity transport, complete common-time transfer), its physical
Euler totals are conserved at common macro synchronization. This is not a
claim that the existing raw partial Q ledger is a synchronized physical
integral at every intermediate fine event.

Freezing mesh velocity for the macrostep is a sufficient simplifying
condition for that argument, not a demonstrated necessity. Compatible
piecewise velocity histories may be used if their geometry and quadrature
are treated consistently. Preserving this flexibility would require further
analysis; it cannot be assumed when simply pulling a new triangle backwards
with its latest velocity.

In AREPO, fixed hydrodynamic connectivity would need to live alongside the
recreated native mesh. `src/mesh/voronoi/voronoi.c:612` frees mesh arrays and
primitive/gradient exchanges; the Delaunay centers, simplices and point
indices are not stable across that operation. A saved integer triangle list
is therefore insufficient. Persistent global IDs, periodic offsets, node
lookup, old-element geometry and remote-node access would be required.
The existing old-mesh diagnostic snapshot is a useful starting point, not
that complete data structure. Preventing inversion of the retained triangles
can also constrain H and reduce the benefit of subcycling.

Thus the macro-epoch route is a good *mathematical reference*, with moderate
to substantial implementation work. Calling it the automatically smallest
engineering change would be misleading.

## 4. A different conserved representation with RD-derived fluxes

The two choices below are independent:

1. what the unknown represents and where its conserved integral is stored;
2. how the numerical transport resolves waves in multiple directions.

One can retain multidimensional RD upwinding while changing the first choice
to native Voronoi cell averages. Let

\[
 W_i=|V_i|\bar U_i,\qquad
 \dot W_i=-\sum_j\mathcal F_{ij},\qquad
 \mathcal F_{ji}=-\mathcal F_{ij}.
\tag{3}
\]

Each face exchange is a zero-sum action, even when one cell is inactive.
Its flux can depend on three or more states; conservation does not require a
two-state one-dimensional Riemann solver. The conserved degrees of freedom
remain attached to generators, while a Delaunay triangle acts as a local
stencil for a corner flux. Disappearance of that stencil does not delete an
independently stored P1 element integral.

This has a significant consequence for LTS. In the present nodal RD route,
an individual triangle residual generally has a nonzero sum, and cancellation
can depend on other triangles covering compatible intervals. In (3), every
individual accepted face transaction preserves the global W sum. Incorrect
time quadrature or a repeated transaction can still corrupt the solution,
but conservation is no longer obtained by cancellation between differently
scheduled triangle histories. Time consistency, free-stream preservation and
positivity remain separate obligations.

There is relevant published support, with an important limitation. Gaburro,
Ricchiuto and Dumbser, arXiv:2506.00207v2, §5 eqs.27–30, construct corner
fluxes from RD fluctuations, including an N-based solver. Their §2 explicitly
uses **barycenter-based Voronoi-like polygons, not true circumcentric Voronoi
cells**. The paper provides a static flux framework, not the present ALE/LTS
extension. Its auxiliary residual triangle also generally differs from the
generator Delaunay triangle. Copying its geometry, or just replacing A/3 by
Volume in current RD, would not solve our problem.
[Primary paper, v2](https://arxiv.org/html/2506.00207v2).

### 4.1 A proposed semidiscrete ALE construction

The following is a design derivation for true Voronoi cells, not a claim that
the cited paper has implemented it. For an ordinary 2-D Voronoi corner p
touching three cells, let N_ip be the sum of the two outward face-normal
vectors adjacent to that corner, each with half its full face length. Then

\[
 \sum_{i\ni p}N_{ip}=0,\qquad \sum_{p\in i}N_{ip}=0.
\tag{4}
\]

Let w_p be the geometric velocity of that corner. With straight faces and
their endpoint velocities, polygon area differentiation gives

\[
 \dot {|V_i|}=\sum_{p\in i} w_p\cdot N_{ip}.
\tag{5}
\]

Define corner contributions

\[
 G_{ip}=\big[F(U_i)-U_i\otimes w_p\big]\cdot N_{ip}+\phi_{ip},
\quad
 \sum_{i\ni p}\phi_{ip}
  =-\sum_{i\ni p}\big[F(U_i)-U_i\otimes w_p\big]\cdot N_{ip}.
\tag{6}
\]

Then sum_i G_ip=0 at every corner. If the RD splitting gives phi_ip=0 on a
uniform state, (4)–(6) imply

\[
 \dot W_i=U_0\dot {|V_i|},
\]

so a uniform state is preserved semidiscretely as well. This supplies an
explicit conservation/GCL target. At finite timestep, matched swept geometry
or suitable quadrature is still needed for the corresponding discrete GCL.
No fully discrete positivity or high-order proof follows from (6) alone.

### 4.2 Fitting corner contributions into AREPO's existing face loop

There is a useful small linear-algebra fact. Assemble the three row normals
N_ip into a 3×2 matrix N. For a nondegenerate ordinary corner, rank(N)=2 and
1^T N=0. Any three corner contributions G_ip whose sum is zero therefore
satisfy

\[
 N\widehat F_p=G_p
\tag{7}
\]

for one common spatial flux vector per conserved component. For Euler,
this is a 2×4 flux tensor. This is a statement about rank and closure, not a
new hydrodynamic accuracy theorem.

At equal time and consistent corner evaluation, averaging the tensors from
the two endpoints of a straight Voronoi face and projecting onto its normal
reproduces the corner quadrature. More generally, that one projected face
flux can be computed on a face's own temporal quadrature and submitted once
to the native two-cell update. The hierarchy's pairwise conservation survives
even if the temporal accuracy of this new flux requires further development.

The new scalar audit tests (7) on 1,000 nondegenerate normal/state samples,
using actual scalar N splitting with a relative advection velocity. Maximum
corner-sum error is `1.34e-15`, maximum flux-representation error `2.67e-15`,
and uniform flux-representation error `1.34e-15`. These are local algebraic
checks, not a Voronoi Euler or hierarchical simulation.

At degenerate corners with more than three cells, zero sum alone no longer
guarantees a common 2-D tensor. A multi-state treatment, consistent geometric
resolution, or a native FV fallback is needed. Nearly singular normals also
need a conditioning check. True Voronoi topology removes the finite volume
jump; it does not ensure a corner Riemann model is insensitive to every
degeneracy or stencil switch.

## 5. What can actually be reused in this AREPO checkout

The practical route is a new numerical-flux option **inside the native FV
driver**, rather than sending Voronoi averages through the existing nodal-RD
time integrator. Source locations below refer to the baseline above.

| Existing component | Evidence in current source | Reuse / required change |
| --- | --- | --- |
| Native moving-mesh/FV call sequence | `src/main/run.c:247`, `:329`, `:365` | Reuse the FV half-call lifecycle and mesh rebuilds |
| Active-face selection and unique owner | `src/hydro/finite_volume_solver.c:211` | Reuse; compute one shared flux for that face |
| Face time interval and prediction offsets | same file `:1063` | Reuse interval choice; add coherent prediction for the third/fourth stencil cells |
| Extensive updates to inactive cells | same file `:500` | Reuse; native code explicitly updates local cells regardless of activity |
| Remote extensive increment exchange | same file `:588`, `:1766` | Reuse existing mass/momentum/energy transport |
| Voronoi primitive recovery | `src/hydro/update_primitive_variables.c:187` | Use the existing Volume branch, not the DualArea branch |
| Voronoi face endpoints | `src/mesh/voronoi/voronoi_2d.c:1346` | Endpoints are DTC[tt], DTC[qq]; expose transient adjacency to the new flux calculation |
| Triangle reference in a face | `src/mesh/mesh.h:178` | Existing TETRA_INDEX_IN_FACE can help recover the second triangle through DT adjacency |
| N eigenstructure and robust small solves | `src/hydro/residual_distribution_solver.c` | Extract/reuse kernels; do not copy its mass/time update or original triangle normals unchanged |
| Gradients and limiters | native FV reconstruction / face limiter | Reuse infrastructure, but verify corner-target reconstruction and its admissibility |

The native face driver multiplies flux density by area, time and its half-call
factor before depositing equal/opposite increments. A new routine should
return exactly the expected laboratory-frame ALE flux density. It must not
multiply by area/time again or subtract mesh transport twice. The current
Riemann branch and its coordinate transformations are inside this driver;
the extension needs a deliberate interface, not insertion at an arbitrary line.

At first, compute the two endpoint corner fluxes on demand for each owned
active face. That costs duplicate corner work, but preserves native face
ownership and does not need a persistent cross-step corner owner. Caching can
follow after validation, with keys including mesh epoch and prediction time.
The existing Delaunay/Voronoi geometry is already available within a live mesh.
An active face's extra corner states and gradients must really be present in
the ghost exchange: native two-cell completeness is not automatically a proof
of the larger stencil's completeness. A full-mesh prototype is an available
first correctness control, followed by a partial-mesh halo audit.

For reconstructed traces, finite-volume U denotes a cell average. Spatial
prediction must use the native cell-centroid interpretation and reach the
corner at a common time. Simply treating that average as an exact value at
the generator would reintroduce the inconsistency discussed in log 2 §7.6.
Likewise, the extra stencil cell's prediction offset must be computed from
its own state time, not copied from one of the face's two cells.

The `RESIDUAL_DISTRIBUTION` macro currently changes both driver selection and
primitive recovery. The proposed FV flux option should not accidentally select
those nodal-RD paths. A small shared N-kernel module with explicit build wiring
would be cleaner. LDA/F1 and Campoli/Arpaia mass formulas are tied to the old
representation and cannot simply be enabled in this option.

This is a new hydrodynamic flux method, but not a new mesh, domain decomposition,
MPI transport, output system or gravity engine. Those are material savings.
They do not establish that the new flux inherits all native FV stability or
the old RD accuracy properties.

## 6. Relative cost and recommended scope

The following is a structural assessment from the code, not a calendar estimate.

| Route | Mathematical change | Main AREPO work | Role now |
| --- | --- | --- | --- |
| Existing equal-step P1 RD plus conservative transfer | Smallest relative to current RD | Complete existing diagnostic transfer into a robust applied operator; its exact-patch and positivity behavior still need care | Closest reference for settling present moving-RD results |
| P1 fixed-connectivity macro epochs plus hierarchy | Moderate, with an explicit conservation composition | Persistent RD mesh/halo, valid geometry over an epoch, synchronized transfer | Useful mathematical reference; not automatically the cheapest implementation |
| P1 immediate-flip hierarchical integrator | Substantial temporal redesign | Element lifetime history, patch/edge registers, coherent states, MPI migration of pending work | Highest coupling risk among incremental P1 paths |
| True Voronoi FV with RD-derived corner flux | New spatial/temporal method, clear local conservation structure | New corner geometry/flux/reconstruction interface, reuse native FV loop and exchanges | Best bounded alternative to test before a major LTS rewrite |
| Full space-time RD or continuous alternative basis | Broad formulation change | New space-time mesh or basis/quadrature machinery | Longer-term research, not the present main implementation plan |

There is existing code for topology repair, but it is not the full formula
set validated algebraically in the previous audit: its compile-time guard
requires equal steps; exact changed patches are still a diagnostic comparison
in the inspected function; the applied high-order repair aborts on an
inadmissible state rather than implementing the patch-common convex fallback.
Do not estimate the remaining work as merely turning on a complete existing
positive remap.

I would keep the present RD result as the main reference and avoid making
Chapter 4 depend immediately on a full new integrator. The next design
experiment should be bounded and answer whether the native FV route retains
the multidimensional benefit with materially less machinery:

1. Add/extract only the necessary scalar/corner geometry and N-flux interface
   in an isolated copy, keeping native FV update/ownership. Establish agreement
   with the intended static corner residual on ordinary meshes.
2. Add Euler on a static mesh, with the existing native solver available as
   the reference/fallback. Check conservation and convergence; then test a
   moving prescribed mesh with flips using equal steps.
3. Exercise native local timesteps and MPI only after those gates. The new
   conservation total should close transaction by transaction; test uniform
   flow and temporal accuracy independently, including changing bins.
4. Compare one smooth vortex and one interface problem against both native
   FV and existing RD at comparable cost. Advance only if this establishes
   an advantage worth the new-method validation work.

The previous immediate-flip P1 lifetime work remains relevant if this route
does not preserve the desired RD behavior. The point of the prototype is to
measure that tradeoff before either approach consumes a large engineering effort.

## 7. Other ideas: what they remove and what they only reformulate

A topology-aware space-time method can treat old/new elements as parts of a
single weak balance, with compatible temporal interfaces. That is a principled
alternative to adding a correction after a hydrodynamic update. With the same
discontinuous P1 basis, however, the balance still has to account for its jump.
It cannot preserve an arbitrary old field in a new incompatible four-node
P1 space without approximation or extra degrees of freedom.

Colombo and Re express local adaptation through fictitious collapse/expansion
and swept geometric contributions; their formulation uses BDF and solves a
new-mesh residual system. This offers a coherent ALE interpretation, not an
existing explicit hierarchical AREPO algorithm. It moves representation
transfer into the geometric flux construction rather than making it vanish.
[Colombo and Re, §3](https://arxiv.org/html/2204.11668v1).

Gaburro et al. construct topology-aware closed space-time volumes with sliver
elements for ALE FV/DG. This establishes that topology changes need not prevent
a conservative formulation, while also illustrating the additional geometry.
[Gaburro et al.](https://arxiv.org/abs/1905.00967).

A genuinely different nodal route would use a partition of unity that varies
continuously with the moving point set, such as suitably designed natural-
neighbor or meshless bases, and consistent mass/geometric derivatives. This
would target the basis-jump mechanism itself. It does not follow that ordinary
P1 N/LDA formulas, positivity or LTS remain valid. AREPO currently supplies
neither the required basis integrals nor that time integration. This is a
research direction, not a lower-cost implementation recommendation.

## 8. What is established and what remains open

Established here: the finite P1 jump at an exact flip; the continuity contrast
with true Voronoi geometry; the conditional meaning of macro-epoch conservation;
the local conservative ALE corner algebra; a scalar verification of its flux
representation; and concrete reuse points in the current source.

Not established: a completed true-Voronoi Euler corner solver, discrete GCL
on changing topology, second-order LTS, positivity under the proposed flux,
robustness at degenerate corners, its MPI halo sufficiency, or favorable cost.
Native pairwise mass/momentum/energy conservation is a weaker, structural
property and can be retained before those harder properties are solved.

New reproduction artifact:
`tests/rd/audit_voronoi_corner_flux_algebra.py` (NumPy; optional Matplotlib plot).
Run output and figure are retained in
`/Users/zhenyuwu/arepo_rd/local_runs/topology_alternatives_20260909`.
This turn did not run a new Euler simulation or modify production solver code.
