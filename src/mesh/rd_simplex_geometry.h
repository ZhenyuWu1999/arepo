#ifndef RD_SIMPLEX_GEOMETRY_H
#define RD_SIMPLEX_GEOMETRY_H

/* Pure spatial geometry; compact arrays x[ndim+1][ndim], unit_normal of the
 * same shape, face_measure[ndim+1]. Coordinates must ALREADY use consistent
 * periodic images; this function does not wrap coordinates.
 * Return signed area/volume for the supplied ordering and inward unit face
 * normals. Both orderings are supported, zero/nonfinite measure is rejected.
 * A time-dependent adapter must track orientation separately: accepting both
 * static orderings is NOT permission to accept an inversion during motion. */
int rd_simplex_geometry(int ndim, const double *x, double *signed_measure,
                        double *unit_normal, double *face_measure);

#endif
