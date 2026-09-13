# Same-time signed geometry for a P1 2-to-2 flip

Research spike, 2026-09-10, branch `test/colombo-re-explicit-hierarchy`.
Implementation: `tests/rd/colombo_re_geometry.py`. This note concerns geometry;
it supplies neither a fluid residual distribution nor a hierarchy scheme.

## Scope and source

The borrowed construction is the signed semi-edge sweep and the separate
old ghost/new element records described in Colombo & Re (2022), sections
2.5, 3 and 3.1. Their published fluid method uses these geometric quantities
in an implicit space-time residual; the Python module does not reproduce
that time solver. Source: [primary full text](https://arxiv.org/html/2204.11668v1).

The module handles two triangulations of one strictly convex four-node
cavity at the same physical time. Both triangulations occupy the same
physical region. All four vertices collapse linearly to a common point
inside the cavity; new elements expand along the reverse vertex paths.
Input triangles may be listed CW or CCW. Output records are CCW and retain
node IDs. Degenerate/nonconvex cavities are explicitly rejected.

## Signed area convention and an independent integral check

For a CCW-oriented boundary segment from `a` to `b`, the outward integrated
normal is the clockwise rotation of `b-a`. With linear endpoint paths from
`(a0,b0)` to `(a1,b1)`, define

\[
S(a,b)=\operatorname{signedArea}[a_0,a_1,b_1,b_0].
\]

A contracting triangle has a negative total outward sweep. The polygon
formula is computed using coordinates relative to its first point to avoid
unnecessary cancellation under translations. Independently, the code
evaluates

\[
\int_0^1\!\int_0^1
  \left[(1-s)(a_1-a_0)+s(b_1-b_0)\right]\cdot
  R_{\rm cw}\left[(1-t)(b_0-a_0)+t(b_1-a_1)\right]\,ds\,dt.
\]

Two-point Gauss quadrature in each coordinate is exact for this integrand.
This check avoids implementing the HTML rendering of paper equation 22
literally: its endpoint-difference expression is suspect, since a rigidly
translating segment has unchanged segment vector but generally nonzero
swept area. The independently derived polygon and surface-integral forms
agree. No claim about whether this defect originates in the PDF or HTML
conversion is needed for the implementation.

Split every oriented element edge `i -> j` at its moving midpoint. Assign
the first half to `i` and the second half to `j`. The sum of its two assigned
semi-edge sweeps is `integrated_nu[i]` for that element. These are signed
areas, not rates; a caller may form a rate only after specifying its time
discretization.

## Exact geometric identities and what they do not imply

Each old ghost has area change `-A_old`; each new record has `+A_new`.
The records satisfy

\[
\sum_{i\in K}N_i^K=\Delta A_K,
\qquad N_i^K=\int\nu_i^K\,dt.
\]

Internal semi-edges cancel between adjacent elements of each triangulation.
Every external semi-edge goes out and back on the same path, so its old/new
contributions cancel. Consequently, across the complete event,

\[
\sum_{K\ni i}N_i^K=0\quad\hbox{for every cavity node }i.
\]

The P1 nodal mass change is a *different* quantity:

\[
\Delta m_i=\tfrac13\sum_{K\ni i}\Delta A_K.
\]

It is generally nonzero even though the nodal summed swept coefficient is
zero. For a unit square with old diagonal 0--2 and new diagonal 1--3,

\[
\Delta m=(-1/6,1/6,-1/6,1/6),
\qquad \sum_K N_i^K=0.
\]

With collapse point `(1/2,1/2)`, the record coefficients are

| Record IDs | Kind | Integrated coefficients, in ID order |
|---|---|---|
| 0,1,2 | old ghost | -1/8, -1/4, -1/8 |
| 0,2,3 | old ghost | -1/8, -1/8, -1/4 |
| 0,1,3 | new | 1/4, 1/8, 1/8 |
| 1,2,3 | new | 1/8, 1/4, 1/8 |

For a *common* nodal trace `U_i` across all records, these identities imply
`sum_K sum_i U_i N_i^K = 0`. They do not imply cancellation if the old and
new records use different evolving/frozen traces. Nor do they define the
nodal distribution of the total residual. A separate explicit topology
operator must establish conservation, GCL and admissibility after that
distribution and its mass update are chosen.

## API and periodic images

```
result = geometry_records(x, old_triangles, new_triangles, collapse_point=None)
```

`result` is JSON-compatible. `records` contains `ids`, `old_or_new`,
`is_ghost`, `area_before`, `area_after`, `signed_area_change`,
`integrated_nu`, and the individual `semi_edges`. Patch arrays `old_mass`,
`new_mass`, `mass_delta`, `node_integrated_nu` align with sorted `node_ids`.
`checks` reports element GCL, nodal cancellation, external round-trip
cancellation, total mass change, and polygon/integral disagreement.

Coordinates must form one continuous periodic embedding. Use
`embed_periodic(x_wrapped, image_shifts, box)` with caller-provided integer
image shifts. The module does not infer winding from wrapped coordinates,
and it cannot detect a physically wrong but geometrically valid embedding.
The tests check known consistent image shifts and common translations; they
do not validate AREPO's distributed cavity reconstruction or periodic halo
ownership.

## Consecutive adjacent flips: retain more than net area

The test uses a convex pentagon and the sequence

```
012,023,034 -> 013,123,034 -> 014,123,134.
```

Summing event nodal mass changes agrees with final-minus-initial P1 masses.
Each event separately has zero nodal summed sweep. However, the intermediate
triangle `013` can have zero net area history and nonzero net nodal sweep if
the two events use different collapse points. In the recorded example its
birth-plus-death coefficients, ordered `0,1,3`, are

```
[0.37215972865401736, -0.6021670902061383, 0.23000736155212104]
```

Their sum is zero, but each entry need not vanish. Therefore, deleting all
records with zero net area, or retaining only the final old/new triangle
set, does not in general preserve a prescribed sequential sweep history.
One may deliberately choose a different direct cavity path; that is a
different geometry construction whose state update must be assessed.
When the intermediate triangle is born and dies via the same collapse
point, its reverse sweeps do cancel. General event histories need not meet
that condition.

Changing the common collapse point changes individual record coefficients,
while preserving all above geometric identities. Geometry alone therefore
does not select a unique distributed fluid update or prove path independence.

## Bounded verification

Command, run in the repository with NumPy available:

```
python tests/rd/colombo_re_geometry.py --samples 1000 > geometry.json
```

The tested interpreter was
`/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python`, seed 2231. The
1000 random cavities are vertex-jittered squares with random convex-combination
collapse points; they do not sample near-degenerate/nonconvex cases.

| Measurement | Maximum absolute discrepancy |
|---|---:|
| Element summed sweep minus area change | 3.33e-16 |
| Per-node summed sweep | 1.39e-16 |
| External semi-edge round trip | 1.11e-16 |
| Total nodal mass change | 3.33e-16 |
| Polygon versus independent surface integral | 1.11e-16 |
| Input CW/CCW and element ordering changes | 0 |
| Known periodic embedding / common translation | 4.44e-16 |
| Adjacent-event mass additivity | 1.11e-16 |

These are geometry tests only. They prove neither Euler positivity nor
accuracy, stable collapse-path fluid marching, arbitrary overlapping-cavity
scheduling, or MPI consistency.
