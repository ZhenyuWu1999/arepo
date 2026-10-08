/* Static-mesh research kernel: common-total Rusanov and convex limiting.
 * Low residual sums to the supplied Gauss total. No state clipping.
 */
#ifndef RD_LDA_RUSANOV_H
#define RD_LDA_RUSANOV_H
#include "rd_rusanov.h"

/* Classical RD B residual-ratio sensor, applied to complete stage residuals.
 * The N endpoint of the published B scheme is replaced here by the existing
 * common-Gauss Rusanov endpoint. Mode 2 is the all-component Bmax choice.
 * This sensor is not a positivity or entropy proof; the coupled limiter
 * below must still act on the resulting conservative correction. */
static void rd_lr_b_sensor(const double total_low[4][3], int mode, double theta[4])
{
  double maximum = 0;
  for(int k = 0; k < 4; k++)
    {
      double scale = fmax(fabs(total_low[k][0]), fmax(fabs(total_low[k][1]), fabs(total_low[k][2])));
      double sum = 0, absolute = 0;
      for(int j = 0; j < 3; j++)
        if(scale > 0)
          {
            double x = total_low[k][j]/scale;
            sum += x;
            absolute += fabs(x);
          }
      theta[k] = absolute > 0 ? fmin(1, fabs(sum)/absolute) : 0;
      maximum = fmax(maximum, theta[k]);
    }
  if(mode == 2)
    for(int k = 0; k < 4; k++) theta[k] = maximum;
}

/* Complete B corrector relative to the admissible SSP low candidate.
 * high/low contain temporal terms + half of the new spatial residual.
 * The old accepted predictor differs from both raw old branches. Replace
 * its implicit half by the new B combination of those raw branches. */
static double rd_lr_b_difference(double high, double low, double old_high,
                                 double old_low, double old_accepted, double theta)
{
  return (1-theta)*(high-low) + .5*((1-theta)*old_high+theta*old_low-old_accepted);
}

static double rd_lr_low(const double u[3][4], const double n[3][2], double gamma,
                        const double phi[4], double low[4][3])
{
  double mean[4] = {0}, alpha = 0;
  for(int j = 0; j < 3; j++)
    {
      if(!rd_rusanov_admissible(u[j])) return -1;
      double vx = u[j][1] / u[j][0], vy = u[j][2] / u[j][0];
      double c = sqrt(gamma * (gamma - 1) * rd_rusanov_internal(u[j]) / u[j][0]);
      for(int k = 0; k < 4; k++) mean[k] += u[j][k] / 3;
      for(int e = 0; e < 3; e++)
        alpha = fmax(alpha, .5 * (fabs(vx*n[e][0] + vy*n[e][1]) + c*hypot(n[e][0], n[e][1])));
    }
  alpha *= 1 + 64*DBL_EPSILON;
  for(int attempt = 0; attempt < 64; attempt++, alpha *= 2)
    {
      double inflow[4];
      for(int k = 0; k < 4; k++) inflow[k] = mean[k] - phi[k]/(3*alpha);
      if(alpha > 0 && isfinite(alpha) && rd_rusanov_admissible(inflow))
        {
          for(int k = 0; k < 4; k++)
            for(int j = 0; j < 3; j++)
              low[k][j] = phi[k]/3 + (alpha/3)*
                  ((u[j][k]-u[(j+1)%3][k])+(u[j][k]-u[(j+2)%3][k]));
          return alpha;
        }
    }
  return -1;
}

/* q and dq may be intensive or extensive, as long as their units agree.
 * The safety margin scales with the admissible base state, not a gas floor. */
static int rd_lr_segment_ok(const double q[4], const double dq[4], double ell)
{
  double trial[4];
  for(int k = 0; k < 4; k++) trial[k] = q[k] + ell*dq[k];
  return rd_rusanov_admissible(trial) && trial[0] >= 1e-12*q[0] &&
         rd_rusanov_internal(trial) >= 1e-12*rd_rusanov_internal(q);
}

static double rd_lr_limit(const double q[4], const double dq[4])
{
  if(!rd_rusanov_admissible(q)) return -1;
  for(int k = 0; k < 4; k++) if(!isfinite(dq[k])) return 0;
  if(rd_lr_segment_ok(q, dq, 1)) return 1;
  double left = 0, right = 1;
  for(int iteration = 0; iteration < 56; iteration++)
    {
      double mid = .5*(left+right);
      if(rd_lr_segment_ok(q, dq, mid)) left = mid;
      else right = mid;
    }
  return left*(1-1e-12);
}

/* Optional local bounds (RD_BLEND_LOCAL_BOUNDS): intensive density inside
 * [bound[0], bound[1]] and K=p/rho^gamma >= bound[2].  The bounds are built
 * from a stencil that contains the node's own low-order state, so ell=0 is
 * admissible up to roundoff.  Both constraint sets are convex in U (density
 * linear; E-|m|^2/2rho - K rho^gamma/(gamma-1) concave), so the admissible
 * ell form an interval containing 0 and bisection is valid.  q and dq are
 * extensive; area converts them to intensive states. */
static int rd_lr_bounds_ok(const double q[4], const double dq[4], double ell, double area, const double bound[3],
                           double gamma)
{
  if(!rd_lr_segment_ok(q, dq, ell)) return 0;
  double u[4];
  for(int k = 0; k < 4; k++) u[k] = (q[k] + ell*dq[k])/area;
  const double slack = 1e-12;
  if(u[0] < bound[0]*(1-slack) || u[0] > bound[1]*(1+slack)) return 0;
  const double internal = rd_rusanov_internal(u);
  return internal - bound[2]*pow(u[0], gamma)/(gamma-1) >= -slack*internal;
}

static double rd_lr_limit_bounds(const double q[4], const double dq[4], double area, const double bound[3],
                                 double gamma)
{
  if(!rd_rusanov_admissible(q)) return -1;
  for(int k = 0; k < 4; k++) if(!isfinite(dq[k])) return 0;
  if(rd_lr_bounds_ok(q, dq, 1, area, bound, gamma)) return 1;
  double left = 0, right = 1;
  for(int iteration = 0; iteration < 56; iteration++)
    {
      double mid = .5*(left+right);
      if(rd_lr_bounds_ok(q, dq, mid, area, bound, gamma)) left = mid;
      else right = mid;
    }
  /* At the active bound the test flips within roundoff (pow, cancellation):
   * back off and verify, so the returned ell itself satisfies the bounds. */
  double ell = left, step = fmax(1e-9*left, 1e-15);
  while(ell > 0 && !rd_lr_bounds_ok(q, dq, ell, area, bound, gamma))
    {
      ell -= step;
      step *= 2;
    }
  return ell > 0 ? ell : 0;
}

/* Widen a node's bounds by one intensive state. */
static void rd_lr_bounds_include(double bound[3], const double u[4], double gamma)
{
  const double k = (gamma-1)*rd_rusanov_internal(u)/pow(u[0], gamma);
  bound[0] = fmin(bound[0], u[0]);
  bound[1] = fmax(bound[1], u[0]);
  bound[2] = fmin(bound[2], k);
}
#endif
