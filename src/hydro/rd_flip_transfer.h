/* Flip element: conservative, admissible transfer of nodal Euler states
 * across a change of P1 connectivity (one changed cavity at one time).
 * Pure C, no AREPO state.  See
 * dev_log/RD_FLIP_ELEMENT_AND_MOVING_HIERARCHY_DESIGN_20261008.md.
 *
 * Inputs for the n cavity vertices:
 *   g[i]   full nodal P1 mass before the change (> 0),
 *   dm[i]  b_i - a_i, new minus old lumped mass inside the cavity
 *          (sum_i dm_i = 0, g_i + dm_i > 0),
 *   u[i]   conserved densities (rho, mx, my, E) before the change.
 * Output uout[i]: densities on the new masses g_i + dm_i with
 *   sum_i (g_i + dm_i) uout_i = sum_i g_i u_i      (per component).
 *
 * The cavity residual is D = sum_i dm_i u_i = int (u_h^new - u_h^old).
 *   High, mode 0 (linear-exact, minimal max-norm change): u_i - D / sum_j (g_j+dm_j).
 *   High, mode 1 (linear-exact, donors untouched): receivers take
 *        g_i u_i + dm_i (ubar_D + u_i - ubar_R), ubar_R the dm-weighted receiver
 *        mean; it differs from the low endpoint by a receiver zero-sum term and
 *        has the same L1 change |D| as mode 0.
 *   Low  (convex donor-cell): donors (dm<0) keep u_i bit-for-bit;
 *        receivers mix g_i u_i + dm_i ubar_D, ubar_D the |dm|-weighted
 *        donor mean.  For one 2-2 flip this is the edge donor-cell exchange.
 *   Blend (1-theta) low + theta high with ONE theta for the cavity and all
 *   components; theta is the largest value keeping every vertex admissible,
 *   with relaxed density bounds and the specific-entropy minimum when
 *   requested.  theta = 0 is always feasible for admissible input.
 */
#ifndef RD_FLIP_TRANSFER_H
#define RD_FLIP_TRANSFER_H
#include <float.h>
#include <math.h>
#include "rd_rusanov.h"

struct rd_flip_options
{
  double gamma;
  double floor_fraction; /* rho, e floors as fractions of the input minima */
  double dmp_relax;      /* density hull relaxation r; negative disables the hull */
  int entropy_bound;     /* nonzero: require K = p/rho^gamma >= min input K */
  int high_mode;         /* 0: uniform shift; 1: receiver-weighted, donors untouched (solver default) */
};

struct rd_flip_diagnostics
{
  double theta;
  double defect_scale;   /* max_k |D_k| / sum_i g_i |u_ik| */
  double max_change;     /* max_i,k |uout - u| / max_i |u_ik| */
  int high_accepted;
  int donors, receivers;
};

#define RD_FLIP_OK 0
#define RD_FLIP_BAD_MASS -1
#define RD_FLIP_BAD_INPUT -2
#define RD_FLIP_BAD_BALANCE -3
#define RD_FLIP_BAD_LOW -4

struct rd_flip_bounds
{
  double rho_floor, e_floor, rho_lo, rho_hi, k_min;
  int use_hull, use_entropy;
  double gm1, gamma;
};

/* Internal energy with a conservative round-off allowance: e is computed as
 * E - |m|^2/(2 rho); its absolute error is bounded by a few ulp of E. */
static int rd_flip_state_ok(const double u[4], const struct rd_flip_bounds *b, int strict)
{
  if(!rd_rusanov_admissible(u))
    return 0;
  const double e = rd_rusanov_internal(u);
  if(!(u[0] > b->rho_floor) || !(e > b->e_floor))
    return 0;
  if(strict)
    return 1; /* the low endpoint: positivity only */
  if(b->use_hull && (u[0] < b->rho_lo || u[0] > b->rho_hi))
    return 0;
  if(b->use_entropy)
    {
      const double slack = 8.0 * DBL_EPSILON * fabs(u[3]);
      if(b->gm1 * (e + slack) / pow(u[0], b->gamma) < b->k_min)
        return 0;
    }
  return 1;
}

/* Where both endpoints agree (donors in mode 1, untouched vertices) the value is
 * copied, so it stays bit-for-bit: (1-theta) u + theta u need not round to u. */
static void rd_flip_blend(int n, double theta, const double (*ul)[4], const double (*uh)[4], double (*out)[4])
{
  for(int i = 0; i < n; i++)
    for(int k = 0; k < 4; k++)
      out[i][k] = (theta == 0.0 || ul[i][k] == uh[i][k]) ? ul[i][k]
                  : (theta == 1.0 ? uh[i][k] : (1.0 - theta) * ul[i][k] + theta * uh[i][k]);
}

static int rd_flip_blend_ok(int n, double theta, const double (*ul)[4], const double (*uh)[4],
                            const struct rd_flip_bounds *b, double (*work)[4])
{
  rd_flip_blend(n, theta, ul, uh, work);
  for(int i = 0; i < n; i++)
    if(!rd_flip_state_ok(work[i], b, 0))
      return 0;
  return 1;
}

/* Returns RD_FLIP_OK or a negative status.  ul, uh and work are caller
 * scratch arrays of length n. */
static int rd_flip_transfer(int n, const double *g, const double *dm, const double (*u)[4], const struct rd_flip_options *opt,
                            double (*ul)[4], double (*uh)[4], double (*work)[4], double (*uout)[4],
                            struct rd_flip_diagnostics *diag)
{
  diag->theta = 0.0;
  diag->defect_scale = 0.0;
  diag->max_change = 0.0;
  diag->high_accepted = 0;
  diag->donors = diag->receivers = 0;
  if(n < 1)
    return RD_FLIP_BAD_MASS;

