#include <math.h>
#include <string.h>

#include "../main/allvars.h"
#include "rd_ale_geometry.h"

static void rd_ale_normals_from_coordinates(const double x[3][2], struct triangle_normals *normals)
{
  memset(normals, 0, sizeof(*normals));

  normals->normal[0][0] = x[1][1] - x[2][1];
  normals->normal[0][1] = x[2][0] - x[1][0];
  normals->normal[1][0] = x[2][1] - x[0][1];
  normals->normal[1][1] = x[0][0] - x[2][0];
  normals->normal[2][0] = x[0][1] - x[1][1];
  normals->normal[2][1] = x[1][0] - x[0][0];

  for(int vertex = 0; vertex < 3; vertex++)
    {
      /* Keep the arithmetic identical to triangle_get_normals_area().  This
       * makes sigma=0 an exact geometry-coefficient collapse test, not merely
       * a tolerance comparison between two equivalent norm formulas. */
      normals->mag[vertex] =
          sqrt(pow(normals->normal[vertex][0], 2) + pow(normals->normal[vertex][1], 2));
      if(normals->mag[vertex] > 0.0)
        {
          normals->normal[vertex][0] /= normals->mag[vertex];
          normals->normal[vertex][1] /= normals->mag[vertex];
        }
    }

  normals->area = 0.5 * ((x[1][0] - x[0][0]) * (x[2][1] - x[0][1]) -
                         (x[2][0] - x[0][0]) * (x[1][1] - x[0][1]));
}

void rd_ale_triangle_geometry_build(const double x_new[3][2], const double velocity[3][2], double dt,
                                    struct rd_ale_triangle_geometry *geometry)
{
  memset(geometry, 0, sizeof(*geometry));

  for(int vertex = 0; vertex < 3; vertex++)
    for(int axis = 0; axis < 2; axis++)
      {
        geometry->velocity[vertex][axis] = velocity[vertex][axis];
        geometry->x[RD_ALE_NEW][vertex][axis] = x_new[vertex][axis];
        geometry->x[RD_ALE_MID][vertex][axis] = x_new[vertex][axis] - 0.5 * dt * velocity[vertex][axis];
        geometry->x[RD_ALE_OLD][vertex][axis] = x_new[vertex][axis] - dt * velocity[vertex][axis];
      }

  for(int level = RD_ALE_OLD; level <= RD_ALE_NEW; level++)
    rd_ale_normals_from_coordinates(geometry->x[level], &geometry->normals[level]);

  double area_old = geometry->normals[RD_ALE_OLD].area;
  double area_mid = geometry->normals[RD_ALE_MID].area;
  double area_new = geometry->normals[RD_ALE_NEW].area;

  geometry->delta_area = 0.5 * (area_old + area_new) - area_mid;
  geometry->arpaia_mass = area_mid;
  geometry->arpaia_divisor = area_mid + 0.5 * (area_new - area_old);
}
