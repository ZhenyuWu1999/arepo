# Blob setup comparison: current RD, Braspenning and Morton

2026-10-22 — Codex (GPT-6), with Zhenyu Wu; local Mac.

**The downloaded RD campaign follows the available Morton BLOB setup. It is
not a matched reproduction of Braspenning's experiment.** Thermal pressure
balance is correct, but matching chi and approximately matching Mach number
does not match the domain, cloud sampling, integration or mass diagnostic.

## Evidence and scope

- AREPO checkout: `feature/3d-moving-mesh`, HEAD `35ecccd16083`; earlier
  uncommitted interface and analysis work is preserved. Downloaded COSMA
  source provenance is established in shared-log entry 21.
- Current IC: `../cosma_runs/blob3d_mac_analysis_20261020_v1/inputs/blob32.hdf5`,
  SHA256 `08457a2040209225e5c57db7a6abf7a13de97bd7e02231b6f0aef0e158c21926`.
- Available predecessor: `/Users/zhenyuwu/rdsolver`,
  `adfbe55586fc926f1911dbecfbdb915c8f667c11`, especially `rd/setup3D.cpp`
  and `rd/constants3D.h.TEMPLATE`. This is not recovered publication-run
  configuration or snapshot provenance.
- SWIFT local checkout: `/Users/zhenyuwu/SWIFT`, clean at
  `8dc43c3c1f08755250a2c0edd141d78120d00b21`.
- Independently downloaded upstream SWIFT sources are pinned to
  `4a7fadaf4a0e23ed60dcddb29d17cca7d8a7182c` (2026-10-21). This is a
  current source inspection; Braspenning reports using SWIFT 0.9.0.
- Audit archive:
  `../local_runs/rd_3d_blob_setup_comparison_20261022_v1/`, containing source
  copies, SHA256 manifests, primary-paper HTML, `source_audit.json` and
  `comparison_values.json`. Both OMP/OpenBLAS thread limits are one.

No solver is built or evolved, no cluster is accessed, and no archived IC or
script is edited. Attempts to access the official n=32, chi=10/100 HDF5 URLs
time out during TLS handshakes; an IPv4 curl retry also times out with zero
bytes. Thus published sampling estimates below are **not measured counts
from those official IC files**. Their absolute thermodynamic values and exact
point realization have not been independently recovered in this task.

## 1. Compare dimensionless setups and diagnostics

