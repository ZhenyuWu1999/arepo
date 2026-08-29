/*!
 * \copyright   This file is part of the public version of the AREPO code.
 * \copyright   Copyright (C) 2009-2019, Max-Planck Institute for Astrophysics
 * \copyright   Developed by Volker Springel (vspringel@MPA-Garching.MPG.DE) and
 *              contributing authors.
 * \copyright   Arepo is free software: you can redistribute it and/or modify
 *              it under the terms of the GNU General Public License as published by
 *              the Free Software Foundation, either version 3 of the License, or
 *              (at your option) any later version.
 *
 *              Arepo is distributed in the hope that it will be useful,
 *              but WITHOUT ANY WARRANTY; without even the implied warranty of
 *              MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *              GNU General Public License for more details.
 *
 *              A copy of the GNU General Public License is available under
 *              LICENSE as part of this program.  See also
 *              <https://www.gnu.org/licenses/>.
 *
 * \file        src/mesh/set_vertex_velocities.c
 * \date        05/2018
 * \brief       Algorithms that decide how individual cells are moving.
 * \details     contains functions:
 *                void set_vertex_velocities(void)
 *                static void validate_vertex_velocities_1d()
 *                void validate_vertex_velocities(void)
 *
 * \par Major modifications and contributions:
 *
 * - DD.MM.YYYY Description
 * - 08.05.2018 Prepared file for public release -- Rainer Weinberger
 */

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../main/allvars.h"
#include "../main/proto.h"
#include "../mesh/voronoi/voronoi.h"

#if defined(RD_ALE_SENSOR_ALL_WAVES) && !defined(RD_ALE_SENSOR_MESH_SMOOTHING)
#error "RD_ALE_SENSOR_ALL_WAVES requires RD_ALE_SENSOR_MESH_SMOOTHING."
#endif

#if defined(RD_ALE_SENSOR_MESH_SMOOTHING) && (!defined(RESIDUAL_DISTRIBUTION) || !defined(RD_ALE_EQUALSTEP))
#error "RD_ALE_SENSOR_MESH_SMOOTHING is currently restricted to equal-step ALE-RD experiments."
#endif

#ifdef ONEDIMS_SPHERICAL
static void validate_vertex_velocities_1d();
#endif /* #ifdef ONEDIMS_SPHERICAL */

#ifdef RD_ALE_SENSOR_MESH_SMOOTHING
static double rd_ale_clamp_unit(double value)
{
  if(value < 0)
    return 0;
  if(value > 1)
    return 1;
  return value;
}

/*! \brief Locally de-Lagrangianize the mesh in non-smooth flow.
 *
 * The correction
 *
 *   sigma_i <- sigma_i + alpha S_i (ubar_i - u_i)
 *
 * uses a face-area weighted neighbour velocity ubar_i. Both ubar_i-u_i and
 * the sensors below are invariant under a uniform velocity boost. The
 * shock-only sensor combines compression with a pressure reconstruction
 * defect. RD_ALE_SENSOR_ALL_WAVES additionally activates on reconstructed
 * density, pressure, or velocity defects, so contacts and rarefaction edges
 * can alter the mesh motion without penalising a locally linear smooth flow.
 *
 * This is an experimental ALE mesh-motion policy, not part of the published
 * Paardekooper B scheme. The final VelVertex is nevertheless the unique mesh
 * velocity subsequently used by the drift, ALE residual, K matrices, mass
 * update, and timestep calculation.
 */
