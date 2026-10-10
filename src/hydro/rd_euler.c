#include "rd_euler.h"

#include <math.h>
#include <float.h>
#include <string.h>

int rd_euler_spectral_matrix(int ndim, const double *velocity, double enthalpy, double cs,
                             double gamma, const double *normal, double face_measure,
                             const double lambda[3], double *matrix)
{
  if((ndim != 2 && ndim != 3) || !(cs > 0.0) || !isfinite(cs) ||
     !(gamma > 1.0) || !isfinite(gamma) || !(face_measure > 0.0) ||
     !isfinite(face_measure) || !isfinite(enthalpy))
    return -1;

  const int nvar = ndim + 2, energy = ndim + 1;
  double speed2 = 0.0, vn = 0.0, norm2 = 0.0, vc[3];
  for(int a = 0; a < ndim; a++)
    {
      if(!isfinite(velocity[a]) || !isfinite(normal[a]))
        return -1;
      speed2 += velocity[a] * velocity[a];
      vn += velocity[a] * normal[a];
      norm2 += normal[a] * normal[a];
      vc[a] = velocity[a] / cs;
    }
  if(fabs(norm2 - 1.0) > 2e-12)
    return -1;
  for(int k = 0; k < 3; k++)
    if(!isfinite(lambda[k]))
      return -1;

  const double gm1 = gamma - 1.0, hc = enthalpy / cs;
  const double ac = (gm1 * speed2 / 2.0) / cs;
  const double v12 = (lambda[0] - lambda[1]) / 2.0;
  const double v123 = (lambda[0] + lambda[1] - 2.0 * lambda[2]) / 2.0;
  const double scale = face_measure / ndim;

  matrix[0] = scale * (ac * v123 / cs - vn * v12 / cs + lambda[2]);
  matrix[energy] = scale * (gm1 * v123 / (cs * cs));
  for(int a = 0; a < ndim; a++)
    {
      matrix[a + 1] = scale * (-gm1 * vc[a] * v123 / cs + normal[a] * v12 / cs);
      matrix[(a + 1) * nvar] = scale * ((ac * vc[a] - vn * normal[a]) * v123 +
                                        (ac * normal[a] - vc[a] * vn) * v12);
      matrix[(a + 1) * nvar + energy] =
          scale * (gm1 * vc[a] * v123 / cs + gm1 * normal[a] * v12 / cs);
      for(int b = 0; b < ndim; b++)
        {
          /* Preserve the existing 2D diagonal arithmetic. The off-diagonal
           * expression is symmetric in its first product, including both
           * transverse momentum components in three dimensions. */
          int lo = a < b ? a : b, hi = a < b ? b : a;
          double value = (normal[lo] * normal[hi] - gm1 * vc[lo] * vc[hi]) * v123;
          if(a == b)
            value = value - (gamma - 2.0) * vc[a] * normal[a] * v12 + lambda[2];
          else
            value += (vc[a] * normal[b] - gm1 * vc[b] * normal[a]) * v12;
          matrix[(a + 1) * nvar + b + 1] = scale * value;
        }
    }
  matrix[energy * nvar] = scale * ((ac * hc - vn * vn) * v123 + vn * (ac - hc) * v12);
  for(int a = 0; a < ndim; a++)
    matrix[energy * nvar + a + 1] = scale * ((vn * normal[a] - velocity[a] - ac * vc[a]) * v123 +
                                            (hc * normal[a] - gm1 * vc[a] * vn) * v12);
  matrix[energy * nvar + energy] = scale * (gm1 * hc * v123 / cs + gm1 * vn * v12 / cs + lambda[2]);
  for(int k = 0; k < nvar * nvar; k++)
    if(!isfinite(matrix[k]))
      return -1;
  return 0;
}

