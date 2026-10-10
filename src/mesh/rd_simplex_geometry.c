#include "rd_simplex_geometry.h"

#include <math.h>

static void rd_cross(const double a[3], const double b[3], double c[3])
{
  c[0] = a[1] * b[2] - a[2] * b[1];
  c[1] = a[2] * b[0] - a[0] * b[2];
  c[2] = a[0] * b[1] - a[1] * b[0];
}

int rd_simplex_geometry(int ndim, const double *x, double *signed_measure,
                        double *unit_normal, double *face_measure)
{
  if(ndim != 2 && ndim != 3)
    return -1;
  for(int k = 0; k < (ndim + 1) * ndim; k++)
    if(!isfinite(x[k]))
      return -1;
  if(ndim == 2)
    *signed_measure = ((x[2] - x[0]) * (x[5] - x[1]) - (x[3] - x[1]) * (x[4] - x[0])) / 2.0;
  else
    {
      double a[3], b[3], c[3];
      for(int k = 0; k < 3; k++)
        a[k] = x[3 + k] - x[k], b[k] = x[6 + k] - x[k];
      rd_cross(a, b, c);
      *signed_measure = (c[0] * (x[9] - x[0]) + c[1] * (x[10] - x[1]) + c[2] * (x[11] - x[2])) / 6.0;
    }
  if(!isfinite(*signed_measure) || *signed_measure == 0.0)
    return -1;

  for(int i = 0; i <= ndim; i++)
    {
      int face[3], count = 0;
      for(int j = 0; j <= ndim; j++)
        if(j != i)
          face[count++] = j;
      double a[3] = {0}, b[3] = {0}, n[3] = {0};
      for(int k = 0; k < ndim; k++)
        {
          a[k] = x[face[1] * ndim + k] - x[face[0] * ndim + k];
          if(ndim == 3)
            b[k] = x[face[2] * ndim + k] - x[face[0] * ndim + k];
        }
      if(ndim == 2)
        n[0] = -a[1], n[1] = a[0];
      else
        {
          rd_cross(a, b, n);
          for(int k = 0; k < 3; k++)
            n[k] *= 0.5; /* triangular area, not parallelogram area */
        }
      double toward = 0.0, norm2 = 0.0;
      for(int k = 0; k < ndim; k++)
        {
          toward += n[k] * (x[i * ndim + k] - x[face[0] * ndim + k]);
          norm2 += n[k] * n[k];
        }
      double mag = sqrt(norm2);
      if(!(mag > 0.0) || !isfinite(mag) || !isfinite(toward) || toward == 0.0)
        return -1;
      face_measure[i] = mag;
      for(int k = 0; k < ndim; k++)
        unit_normal[i * ndim + k] = (toward > 0.0 ? n[k] : -n[k]) / mag;
    }
  return 0;
}
