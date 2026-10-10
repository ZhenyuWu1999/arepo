/* AREPO nodal state storage and RK stage transitions. Numerical element
 * kernels live in rd_euler.c; no mesh connectivity is managed here. */
#include <float.h>
#include <math.h>
#include <stdio.h>

#include "../main/allvars.h"
#include "../main/proto.h"
#include "rd_state.h"

#if defined(RESIDUAL_DISTRIBUTION) && defined(RD_RK2_TOTAL_RESIDUAL) && !defined(RD_HIERARCHICAL_TIMESTEPS)
/*! \brief Snapshot the intensive nodal state U^n before the predictor sweep. */
void rd_rk2_save_stage0(void)
{
  for(int i = 0; i < NumGas; i++)
    {
      double inv_area = 1.0 / SphP[i].DualArea;

      SphP[i].RD_Ustage0[0] = P[i].Mass * inv_area;
      SphP[i].RD_Ustage0[1] = SphP[i].Momentum[0] * inv_area;
      SphP[i].RD_Ustage0[2] = SphP[i].Momentum[1] * inv_area;
#ifndef TWODIMS
      SphP[i].RD_Ustage0[3] = SphP[i].Momentum[2] * inv_area;
#endif
      SphP[i].RD_Ustage0[RD_ENERGY] = SphP[i].Energy * inv_area;

      for(int k = 0; k < RD_NVAR; k++)
        SphP[i].RD_dU[k] = 0.0;
    }
}

/*! \brief Between the stages: form dU, recover the stage primitives, and,
 *         unless an explicit old-element residual is required, apply the
 *         corrector's local +1/2 (Q* - Q^n) contribution.
 *
 *  This deliberately does NOT call update_primitive_variables(): that routine
 *  stamps OldMass and TimeLastPrimUpdate and, when the MinEgySpec floor
 *  fires, rewrites the conserved energy and the global EgyInjection
 *  accumulator, so the corrector would no longer see the predictor the RD
 *  equations define (Codex audit 11.3). The recovery here is side-effect free
 *  apart from writing the primitive fields themselves; a non-finite or
 *  non-positive predictor state terminates diagnostically instead of being
 *  floored.
 *
 *  The corrector update is
 *      U^{n+1}_i = U*_i + 1/2 (U*_i - U^n_i)
 *                  - (dt/|S_i|) sum_T [ sum_j m_ij dU_j/dt + 1/2 phi_i^T(U*) ]
 *  (analysis document section 4); the +1/2 dU term is purely local and is
 *  added here, before the corrector sweep contributes the element sums. B
 *  instead needs the saved old N and LDA pieces so one total-residual theta can
 *  blend both stages; the assembled shortcut has discarded that information.
 */
