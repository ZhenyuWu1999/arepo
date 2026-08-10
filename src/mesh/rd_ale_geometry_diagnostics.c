/*
 * Stage-0 ALE geometry diagnostics for the moving-mesh RD development.
 *
 * This file deliberately does not read or update the hydrodynamic solution.
 * A normal finite-volume AREPO run supplies the real mesh-generating velocity,
 * regularisation and Delaunay rebuild.  The diagnostic then evaluates every
 * triangle of the post-rebuild connectivity at
 *
 *   x^n       = x^{n+1} - dt_drift * VelVertex,
 *   x^{n+1/2} = x^{n+1} - 0.5 * dt_drift * VelVertex,
 *   x^{n+1},
 *
 * and compares the pulled-back old quadrature with the actual triangulation
 * saved at the preceding synchronization point.  No flux, conserved variable,
 * primitive variable or timestep is modified here.
 *
 * The first implementation is intentionally narrow: two-dimensional periodic
 * geometry, global timesteps, no refinement and one MPI rank.  Keeping those
 * restrictions explicit prevents a diagnostic ownership shortcut from being
 * mistaken for the later production ALE-RD implementation.
 */

#include <float.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../main/allvars.h"
#include "../main/proto.h"
#include "../mesh/mesh.h"
#include "../mesh/rd_ale_geometry.h"
#include "../mesh/voronoi/voronoi.h"

#ifdef RD_ALE_GEOMETRY_DIAGNOSTICS

#if !defined(TWODIMS)
#error "RD_ALE_GEOMETRY_DIAGNOSTICS is currently implemented only in two dimensions."
#endif

#if !defined(FORCE_EQUAL_TIMESTEPS)
#error "RD_ALE_GEOMETRY_DIAGNOSTICS Stage 0 currently requires FORCE_EQUAL_TIMESTEPS."
#endif

#if defined(VORONOI_STATIC_MESH)
#error "RD_ALE_GEOMETRY_DIAGNOSTICS requires a moving mesh."
#endif

#if defined(REFLECTIVE_X) || defined(REFLECTIVE_Y) || defined(REFLECTIVE_Z)
#error "RD_ALE_GEOMETRY_DIAGNOSTICS Stage 0 currently supports periodic boundaries only."
#endif

#if defined(REFINEMENT)
#error "RD_ALE_GEOMETRY_DIAGNOSTICS Stage 0 currently excludes refinement and derefinement."
#endif

#define RD_ALE_NPROBE 2

struct rd_ale_edge
{
  MyIDType lo, hi;
};

/*! Median-dual lumped mass of one generator, keyed by particle ID.
 *
 *  The aggregate probe defect below is built from spatially periodic functions
 *  and is therefore blind to an error of a whole lattice vector in a ghost
 *  image, and it can hide a large nodal error behind a cancellation. Carrying
 *  the nodal masses by ID makes the two moment identities of the development
 *  log testable per generator rather than only in aggregate, and localises any
 *  failure to a particle. IDs are used rather than indices because the domain
 *  decomposition reorders P and SphP even on a single rank.
 */
struct rd_ale_node
{
  MyIDType id;
  double mass;
  double pos[2]; /*!< primary generator position at the time of the snapshot */
};

struct rd_ale_snapshot
{
  double area;
  double probe[RD_ALE_NPROBE];
  struct rd_ale_edge *edges;
  int nedge;
  int ntriangle;
  struct rd_ale_node *nodes;
  int nnode;
};

static struct rd_ale_snapshot RdAleOld;
static int RdAleHaveOld = 0;
static FILE *RdAleFile  = NULL;
static double RdAleCumulativeDefect[RD_ALE_NPROBE];

static double *RdAleBaseVelocity = NULL;
static int RdAleBaseVelocitySize = 0;
static double RdAleRegularisationRms;
static double RdAleRegularisationMax;
static double RdAleRegularisationActiveFraction;
static double RdAleQuasiLagrangianRms;

