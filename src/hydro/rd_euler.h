#ifndef RD_EULER_H
#define RD_EULER_H

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

#endif
