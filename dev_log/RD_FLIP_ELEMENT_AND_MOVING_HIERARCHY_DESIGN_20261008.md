# Flip element and moving-mesh hierarchy: design report

Author: Claude Code (Opus 5.5), 2026-10-08, at the request of Zhenyu Wu.
Branch `feature/ale-flip-conservation-hierarchy`, based on `eacc3f9`. That
commit is a snapshot of the `develop_pureC_RD` state used for the submitted
thesis.

The approved plan is `~/.claude/plans/i-have-already-submitted-tender-spindle.md`.

**Aim.** Conserve mass, momentum and energy exactly and keep the state
positive across Delaunay edge flips on the moving-mesh RD solver. Then
extend hierarchical timesteps to the moving mesh, for N, LDA, B and FV-RD.

**Scope.** One MPI rank. The thesis is unchanged.

This report records the mathematics and the design, and states what has
been checked and how. Prior work it relies on:

- `RD_topology_hierarchy_conservation_20260909.md`
- `RD_moving_representation_design_20260909.md`
- `RD_SEDOV_TOPOLOGY_REPAIR_20260929.md`
- the Python actual-interval prototype
  `test/colombo-re-explicit-hierarchy:dev_log/colombo_re_spike/euler_flip_closure.md`

## 1. Where conservation is lost today

The equal-step ALE step stores Q_i = |S_i|U_i. All residual sweeps run on
the **new** connectivity, pulled back to x^n along linear trajectories
(`rd_ale_prepare_step`). The step loses conservation in two places.

