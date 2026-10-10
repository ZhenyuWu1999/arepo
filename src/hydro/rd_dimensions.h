#ifndef RD_DIMENSIONS_H
#define RD_DIMENSIONS_H

/* Storage dimensions are needed by mesh.h BEFORE voronoi.h defines DIMS.
 * Keep spatial dimension, vertex count, variable count and energy index
 * distinct. Pure numerical kernels receive ndim explicitly instead. */
#ifdef TWODIMS
enum { RD_NDIM = 2 };
#else
enum { RD_NDIM = 3 };
#endif
enum { RD_NVERT = RD_NDIM + 1, RD_NVAR = RD_NDIM + 2, RD_ENERGY = RD_NVAR - 1 };

#endif
