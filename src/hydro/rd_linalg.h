#ifndef RD_LINALG_H
#define RD_LINALG_H

struct rd_solve_info
{
  int rank;              /* -1 if solve failed */
  int used_svd;
  int exact_singular;
  double pivot_ratio;    /* LU selection proxy, NOT a condition estimate */
};

/* Solve S X = rhs for n=4 or 5. Compact row-major S[n][n] is unchanged;
 * rhs[n][nrhs] is overwritten. LU pivot spread selects DGELSD when needed;
 * rcond is DGELSD's separate numerical-rank threshold (-1: LAPACK default).
 * A successful least-squares solve does not establish RHS compatibility:
 * callers must check the residual / distribution's conservation identity. */
int rd_upwind_solve(int n, const double *s, double *rhs, int nrhs, double rcond,
                    int always_svd, struct rd_solve_info *result);

#endif
