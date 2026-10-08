/* Experimental P1 median-dual edge HLLC kernel: a low-order FV-RD residual.
 * No AREPO state, floors or clipping.  Used only with RD_RUSANOV_LOW_ORDER.
 *
 * n[j] is the inward length-weighted normal opposite vertex j of a
 * counter-clockwise triangle.  Inside T the median-dual face between i and j
 * has the scaled normal
 *
 *     nu_ij = (n_j - n_i)/6,   pointing from i towards j,
 *
 * and the nodal residual is (Deconinck & Ricchiuto, FV schemes in FS form)
 *
 *     phi_i = sum_{j != i} [ H(U_i, U_j; nu_ij) - G(U_i).nu_ij ],  G = F - U (x) w.
 *
 * Because sum_{j != i} nu_ij = -n_i/2, sum_i phi_i = 1/2 sum_j G(U_j).n_j:
 * the same trapezoidal ALE total as rd_rusanov.h.  H is HLLC solved in the
 * frame moving with w, with Einfeldt/Batten wave speeds, and mapped back by
 * the Galilean matrix.  Each pair term is a one-sided average of the HLLC
 * Riemann fan, so a forward-Euler stage with nodal coefficient S_i is a convex
 * combination of admissible states if
 *
 *     (dt/S_i) sum_{T, j != i} |nu_ij| s_ij <= 1,   s_ij = max(|S_L|, |S_R|).
 *
 * The kernel returns these per-vertex coefficients.  Every HLLC star state is
 * checked; an inadmissible input or star state returns -1 (the caller aborts).
 * See dev_log/RD_SEDOV_HLLC_LOW_ORDER_20260930.md.
 */
#ifndef RD_HLLC_H
#define RD_HLLC_H
#include <math.h>
#include "rd_rusanov.h"

/* Left fluctuation |nu| [H(ul, ur) - G(ul).nu_hat] in laboratory conserved
 * variables.  Returns the largest HLLC signal speed, or -1 on failure. */
