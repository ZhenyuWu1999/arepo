# Sod initial-condition, coordinate and resolution audit

2026-09-28, Codex. User asked whether the current tube coordinates/time and
effective resolution match Morton et al. (2023), including the periodic mirror
problem, and requested a comparison with SWIFT's standard 2D Sod IC.
No solver run, production/IC modification, thesis edit or Git publication.

## Findings

- The current conversion `xi=2(x-.25), tau=2t` is correct for the displayed
  half-box tube. The existing analytic reference uses gamma1.4 and the correct
  raw coordinates/time; it is not accidentally comparing rawt=.08 with
  unit-tube time=.08. An independent coordinate-rescaling check at10001
  positions has zero numerical difference.
- The full box has16384 nodes (128²); the initial effective longitudinal
  resolution of the displayed length-.5 tube is Nx=64. The mirror is already
  accounted for. This is nominal spacing equivalence to Morton's N64, not
  identical geometry or a claim that glass has literal columns.
- Primitive left/right states match Morton, but the EOS does not: ours
  gamma1.4, Morton5/3. Mesh layout, timestep choice and temporal method also
  differ. Current figures are not a reproduction of Morton Fig7.
- SWIFT SodShock_2D defaults to gamma5/3 and rhoR=.140625, not .125. It uses
  two different glass number densities to obtain equal nominal particle
  masses. Its `glassPlane_128` is not equivalent to our effective Nx64, nor to
  a uniform Nx128 across its plotted unit-width tube.

## Current data, not the older campaign template

Audited actual IC:
`../../local_runs/sod_static_matched_20260928_v1/inputs/sod_glass_nx64.hdf5`.
SHA256 `0cf27ca817f58e4a3fc9cc6275b8593fab82a70f8dfe113ae68bcfc34b49935c`.
It is shared by all four September28 static and two September24 lab moving
cases. Checked their archived Config, parameter hashes, IC hashes and t=0
snapshots, rather than relying on an older shocktube generator whose geometry
uses a length10 box and two interior discontinuities.

Actual box: `[0,1) x [0,1)`, periodic, with

| Raw x | rho | vx, vy | p | Specific internal energy e |
|---|---:|---:|---:|---:|
| [0,.5) | 1 | 0,0 | 1 | 2.5 |
| [.5,1) | .125 | 0,0 | .1 | 2 |

The second discontinuity is at the periodic seam x=0=1. It is the reversed
Riemann problem; it is not a reflecting wall. The continuum fields have the
mirror relation, but the individual glass positions are not mirror copies.
The IC positions equal the local SWIFT glassPlane_128 coordinates modulo1
bit for bit. All16384 are independent physical nodes in this full box.

The input field named `Masses` contains density under
`READ_MASS_AS_DENSITY_IN_INPUT`. In `src/init/init.c`, RD multiplies it by the
median-dual area. Snapshot0 confirms rho/p/e/v as above to1e-14. Consequently,
this IC is approximately uniform in point spacing, with differing masses;
it is not SWIFT's equal-mass two-density sampling.

## Coordinates, time and isolation from the mirror

The selected tube is raw x in(.25,.75), retaining the full y range. Its
discontinuity x=.5 maps to xi=.5 under

    xi = (x-.25)/.5 = 2(x-.25),       tau = t/.5 = 2t.

For the pseudo-1D continuum solution, both temporal and longitudinal spatial
derivatives acquire the same factor2, leaving the Euler equation unchanged.
Velocity, density and pressure retain their numerical values; in particular
dxi/dtau=dx/dt. A full2D similarity transformation would also scale y by2;
the resulting transverse extent need not equal that of another pseudo-1D
test. Equal initial Nx does not enforce identical transverse mesh noise.

Current rawt=.08 is tau=.16. The exact gamma1.4 solution gives

| Feature | Speed | Raw x at t=.08 | xi at tau=.16 |
|---|---:|---:|---:|
| Rarefaction head | -1.18321596 | .40534272 | .31068545 |
| Rarefaction tail | -.07027281 | .49437817 | .48875635 |
| Contact | .92745262 | .57419621 | .64839242 |
| Shock | 1.75215573 | .64017246 | .78034492 |

In the exact periodic continuum problem, the two shocks first meet at x=.75
when rawt=.25/1.75215573=.14268138 (tau=.28536276). The rarefaction heads meet
later. Thus the present end time precedes physical mirror interaction; this
calculation is not a claim of zero numerical influence at arbitrary precision.

## Effective initial resolution

For this spatially uniform glass, use the nominal area-based separation

    h0 = sqrt(A_box/N_total) = sqrt(1/16384) = 1/128,
    Nx,eff = L_tube/h0 = .5/(1/128) = 64,
    Delta xi = h0/.5 = 1/64.

