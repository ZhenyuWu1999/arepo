/* Distributed static RD spectral bound. Mesh ownership is supplied by the
 * adapter, so CFL, dual volumes and residuals use the same physical simplices. */
#include <float.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include "../main/allvars.h"
#include "../main/proto.h"
#include "../mesh/mesh.h"
#include "../mesh/voronoi/voronoi.h"
#include "rd_timestep.h"

#ifdef RD_3D_STATIC
struct rd_cfl_deposit
{
  int task, index;
  double volume, alpha;
};

static int rd_cfl_compare(const void *a, const void *b)
{
  const struct rd_cfl_deposit *x = a, *y = b;
  return (x->task > y->task) - (x->task < y->task);
}

void rd_static_tetra_cfl(tessellation *T, int n, const int *element,
                         const struct triangle_normals *geometry)
{
  double *mass = mymalloc("RD_CFLMass", NumGas * sizeof(*mass));
  double *alpha_sum = mymalloc("RD_CFLAlpha", NumGas * sizeof(*alpha_sum));
  memset(mass, 0, NumGas * sizeof(*mass));
  memset(alpha_sum, 0, NumGas * sizeof(*alpha_sum));
  struct rd_cfl_deposit *out = mymalloc("RD_CFLExport", (4 * n + 1) * sizeof(*out));
  int nexport = 0;
  for(int slot = 0; slot < n; slot++)
    {
      double weight = 0.0, velocity[3] = {0}, enthalpy = 0.0;
      for(int vertex = 0; vertex < 4; vertex++)
        {
          const point *dp = &T->DP[T->DT[element[slot]].p[vertex]];
          double rho, pressure, vel[3];
          if(dp->task == ThisTask)
            {
              int j = dp->index >= NumGas ? dp->index - NumGas : dp->index;
              if(j < 0 || j >= NumGas)
                terminate_program("RD tetra CFL invalid local point");
              rho = SphP[j].Density;
              pressure = SphP[j].Pressure;
              for(int axis = 0; axis < 3; axis++)
                vel[axis] = P[j].Vel[axis];
            }
          else
            {
              rho = PrimExch[dp->index].Density;
              pressure = PrimExch[dp->index].Pressure;
              for(int axis = 0; axis < 3; axis++)
                vel[axis] = PrimExch[dp->index].VelGas[axis];
            }
          if(!(rho > 0.0) || !(pressure > 0.0) || !isfinite(rho) || !isfinite(pressure))
            terminate_program("RD tetra CFL invalid primitive state");
          double root = sqrt(rho), speed2 = 0.0;
          for(int axis = 0; axis < 3; axis++)
            {
              velocity[axis] += root * vel[axis];
              speed2 += vel[axis] * vel[axis];
            }
          enthalpy += root * (GAMMA / GAMMA_MINUS1 * pressure / rho + 0.5 * speed2);
          weight += root;
        }
      double speed2 = 0.0;
      for(int axis = 0; axis < 3; axis++)
        {
          velocity[axis] /= weight;
          speed2 += velocity[axis] * velocity[axis];
        }
      const double cs = sqrt(GAMMA_MINUS1 * (enthalpy / weight - 0.5 * speed2));
      if(!(cs > 0.0) || !isfinite(cs))
        terminate_program("RD tetra CFL invalid Roe sound speed");
      double alpha = 0.0;
      for(int vertex = 0; vertex < 4; vertex++)
        {
          double vn = 0.0;
          for(int axis = 0; axis < 3; axis++)
            vn += velocity[axis] * geometry[slot].normal[vertex][axis];
          alpha = dmax(alpha, geometry[slot].mag[vertex] / 3.0 * (cs + fabs(vn)));
        }
      for(int vertex = 0; vertex < 4; vertex++)
        {
          const point *dp = &T->DP[T->DT[element[slot]].p[vertex]];
          if(dp->task == ThisTask)
            {
              int j = dp->index >= NumGas ? dp->index - NumGas : dp->index;
              mass[j] += geometry[slot].area / 4.0;
              alpha_sum[j] += alpha;
            }
          else
            out[nexport++] = (struct rd_cfl_deposit){dp->task, dp->originalindex, geometry[slot].area / 4.0, alpha};
        }
    }

  mysort(out, nexport, sizeof(*out), rd_cfl_compare);
  int *sc = mymalloc("RD_CFLSendCount", NTask * sizeof(*sc));
  int *rc = mymalloc("RD_CFLRecvCount", NTask * sizeof(*rc));
  int *so = mymalloc("RD_CFLSendOffset", NTask * sizeof(*so));
  int *ro = mymalloc("RD_CFLRecvOffset", NTask * sizeof(*ro));
  memset(sc, 0, NTask * sizeof(*sc));
  for(int k = 0; k < nexport; k++)
    sc[out[k].task]++;
  MPI_Alltoall(sc, 1, MPI_INT, rc, 1, MPI_INT, MPI_COMM_WORLD);
  int nimport = 0, offset = 0;
  for(int task = 0; task < NTask; task++)
    {
      so[task] = offset;
      ro[task] = nimport;
      offset += sc[task];
      nimport += rc[task];
    }
  struct rd_cfl_deposit *in = mymalloc("RD_CFLImport", (nimport + 1) * sizeof(*in));
  for(int group = 1; group < (1 << PTask); group++)
    {
      int task = ThisTask ^ group;
      if(task < NTask && (sc[task] || rc[task]))
        MPI_Sendrecv(out + so[task], sc[task] * sizeof(*out), MPI_BYTE, task, TAG_DENS_A,
                     in + ro[task], rc[task] * sizeof(*in), MPI_BYTE, task, TAG_DENS_A,
                     MPI_COMM_WORLD, MPI_STATUS_IGNORE);
    }
  for(int k = 0; k < nimport; k++)
    {
      int j = in[k].index;
      if(j < 0 || j >= NumGas)
        terminate_program("RD tetra CFL invalid remote deposit");
      mass[j] += in[k].volume;
      alpha_sum[j] += in[k].alpha;
    }
  myfree(in);
  myfree(ro); myfree(so); myfree(rc); myfree(sc);
  myfree(out);

  struct { double value; int task; } local = {DBL_MAX, ThisTask}, global;
  MyIDType limiting_id = 0;
  for(int j = 0; j < NumGas; j++)
    {
      if(!(mass[j] > 0.0) || !(alpha_sum[j] > 0.0) || !isfinite(alpha_sum[j]))
        terminate_program("RD tetra CFL invalid assembled coefficient");
      double candidate = mass[j] / alpha_sum[j];
      SphP[j].CurrentMaxTiStep = dmin(SphP[j].CurrentMaxTiStep, candidate);
      if(candidate < local.value)
        {
          local.value = candidate;
          limiting_id = P[j].ID;
        }
    }
  MPI_Allreduce(&local, &global, 1, MPI_DOUBLE_INT, MPI_MINLOC, MPI_COMM_WORLD);
  MPI_Bcast(&limiting_id, sizeof(limiting_id), MPI_BYTE, global.task, MPI_COMM_WORLD);
  mpi_printf("RD-CFL-SELECT time=%.8g current_mesh_raw=%.8g courant_limit=%.8g limiting_id=%llu\n",
             All.Time, global.value, All.CourantFac * global.value, (unsigned long long)limiting_id);
  myfree(alpha_sum); myfree(mass);
}
#endif
