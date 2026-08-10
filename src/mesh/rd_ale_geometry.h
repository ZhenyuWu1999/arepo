#ifndef RD_ALE_GEOMETRY_H
#define RD_ALE_GEOMETRY_H

#include "mesh.h"

enum rd_ale_time_level
{
  RD_ALE_OLD = 0,
  RD_ALE_MID = 1,
  RD_ALE_NEW = 2
};

struct rd_ale_triangle_geometry
{
  double x[3][3][2];          /*!< [time level][vertex][axis] */
  double velocity[3][2];      /*!< vertex displacement velocity */
  struct triangle_normals normals[3];
  double delta_area;          /*!< (A_old + A_new)/2 - A_mid */
  double arpaia_mass;         /*!< A_mid */
  double arpaia_divisor;      /*!< A_mid + (A_new - A_old)/2 */
};

/*! Build old, midpoint and new geometry on one fixed connectivity.
 *
 * `x_new` must use one coherent periodic image of the triangle. The vertex
 * trajectory is linear over `dt`. Signed areas are retained so callers can
 * diagnose pulled-back inversions before deciding whether to reject them.
 */
void rd_ale_triangle_geometry_build(const double x_new[3][2], const double velocity[3][2], double dt,
                                    struct rd_ale_triangle_geometry *geometry);

#endif
