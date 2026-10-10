#include "rd_euler.h"

#include <math.h>

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