static int rd_ale_triangle_is_physical(const tessellation *T, int triangle)
{
  if(triangle < 0 || triangle >= T->Ndt)
    return 0;

  for(int vertex = 0; vertex < 3; vertex++)
    {
      int point_index = T->DT[triangle].p[vertex];

      if(point_index < 0 || point_index >= T->Ndp)
        return 0;
      if(T->DP[point_index].task < 0 || T->DP[point_index].task >= NTask || T->DP[point_index].index < 0)
        return 0;
    }

  return 1;
}

/* This is the equal-step form of the RD minimum-ID ownership rule. */
static int rd_ale_triangle_claimed(const tessellation *T, int triangle)
{
  MyIDType min_id = 0;
  int min_task = -1;

  for(int vertex = 0; vertex < 3; vertex++)
    {
      const point *dp = &T->DP[T->DT[triangle].p[vertex]];

      if(min_task < 0 || dp->ID < min_id || (dp->ID == min_id && dp->task < min_task))
        {
          min_id   = dp->ID;
          min_task = dp->task;
        }
    }

  for(int vertex = 0; vertex < 3; vertex++)
    {
      const point *dp = &T->DP[T->DT[triangle].p[vertex]];

      if(dp->ID == min_id && dp->task == ThisTask && dp->task == min_task && dp->index >= 0 && dp->index < NumGas)
        return 1;
    }

  return 0;
}

static double rd_ale_signed_area(const double x[3], const double y[3])
{
  return 0.5 * ((x[1] - x[0]) * (y[2] - y[0]) - (x[2] - x[0]) * (y[1] - y[0]));
}

static double rd_ale_wrap(double x, double length)
{
  double wrapped = fmod(x, length);
  if(wrapped < 0.0)
    wrapped += length;
  return wrapped;
}

static double rd_ale_probe(int which, double x, double y)
{
  const double twopi = 6.283185307179586476925286766559;
  double xx          = rd_ale_wrap(x, boxSize_X) / boxSize_X;
  double yy          = rd_ale_wrap(y, boxSize_Y) / boxSize_Y;

  if(which == 0)
    return sin(twopi * xx) + 0.5 * cos(twopi * yy) + 0.25 * sin(twopi * (xx + yy));

  return sin(twopi * xx) * sin(twopi * yy) + 0.25 * cos(twopi * (2.0 * xx - yy));
}

static int rd_ale_node_compare(const void *a, const void *b)
{
  const struct rd_ale_node *na = (const struct rd_ale_node *)a;
  const struct rd_ale_node *nb = (const struct rd_ale_node *)b;

  if(na->id < nb->id)
    return -1;
  if(na->id > nb->id)
    return 1;
  return 0;
}

/*! Add one third of a triangle area to the entry of generator `id`. */
static void rd_ale_add_node_mass(struct rd_ale_node *nodes, int nnode, MyIDType id, double contribution)
{
  int low = 0, high = nnode - 1;

  while(low <= high)
    {
      int middle = (low + high) / 2;
      if(nodes[middle].id == id)
        {
          nodes[middle].mass += contribution;
          return;
        }
      if(nodes[middle].id < id)
        low = middle + 1;
      else
        high = middle - 1;
    }

  terminate_program("RD ALE Stage 0 saw a triangle vertex whose ID is not a local generator");
}

static int rd_ale_edge_compare(const void *a, const void *b)
{
  const struct rd_ale_edge *ea = (const struct rd_ale_edge *)a;
  const struct rd_ale_edge *eb = (const struct rd_ale_edge *)b;

  if(ea->lo < eb->lo)
    return -1;
  if(ea->lo > eb->lo)
    return 1;
  if(ea->hi < eb->hi)
    return -1;
  if(ea->hi > eb->hi)
    return 1;
  return 0;
}

static void rd_ale_add_edge(struct rd_ale_edge *edges, int *nedge, MyIDType a, MyIDType b)
{
  if(a < b)
    {
      edges[*nedge].lo = a;
      edges[*nedge].hi = b;
    }
  else
    {
      edges[*nedge].lo = b;
      edges[*nedge].hi = a;
    }
  (*nedge)++;
}