void rd_rk2_prepare_corrector(double *min_rho, double *min_press)
{
  for(int i = 0; i < NumGas; i++)
    {
      double inv_area = 1.0 / SphP[i].DualArea;

      double u0 = P[i].Mass * inv_area;
      double u1 = SphP[i].Momentum[0] * inv_area;
      double u2 = SphP[i].Momentum[1] * inv_area;
      double energy = SphP[i].Energy * inv_area;

      SphP[i].RD_dU[0] = u0 - SphP[i].RD_Ustage0[0];
      SphP[i].RD_dU[1] = u1 - SphP[i].RD_Ustage0[1];
      SphP[i].RD_dU[2] = u2 - SphP[i].RD_Ustage0[2];
      SphP[i].RD_dU[RD_ENERGY] = energy - SphP[i].RD_Ustage0[RD_ENERGY];
#ifndef TWODIMS
      double u3 = SphP[i].Momentum[2] * inv_area;
      double velz = u3 / u0;
      SphP[i].RD_dU[3] = u3 - SphP[i].RD_Ustage0[3];
#endif

      double rho   = u0;
      double velx  = u1 / u0;
      double vely  = u2 / u0;
      double kinetic = velx * velx + vely * vely;
#ifndef TWODIMS
      kinetic += velz * velz;
#endif
      double egy   = energy / u0 - 0.5 * kinetic;
      double press = GAMMA_MINUS1 * rho * egy;

      if(!isfinite(rho) || !isfinite(press) || rho <= 0 || press <= 0)
        {
          printf("RD predictor state invalid: task=%d i=%d ID=%llu rho=%g press=%g pos=%g|%g\n", ThisTask, i,
                 (unsigned long long)P[i].ID, rho, press, P[i].Pos[0], P[i].Pos[1]);
          terminate_program("RD predictor produced a non-physical state");
        }

      *min_rho = dmin(*min_rho, rho);
      *min_press = dmin(*min_press, press);

#ifdef RD_DIAG_DUMP_STAGE
      /* diagnostic only: per-rank dump of the recovered stage state */
      {
        static int rd_dump_step = 0;
        static FILE *rd_dump_fp = NULL;
        if(i == 0)
          rd_dump_step++;
        if(rd_dump_step == 1)
          {
            if(rd_dump_fp == NULL)
              {
                char nm[256];
                sprintf(nm, "%s/rdstage_task%03d.txt", All.OutputDir, ThisTask);
                rd_dump_fp = fopen(nm, "w");
              }
            if(rd_dump_fp)
              fprintf(rd_dump_fp, "%llu %.17g %.17g %.17g %.17g %.17g %.17g\n", (unsigned long long)P[i].ID, rho, velx, vely,
                      press, SphP[i].DualArea, P[i].Mass);
          }
      }
#endif
      SphP[i].Density  = rho;
      P[i].Vel[0]      = velx;
      P[i].Vel[1]      = vely;
#ifndef TWODIMS
      P[i].Vel[2] = velz;
#endif
      SphP[i].Utherm   = egy;
      SphP[i].Pressure = press;
#ifdef TREE_BASED_TIMESTEPS
      SphP[i].Csnd = sqrt(GAMMA * press / rho);
#endif

#if !defined(RD_DIAG_NO_KICK) && !defined(B_SCHEME)
      /* the local +1/2 (Q* - Q^n) part of the corrector */
      P[i].Mass += 0.5 * SphP[i].DualArea * SphP[i].RD_dU[0];
      SphP[i].Momentum[0] += 0.5 * SphP[i].DualArea * SphP[i].RD_dU[1];
      SphP[i].Momentum[1] += 0.5 * SphP[i].DualArea * SphP[i].RD_dU[2];
#ifndef TWODIMS
      SphP[i].Momentum[2] += 0.5 * SphP[i].DualArea * SphP[i].RD_dU[3];
#endif
      SphP[i].Energy += 0.5 * SphP[i].DualArea * SphP[i].RD_dU[RD_ENERGY];
#endif
    }
}
#endif

#ifdef RD_3D_STATIC
void rd_static_validate_stage(int rd_stage, int elements)
{
  double total[5] = {0}, min_rho = DBL_MAX, min_pressure = DBL_MAX;
  for(int node = 0; node < NumGas; node++)
    {
      double q[5] = {P[node].Mass, SphP[node].Momentum[0], SphP[node].Momentum[1],
                     SphP[node].Momentum[2], SphP[node].Energy};
      double mom2 = q[1] * q[1] + q[2] * q[2] + q[3] * q[3];
      double rho = q[0] / SphP[node].DualArea;
      double pressure = GAMMA_MINUS1 * (q[4] - 0.5 * mom2 / q[0]) / SphP[node].DualArea;
      if(!(rho > 0.0) || !(pressure > 0.0) || !isfinite(rho) || !isfinite(pressure))
        terminate_program("RD tetra stage inadmissible: stage=%d ID=%llu rho=%.17g p=%.17g",
                          rd_stage, (unsigned long long)P[node].ID, rho, pressure);
      for(int component = 0; component < 5; component++)
        total[component] += q[component];
      min_rho = dmin(min_rho, rho);
      min_pressure = dmin(min_pressure, pressure);
    }
  double global_total[5], local_min[2] = {min_rho, min_pressure}, global_min[2];
  int global_elements;
  MPI_Allreduce(total, global_total, 5, MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);
  MPI_Allreduce(local_min, global_min, 2, MPI_DOUBLE, MPI_MIN, MPI_COMM_WORLD);
  MPI_Allreduce(&elements, &global_elements, 1, MPI_INT, MPI_SUM, MPI_COMM_WORLD);
  mpi_printf("RD-3D-STAGE time=%.17g stage=%d tetra=%d rho_min=%.17g p_min=%.17g "
             "Q=[%.17g,%.17g,%.17g,%.17g,%.17g]\n", All.Time, rd_stage, global_elements,
             global_min[0], global_min[1], global_total[0], global_total[1], global_total[2], global_total[3], global_total[4]);
}
#endif