Raw quarter counts are4091,4099,4088,4106; the displayed tube initially
contains4099+4088=8187 nodes. Taking sqrt8187 as longitudinal resolution would
be wrong because this is a .5-by-1 rectangle. The128 plotting bins also do not
create Nx128 physical resolution. The label should retain both quantities:
`N_tot=128²; initial N_x,eff≈64`. The equal-spacing full-box analogue of
Morton's N128 would be256² in this periodic geometry; this does not match the
paper's structured layout or temporal method automatically.

## Morton et al. (2023)

Primary source: [§5 introduction, §5.1.1 and Fig7, author manuscript](https://www.pure.ed.ac.uk/ws/portalfiles/portal/327346950/2204.01757v2.pdf),
printed pp.9–10; [published article](https://doi.org/10.1093/mnras/stac3427).

The paper specifies (rho,v,p)L=(1,0,1), (rho,v,p)R=(.125,0,.1), gamma5/3,
CFL.4, first-order LDA1/N1, N64/128 vertices along x. Its uniform mesh is a
Cartesian placement with alternate rows shifted by half a spacing. The final
time and exact Sod boundary implementation are not stated in the examined
section/caption; an inferred time from the figure is not verified run metadata.

Changing gamma is not a coordinate/unit relabelling. For the same rho,p,
initial eL/eR are1.5/1.2 at5/3 instead of2.5/2 at1.4. Computed exact star states
also differ: (p*,v*)=(.30313018,.92745262) for ours and
(.29394519,.84119485) for Morton. These numbers are our Riemann calculations,
not quoted values from the paper.

The earlier static/moving and F1/FE internal controls remain valid matched-IC
comparisons. Their common IC does not become paper-matched merely by converting
x,t to xi,tau. Reproduction would require matching gamma, structured geometry,
N, temporal scheme, CFL, boundary treatment and output time.

## SWIFT SodShock_2D

Checked local SWIFT HEAD8dc43c3c1f08755250a2c0edd141d78120d00b21 and upstream
HEADb2ac805c50054fb9de2836f77bfd7966071e6748. makeIC.py and sodShock.yml are
byte-identical locally/upstream; plotSolution.py differs only in whitespace.
Pinned sources:

- [IC generator](https://github.com/SWIFTSIM/SWIFT/blob/b2ac805c50054fb9de2836f77bfd7966071e6748/examples/HydroTests/SodShock_2D/makeIC.py).
- [Run parameters](https://github.com/SWIFTSIM/SWIFT/blob/b2ac805c50054fb9de2836f77bfd7966071e6748/examples/HydroTests/SodShock_2D/sodShock.yml).
- [Plotting/analytic reference](https://github.com/SWIFTSIM/SWIFT/blob/b2ac805c50054fb9de2836f77bfd7966071e6748/examples/HydroTests/SodShock_2D/plotSolution.py).

Defaults: gamma5/3; left rho1,p1,v0; right rho.140625,p.1,v0. Box is2-by-.5
in2D, with physical periodic seam and central jump at stored X=1. The plotted
coordinate q=X-1 is shown over[-.5,.5]; using xi=q+.5 merely shifts the
displayed unit-width interval, so tau=t_SWIFT for that comparison window.
Default finalt=.2, CFL.1. Our tau=.16 is earlier; matching SWIFT's default time
in our raw length-.5 tube would require rawt=.1, alongside EOS/state matching.

The IC generator takes unit-square128² and48² glasses, scales each by.5, then
tiles two copies along x on its respective side. Nominal counts and spacings:

| Quantity | SWIFT left | SWIFT right |
|---|---:|---:|
| Full-side node count | 2×128²=32768 | 2×48²=4608 |
| Side area | .5 | .5 |
| Initial nominal spacing | 1/256 | 1/96 |
| Nominal longitudinal intervals in the displayed half-tube of length.5 | 128 | 48 |
| Nominal mass per particle | 1/65536 | 1/65536 |

Total37376. Local cached input glasses verified to contain16384 and2304
points. Counts above describe their nominal tiled blocks, not literal glass
columns or a newly computed SPH density field. Small glass displacements do
not change this nominal resolution convention.

From the code's mass formula and equal side areas,

    rhoR/rhoL = (48/128)² = 9/64 = .140625

makes the particle masses equal. This equality follows directly from the
generator; no distinct author-intent claim is needed. Our equal-spacing glass
instead carries the density jump mainly through different nodal masses.
Across the common unit-width plotting interval, our Delta xi=1/64 on both
sides; SWIFT has1/256 left and1/96 right. Its left spacing is4 times finer and
right spacing1.5 times finer. There is no single uniform Nx128 for that IC.
SPH's smoothing length/kernel support further prevents equating point spacing
alone with the RD method's effective resolving power.

## Reproducibility

Archive `../../local_runs/sod_ic_audit_20260928_v1/` contains audit.py,
audit.json (input hashes, six snapshot checks, coordinate identity, exact wave
calculations, node counts), upstream.json and copies of pinned SWIFT sources.
Only read existing physical inputs/results; all remembered hashes rechecked
unchanged. No new evolution, solver/default/IC/thesis edits, commit or push.
