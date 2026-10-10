#ifndef RD_TIMESTEP_H
#define RD_TIMESTEP_H

/* Native static tetra CFL on a uniquely owned complete element set. Deposits
 * V/4 and max_i[A_i/3 (c+|v.n_i|)] to every primary, including remote ranks.
 * Caller refreshes primitive ghosts before constructing the coefficients. */
void rd_static_tetra_cfl(tessellation *T, int n, const int *element,
                         const struct triangle_normals *geometry);

#endif
