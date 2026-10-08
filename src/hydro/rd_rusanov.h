/* Experimental P1 Euler Rusanov RD kernel. No AREPO state or floors.
 * See dev_log/RD_SEDOV_POSITIVITY_20260929.md for the CFL/convexity argument.
 * n[j] is the inward length-weighted normal opposite vertex j.
 */
#ifndef RD_RUSANOV_H
#define RD_RUSANOV_H
#include <float.h>
#include <math.h>

static double rd_rusanov_internal(const double u[4])
{
  return u[3] - 0.5 * (u[1] * u[1] + u[2] * u[2]) / u[0];
}

static int rd_rusanov_admissible(const double u[4])
{
  return isfinite(u[0]) && isfinite(u[1]) && isfinite(u[2]) && isfinite(u[3]) && u[0] > 0.0 &&
         isfinite(rd_rusanov_internal(u)) && rd_rusanov_internal(u) > 0.0;
}

/* Return alpha, or -1 on invalid input/bar states.  Each pair bar state is
 * checked as well as the analytic endpoint wave-speed bound: do not accept
 * loss of positivity due to unresolved kinetic/internal-energy cancellation.
 */
static double rd_rusanov_residual(const double u[3][4], const double n[3][2], const double w[2],
                                  double gamma, double phi[4], double residual[4][3], double *scale)
{
  double g[3][2][4], alpha = 0.0;
  for(int j = 0; j < 3; j++)
    {
      if(!rd_rusanov_admissible(u[j]))
        return -1.0;
      const double vx = u[j][1] / u[j][0], vy = u[j][2] / u[j][0];
      const double p = (gamma - 1.0) * rd_rusanov_internal(u[j]);
      const double c = sqrt(gamma * p / u[j][0]);
      for(int edge = 0; edge < 3; edge++)
        {
          const double length = hypot(n[edge][0], n[edge][1]);
          const double speed = fabs((vx - w[0]) * n[edge][0] + (vy - w[1]) * n[edge][1]) + c * length;
          alpha = fmax(alpha, 0.5 * speed);
        }
      for(int k = 0; k < 4; k++)
        {
          g[j][0][k] = (vx - w[0]) * u[j][k];
          g[j][1][k] = (vy - w[1]) * u[j][k];
        }
      g[j][0][1] += p;
      g[j][1][2] += p;
      g[j][0][3] += p * vx;
      g[j][1][3] += p * vy;
    }
  alpha *= 1.0 + 64.0 * DBL_EPSILON;
  if(!(alpha > 0.0) || !isfinite(alpha))
    return -1.0;
  *scale = 0.0;
  for(int k = 0; k < 4; k++)
    {
      phi[k] = 0.0;
      for(int j = 0; j < 3; j++)
        {
          /* Difference form preserves a uniform state exactly. */
          phi[k] += 0.5 * (n[j][0] * (g[j][0][k] - g[0][0][k]) +
                          n[j][1] * (g[j][1][k] - g[0][1][k]));
          residual[k][j] = 0.0;
        }
    }
  for(int i = 0; i < 3; i++)
    for(int j = 0; j < 3; j++)
      if(i != j)
        {
          double bar[4];
          for(int k = 0; k < 4; k++)
            {
              const double flux_difference = (n[j][0] * (g[j][0][k] - g[i][0][k]) +
                                              n[j][1] * (g[j][1][k] - g[i][1][k])) / 6.0;
              const double viscosity = alpha * (u[i][k] - u[j][k]) / 3.0;
              residual[k][i] += flux_difference + viscosity;
              *scale += fabs(flux_difference) + fabs(viscosity);
              bar[k] = 0.5 * (u[i][k] + u[j][k]) - 1.5 * flux_difference / alpha;
            }
          if(!rd_rusanov_admissible(bar))
            return -1.0;
        }
  return alpha;
}
#endif