static void rd_ale_snapshot_free(struct rd_ale_snapshot *snapshot)
{
  free(snapshot->edges);
  free(snapshot->nodes);
  memset(snapshot, 0, sizeof(*snapshot));
}

static void rd_ale_build_snapshot(const tessellation *T, struct rd_ale_snapshot *snapshot)
{
  memset(snapshot, 0, sizeof(*snapshot));

  int nclaimed = 0;
  for(int triangle = 0; triangle < T->Ndt; triangle++)
    if(rd_ale_triangle_is_physical(T, triangle) && rd_ale_triangle_claimed(T, triangle))
      nclaimed++;

  snapshot->edges = (struct rd_ale_edge *)malloc((size_t)(3 * nclaimed) * sizeof(*snapshot->edges));
  if(nclaimed > 0 && snapshot->edges == NULL)
    terminate_program("RD ALE Stage 0 could not allocate the edge snapshot");

  snapshot->nodes = (struct rd_ale_node *)malloc((size_t)NumGas * sizeof(*snapshot->nodes));
  if(NumGas > 0 && snapshot->nodes == NULL)
    terminate_program("RD ALE Stage 0 could not allocate the nodal mass snapshot");
  snapshot->nnode = NumGas;
  for(int i = 0; i < NumGas; i++)
    {
      snapshot->nodes[i].id     = P[i].ID;
      snapshot->nodes[i].mass   = 0.0;
      snapshot->nodes[i].pos[0] = P[i].Pos[0];
      snapshot->nodes[i].pos[1] = P[i].Pos[1];
    }
  qsort(snapshot->nodes, (size_t)snapshot->nnode, sizeof(*snapshot->nodes), rd_ale_node_compare);

  int nedge = 0;
  for(int triangle = 0; triangle < T->Ndt; triangle++)
    {
      if(!rd_ale_triangle_is_physical(T, triangle) || !rd_ale_triangle_claimed(T, triangle))
        continue;

      double x[3], y[3];
      MyIDType id[3];
      for(int vertex = 0; vertex < 3; vertex++)
        {
          const point *dp = &T->DP[T->DT[triangle].p[vertex]];
          x[vertex]       = dp->x;
          y[vertex]       = dp->y;
          id[vertex]      = dp->ID;
        }

      double area = rd_ale_signed_area(x, y);
      if(!(area > 0.0))
        terminate_program("RD ALE Stage 0 found a non-positive current Delaunay triangle");

      snapshot->area += area;
      for(int probe = 0; probe < RD_ALE_NPROBE; probe++)
        snapshot->probe[probe] +=
            area * (rd_ale_probe(probe, x[0], y[0]) + rd_ale_probe(probe, x[1], y[1]) + rd_ale_probe(probe, x[2], y[2])) / 3.0;

      for(int vertex = 0; vertex < 3; vertex++)
        rd_ale_add_node_mass(snapshot->nodes, snapshot->nnode, id[vertex], area / 3.0);

      rd_ale_add_edge(snapshot->edges, &nedge, id[0], id[1]);
      rd_ale_add_edge(snapshot->edges, &nedge, id[1], id[2]);
      rd_ale_add_edge(snapshot->edges, &nedge, id[2], id[0]);
      snapshot->ntriangle++;
    }

  qsort(snapshot->edges, (size_t)nedge, sizeof(*snapshot->edges), rd_ale_edge_compare);

  int unique = 0;
  for(int edge = 0; edge < nedge; edge++)
    if(unique == 0 || rd_ale_edge_compare(&snapshot->edges[edge], &snapshot->edges[unique - 1]) != 0)
      snapshot->edges[unique++] = snapshot->edges[edge];

  snapshot->nedge = unique;
}

