# Smoothed KH on the moving mesh

## Problem definition

Throughout this folder, **smoothed KH** means the glass48 Kelvin--Helmholtz
initial condition with transition width \(w=0.025\),

\[
B(y)=\frac12\left[
\tanh\left(\frac{y-0.25}{0.025}\right)
-\tanh\left(\frac{y-0.75}{0.025}\right)
\right].
\]

The density and streamwise velocity are \(\rho=1+B\) and \(v_x=-0.5+B\);
\(p=2.5\), \(\gamma=1.4\), and
\(v_y=0.1\sin(4\pi x)\). The IC is a relaxed periodic glass, SHA256
`e2db4f6f1b3682029f13f93bafd2e1f89dc4b8e6ad0920203d564123b1e47888`.
There is no additional runtime filter or damping layer.

The matched moving runs use Arpaia equal-step ALE, the P1(U) contour total,
the element-comoving frame, \(f=1\), and coherent RK2 total residuals unless
stated otherwise.

## Successful attempts

- **Scalar B:** completed the smoothed glass48 KH test to \(t=10\) with
  \(f=1\). This is the current temporary robust moving-mesh method. It is less
  dissipative than pure N but costs about 20 per cent in matched Gresho error
  relative to LDA and lowers the measured Yee order to about 1.4.
- **Pure N:** completed the identical \(f=1\) test to \(t=10\). It is the
  robust low-order control, but has a roughly 5 per-cent lower and later
  transverse-energy peak and 8.5 per-cent lower final density standard
  deviation than scalar B.
- **Static LDA control:** completed to \(t=2\), demonstrating that the failure
  is specific to long-time moving LDA rather than the KH IC alone.

Reducing the fluid-following fraction to \(f=0.90\) or \(0.75\) also completed
to \(t=10\), but this is not accepted as a solution: \(f=0.95\) still failed,
and the successful values measurably surrender the Galilean/boost advantage.

## Failed or rejected attempts

- Moving contour-LDA failed at \(t=0.46442\) on the glass through negative
  endpoint mass.
- Moving Roe+split LDA failed at \(t=1.15515\) through a non-physical RK
  predictor. Changing the element-total formula therefore does not cure the
  problem.
- Component-wise B delayed but did not prevent failure; the final matched run
  stopped at \(t=0.873680\).
- Targeted entropy-mode dissipation changed the entropy excursion but not the
  order-one failure time.
- Four-times-stronger ordinary mesh regularisation left the \(f=1\) failure
  essentially unchanged.
- A shock/all-wave mesh-velocity sensor was tested as a moving-N Sod
  discriminator. The shock arm was nearly inert; the all-wave arm changed the
  topology and extrema without reducing the transverse-noise floor. It was not
  a direct successful KH treatment.
- Per-step a-posteriori rollback restored the LDA trial and recomputed the
  flagged vertex star with N. Two retries were accepted, but the third failed
  because the incoming LDA history was already contaminated. Expanding the
  patch to 24.5 per cent of all triangles did not change the bad nodal value.
- Replacing jitter with a relaxed glass reduced structured-mesh artefacts but
  did not remove the moving-LDA failure.
- Zero mesh velocity, disabled regularisation and first-flip timing were useful
  isolation controls, but did not supply an \(f=1\) LDA remedy.

Local LF, Bmax, Dobeš--Deconinck Bx, SUPG and the shear-eigenvalue floor were
proposed but not run as production KH candidates; they are not failed
experiments.

## Figures

### Main solution comparison

- `glass-kh-static-moving-density.png`: static LDA, moving Roe-LDA, moving
  contour-LDA and moving N.
- `kh-b-n-density-matched-t0-t08.png`: matched component-B, scalar-B and N
  evolution through the component-B failure precursor.
- `kh-b-n-density-long-t1-t10.png`: long scalar-B/N morphology and the
  component-B failure.
- `kh-b-n-diagnostics.png`: density minimum, transverse kinetic energy and
  density standard deviation.
- `scalarb-kh-density-t0-t10.png`: scalar-B long-time density evolution.
- `scalarb-kh-theta-history.png`: scalar-B limiter activity.

### Failed-remedy diagnostics

- `kh-entropy-sweep-density.png` and `kh-entropy-sweep-curves.png`:
  entropy-dissipation test.
- `kh-fraction-threshold.png` and `kh-fraction-long.png`: mesh-following
  fraction threshold and long runs.
- `gresho-boost-fraction-profiles.png`: Galilean cost of reducing \(f\).
- `kh_aposteriori_density_comparison.png`,
  `kh_aposteriori_minima_history.png` and
  `kh_aposteriori_halo_growth.png`: rollback/fallback experiment.
- `sod-n-mesh-sensor-profiles.png` and
  `sod-n-mesh-sensor-evolution.png`: supporting mesh-velocity-sensor
  discriminator; this is Sod rather than KH.
