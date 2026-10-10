#include "rd_linalg.h"

#include <lapacke.h>
#include <math.h>
#include <string.h>

int rd_upwind_solve(int n, const double *s, double *rhs, int nrhs, double rcond,
                    int always_svd, struct rd_solve_info *result)
{
  *result = (struct rd_solve_info){.rank = -1, .pivot_ratio = 1.0};
  if((n != 4 && n != 5) || nrhs < 1 || !isfinite(rcond))
    return -1;
  for(int k = 0; k < n * n; k++)
    if(!isfinite(s[k]))
      return -1;
  for(int k = 0; k < n * nrhs; k++)
    if(!isfinite(rhs[k]))
      return -1;

  double a[25];
  lapack_int ipiv[5], info = 0;
  memcpy(a, s, n * n * sizeof(double));
  int use_svd = always_svd;
  if(!use_svd)
    {
      info = LAPACKE_dgetrf(LAPACK_ROW_MAJOR, n, n, a, n, ipiv);
      if(info < 0)
        return info;
      if(info > 0)
        {
          use_svd = 1;
          result->exact_singular = 1;
          result->pivot_ratio = 0.0;
        }
      else
        {
          double pivot_max = fabs(a[0]), pivot_min = fabs(a[0]);
          for(int k = 1; k < n; k++)
            {
              pivot_max = fmax(pivot_max, fabs(a[k * n + k]));
              pivot_min = fmin(pivot_min, fabs(a[k * n + k]));
            }
          result->pivot_ratio = pivot_max > 0.0 ? pivot_min / pivot_max : 0.0;
          use_svd = !(result->pivot_ratio >= 1e-12);
        }
    }
  if(!use_svd)
    {
      info = LAPACKE_dgetrs(LAPACK_ROW_MAJOR, 'N', n, nrhs, a, n, ipiv, rhs, nrhs);
      if(info == 0)
        result->rank = n;
      return info;
    }

  double singular_values[5];
  lapack_int rank;
  memcpy(a, s, n * n * sizeof(double));
  result->used_svd = 1;
  info = LAPACKE_dgelsd(LAPACK_ROW_MAJOR, n, n, nrhs, a, n, rhs, nrhs, singular_values, rcond, &rank);
  if(info == 0)
    result->rank = rank;
  return info;
}