static void rd_ale_compare_edges(const struct rd_ale_snapshot *old_snapshot, const struct rd_ale_snapshot *new_snapshot,
                                 int *removed, int *added)
{
  int old_edge = 0, new_edge = 0;
  *removed = *added = 0;

  while(old_edge < old_snapshot->nedge && new_edge < new_snapshot->nedge)
    {
      int comparison = rd_ale_edge_compare(&old_snapshot->edges[old_edge], &new_snapshot->edges[new_edge]);
      if(comparison < 0)
        {
          (*removed)++;
          old_edge++;
        }
      else if(comparison > 0)
        {
          (*added)++;
          new_edge++;
        }
      else
        {
          old_edge++;
          new_edge++;
        }
    }

  *removed += old_snapshot->nedge - old_edge;
  *added += new_snapshot->nedge - new_edge;
}

static int rd_ale_local_index(const point *dp)
{
  if(dp->task != ThisTask)
    terminate_program("RD ALE Stage 0 v1 encountered a remote vertex despite its one-rank guard");

  int index = dp->index;
  if(index >= NumGas)
    index -= NumGas;
  if(index < 0 || index >= NumGas)
    terminate_program("RD ALE Stage 0 could not map a local periodic image to its primary");
  return index;
}

static void rd_ale_point_velocity(const point *dp, double velocity[2])
{
  int index   = rd_ale_local_index(dp);
  velocity[0] = SphP[index].VelVertex[0];
  velocity[1] = SphP[index].VelVertex[1];
}

static double rd_ale_minimum_angle(const double x[3], const double y[3])
{
  double minimum = DBL_MAX;

  for(int vertex = 0; vertex < 3; vertex++)
    {
      int a = (vertex + 1) % 3;
      int b = (vertex + 2) % 3;
      double ax = x[a] - x[vertex], ay = y[a] - y[vertex];
      double bx = x[b] - x[vertex], by = y[b] - y[vertex];
      double cross = fabs(ax * by - ay * bx);
      double dot   = ax * bx + ay * by;
      double angle = atan2(cross, dot);
      if(angle < minimum)
        minimum = angle;
    }

  return minimum;
}

static double rd_ale_drift_interval(void)
{
  if(All.ComovingIntegrationOn)
    return get_drift_factor(All.Previous_Ti_Current, All.Ti_Current);
  return (All.Ti_Current - All.Previous_Ti_Current) * All.Timebase_interval;
}

static void rd_ale_open_output(void)
{
  if(RdAleFile != NULL || ThisTask != 0)
    return;

  char filename[MAXLEN_PATH + 64];
  snprintf(filename, sizeof(filename), "%srd_ale_geometry_stage0.csv", All.OutputDir);

  const char *mode = (All.NumCurrentTiStep == 0) ? "w" : "a";
  RdAleFile        = fopen(filename, mode);
  if(RdAleFile == NULL)
    terminate_program("RD ALE Stage 0 could not open its CSV output");

  if(mode[0] == 'w')
    fprintf(RdAleFile,
            "step,time,time_dt,drift_dt,ntriangle,removed_edges,added_edges,"
            "area_old_actual,area_old_pulled,area_mid,area_new,"
            "coverage_old_rel,coverage_mid_rel,coverage_new_rel,"
            "defect_trig,defect_wave,cumulative_trig,cumulative_wave,"
            "max_delta_identity,max_delta_over_area,inverted_old,nonpositive_mid,nonpositive_arpaia_nodes,"
            "min_arpaia_mass,min_campoli_mass,min_old_area_over_mean,min_mid_area_over_mean,min_new_area_over_mean,"
            "min_angle_new,max_centroid_offset_r,rms_centroid_offset_r,quasi_lagrangian_velocity_rms,mesh_velocity_rms,"
            "regularisation_velocity_rms,regularisation_velocity_max,regularisation_active_fraction,"
            "dm_signed_sum,dm_abs_sum,dm_abs_max,dm_touched_nodes,"
            "dm_first_moment_x,dm_first_moment_y,max_pullback_position_error\n");
}