static int rd_euler_residual(int ndim, const double *u, const double *normal, const double *measure,
                             double gamma, double rcond, int always_svd, int lda, const double *temporal,
                             double *phi, double *residual, double *f1, struct rd_n_diagnostics *diag)
{
  memset(diag, 0, sizeof(*diag));
  if((ndim != 2 && ndim != 3) || !(gamma > 1.0) || !isfinite(gamma))
    return -1;
  const int nv = ndim + 1, nc = ndim + 2, energy = nc - 1;
  double z[4][5] = {{0}}, mean[5] = {0}, uhat[4][5];
  for(int i = 0; i < nv; i++)
    {
      for(int k = 0; k < nc; k++)
        if(!isfinite(u[i * nc + k]))
          return -1;
      const double rho = u[i * nc];
      if(!(rho > 0.0))
        return -1;
      double kinetic = 0.0;
      for(int a = 0; a < ndim; a++)
        kinetic += u[i * nc + a + 1] * u[i * nc + a + 1];
      const double pressure = (gamma - 1.0) * (u[i * nc + energy] - 0.5 * kinetic / rho);
      if(!(pressure > 0.0) || !isfinite(pressure))
        return -1;
      z[i][0] = sqrt(rho);
      for(int a = 0; a < ndim; a++)
        z[i][a + 1] = u[i * nc + a + 1] / z[i][0];
      z[i][energy] = (u[i * nc + energy] + pressure) / z[i][0];
      for(int k = 0; k < nc; k++)
        mean[k] += z[i][k] / nv;
    }
  double v[3], speed2 = 0.0;
  for(int a = 0; a < ndim; a++)
    {
      v[a] = mean[a + 1] / mean[0];
      speed2 += v[a] * v[a];
    }
  const double h = mean[energy] / mean[0];
  const double cs = sqrt((gamma - 1.0) * (h - 0.5 * speed2));
  if(!(cs > 0.0) || !isfinite(cs))
    return -1;
  for(int i = 0; i < nv; i++)
    {
      uhat[i][0] = 2.0 * mean[0] * z[i][0];
      uhat[i][energy] = mean[energy] * z[i][0] + mean[0] * z[i][energy];
      for(int a = 0; a < ndim; a++)
        {
          uhat[i][a + 1] = mean[a + 1] * z[i][0] + mean[0] * z[i][a + 1];
          uhat[i][energy] += (gamma - 1.0) * mean[a + 1] * z[i][a + 1];
        }
      uhat[i][energy] /= gamma;
    }
  /* Reference subtraction cancels a uniform field before large products. */
  for(int i = nv - 1; i >= 0; i--)
    for(int k = 0; k < nc; k++)
      uhat[i][k] -= uhat[0][k];

  double plus[4][25], minus[25], full[25], sm[25] = {0}, rhs[5] = {0}, original[5];
  for(int k = 0; k < nc; k++)
    phi[k] = 0.0;
  for(int i = 0; i < nv; i++)
    {
      double vn = 0.0, lp[3], lm[3];
      for(int a = 0; a < ndim; a++)
        vn += v[a] * normal[i * ndim + a];
      const double lambda[3] = {vn + cs, vn - cs, vn};
      for(int k = 0; k < 3; k++)
        lp[k] = fmax(lambda[k], 0.0), lm[k] = fmin(lambda[k], 0.0);
      if(rd_euler_spectral_matrix(ndim, v, h, cs, gamma, normal + i * ndim, measure[i], lambda, full) ||
         rd_euler_spectral_matrix(ndim, v, h, cs, gamma, normal + i * ndim, measure[i], lp, plus[i]) ||
         rd_euler_spectral_matrix(ndim, v, h, cs, gamma, normal + i * ndim, measure[i], lm, minus))
        return -1;
      for(int r = 0; r < nc; r++)
        for(int c = 0; c < nc; c++)
          {
            const int k = r * nc + c;
            sm[k] += minus[k];
            rhs[r] += minus[k] * uhat[i][c];
            phi[r] += full[k] * uhat[i][c];
            diag->roundoff_scale += (fabs(full[k]) + fabs(minus[k])) * fabs(uhat[i][c]);
          }
    }
  if(lda)
    memcpy(rhs, phi, nc * sizeof(double));
  memcpy(original, rhs, nc * sizeof(double));
  if(rd_upwind_solve(nc, sm, rhs, 1, rcond, always_svd, &diag->solve) != 0)
    return -2;
  for(int r = 0; r < nc; r++)
    {
      double defect = -original[r], sum = 0.0;
      for(int c = 0; c < nc; c++)
        {
          defect += sm[r * nc + c] * rhs[c];
          diag->roundoff_scale += fabs(sm[r * nc + c] * rhs[c]);
        }
      diag->solve_defect = fmax(diag->solve_defect, fabs(defect));
      diag->max_phi = fmax(diag->max_phi, fabs(phi[r]));
      for(int i = 0; i < nv; i++)
        {
          double value = 0.0;
          for(int c = 0; c < nc; c++)
            {
              value += plus[i][r * nc + c] * (lda ? -rhs[c] : uhat[i][c] - rhs[c]);
              diag->roundoff_scale += fabs(plus[i][r * nc + c]) * (fabs(uhat[i][c]) + fabs(rhs[c]));
            }
          residual[i * nc + r] = value;
          sum += value;
        }
      diag->conservation_defect = fmax(diag->conservation_defect, fabs(sum - phi[r]));
    }
  if(lda && temporal)
    {
      memset(f1, 0, nv * nc * sizeof(double));
      if(diag->solve.rank == nc)
        {
          double target[5];
          struct rd_solve_info time_solve;
          memcpy(target, temporal, nc * sizeof(double));
          if(rd_upwind_solve(nc, sm, target, 1, rcond, always_svd, &time_solve) != 0 || time_solve.rank != nc)
            return -2;
          for(int r = 0; r < nc; r++)
            {
              double defect = -temporal[r], sum = 0.0;
              for(int c = 0; c < nc; c++)
                {
                  defect += sm[r * nc + c] * target[c];
                  diag->roundoff_scale += fabs(sm[r * nc + c] * target[c]);
                }
              diag->solve_defect = fmax(diag->solve_defect, fabs(defect));
              for(int i = 0; i < nv; i++)
                {
                  for(int c = 0; c < nc; c++)
                    {
                      f1[i * nc + r] -= plus[i][r * nc + c] * target[c];
                      diag->roundoff_scale += fabs(plus[i][r * nc + c] * target[c]);
                    }
                  sum += f1[i * nc + r];
                }
              diag->conservation_defect = fmax(diag->conservation_defect, fabs(sum - temporal[r]));
            }
        }
    }
  const double tolerance = 4096.0 * DBL_EPSILON * fmax(diag->roundoff_scale, DBL_MIN);
  if(!isfinite(diag->roundoff_scale) || !isfinite(diag->solve_defect) || !isfinite(diag->conservation_defect) ||
     diag->solve_defect > tolerance || diag->conservation_defect > tolerance)
    return -3;
  return 0;
}

int rd_euler_n_residual(int ndim, const double *u, const double *normal, const double *measure,
                       double gamma, double rcond, int always_svd, double *phi, double *residual,
                       struct rd_n_diagnostics *diag)
{
  return rd_euler_residual(ndim, u, normal, measure, gamma, rcond, always_svd, 0, NULL,
                           phi, residual, NULL, diag);
}

int rd_euler_lda_residual(int ndim, const double *u, const double *normal, const double *measure,
                         double gamma, double rcond, int always_svd, const double *temporal,
                         double *phi, double *residual, double *f1, struct rd_n_diagnostics *diag)
{
  return rd_euler_residual(ndim, u, normal, measure, gamma, rcond, always_svd, 1, temporal,
                           phi, residual, f1, diag);
}