static void rd_ale_apply_sensor_mesh_smoothing(void)
{
  const double alpha = RD_ALE_SENSOR_MESH_SMOOTHING;
  const double tiny  = 1.0e-30;
  long long local_count = 0, local_active = 0;
  double local_sum_sensor = 0, local_sum_correction2 = 0, local_max_correction = 0;
  double local_sum_rel_before2 = 0, local_sum_rel_after2 = 0;

  if(!(alpha > 0 && alpha <= 1))
    terminate_program("RD_ALE_SENSOR_MESH_SMOOTHING must lie in (0,1], got %g", alpha);

  for(int idx = 0; idx < TimeBinsHydro.NActiveParticles; idx++)
    {
      int i = TimeBinsHydro.ActiveParticleList[idx];
      if(i < 0)
        continue;

      double weighted_velocity[3] = {0, 0, 0};
      double weight_sum = 0;
      double max_pressure_defect = 0, max_wave_defect = 0;
      int q = SphP[i].first_connection;

      while(q >= 0)
        {
          int dp       = DC[q].dp_index;
          int vf       = DC[q].vf_index;
          int particle = Mesh.DP[dp].index;

          if(particle >= 0 && Mesh.VF[vf].area > 1.0e-10 * SphP[i].SurfaceArea && Mesh.DP[dp].ID != P[i].ID)
            {
              const MyFloat *velocity_other;
              const MyDouble *center_other;
              double density_other, pressure_other, sound_other;

              if(particle >= NumGas && Mesh.DP[dp].task == ThisTask)
                particle -= NumGas;

              if(Mesh.DP[dp].task == ThisTask)
                {
                  velocity_other = P[particle].Vel;
                  center_other   = SphP[particle].Center;
                  density_other  = SphP[particle].Density;
                  pressure_other = SphP[particle].Pressure;
                  sound_other    = get_sound_speed(particle);
                }
              else
                {
                  velocity_other = PrimExch[particle].VelGas;
                  center_other   = PrimExch[particle].Center;
                  density_other  = PrimExch[particle].Density;
                  pressure_other = PrimExch[particle].Pressure;
                  sound_other    = PrimExch[particle].Csnd;
                }

              double dx[3];
              dx[0] = nearest_x(center_other[0] - SphP[i].Center[0]);
              dx[1] = nearest_y(center_other[1] - SphP[i].Center[1]);
              dx[2] = nearest_z(center_other[2] - SphP[i].Center[2]);

              double density_predict  = SphP[i].Density;
              double pressure_predict = SphP[i].Pressure;
              double velocity_defect2 = 0;
              for(int dim = 0; dim < NUMDIMS; dim++)
                {
                  density_predict += SphP[i].Grad.drho[dim] * dx[dim];
                  pressure_predict += SphP[i].Grad.dpress[dim] * dx[dim];
                }
              for(int component = 0; component < NUMDIMS; component++)
                {
                  double velocity_predict = P[i].Vel[component];
                  for(int dim = 0; dim < NUMDIMS; dim++)
                    velocity_predict += SphP[i].Grad.dvel[component][dim] * dx[dim];
                  double defect = velocity_other[component] - velocity_predict;
                  velocity_defect2 += defect * defect;
                }

              double density_defect = fabs(density_other - density_predict) /
                                      (fabs(density_other) + fabs(SphP[i].Density) + tiny);
              double pressure_defect = fabs(pressure_other - pressure_predict) /
                                       (fabs(pressure_other) + fabs(SphP[i].Pressure) + tiny);
              double velocity_defect = sqrt(velocity_defect2) /
                                       (fabs(sound_other) + fabs(get_sound_speed(i)) + tiny);
              double wave_defect = dmax(density_defect, dmax(pressure_defect, velocity_defect));

              if(pressure_defect > max_pressure_defect)
                max_pressure_defect = pressure_defect;
              if(wave_defect > max_wave_defect)
                max_wave_defect = wave_defect;

              double weight = Mesh.VF[vf].area;
              for(int component = 0; component < NUMDIMS; component++)
                weighted_velocity[component] += weight * velocity_other[component];
              weight_sum += weight;
            }

          if(q == SphP[i].last_connection)
            break;
          q = DC[q].next;
        }

      double div_velocity = 0;
      for(int dim = 0; dim < NUMDIMS; dim++)
        div_velocity += SphP[i].Grad.dvel[dim][dim];

      double sound = get_sound_speed(i);
      double compression_speed = get_cell_radius(i) * dmax(-div_velocity, 0.0);
      double compression = compression_speed / (fabs(sound) + compression_speed + tiny);
      double sensor = rd_ale_clamp_unit(8.0 * compression * max_pressure_defect);

#ifdef RD_ALE_SENSOR_ALL_WAVES
      /* A reconstruction defect below 0.02 is treated as smooth. Defects at
       * 0.20 and above receive the full correction. This second branch is
       * deliberately broader than the compression sensor and is the part of
       * the experiment that targets contacts and rarefaction edges. */
      double all_wave_sensor = rd_ale_clamp_unit((max_wave_defect - 0.02) / 0.18);
      sensor = dmax(sensor, all_wave_sensor);
#endif

      double correction2 = 0, rel_before2 = 0, rel_after2 = 0;
      if(weight_sum > 0)
        for(int component = 0; component < NUMDIMS; component++)
          {
            double relative_before = P[i].Vel[component] - SphP[i].VelVertex[component];
            double mean_velocity = weighted_velocity[component] / weight_sum;
            double correction = alpha * sensor * (mean_velocity - P[i].Vel[component]);
            SphP[i].VelVertex[component] += correction;
            double relative_after = P[i].Vel[component] - SphP[i].VelVertex[component];
            correction2 += correction * correction;
            rel_before2 += relative_before * relative_before;
            rel_after2 += relative_after * relative_after;
          }

      double correction_norm = sqrt(correction2);
      local_count++;
      if(sensor > 1.0e-12)
        local_active++;
      local_sum_sensor += sensor;
      local_sum_correction2 += correction2;
      local_sum_rel_before2 += rel_before2;
      local_sum_rel_after2 += rel_after2;
      if(correction_norm > local_max_correction)
        local_max_correction = correction_norm;
    }

  long long global_count = 0, global_active = 0;
  double local_values[5] = {local_sum_sensor, local_sum_correction2, local_max_correction, local_sum_rel_before2,
                            local_sum_rel_after2};
  double global_values[5] = {0, 0, 0, 0, 0};
  MPI_Reduce(&local_count, &global_count, 1, MPI_LONG_LONG_INT, MPI_SUM, 0, MPI_COMM_WORLD);
  MPI_Reduce(&local_active, &global_active, 1, MPI_LONG_LONG_INT, MPI_SUM, 0, MPI_COMM_WORLD);
  MPI_Reduce(local_values, global_values, 2, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);
  MPI_Reduce(&local_values[2], &global_values[2], 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
  MPI_Reduce(&local_values[3], &global_values[3], 2, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);

  if(ThisTask == 0 && global_count > 0)
    mpi_printf("RD_ALE_MESH_SENSOR: time=%g alpha=%g active_fraction=%.9g mean_sensor=%.9g corr_rms=%.9g corr_max=%.9g rel_rms_before=%.9g rel_rms_after=%.9g mode=%s\n",
               All.Time, alpha, (double)global_active / global_count, global_values[0] / global_count,
               sqrt(global_values[1] / global_count), global_values[2], sqrt(global_values[3] / global_count),
               sqrt(global_values[4] / global_count),
#ifdef RD_ALE_SENSOR_ALL_WAVES
               "all-waves"
#else
               "shock-only"
#endif
    );
}
#endif

/*! \brief Sets velocities of individual mesh-generating points.
 *
 *  \retur void
 */
void set_vertex_velocities(void)
{
  TIMER_START(CPU_SET_VERTEXVELS);

  int idx, i, j;
  double dt;

#if defined(VORONOI_STATIC_MESH) || defined(NOHYDRO)
  for(idx = 0; idx < TimeBinsHydro.NActiveParticles; idx++)
    {
      i = TimeBinsHydro.ActiveParticleList[idx];
      if(i < 0)
        continue;

      for(j = 0; j < 3; j++)
        SphP[i].VelVertex[j] = 0;
    }
  TIMER_STOP(CPU_SET_VERTEXVELS);
  return;
#endif /* #if defined (VORONOI_STATIC_MESH) || defined (NOHYDRO) */

  for(idx = 0; idx < TimeBinsHydro.NActiveParticles; idx++)
    {
      i = TimeBinsHydro.ActiveParticleList[idx];
      if(i < 0)
        continue;

#ifdef MESHRELAX
      for(j = 0; j < 3; j++)
        SphP[i].VelVertex[j] = 0;
#else /* #ifdef MESHRELAX */
      for(j = 0; j < 3; j++)
        SphP[i].VelVertex[j] = P[i].Vel[j]; /* make cell velocity equal to fluid's velocity */
#endif /* #ifdef MESHRELAX #else */

      double acc[3];

      /*  the actual time-step of particle */
      integertime ti_step = P[i].TimeBinHydro ? (((integertime)1) << P[i].TimeBinHydro) : 0;
      dt                  = ti_step * All.Timebase_interval;
      dt /= All.cf_hubble_a; /* this gives the actual timestep: dt = dloga/ (adot/a) */

      /* now let's add the gradient of the pressure force
       * note that the gravity half-step was already included in P[i].Vel[j]
       * prior to calling this function, thus it does not need to be accounted
       * here explicitly.
       */
      if(SphP[i].Density > 0)
        {
          acc[0] = -SphP[i].Grad.dpress[0] / SphP[i].Density;
          acc[1] = -SphP[i].Grad.dpress[1] / SphP[i].Density;
          acc[2] = -SphP[i].Grad.dpress[2] / SphP[i].Density;

#ifdef MHD
          /* we also add the acceleration due to the Lorentz force */
          acc[0] += (SphP[i].CurlB[1] * SphP[i].B[2] - SphP[i].CurlB[2] * SphP[i].B[1]) / SphP[i].Density;
          acc[1] += (SphP[i].CurlB[2] * SphP[i].B[0] - SphP[i].CurlB[0] * SphP[i].B[2]) / SphP[i].Density;
          acc[2] += (SphP[i].CurlB[0] * SphP[i].B[1] - SphP[i].CurlB[1] * SphP[i].B[0]) / SphP[i].Density;

#endif /* #ifdef MHD */

          SphP[i].VelVertex[0] += 0.5 * dt * acc[0];
          SphP[i].VelVertex[1] += 0.5 * dt * acc[1];
          SphP[i].VelVertex[2] += 0.5 * dt * acc[2];
        }

#ifdef RD_ALE_MESH_VELOCITY_FRACTION
#if !defined(RD_ALE_EQUALSTEP) && !defined(RD_ALE_HIERARCHICAL)
#error "RD_ALE_MESH_VELOCITY_FRACTION is only a test policy for the supported moving ALE paths."
#endif
      /* Scale the complete quasi-Lagrangian predictor
       * sigma_QL = u + 0.5 dt a_pressure, but not the optional regularisation
       * correction added by the second loop below.  Applying f before the
       * pressure predictor left a non-zero mesh speed at f = 0 for dynamic
       * flows.  Here f = 0 and no regularisation switches means sigma = 0
       * exactly; f = 1 is the unchanged quasi-Lagrangian default. */
      for(j = 0; j < 3; j++)
        SphP[i].VelVertex[j] *= (double)(RD_ALE_MESH_VELOCITY_FRACTION);
#endif
    } /* for loop of active particles */

#ifdef RD_ALE_SENSOR_MESH_SMOOTHING
  rd_ale_apply_sensor_mesh_smoothing();
#endif

#ifdef RD_ALE_GEOMETRY_DIAGNOSTICS
  /* Snapshot the quasi-Lagrangian velocity before the optional centroid/face
   * regularisation is added.  The matching call below records only the
   * correction introduced by the second loop. */
  rd_ale_geometry_velocity_begin();
#endif

  for(idx = 0; idx < TimeBinsHydro.NActiveParticles; idx++)
    {
      i = TimeBinsHydro.ActiveParticleList[idx];
      if(i < 0)
        continue;

#ifdef REGULARIZE_MESH_CM_DRIFT

      double dx, dy, dz, d, fraction;

      dx = nearest_x(P[i].Pos[0] - SphP[i].Center[0]);
      dy = nearest_y(P[i].Pos[1] - SphP[i].Center[1]);
      dz = nearest_z(P[i].Pos[2] - SphP[i].Center[2]);

      /*  the actual time-step of particle */
      dt = (P[i].TimeBinHydro ? (((integertime)1) << P[i].TimeBinHydro) : 0) * All.Timebase_interval;
      dt /= All.cf_hubble_a; /* this is dt, the actual timestep  */

      double cellrad = get_cell_radius(i);

#if !defined(REGULARIZE_MESH_FACE_ANGLE)
      /* if there is a density gradient, use a center that is displaced slightly in the direction of the gradient.
       * This makes sure that the Lloyd scheme does not simply iterate towards cells of equal volume, instead
       * we keep cells of roughly equal mass.
       */
      double dgrad = sqrt(SphP[i].Grad.drho[0] * SphP[i].Grad.drho[0] + SphP[i].Grad.drho[1] * SphP[i].Grad.drho[1] +
                          SphP[i].Grad.drho[2] * SphP[i].Grad.drho[2]);

      if(dgrad > 0)
        {
          double scale = SphP[i].Density / dgrad;
          double tmp   = 3 * cellrad + scale;
          double x     = (tmp - sqrt(tmp * tmp - 8 * cellrad * cellrad)) / 4;

          if(x < 0.25 * cellrad)
            {
              dx = nearest_x(P[i].Pos[0] - (SphP[i].Center[0] + x * SphP[i].Grad.drho[0] / dgrad));
              dy = nearest_y(P[i].Pos[1] - (SphP[i].Center[1] + x * SphP[i].Grad.drho[1] / dgrad));
              dz = nearest_z(P[i].Pos[2] - (SphP[i].Center[2] + x * SphP[i].Grad.drho[2] / dgrad));
            }
        }
#endif /* #if !defined(REGULARIZE_MESH_FACE_ANGLE) */

      d = sqrt(dx * dx + dy * dy + dz * dz);

      fraction = 0;

#if !defined(REGULARIZE_MESH_FACE_ANGLE)
      if(d > 0.75 * All.CellShapingFactor * cellrad && dt > 0)
        {
          if(d > All.CellShapingFactor * cellrad)
            fraction = All.CellShapingSpeed;
          else
            fraction = All.CellShapingSpeed * (d - 0.75 * All.CellShapingFactor * cellrad) / (0.25 * All.CellShapingFactor * cellrad);
        }
#else /* #if !defined(REGULARIZE_MESH_FACE_ANGLE) */
      if(SphP[i].MaxFaceAngle > 0.75 * All.CellMaxAngleFactor && dt > 0)
        {
          if(SphP[i].MaxFaceAngle > All.CellMaxAngleFactor)
            fraction = All.CellShapingSpeed;
          else
            fraction = All.CellShapingSpeed * (SphP[i].MaxFaceAngle - 0.75 * All.CellMaxAngleFactor) / (0.25 * All.CellMaxAngleFactor);
        }
#endif /* #if !defined(REGULARIZE_MESH_FACE_ANGLE) #else */

      if(d > 0 && fraction > 0)
        {
          double v;
#ifdef REGULARIZE_MESH_CM_DRIFT_USE_SOUNDSPEED

          v = All.cf_atime * get_sound_speed(i);

#if defined(SELFGRAVITY) || defined(EXTERNALGRAVITY) || defined(EXACT_GRAVITY_FOR_PARTICLE_TYPE)
          /* calculate gravitational velocity scale */
          double ax, ay, az, ac, vgrav;
#ifdef HIERARCHICAL_GRAVITY
          ax = SphP[i].FullGravAccel[0];
          ay = SphP[i].FullGravAccel[1];
          az = SphP[i].FullGravAccel[2];
#else /* #ifdef HIERARCHICAL_GRAVITY */
          ax = P[i].GravAccel[0];
          ay = P[i].GravAccel[1];
          az = P[i].GravAccel[2];
#endif /* #ifdef HIERARCHICAL_GRAVITY #else */
#ifdef PMGRID
          ax += P[i].GravPM[0];
          ay += P[i].GravPM[1];
          az += P[i].GravPM[2];
#endif /* #ifdef PMGRID */
          ac    = sqrt(ax * ax + ay * ay + az * az);
          vgrav = 4 * sqrt(All.cf_atime * cellrad * ac);
          if(v < vgrav)
            v = vgrav;
#endif /* #if defined(SELFGRAVITY) || defined(EXTERNALGRAVITY) || defined(EXACT_GRAVITY_FOR_PARTICLE_TYPE) */

          double vcurl = cellrad * SphP[i].CurlVel;
          if(v < vcurl)
            v = vcurl;

#else /* #ifdef REGULARIZE_MESH_CM_DRIFT_USE_SOUNDSPEED */
          v = All.cf_atime * All.cf_atime * d / dt; /* use fiducial velocity */

          double vel  = sqrt(P[i].Vel[0] * P[i].Vel[0] + P[i].Vel[1] * P[i].Vel[1] + P[i].Vel[2] * P[i].Vel[2]);
          double vmax = dmax(All.cf_atime * get_sound_speed(i), vel);
          if(v > vmax)
            v = vmax;
#endif /* #ifdef REGULARIZE_MESH_CM_DRIFT_USE_SOUNDSPEED #else */

#ifdef REFINEMENT_SPLIT_CELLS
          double proj = SphP[i].SepVector[0] * dx + SphP[i].SepVector[1] * dy + SphP[i].SepVector[2] * dz;

          if(proj != 0)
            {
              dx = proj * SphP[i].SepVector[0];
              dy = proj * SphP[i].SepVector[1];
              dz = proj * SphP[i].SepVector[2];
            }

          SphP[i].SepVector[0] = 0;
          SphP[i].SepVector[1] = 0;
          SphP[i].SepVector[2] = 0;
#endif /* #ifdef REFINEMENT_SPLIT_CELLS */

          SphP[i].VelVertex[0] += fraction * v * (-dx / d);
          SphP[i].VelVertex[1] += fraction * v * (-dy / d);
          SphP[i].VelVertex[2] += fraction * v * (-dz / d);
        }
#endif /* #ifdef REGULARIZE_MESH_CM_DRIFT */

      for(j = NUMDIMS; j < 3; j++)
        {
          SphP[i].VelVertex[j] = 0; /* vertex velocities for unused dimensions set to zero */
        }
    } /* for loop of active particles */

#ifdef RD_ALE_TEST_ZERO_MESH_VELOCITY
#ifndef RD_ALE_EQUALSTEP
#error "RD_ALE_TEST_ZERO_MESH_VELOCITY is only a test policy for RD_ALE_EQUALSTEP."
#endif
  for(idx = 0; idx < TimeBinsHydro.NActiveParticles; idx++)
    {
      i = TimeBinsHydro.ActiveParticleList[idx];
      if(i < 0)
        continue;
      for(j = 0; j < 3; j++)
        SphP[i].VelVertex[j] = 0.0;
    }
#endif

#ifdef RD_ALE_GEOMETRY_DIAGNOSTICS
  rd_ale_geometry_velocity_end();
#endif

#ifdef OUTPUT_VERTEX_VELOCITY_DIVERGENCE
  voronoi_exchange_primitive_variables();
  calculate_vertex_velocity_divergence();
#endif /* #ifdef OUTPUT_VERTEX_VELOCITY_DIVERGENCE */

#if defined(REFLECTIVE_X) || defined(REFLECTIVE_Y) || defined(REFLECTIVE_Z)
  validate_vertex_velocities();
#endif /* #if defined(REFLECTIVE_X) || defined(REFLECTIVE_Y) || defined(REFLECTIVE_Z) */

#ifdef ONEDIMS_SPHERICAL
  validate_vertex_velocities_1d();
#endif /* #ifdef ONEDIMS_SPHERICAL */

  TIMER_STOP(CPU_SET_VERTEXVELS);
}

#ifdef ONEDIMS_SPHERICAL
/*! \brief Handles inner boundary cells in 1d spherical case.
 *
 *  \return void
 */
static void validate_vertex_velocities_1d()
{
  double dt = (P[0].TimeBinHydro ? (((integertime)1) << P[0].TimeBinHydro) : 0) * All.Timebase_interval;
  if(P[0].Pos[0] + dt * SphP[0].VelVertex[0] < All.CoreRadius)
    SphP[0].VelVertex[0] = 0.;
}
#endif /* #ifdef ONEDIMS_SPHERICAL */

#if defined(REFLECTIVE_X) || defined(REFLECTIVE_Y) || defined(REFLECTIVE_Z)
/*! \brief Checks validity of vertex velocities with boundary conditions.
 *
 *  In case we have reflecting boundaries, make sure that cell does not drift
 *  beyond boundary.
 *
 *  \return void
 */
void validate_vertex_velocities(void)
{
  int idx, i;

  for(idx = 0; idx < TimeBinsHydro.NActiveParticles; idx++)
    {
      i = TimeBinsHydro.ActiveParticleList[idx];
      if(i < 0)
        continue;

      integertime ti_step = P[i].TimeBinHydro ? (((integertime)1) << P[i].TimeBinHydro) : 0;
      double dt_drift;

      if(All.ComovingIntegrationOn)
        dt_drift = get_drift_factor(All.Ti_Current, All.Ti_Current + ti_step);
      else
        dt_drift = ti_step * All.Timebase_interval;

#if defined(REFLECTIVE_X)
      if((P[i].Pos[0] + dt_drift * SphP[i].VelVertex[0]) < 0 || (P[i].Pos[0] + dt_drift * SphP[i].VelVertex[0]) >= boxSize_X)
        SphP[i].VelVertex[0] = 0;
#endif /* #if defined(REFLECTIVE_X) */
#if defined(REFLECTIVE_Y)
      if((P[i].Pos[1] + dt_drift * SphP[i].VelVertex[1]) < 0 || (P[i].Pos[1] + dt_drift * SphP[i].VelVertex[1]) >= boxSize_Y)
        SphP[i].VelVertex[1] = 0;
#endif /* #if defined(REFLECTIVE_Y) */
#if defined(REFLECTIVE_Z)
      if((P[i].Pos[2] + dt_drift * SphP[i].VelVertex[2]) < 0 || (P[i].Pos[2] + dt_drift * SphP[i].VelVertex[2]) >= boxSize_Z)
        SphP[i].VelVertex[2] = 0;
#endif /* #if defined(REFLECTIVE_Z) */
    }
}
#endif /* #if defined(REFLECTIVE_X) || defined(REFLECTIVE_Y) || defined(REFLECTIVE_Z) */
