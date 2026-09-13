#ifndef RD_CONTOUR_QUADRATURE_H
#define RD_CONTOUR_QUADRATURE_H

/* Experimental replacement of the physical-flux edge trapezoid by Gauss
 * on the conservative P1 state. Mesh transport is already exact for that
 * state and is not changed. Normals point inward, opposite each vertex.
 * Shared-edge corrections cancel; a Galilean boost changes F by a linear
 * function of U, whose quadrature defect is zero. No limiter is applied. */
static void rd_contour_physical_flux(const double u[4], double gamma, double f[2][4])
{
  double vx = u[1] / u[0], vy = u[2] / u[0];
  double p = (gamma - 1.0) * (u[3] - 0.5 * (u[1] * vx + u[2] * vy));
  f[0][0] = u[1]; f[1][0] = u[2];
  f[0][1] = u[1] * vx + p; f[1][1] = u[1] * vy;
  f[0][2] = u[2] * vx; f[1][2] = u[2] * vy + p;
  f[0][3] = (u[3] + p) * vx; f[1][3] = (u[3] + p) * vy;
}

static void rd_contour_gauss_correction(const double u[3][4], const double nx[3], const double ny[3],
                                        const double mag[3], double gamma, double phi[4], double *scale)
{
#if defined(RD_ALE_CONTOUR_GAUSS) && RD_ALE_CONTOUR_GAUSS == 5
  const int nq = 5;
  const double x[5] = {0.04691007703066800360, 0.23076534494715845448, 0.5,
                       0.76923465505284154552, 0.95308992296933199640};
  const double w[5] = {0.11846344252809454376, 0.23931433524968323402, 0.28444444444444444444,
                       0.23931433524968323402, 0.11846344252809454376};
#else
  const int nq = 3;
  const double x[3] = {0.11270166537925831148, 0.5, 0.88729833462074168852};
  const double w[3] = {5.0 / 18.0, 4.0 / 9.0, 5.0 / 18.0};
#endif
  double f[3][2][4];
  for(int j = 0; j < 3; j++) rd_contour_physical_flux(u[j], gamma, f[j]);
  for(int j = 0; j < 3; j++)
    {
      int a = (j + 1) % 3, b = (j + 2) % 3;
      for(int q = 0; q < nq; q++)
        {
          double uq[4], fq[2][4];
          for(int k = 0; k < 4; k++) uq[k] = (1.0 - x[q]) * u[a][k] + x[q] * u[b][k];
          rd_contour_physical_flux(uq, gamma, fq);
          /* Mass flux is linear in U: its correction is identically zero. */
          for(int k = 1; k < 4; k++)
            {
              double dx = fq[0][k] - ((1.0 - x[q]) * f[a][0][k] + x[q] * f[b][0][k]);
              double dy = fq[1][k] - ((1.0 - x[q]) * f[a][1][k] + x[q] * f[b][1][k]);
              double c = -mag[j] * w[q] * (nx[j] * dx + ny[j] * dy);
              phi[k] += c;
              *scale += fabs(c);
            }
        }
    }
}
#endif