  double mass_new = 0.0, donor_mass = 0.0, receiver_mass = 0.0, dm_abs = 0.0;
  for(int i = 0; i < n; i++)
    {
      if(!(g[i] > 0.0) || !isfinite(dm[i]) || !(g[i] + dm[i] > 0.0))
        return RD_FLIP_BAD_MASS;
      if(!rd_rusanov_admissible(u[i]))
        return RD_FLIP_BAD_INPUT;
      mass_new += g[i] + dm[i];
      dm_abs += fabs(dm[i]);
      if(dm[i] < 0.0)
        {
          donor_mass -= dm[i];
          diag->donors++;
        }
      else if(dm[i] > 0.0)
        {
          receiver_mass += dm[i];
          diag->receivers++;
        }
    }
  /* Both triangulations tile the cavity: the dm balance closes to round-off. */
  if(fabs(donor_mass - receiver_mass) > 64.0 * DBL_EPSILON * (dm_abs + mass_new))
    return RD_FLIP_BAD_BALANCE;

  double defect[4] = {0, 0, 0, 0}, ubar[4] = {0, 0, 0, 0}, urec[4] = {0, 0, 0, 0}, scale[4] = {0, 0, 0, 0},
         umax[4] = {0, 0, 0, 0};
  for(int i = 0; i < n; i++)
    for(int k = 0; k < 4; k++)
      {
        defect[k] += dm[i] * u[i][k];
        scale[k] += g[i] * fabs(u[i][k]);
        umax[k] = fmax(umax[k], fabs(u[i][k]));
        if(dm[i] < 0.0)
          ubar[k] += -dm[i] * u[i][k];
        else if(dm[i] > 0.0)
          urec[k] += dm[i] * u[i][k];
      }
  for(int k = 0; k < 4; k++)
    {
      if(donor_mass > 0.0)
        ubar[k] /= donor_mass;
      if(receiver_mass > 0.0)
        urec[k] /= receiver_mass;
      if(scale[k] > 0.0)
        diag->defect_scale = fmax(diag->defect_scale, fabs(defect[k]) / scale[k]);
    }

  /* Endpoints.  Donors and untouched vertices keep their state bit-for-bit
   * in the low endpoint; receivers are convex combinations. */
  for(int i = 0; i < n; i++)
    {
      const double gnew = g[i] + dm[i];
      for(int k = 0; k < 4; k++)
        {
          if(opt->high_mode == 1)
            uh[i][k] = dm[i] > 0.0 ? (g[i] * u[i][k] + dm[i] * (ubar[k] + u[i][k] - urec[k])) / gnew : u[i][k];
          else
            uh[i][k] = u[i][k] - defect[k] / mass_new;
          if(dm[i] > 0.0)
            ul[i][k] = (g[i] * u[i][k] + dm[i] * ubar[k]) / gnew;
          else
            ul[i][k] = u[i][k];
        }
    }

  struct rd_flip_bounds b;
  double rho_min = DBL_MAX, rho_max = 0.0, e_min = DBL_MAX, k_min = DBL_MAX;
  b.gamma = opt->gamma;
  b.gm1 = opt->gamma - 1.0;
  for(int i = 0; i < n; i++)
    {
      const double e = rd_rusanov_internal(u[i]);
      rho_min = fmin(rho_min, u[i][0]);
      rho_max = fmax(rho_max, u[i][0]);
      e_min = fmin(e_min, e);
      k_min = fmin(k_min, b.gm1 * e / pow(u[i][0], b.gamma));
    }
  b.rho_floor = opt->floor_fraction * rho_min;
  b.e_floor = opt->floor_fraction * e_min;
  b.use_hull = opt->dmp_relax >= 0.0;
  const double width = rho_max - rho_min;
  b.rho_lo = rho_min * (1.0 - 16.0 * DBL_EPSILON) - opt->dmp_relax * width;
  b.rho_hi = rho_max * (1.0 + 16.0 * DBL_EPSILON) + opt->dmp_relax * width;
  b.use_entropy = opt->entropy_bound != 0;
  b.k_min = k_min;

  /* theta = 0 must be admissible (convexity); otherwise the input or the
   * masses are inconsistent, which is reported rather than floored. */
  for(int i = 0; i < n; i++)
    if(!rd_flip_state_ok(ul[i], &b, 1))
      return RD_FLIP_BAD_LOW;

  double theta = 0.0;
  if(rd_flip_blend_ok(n, 1.0, (const double(*)[4])ul, (const double(*)[4])uh, &b, work))
    {
      theta = 1.0;
      diag->high_accepted = 1;
    }
  else
    {
      double lo = 0.0, hi = 1.0;
      for(int it = 0; it < 60; it++)
        {
          const double mid = 0.5 * (lo + hi);
          if(rd_flip_blend_ok(n, mid, (const double(*)[4])ul, (const double(*)[4])uh, &b, work))
            lo = mid;
          else
            hi = mid;
        }
      theta = lo; /* lo was verified on the actual floating-point values */
    }
  rd_flip_blend(n, theta, (const double(*)[4])ul, (const double(*)[4])uh, uout);
  diag->theta = theta;
  for(int i = 0; i < n; i++)
    for(int k = 0; k < 4; k++)
      if(umax[k] > 0.0)
        diag->max_change = fmax(diag->max_change, fabs(uout[i][k] - u[i][k]) / umax[k]);
  return RD_FLIP_OK;
}
#endif