static double rd_hllc_pair(const double ul[4], const double ur[4], const double nu[2], const double w[2], double gamma,
                           double out[4])
{
  for(int k = 0; k < 4; k++)
    out[k] = 0.0;
  const double length = hypot(nu[0], nu[1]);
  if(!(length > 0.0) || !isfinite(length) || !rd_rusanov_admissible(ul) || !rd_rusanov_admissible(ur))
    return -1.0;
  const double nx = nu[0] / length, ny = nu[1] / length; /* tangent t = (-ny, nx) */

  double rho[2], un[2], ut[2], p[2], c[2], e[2], h[2];
  const double *state[2] = {ul, ur};
  for(int s = 0; s < 2; s++)
    {
      const double vx = state[s][1] / state[s][0] - w[0], vy = state[s][2] / state[s][0] - w[1];
      rho[s] = state[s][0];
      un[s]  = vx * nx + vy * ny;
      ut[s]  = -vx * ny + vy * nx;
      p[s]   = (gamma - 1.0) * rd_rusanov_internal(state[s]);
      c[s]   = sqrt(gamma * p[s] / rho[s]);
      e[s]   = p[s] / (gamma - 1.0) + 0.5 * rho[s] * (un[s] * un[s] + ut[s] * ut[s]);
      h[s]   = (e[s] + p[s]) / rho[s];
    }

  double speed_l = fmin(un[0] - c[0], un[1] - c[1]), speed_r = fmax(un[0] + c[0], un[1] + c[1]);
  const double wl = sqrt(rho[0]), wr = sqrt(rho[1]), inverse = 1.0 / (wl + wr);
  const double un_roe = (wl * un[0] + wr * un[1]) * inverse, ut_roe = (wl * ut[0] + wr * ut[1]) * inverse;
  const double c2_roe = (gamma - 1.0) * ((wl * h[0] + wr * h[1]) * inverse - 0.5 * (un_roe * un_roe + ut_roe * ut_roe));
  if(c2_roe > 0.0 && isfinite(c2_roe))
    {
      speed_l = fmin(speed_l, un_roe - sqrt(c2_roe));
      speed_r = fmax(speed_r, un_roe + sqrt(c2_roe));
    }
  const double speed = fmax(fabs(speed_l), fabs(speed_r));
  if(!isfinite(speed) || !(speed > 0.0))
    return -1.0;

  /* Bitwise identical states: the flux is exactly G(U), so no fluctuation. */
  if(ul[0] == ur[0] && ul[1] == ur[1] && ul[2] == ur[2] && ul[3] == ur[3])
    return speed;

  const double dl = rho[0] * (speed_l - un[0]), dr = rho[1] * (speed_r - un[1]);
  const double contact = (p[1] - p[0] + un[0] * dl - un[1] * dr) / (dl - dr);
  if(!isfinite(contact) || !(speed_l < contact) || !(contact < speed_r))
    return -1.0;

  /* Frame states and star states in (normal, tangential) components. */
  double q[2][4], star[2][4];
  const double wave[2] = {speed_l, speed_r};
  for(int s = 0; s < 2; s++)
    {
      q[s][0] = rho[s];
      q[s][1] = rho[s] * un[s];
      q[s][2] = rho[s] * ut[s];
      q[s][3] = e[s];
      const double factor = rho[s] * (wave[s] - un[s]) / (wave[s] - contact);
      star[s][0] = factor;
      star[s][1] = factor * contact;
      star[s][2] = factor * ut[s];
      star[s][3] = factor * (e[s] / rho[s] + (contact - un[s]) * (contact + p[s] / (rho[s] * (wave[s] - un[s]))));
      const double star_internal = star[s][3] - 0.5 * (star[s][1] * star[s][1] + star[s][2] * star[s][2]) / star[s][0];
      if(!(star[s][0] > 0.0) || !isfinite(star[s][0]) || !(star_internal > 0.0) || !isfinite(star_internal))
        return -1.0;
    }

  double f[4] = {0.0, 0.0, 0.0, 0.0};
  if(speed_r <= 0.0)
    {
      for(int s = 0; s < 2; s++)
        {
          const double sign   = s == 0 ? -1.0 : 1.0;
          const double flux[4] = {q[s][1], q[s][1] * un[s] + p[s], q[s][2] * un[s], un[s] * (e[s] + p[s])};
          for(int k = 0; k < 4; k++)
            f[k] += sign * flux[k];
        }
    }
  else if(speed_l < 0.0)
    {
      for(int k = 0; k < 4; k++)
        f[k] = speed_l * (star[0][k] - q[0][k]);
      if(contact < 0.0)
        for(int k = 0; k < 4; k++)
          f[k] += contact * (star[1][k] - star[0][k]);
    }

  /* Rotate momentum back to x/y, then apply G(-w) to leave the moving frame. */
  const double fx = f[1] * nx - f[2] * ny, fy = f[1] * ny + f[2] * nx;
  out[0] = length * f[0];
  out[1] = length * (fx + w[0] * f[0]);
  out[2] = length * (fy + w[1] * f[0]);
  out[3] = length * (f[3] + w[0] * fx + w[1] * fy + 0.5 * (w[0] * w[0] + w[1] * w[1]) * f[0]);
  for(int k = 0; k < 4; k++)
    if(!isfinite(out[k]))
      return -1.0;
  return speed;
}

/* Element residual.  Returns max(coeff), or -1 on invalid input/orientation
 * or an inadmissible HLLC state.  residual[k][i] is component k at vertex i. */