The primary descriptions are [Braspenning, Methods](https://arxiv.org/html/2203.13915v2#S2)
and [Morton, section 5.3.1](https://arxiv.org/html/2204.01757v2#S5.SS3.SSS1).
The SWIFT [dedicated analysis script](https://github.com/SWIFTSIM/SWIFT/blob/4a7fadaf4a0e23ed60dcddb29d17cca7d8a7182c/examples/HydroTests/BlobTest_Braspenning2022/plot_cloud_evolution.py)
independently confirms the density selection and radius-based clock.

| Quantity | Downloaded RD campaign | Braspenning setup | Morton paper / available implementation |
| --- | --- | --- | --- |
| Density contrast chi | 10 | 10 and 100 | 10 in BLOB source |
| Gamma | 5/3 | 5/3 in SWIFT analysis | 5/3 in source |
| Initial thermal balance | p=100; rho_cloud/rho_wind=100/10 | equal thermal pressure, T_wind/T_cloud=chi | same nodal values in BLOB source |
| Wind Mach number | 1.506436 | 1.5 | nominal 1.5; BLOB source gives the same 1.506436 |
| Box dimensions / cloud radius | 10 x 10 x 10 | 40 x 10 x 10 | 10 x 10 x 10 |
| Boundaries | periodic in all directions | periodic in all directions | periodic in available configuration |
| Initial points | uniformly random, NumPy seed 68315 | grid sampling, enhanced inside cloud | random vertices; exact publication realization unavailable |
| Cloud / wind point number density | equal in expectation | approximately chi | same uniform sampling concept as current RD |
| Mesh / solver | static tetrahedral N/lumped RK2, equal or hierarchical | multiple SPH, MFM, MFV, moving-mesh and AMR methods | static tetrahedral N1 figures |
| Dense/cold cloud selection | rho>0.64 rho_cloud AND T<0.9 T_wind | rho>rho_cloud/3 | same combined selection as current analysis |
| Clock | diameter-based t_cr; also t_KH=1.6 t_cr | radius-based t_cc | t_cr in sections; t_KH in Fig. 20 |

Absolute code-unit density, pressure and length need not agree for these
non-radiative scale-free Euler problems. Dimensionless controls, boundaries,
sampling and diagnostics do. The actual current sound speed is
sqrt((5/3)*100/10)=4.082482905; v=6.15 gives Mach 1.506436192, about 0.429%
above 1.5. Exact Mach 1.5 with the same p/rho would use v=6.123724357.
Retain v=6.15 when comparing against the available Morton source; changing it
would define a separately labelled control, not repair a demonstrated error.

Morton's prose prints both cloud and wind density as 100 despite stating a
factor-ten contrast. The inspected BLOB function explicitly uses 100/10.
Its printed wind speed 6.2 is rounded; the available code uses 1.5*4.1=6.15.
Source agreement cannot establish the provenance of the missing figure runs.

## 2. Equal nominal n does not give equal cloud resolution

Let n denote wind points per transverse box width, and R/L=0.1. The idealized
sampling estimates are

```
current uniform sampling: N_cloud ~ (4*pi/3) (0.1*n)^3
Braspenning sampling:     N_cloud ~ chi * (4*pi/3) (0.1*n)^3
                         N_total ~ 4*n^3 + (chi-1)*(4*pi/3)*(0.1*n)^3.
```

At wind n=32 and chi=10, current RD has **140 measured cloud nodes**,
whereas the reference rule implies about **1373 cloud nodes**, with about
132307 total nodes rather than 32768. The radius spans 3.2 mean internal
spacings here, versus approximately 6.89 under the reference sampling rule.
At chi=100 the analogous estimates are 13726 cloud nodes and 14.85 internal
spacings per radius. These are geometric estimates; boundary cutting and
integer grid choices change exact counts.

The reference's roughly equal particle masses and the current RD's roughly
equal volume sampling distribute resolution differently. This matters near
the contact even when the integrated initial cloud mass is accurate. The
domain aspect ratio is another independent difference. Initial wind advection
over one box length takes 3.16 t_cc here versus 12.65 t_cc in the long tunnel
at chi=10; these are nominal transport times, not measured onset times of
periodic contamination. No boundary effect is established by that estimate.

## 3. Use the dedicated SWIFT reference, not its generic Blob example

SWIFT has two distinct example directories:

- [BlobTest_Braspenning2022](https://github.com/SWIFTSIM/SWIFT/tree/4a7fadaf4a0e23ed60dcddb29d17cca7d8a7182c/examples/HydroTests/BlobTest_Braspenning2022)
  explicitly identifies itself as the paper reproduction. `getICs.sh` supplies
  official IC URLs labelled by wind resolution and chi. `blob.yml` defaults
  to `blob_16_100.hdf5`, periodic boundaries, CFL 0.1, dt_max=1e-4,
  time_end=0.1, a 10 K temperature floor and H fraction 0.76. The README's
  run command includes the timestep limiter. Those dimensional limits and
  floor need conversion against the actual IC units before copying them.
  Its `plot_cloud_evolution.py` uses rho>rho_cloud/3 and derives t_cc from
  the initial wind velocity and 0.1 times the box width. The analysis also
  defines intermediate-temperature and coarse-grained diagnostics separately.
- [BlobTest_3D/makeIC.py](https://github.com/SWIFTSIM/SWIFT/blob/4a7fadaf4a0e23ed60dcddb29d17cca7d8a7182c/examples/HydroTests/BlobTest_3D/makeIC.py)
  is a different, generic BCC example. Its default argument named Mach is
  2.7. As written, u_wind=v_wind^2/[M_arg^2*(gamma-1)], so for the ideal-gas
  sound speed c_s^2=gamma*(gamma-1)*u it implies M_actual=M_arg/sqrt(gamma),
  or 2.09141 at gamma=5/3. This is an algebraic source observation about
  that example, not a claim about the dedicated paper ICs.

The generic BCC generator has `2*(num_on_side//2)^3` points per unit cube,
not `num_on_side^3`. Direct execution of its four coordinate functions gives
8192 wind points per unit cube and 331 cloud points for argument 32, chi=10;
the total four-cube setup has 33072 points. Therefore its argument 32 is not
the paper's wind n=32. These generic-example counts must not replace the
reference sampling estimates in section 2. No full SWIFT simulation or Writer
invocation is used for this coordinate/source audit.

Nominal CFL numbers also do not equate timesteps across solvers. Current
COSMA uses CFL .01 with its RD spectral selector and timestep quantization;
the dedicated SWIFT example uses .1 with its own scheme-dependent selector.
The earlier [N1 diagnosis](RD_3D_BLOB_N1_DIAGNOSIS_20261020.md#3-n1-versus-the-current-nlumped-rk2-update)
already measures the predecessor/current selector difference on the actual
RD mesh. There is no claim of matched temporal errors across these methods.

## 4. Clock and threshold differences already affect the existing curves

For the same R, chi and v:

```
t_cc = R*sqrt(chi)/v
t_cr = 2*t_cc
t_KH = 1.6*t_cr = 3.2*t_cc.
```

Re-expressing the previously measured N/equal half-mass interpolations from
entry 22 gives 0.8084 t_cc for the Morton criterion and 1.2738 t_cc for the
Braspenning density criterion. This is a changed diagnostic on the **same
current simulation**, not a matched Braspenning run. The temperature cut does
not bind at any saved current state under the Morton density cut. Fig. 20's
traced Morton n=32 half-mass point is about 2.262 t_cc, still later than the
current 0.8084 after consistent conversion. Changing comparison papers does
not explain that remaining gap.

## 5. Implications for subsequent controls

The subsequent [COSMA campaign plan](RD_3D_BLOB_COSMA_PLAN_20261022.md) and
shared-log entry 25 turn these recommendations into staged mesh/resolution
controls and retain the numerical handoff tables. They remain proposed work.

Keep the current archived Morton-inspired campaign intact. For a quantitative
Braspenning comparison, obtain the dedicated official IC, verify its actual
Mach/chi/coordinates/masses/units, and adapt its long periodic box and enhanced
cloud point density to RD with explicit median-dual initialization. Apply
the same density criterion and radius-based clock, recording any change
introduced by meshing or loading. Use a separately archived short pipeline
gate before a full cluster run; no such run is submitted here.

For the unresolved Morton discrepancy, retain the current physical setup
and perform a full N1-versus-RK2 control on the same mesh with recorded actual
timesteps, while retrieving the original figure analysis and run provenance.
Entry 22's spatial-kernel agreement and shared contact limitation remain the
relevant evidence. Neither the SWIFT example nor a new IC should be used to
retroactively classify the existing run as a publication reproduction.