void rd_ale_geometry_velocity_begin(void)
{
  if(NTask != 1)
    return;

  if(RdAleBaseVelocitySize != NumGas)
    {
      free(RdAleBaseVelocity);
      RdAleBaseVelocity = (double *)malloc((size_t)(3 * NumGas) * sizeof(*RdAleBaseVelocity));
      if(NumGas > 0 && RdAleBaseVelocity == NULL)
        terminate_program("RD ALE Stage 0 could not allocate its velocity snapshot");
      RdAleBaseVelocitySize = NumGas;
    }

  for(int i = 0; i < NumGas; i++)
    for(int axis = 0; axis < 3; axis++)
      RdAleBaseVelocity[3 * i + axis] = SphP[i].VelVertex[axis];
}

void rd_ale_geometry_velocity_end(void)
{
  if(NTask != 1 || RdAleBaseVelocitySize != NumGas)
    return;

  double sum2 = 0.0, base_sum2 = 0.0, maximum = 0.0;
  int active = 0;

  for(int i = 0; i < NumGas; i++)
    {
      double correction2 = 0.0, scale2 = 1.0;
      for(int axis = 0; axis < 3; axis++)
        {
          base_sum2 += RdAleBaseVelocity[3 * i + axis] * RdAleBaseVelocity[3 * i + axis];
          double correction = SphP[i].VelVertex[axis] - RdAleBaseVelocity[3 * i + axis];
          correction2 += correction * correction;
          scale2 += SphP[i].VelVertex[axis] * SphP[i].VelVertex[axis] +
                    RdAleBaseVelocity[3 * i + axis] * RdAleBaseVelocity[3 * i + axis];
        }

      double magnitude = sqrt(correction2);
      sum2 += correction2;
      if(magnitude > maximum)
        maximum = magnitude;
      if(magnitude > 64.0 * DBL_EPSILON * sqrt(scale2))
        active++;
    }

  RdAleRegularisationRms            = (NumGas > 0) ? sqrt(sum2 / NumGas) : 0.0;
  RdAleRegularisationMax            = maximum;
  RdAleRegularisationActiveFraction = (NumGas > 0) ? (double)active / NumGas : 0.0;
  RdAleQuasiLagrangianRms           = (NumGas > 0) ? sqrt(base_sum2 / NumGas) : 0.0;
}