static double rd_hllc_residual(const double u[3][4], const double n[3][2], const double w[2], double gamma, double phi[4],
                               double residual[4][3], double coeff[3], double *scale)
{
  double g[3][2][4];
  for(int j = 0; j < 3; j++)
    {
      if(!rd_rusanov_admissible(u[j]))
        return -1.0;
      const double vx = u[j][1] / u[j][0], vy = u[j][2] / u[j][0];
      const double p = (gamma - 1.0) * rd_rusanov_internal(u[j]);
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
  if(!(n[0][0] * n[1][1] - n[0][1] * n[1][0] > 0.0))
    return -1.0;

  *scale = 0.0;
  for(int k = 0; k < 4; k++)
    {
      phi[k] = 0.0;
      for(int j = 0; j < 3; j++)
        {
          /* Difference form preserves a uniform state exactly. */
          phi[k] += 0.5 * (n[j][0] * (g[j][0][k] - g[0][0][k]) + n[j][1] * (g[j][1][k] - g[0][1][k]));
          residual[k][j] = 0.0;
        }
    }
  for(int j = 0; j < 3; j++)
    coeff[j] = 0.0;

  for(int pair = 0; pair < 3; pair++)
    {
      const int i = pair, j = (pair + 1) % 3;
      const double nu[2] = {(n[j][0] - n[i][0]) / 6.0, (n[j][1] - n[i][1]) / 6.0};
      double left[4];
      const double speed = rd_hllc_pair(u[i], u[j], nu, w, gamma, left);
      if(!(speed > 0.0))
        return -1.0;
      for(int k = 0; k < 4; k++)
        {
          /* The two one-sided fluctuations sum to (G_j - G_i).nu_ij. */
          const double jump  = nu[0] * (g[j][0][k] - g[i][0][k]) + nu[1] * (g[j][1][k] - g[i][1][k]);
          const double right = jump - left[k];
          residual[k][i] += left[k];
          residual[k][j] += right;
          *scale += fabs(left[k]) + fabs(right) + fabs(nu[0] * g[j][0][k]) + fabs(nu[0] * g[i][0][k]) +
                    fabs(nu[1] * g[j][1][k]) + fabs(nu[1] * g[i][1][k]);
        }
      const double weight = hypot(nu[0], nu[1]) * speed;
      coeff[i] += weight;
      coeff[j] += weight;
    }
  return fmax(coeff[0], fmax(coeff[1], coeff[2]));
}

/* LDA/HLLC blend only.  Add the Gauss3-minus-trapezoid physical-flux term of
 * each edge (same arithmetic as rd_contour_gauss_correction) half to each of
 * its two endpoints.  The element low-order total then equals the Gauss3
 * contour total used by LDA, so a high-minus-low correction sums to zero per
 * element.  The adjacent triangle carries the opposite term on the same edge
 * (same states and quadrature points, opposite normal), hence each node's
 * assembled low-order update is unchanged up to roundoff.  nx, ny are unit
 * inward normals and mag the edge lengths, as in rd_contour_gauss_correction. */
static void rd_hllc_gauss_edge_split(const double u[3][4], const double nx[3], const double ny[3], const double mag[3],
                                     double gamma, double residual[4][3], double phi[4], double *scale)
{
  const double x[3] = {0.11270166537925831148, 0.5, 0.88729833462074168852};
  const double wq[3] = {5.0 / 18.0, 4.0 / 9.0, 5.0 / 18.0};
  double f[3][2][4];
  for(int j = 0; j < 3; j++)
    {
      const double vx = u[j][1] / u[j][0], vy = u[j][2] / u[j][0];
      const double p = (gamma - 1.0) * (u[j][3] - 0.5 * (u[j][1] * vx + u[j][2] * vy));
      f[j][0][0] = u[j][1], f[j][1][0] = u[j][2];
      f[j][0][1] = u[j][1] * vx + p, f[j][1][1] = u[j][1] * vy;
      f[j][0][2] = u[j][2] * vx, f[j][1][2] = u[j][2] * vy + p;
      f[j][0][3] = (u[j][3] + p) * vx, f[j][1][3] = (u[j][3] + p) * vy;
    }
  for(int j = 0; j < 3; j++)
    {
      const int a = (j + 1) % 3, b = (j + 2) % 3;
      for(int q = 0; q < 3; q++)
        {
          double uq[4];
          for(int k = 0; k < 4; k++)
            uq[k] = (1.0 - x[q]) * u[a][k] + x[q] * u[b][k];
          const double vx = uq[1] / uq[0], vy = uq[2] / uq[0];
          const double p = (gamma - 1.0) * (uq[3] - 0.5 * (uq[1] * vx + uq[2] * vy));
          const double fq[2][4] = {{uq[1], uq[1] * vx + p, uq[2] * vx, (uq[3] + p) * vx},
                                   {uq[2], uq[1] * vy, uq[2] * vy + p, (uq[3] + p) * vy}};
          /* Mass flux is linear in U: its correction is identically zero. */
          for(int k = 1; k < 4; k++)
            {
              const double dx = fq[0][k] - ((1.0 - x[q]) * f[a][0][k] + x[q] * f[b][0][k]);
              const double dy = fq[1][k] - ((1.0 - x[q]) * f[a][1][k] + x[q] * f[b][1][k]);
              const double c  = -mag[j] * wq[q] * (nx[j] * dx + ny[j] * dy);
              residual[k][a] += 0.5 * c;
              residual[k][b] += 0.5 * c;
              phi[k] += c;
              *scale += fabs(c);
            }
        }
    }
}
#endif