1. **Basis change at t^n (the flip defect).** For every changed cavity C,
   take the same nodal U on two triangulations. The difference in the
   represented totals is

   $$D_C=\sum_{i\in C}\delta m_i\,U_i=\int_C\left(U_h^{\rm new}-U_h^{\rm old}\right)dA,
   \qquad \delta m_i=b_i-a_i .$$

   Here a_i and b_i are the old and new P1 lumped masses inside C (one third
   of each incident cavity triangle's area).

2. **Arpaia endpoint conversion.** Q^{n+1}=S^{n+1}U^{n+1} differs from the
   divisor ledger D_iU^{n+1}. The Campoli mass variant (`RD_ALE_CAMPOLI_MASS`)
   uses divisor S^{n+1} and temporal mass (A_old+A_new)/2, and has no such
   term. With no flips, Campoli conserves to round-off (log3 §27; Sod n32
   1.97e-16).

## 2. The flip defect

**Identities.** For any cavity:

- Σ δm_i = 0, because both triangulations tile C.
- Σ δm_i x_i = 0, because both P1 bases reproduce affine functions.

Hence D_C = Σ δm_i (U_i − L(x_i)) for every affine L. D_C vanishes for
affine conserved fields, and is O(Σ|δm| h²|∇²U|) when the field is smooth.

**Single 2-2 flip.** Take a quad abcd, with old diagonal ac and new
diagonal bd:

$$\delta m=\tfrac13\left(-|bcd|,\;+|acd|,\;-|abd|,\;+|abc|\right)\quad(a,b,c,d).$$

D_C is ±(det of [x_i, y_i, U_i, 1])/6 per component. Geometrically, it is
the signed volume of the **flip tetrahedron** spanned by the four points
(x_i, U_i). It is zero exactly when the four nodal values are coplanar.

*Checked:* 20 000 random convex quads with Euler states of contrast up to
10⁶. Defect = ∫(U_h^new − U_h^old) to 4.6e-12 relative (cancellation in
large totals). |D_ρ| equals the tetrahedron volume to 8.3e-14.

**Lower bound (prior work, Aug 26 §2.5 and log3 §17.2).** Let a map keep
all nodes outside C fixed and conserve the cavity totals. Then

$$\max_i|U_i^+-U_i^-|\ \ge\ |D_C|\Big/\sum_{i\in C}g_i^+ ,$$

and the uniform shift attains it. So no local formula can make the
perturbation smaller. It can only (i) place it, (ii) keep it admissible,
or (iii) make it happen less often (deferred flips).

## 3. The flip element

We treat each changed cavity as a **degenerate element whose residual is
D_C**, and distribute that residual with an RD-style blended scheme. In the
literature (section 7) this is the explicit, same-time counterpart of:

- the ghost elements of Colombo & Re (2022), whose residual is a pure
  volume-change term, stabilised for positivity;
- the space-time "sliver" elements of Gaburro et al. (2020).

The P1 analogue of the sliver is the space-time tetrahedron
(a^n, c^n, b^{n+1}, d^{n+1}). Our element is its zero-time-width limit.

**Notation.**
- g_i: full nodal mass before the flip.
- g_i⁺ = g_i + δm_i: full nodal mass after the flip.
- Q_i = g_i U_i: extensive state.

**High endpoint (linear-exact, centred).** Keep U and shift uniformly:

$$U_i^H=U_i-\frac{D_C}{\sum_jg_j^+},\qquad Q_i^H=g_i^+U_i^H .$$

Properties:
- conserves the cavity totals;
- unchanged for affine fields;
- has the minimal max-norm change;
- invertible at the same time (flip followed by its reverse is the
  identity);
- **not** a convex combination, so it can be negative at strong contrasts.
  Prior counterexamples: Sedov p = −0.019; E = (100, 1e-6, …) → −16.7.

This is the existing `RD_ALE_TOPOLOGY_REPAIR_DIAGNOSTIC` map.

**Low endpoint (positive, minimal mixing: donor-cell).**

- Donors (δm_i < 0) keep their state exactly: U_i^L = U_i.
- Receivers (δm_i > 0) take a convex combination:

  $$U_i^L=\frac{g_iU_i+\delta m_i\bar U_D}{g_i^+},\qquad
  \bar U_D=\frac{\sum_{j:\delta m_j<0}|\delta m_j|U_j}{\sum_{j:\delta m_j<0}|\delta m_j|}.$$

For a single 2-2 flip, this proportional plan is exactly the edge
donor-cell exchange along the quad edges. Donors a and c send to receivers
b and d the volumes

$$x_{ab}=\tfrac{|bcd||acd|}{3|Q|},\ x_{ad}=\tfrac{|bcd||abc|}{3|Q|},\
x_{cb}=\tfrac{|abd||acd|}{3|Q|},\ x_{cd}=\tfrac{|abd||abc|}{3|Q|},$$

and these reproduce every δm_i. (The median-dual analogue of Steinberg,
Yalinewich & Sari 2016, who fix the "volume inconsistency" with donor states.)

The low endpoint satisfies:

- **Conservation.** Exact.
- **Admissibility.** Every new state is a convex combination of old states.
  The set {ρ > 0, e(U) > 0} is convex, so the result is admissible.
- **Local density bounds.** Density stays within the hull of the mixed
  inputs.
- **Entropy minimum.** The specific entropy is quasi-concave in conserved
  variables, so K = p/ρ^γ ≥ min K of the mixed inputs.
- **Less diffusion than earlier low maps.** It is less diffusive than the
  earlier "full-patch average" low map (log2 §68.4): donors are untouched,
  and receivers mix only the fraction δm_i/g_i⁺.

*Checked:* 20 000 random flips with ρ ∈ [1e-3, 1e3], p ∈ [1e-6, 1e3] and
|v| ~ 3:
- edge volumes reproduce δm to 7.5e-16;
- conservation to 4.4e-16;
- all states admissible; donors unchanged; density within the hull;
- the entropy lower bound holds in exact rational arithmetic and in floating
  point for receiver mixtures.

*Implementation rule:* donor states must be kept bit-identical, not
recomputed as Q/g⁺. Recomputation lost ~1e-6 relative internal energy in
cold, fast gas and appeared to violate the entropy bound.

**Blend.** Q^θ = (1−θ)Q^L + θQ^H, with **one** θ ∈ [0,1] for the whole
cavity and all components. A per-node or per-component θ would break
conservation or convexity.

Choose the largest θ such that every node satisfies:
- ρ ≥ ρ_* and e ≥ e_* (positivity floors);
- ρ ∈ [ρ_min − r Δρ, ρ_max + r Δρ] over the cavity (relaxed density hull);
- K ≥ K_min.

θ = 0 is always feasible. Because of convexity, the feasible θ form an
interval [0, θ_max]. Find θ_max by bisection, with a final check on the
actual floating-point values and back-off (as in `limited_operator.md`;
`rd_lr_limit_bounds` does the same).

In smooth flow the high endpoint is accepted directly (θ = 1), so the map
equals the uniform shift. The low order enters only where bounds bind:
Sedov fronts and under-resolved KH layers.

**Optional refinement.** Write Q^H − Q^L as antisymmetric fluxes on the
cavity edges and limit edge by edge (Zalesak, or Guermond-style convex
limiting with the quasi-concave internal energy). This is more selective
than one common θ. It is implemented only if KH still shows a visible cost.

## 4. Where the transfer acts in the equal-step step

The transfer acts at t^n, before the divisor rebase in `rd_ale_prepare_step`:

- **Inputs.** Old masses a_i come from the triangle registry, stored at the
  end of the previous step at the same positions x^n. New masses b_i come
  from the pull-back of the new triangles (A_old/3).
- **Cavities.** Union-find components of the symmetric difference of the
  key sets. Keys are sorted ParticleID triples plus periodic image offsets.
- **Refresh.** After the transfer, primitives are refreshed for every
  scheme. Today only the Rusanov path refreshes them; N/LDA/B evaluate the
  predictor with unrepaired primitives.
- **Totals.** With Campoli, the transfer conserves the totals exactly, and
  the fixed-connectivity update telescopes. So the global budget should
  close to round-off for any state, and `RD-ALE-FINISH` can assert it.

## 5. Moving hierarchy: actual-interval closure

This is the design validated in Python (22 controls to ~1e-14, including
glass Sod and KH with thousands of cavity events):

- **Registry.** Each triangle has a persistent key, a birth time and its
  last integrated time s_T.
- **At each fine endpoint t,** for every changed cavity:
  - close the **entire old star** of each cavity vertex over [s_T, t];
  - refresh the cavity vertices;
  - apply the flip element (section 3).
- **New triangles** start at s_T = t.
- **Predictor mask.** A vertex predictor is live only if every incident
  triangle is due and all share the same actual start.
- **Deposit (Campoli-consistent moving F1 interval):**

  $$\Delta Q_{iT}=\tfrac{\Delta A}{3}U_i-\tfrac{h_T}{2}(\phi_i^0+\phi_i^1)
  +\tfrac{\Delta A}{6}dU_i+\tfrac{M}{3}\Big(dU_i-\beta_i^1\sum_jdU_j\Big),$$

  with M = (A_0+A_1)/2. N and HLLC use only the lumped part.
- **Why it conserves.** Unequal neighbouring intervals freeze the endpoints
  of the shared edge, so the shared-edge flux integrals cancel exactly.

Native work still needed:
- AREPO time-bin wake-up of cavity vertices at arbitrary fine endpoints;
- a policy for inverted pull-backs;
- the frozen-F1 accuracy issue (log3 §33);
- first-order accuracy across bin interfaces (as in the static hierarchy).

## 6. Deferred flips (stage 2, evaluation only)

P1 RD needs valid triangles, not Delaunay ones. A registry-driven RD element
set could keep a cavity's old triangles until either:
- a quality or in-circle-violation threshold is exceeded; or
- all cavity vertices are synchronised.

The second rule removes forced early closures in the hierarchy.
Gaburro's group mentions a "deferred-in-time" treatment of connectivity
changes (SISMA talk, 2022; no paper found). This stage is adopted only if
it lowers the KH perturbation or the hierarchy cost without loss of
accuracy.

## 7. Literature (verified unless marked)

- **Colombo & Re**, Comput. Fluids 239:105414 (2022), arXiv:2204.11668.
  ALE RD with edge swaps by fictitious collapse and expansion, ghost
  elements, implicit BDF2. Local adaptation of a deforming mesh, not a full
  rebuild.
- **Gaburro, Boscheri, Chiocchetti, Klingenberg, Springel & Dumbser**,
  JCP 407:109167 (2020), arXiv:1905.00967. Voronoi direct ALE with
  space-time sliver elements; Sedov included.
- **Gaburro, Klima, Bonafini & Tavelli**, arXiv:2605.23506 (2026).
  4D hole-like elements for 3D flips.
- **Bonafini, Torlo & Gaburro**, arXiv:2602.09198 (2026). Stability analysis.
- **Guardone, Isola & Quaranta**, JCP 230:7706 (2011); **Isola, Guardone &
  Quaranta**, JCP 285:1 (2015). Node-centred ALE with edge swaps.
- **Steinberg, Yalinewich & Sari**, MNRAS 459:1596 (2016),
  arXiv:1603.06753. Volume-inconsistency fix with donor states.
- **Loubère, Maire, Shashkov, Breil & Galera**, JCP 229:4724 (2010). ReALE.
- **Kucharik & Shashkov**, IJNMF 56 (2008). Swept remap with changing
  connectivity; details [unverified].
- **Alauzet & Mehrenberger**, IJNME 84:1552 (2010). P1-conservative
  interpolation with a maximum principle.
- **Kuzmin, Möller, Shadid & Shashkov**, JCP 229:8766 (2010). Failsafe
  limiting and constrained projections.
- **Bochev, Ridzal, Scovazzi & Shashkov**, JCP 230:5199 (2011).
  Optimisation-based remap.
- **Guermond, Popov, Saavedra & Yang**, SISC 39:A385 (2017); **Guermond,
  Popov & Saavedra**, JCP 401:108927 (2020). Invariant-domain ALE and
  convex limiting.
- **Boscheri, Dumbser & Zanotti**, JCP 291:120 (2015). Conservative ALE
  local time stepping, with fixed topology.
- **Hubbard, Ricchiuto & Sármány**, CAMWA 79:1561 (2020). Space-time RD with
  fixed connectivity.
- **Ricchiuto, Csík & Deconinck**, JCP 209 (2005). Space-time RD.
- **Gap.** No published scheme combines local time stepping with mid-step
  reconnection.

## 8. Next steps (Phase 1)

1. `src/hydro/rd_flip_transfer.h`: a pure-C kernel. Add a ctypes test
   `tests/rd/test_flip_transfer.py` and put it in `make check_rd`.
2. `src/hydro/rd_ale_registry.{c,h}`: persistent keys with periodic offsets,
   cavity grouping.
3. `RD_ALE_FLIP_TRANSFER` wiring, primitive refresh for all schemes, and
   Campoli for all schemes (including HLLC-RD).
4. Native gates, then Sedov, KH 48/96, Yee and Gresho.