void rd_ale_geometry_after_mesh(tessellation *T)
{
  if(NTask != 1)
    terminate_program("RD_ALE_GEOMETRY_DIAGNOSTICS Stage 0 v1 is deliberately restricted to one MPI rank");

  struct rd_ale_snapshot current;
  rd_ale_build_snapshot(T, &current);
  rd_ale_open_output();

  if(!RdAleHaveOld)
    {
      RdAleOld     = current;
      RdAleHaveOld = 1;
      mpi_printf("RD-ALE-GEOM: captured baseline mesh with %d triangles and %d edges\n", RdAleOld.ntriangle, RdAleOld.nedge);
      return;
    }

  double drift_dt = rd_ale_drift_interval();
  if(!(drift_dt > 0.0))
    {
      rd_ale_snapshot_free(&RdAleOld);
      RdAleOld = current;
      mpi_printf("RD-ALE-GEOM: reset baseline because the drift interval is not positive\n");
      return;
    }

  struct rd_ale_node *pulled_nodes = (struct rd_ale_node *)malloc((size_t)NumGas * sizeof(*pulled_nodes));
  if(NumGas > 0 && pulled_nodes == NULL)
    terminate_program("RD ALE Stage 0 could not allocate the pulled-back nodal mass");
  for(int i = 0; i < NumGas; i++)
    {
      pulled_nodes[i].id     = P[i].ID;
      pulled_nodes[i].mass   = 0.0;
      pulled_nodes[i].pos[0] = rd_ale_wrap(P[i].Pos[0] - drift_dt * SphP[i].VelVertex[0], boxSize_X);
      pulled_nodes[i].pos[1] = rd_ale_wrap(P[i].Pos[1] - drift_dt * SphP[i].VelVertex[1], boxSize_Y);
    }
  qsort(pulled_nodes, (size_t)NumGas, sizeof(*pulled_nodes), rd_ale_node_compare);

  double *arpaia_mass  = (double *)calloc((size_t)NumGas, sizeof(*arpaia_mass));
  double *campoli_mass = (double *)calloc((size_t)NumGas, sizeof(*campoli_mass));
  if(NumGas > 0 && (arpaia_mass == NULL || campoli_mass == NULL))
    terminate_program("RD ALE Stage 0 could not allocate nodal divisor diagnostics");

  double pulled_area = 0.0, midpoint_area = 0.0;
  double pulled_probe[RD_ALE_NPROBE] = {0.0, 0.0};
  double min_old_area = DBL_MAX, min_mid_area = DBL_MAX, min_new_area = DBL_MAX;
  double min_angle_new = DBL_MAX;
  double max_delta_identity = 0.0, max_delta_over_area = 0.0;
  int inverted_old = 0, nonpositive_mid = 0;
  int ntriangle = 0;

  for(int triangle = 0; triangle < T->Ndt; triangle++)
    {
      if(!rd_ale_triangle_is_physical(T, triangle) || !rd_ale_triangle_claimed(T, triangle))
        continue;

      double xnew[3][2], velocity[3][2];

      for(int vertex = 0; vertex < 3; vertex++)
        {
          const point *dp = &T->DP[T->DT[triangle].p[vertex]];
          rd_ale_point_velocity(dp, velocity[vertex]);
          xnew[vertex][0] = dp->x;
          xnew[vertex][1] = dp->y;
        }

      struct rd_ale_triangle_geometry geometry;
      rd_ale_triangle_geometry_build(xnew, velocity, drift_dt, &geometry);

      double area_old = geometry.normals[RD_ALE_OLD].area;
      double area_mid = geometry.normals[RD_ALE_MID].area;
      double area_new = geometry.normals[RD_ALE_NEW].area;

      pulled_area += area_old;
      midpoint_area += area_mid;
      if(area_old < min_old_area)
        min_old_area = area_old;
      if(area_mid < min_mid_area)
        min_mid_area = area_mid;
      if(area_new < min_new_area)
        min_new_area = area_new;
      if(area_old <= 0.0)
        inverted_old++;
      if(area_mid <= 0.0)
        nonpositive_mid++;

      double angle = rd_ale_minimum_angle((double[3]){xnew[0][0], xnew[1][0], xnew[2][0]},
                                          (double[3]){xnew[0][1], xnew[1][1], xnew[2][1]});
      if(angle < min_angle_new)
        min_angle_new = angle;

      for(int probe = 0; probe < RD_ALE_NPROBE; probe++)
        pulled_probe[probe] += area_old * (rd_ale_probe(probe, geometry.x[RD_ALE_OLD][0][0], geometry.x[RD_ALE_OLD][0][1]) +
                                            rd_ale_probe(probe, geometry.x[RD_ALE_OLD][1][0], geometry.x[RD_ALE_OLD][1][1]) +
                                            rd_ale_probe(probe, geometry.x[RD_ALE_OLD][2][0], geometry.x[RD_ALE_OLD][2][1])) /
                               3.0;

      double delta_from_area = geometry.delta_area;
      double dv10x = velocity[1][0] - velocity[0][0];
      double dv10y = velocity[1][1] - velocity[0][1];
      double dv20x = velocity[2][0] - velocity[0][0];
      double dv20y = velocity[2][1] - velocity[0][1];
      double delta_from_velocity = 0.125 * drift_dt * drift_dt * (dv10x * dv20y - dv10y * dv20x);
      double identity_error = fabs(delta_from_area - delta_from_velocity);
      if(identity_error > max_delta_identity)
        max_delta_identity = identity_error;
      double delta_ratio = fabs(delta_from_area) / dmax(fabs(area_mid), DBL_MIN);
      if(delta_ratio > max_delta_over_area)
        max_delta_over_area = delta_ratio;

      double arpaia_contribution = geometry.arpaia_divisor;
      for(int vertex = 0; vertex < 3; vertex++)
        {
          const point *dp = &T->DP[T->DT[triangle].p[vertex]];
          int index       = rd_ale_local_index(dp);
          arpaia_mass[index] += arpaia_contribution / 3.0;
          campoli_mass[index] += area_new / 3.0;
          rd_ale_add_node_mass(pulled_nodes, NumGas, dp->ID, area_old / 3.0);
        }

      ntriangle++;
    }

  int nonpositive_arpaia = 0;
  double min_arpaia = DBL_MAX, min_campoli = DBL_MAX;
  for(int i = 0; i < NumGas; i++)
    {
      if(arpaia_mass[i] <= 0.0)
        nonpositive_arpaia++;
      if(arpaia_mass[i] < min_arpaia)
        min_arpaia = arpaia_mass[i];
      if(campoli_mass[i] < min_campoli)
        min_campoli = campoli_mass[i];
    }

  double centroid_sum2 = 0.0, centroid_max = 0.0, mesh_velocity_sum2 = 0.0;
  for(int i = 0; i < NumGas; i++)
    {
      double dx = nearest_x(P[i].Pos[0] - SphP[i].Center[0]);
      double dy = nearest_y(P[i].Pos[1] - SphP[i].Center[1]);
      double radius = get_cell_radius(i);
      double ratio  = (radius > 0.0) ? sqrt(dx * dx + dy * dy) / radius : DBL_MAX;
      centroid_sum2 += ratio * ratio;
      if(ratio > centroid_max)
        centroid_max = ratio;
      mesh_velocity_sum2 += SphP[i].VelVertex[0] * SphP[i].VelVertex[0] + SphP[i].VelVertex[1] * SphP[i].VelVertex[1];
    }

  double centroid_rms = (NumGas > 0) ? sqrt(centroid_sum2 / NumGas) : 0.0;
  double mesh_velocity_rms = (NumGas > 0) ? sqrt(mesh_velocity_sum2 / NumGas) : 0.0;

  /* Per-generator topology defect dm_i = mhat_i^n - m_i^n.
   *
   * Two things are measured here. The zeroth moment sum_i dm_i must vanish to
   * round-off, because both triangulations tile the same domain. The first
   * moment sum_i dm_i x_i must vanish as well, by the P^1 linear-reproduction
   * argument of the development log, but only when it is evaluated with
   * positions that are consistent across a flip patch. The stored primary
   * positions are used for exactly that reason. A patch that straddles the
   * periodic boundary has its nodes on opposite sides of the box, so its
   * contribution is displaced by a lattice vector and the first moment then
   * carries a term of order boxsize * h^2. The diagnostic is therefore binary
   * in practice: round-off when no straddling patch flipped, and a value some
   * ten orders larger when one did. It is reported, not asserted.
   *
   * The reconstruction x^n = x^{n+1} - dt * VelVertex is also checked here
   * against the position actually recorded at the previous synchronisation
   * point, which is the first direct test of that identity inside AREPO
   * rather than an assumption about the drift. */
  double dm_signed_sum = 0.0, dm_abs_sum = 0.0, dm_abs_max = 0.0;
  double dm_first_moment[2] = {0.0, 0.0};
  double pullback_position_error = 0.0;
  int dm_touched = 0;
  {
    double mass_scale = (NumGas > 0) ? (boxSize_X * boxSize_Y / NumGas) : 1.0;
    double tolerance  = 1024.0 * DBL_EPSILON * mass_scale;
    int old_node = 0;

    for(int node = 0; node < NumGas; node++)
      {
        while(old_node < RdAleOld.nnode && RdAleOld.nodes[old_node].id < pulled_nodes[node].id)
          old_node++;
        if(old_node >= RdAleOld.nnode || RdAleOld.nodes[old_node].id != pulled_nodes[node].id)
          terminate_program("RD ALE Stage 0 lost a generator between snapshots");

        double dm = pulled_nodes[node].mass - RdAleOld.nodes[old_node].mass;
        dm_signed_sum += dm;
        dm_abs_sum += fabs(dm);
        if(fabs(dm) > dm_abs_max)
          dm_abs_max = fabs(dm);
        if(fabs(dm) > tolerance)
          dm_touched++;

        /* The old snapshot's primary position gives an unambiguous per-ID
         * reference. A patch-coherent image choice is still required before
         * the periodic first-moment identity can be used as a hard gate. */
        dm_first_moment[0] += dm * RdAleOld.nodes[old_node].pos[0];
        dm_first_moment[1] += dm * RdAleOld.nodes[old_node].pos[1];

        double error_x = fabs(nearest_x(pulled_nodes[node].pos[0] - RdAleOld.nodes[old_node].pos[0]));
        double error_y = fabs(nearest_y(pulled_nodes[node].pos[1] - RdAleOld.nodes[old_node].pos[1]));
        double error   = (error_x > error_y) ? error_x : error_y;
        if(error > pullback_position_error)
          pullback_position_error = error;
      }
  }

  int removed_edges, added_edges;
  rd_ale_compare_edges(&RdAleOld, &current, &removed_edges, &added_edges);

  double defect[RD_ALE_NPROBE];
  for(int probe = 0; probe < RD_ALE_NPROBE; probe++)
    {
      defect[probe] = pulled_probe[probe] - RdAleOld.probe[probe];
      RdAleCumulativeDefect[probe] += defect[probe];
    }

  double box_area = boxSize_X * boxSize_Y;
  double mean_area = (ntriangle > 0) ? current.area / ntriangle : 1.0;

  fprintf(RdAleFile,
          "%d,%.17g,%.17g,%.17g,%d,%d,%d,"
          "%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,"
          "%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%d,%d,%d,"
          "%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,"
          "%.17g,%.17g,%.17g,%d,%.17g,%.17g,%.17g\n",
          All.NumCurrentTiStep, All.Time, All.TimeStep, drift_dt, ntriangle, removed_edges, added_edges,
          RdAleOld.area, pulled_area, midpoint_area, current.area,
          (pulled_area - box_area) / box_area, (midpoint_area - box_area) / box_area, (current.area - box_area) / box_area,
          defect[0], defect[1], RdAleCumulativeDefect[0], RdAleCumulativeDefect[1], max_delta_identity, max_delta_over_area,
          inverted_old, nonpositive_mid, nonpositive_arpaia, min_arpaia, min_campoli,
          min_old_area / mean_area, min_mid_area / mean_area, min_new_area / mean_area, min_angle_new,
          centroid_max, centroid_rms, RdAleQuasiLagrangianRms, mesh_velocity_rms, RdAleRegularisationRms, RdAleRegularisationMax,
          RdAleRegularisationActiveFraction, dm_signed_sum, dm_abs_sum, dm_abs_max, dm_touched, dm_first_moment[0], dm_first_moment[1],
          pullback_position_error);
  fflush(RdAleFile);

  mpi_printf("RD-ALE-GEOM: step=%d replaced_edges=%d/%d D=(%.3e,%.3e) cum=(%.3e,%.3e) minA/mean=%.3e "
             "minangle=%.3e inverted=%d nonpos_Sbar=%d reg_rms=%.3e sum_dm=%.3e touched=%d "
             "first_moment=(%.3e,%.3e) pullback_err=%.3e\n",
             All.NumCurrentTiStep, removed_edges, added_edges, defect[0], defect[1], RdAleCumulativeDefect[0],
             RdAleCumulativeDefect[1], min_new_area / mean_area, min_angle_new, inverted_old, nonpositive_arpaia,
             RdAleRegularisationRms, dm_signed_sum, dm_touched, dm_first_moment[0], dm_first_moment[1],
             pullback_position_error);

  free(campoli_mass);
  free(arpaia_mass);
  free(pulled_nodes);
  rd_ale_snapshot_free(&RdAleOld);
  RdAleOld = current;
}

#endif /* RD_ALE_GEOMETRY_DIAGNOSTICS */
