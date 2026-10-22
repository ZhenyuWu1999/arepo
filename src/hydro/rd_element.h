#ifndef RD_ELEMENT_H
#define RD_ELEMENT_H

#include "rd_euler.h"

/* Borrowed element views, independent of AREPO storage and compile-time DIMS.
 * ndim is 2 or 3; nvert=ndim+1 and nvar=ndim+2. All arrays are compact.
 * The caller owns the arrays and selects the geometrical/time policy.
 * For a static element measure is area/volume. An ALE adapter may supply its
 * selected temporal measure: positivity of that number does NOT certify an
 * orientation-preserving trajectory or a valid connectivity change. */
struct rd_element_geometry
{
  int ndim;
  double measure;
  const double *unit_normal;  /* [nvert][ndim], inward */
  const double *face_measure; /* [nvert], edge length / triangular face area */
};

struct rd_element_input
{
  struct rd_element_geometry geometry;
  const double *conserved; /* [nvert][nvar], rho, momenta, energy */
};

enum rd_element_scheme { RD_ELEMENT_N, RD_ELEMENT_LDA };

struct rd_element_output
{
  double *total;    /* [nvar], integrated spatial divergence */
  double *spatial;  /* [nvar][nvert], NO timestep factor */
  double *temporal; /* [nvar][nvert], required only for an F1 target */
};

/* Static P1-Z/Roe backend. This is an explicit residual policy, not a default
 * replacement for a Gauss-contour or ALE backend. The adapter only changes
 * array layout around the existing Euler kernel; the arithmetic stays there.
 * Rank-deficient F1 returns zero temporal output, as rd_euler.h specifies;
 * the temporal integrator must choose the conservative lumped action.
 * Return codes and raw diagnostics are those of the underlying Euler kernel. */
int rd_element_roe_residual(const struct rd_element_input *input, enum rd_element_scheme scheme,
                            double gamma, double rcond, int always_svd, const double *temporal_target,
                            struct rd_element_output *output, struct rd_n_diagnostics *diagnostics);

/* Final stage rate at the boundary with the native conservative ledger.
 * The backend has already included its spatial/temporal corrections. The
 * native scheduler applies the deposit timestep exactly once, outside the
 * pure spatial kernel. Both legacy 2D and pure-kernel 3D emit this layout. */
struct rd_element_flux
{
  int ndim;
  const double *rate; /* [nvar][nvert], component first */
};

#endif
