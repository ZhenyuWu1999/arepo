#ifndef RD_EULER_H
#define RD_EULER_H

#include "rd_linalg.h"

/* Pure Euler algebra, independent of AREPO storage and compile-time dimension.
 * ndim is 2 or 3; conserved ordering is rho, ndim momenta, total energy.
 * Arrays are compact row-major, with nvar = ndim + 2. */

/* Spectral function of the directional Euler Jacobian, multiplied by
 * face_measure / ndim. normal MUST be unit length and point toward the
 * opposite vertex; face_measure is edge length (2D) or triangle area (3D).
 * lambda = {u.n+c, u.n-c, u.n}, optionally shifted by -mesh_velocity.n
 * and/or split into positive/negative parts BEFORE this call. The repeated
 * advective eigenvalue includes entropy and ALL ndim-1 shear fields.
 * Returns 0 on success, -1 for invalid inputs. No floors or regularisation.
 * See dev_log/RD_3D_KERNEL_MATHEMATICS_20261010.md. */
int rd_euler_spectral_matrix(int ndim, const double *velocity, double enthalpy, double sound_speed,
                             double gamma, const double *normal, double face_measure,
                             const double lambda[3], double *matrix);

struct rd_n_diagnostics
{
  struct rd_solve_info solve;
  double conservation_defect, solve_defect, roundoff_scale, max_phi;
};

/* Static N distribution on a simplex, with the conservative P1-Z residual.
 * u and residual are [ndim+1][ndim+2], normals [ndim+1][ndim]. phi[ndim+2]
 * is the element total. No time-step factor (including 1/2) is included.
 * Checks raw solve compatibility and conservation; never repairs the result.
 * Returns 0 success, -1 invalid state/geometry, -2 solve failure,
 * -3 incompatible solve or failed element conservation. */
int rd_euler_n_residual(int ndim, const double *u, const double *unit_normal,
                       const double *face_measure, double gamma, double rcond,
                       int always_svd, double *phi, double *residual, struct rd_n_diagnostics *diagnostics);

/* Static LDA: phi_i = -K_i^+ (sum K^-)_solve phi. If temporal != NULL,
 * full-rank F1 applies the same distribution to temporal[nvar]. f1 is then
 * required [nvert][nvar]. For deficient rank f1 is zero: the caller MUST use
 * conservative element-local lumping, since an arbitrary temporal target
 * need not lie in range(sum K^-). Spatial compatibility is always checked.
 * Geometry and error conventions are identical to rd_euler_n_residual. */
int rd_euler_lda_residual(int ndim, const double *u, const double *unit_normal,
                         const double *face_measure, double gamma, double rcond,
                         int always_svd, const double *temporal, double *phi,
                         double *residual, double *f1, struct rd_n_diagnostics *diagnostics);

#endif
