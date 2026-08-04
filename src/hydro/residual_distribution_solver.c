
#include <float.h>
#include <lapacke.h>
#include <math.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../main/allvars.h"
#include "../main/cpp_functions.h"
#include "../main/proto.h"
#include "../mesh/mesh.h"
#include "../mesh/voronoi/voronoi.h"
/* The LU diagonal-pivot spread is only a cheap trigger for switching to the
 * more reliable SVD solver.  It is not a numerical-rank decision. */
#define RD_LU_FALLBACK_PIVOT_RATIO 1e-12

/* DGELSD makes the authoritative numerical-rank decision.  Its machine-
 * precision default preserves every resolvable direction and therefore the
 * consistent equation S^- x = rhs.  A sensitivity scan found that forcing
 * rcond=1e-12 truncated resolvable fourth singular values and enlarged the raw
 * conservation defect; see the 2026-07-29 development-log entry. */
#ifndef RD_SVD_RCOND
#define RD_SVD_RCOND -1.0
#endif

/* Safety factor for assertion A2's forward round-off bound.  The scale passed
 * to the assertion is built from absolute pre-cancellation matrix-vector
 * products, not from the possibly vanishing element residual. */
#define RD_CONSERVATION_ROUNDOFF_FACTOR 4096.0

static lapack_int mat_inv(double *A, unsigned n);
static lapack_int solve_system(int n, double *A, double *b);

// static struct flux_list_data
//{
//  int task, index;
//  double dM, dP[3];
// #ifdef MHD
//  double dB[3];
// #endif /* #ifdef MHD */
//
// #ifndef ISOTHERM_EQS
//  double dEnergy;
// #endif /* #ifndef ISOTHERM_EQS */
// #ifdef MAXSCALARS
//  double dConservedScalars[MAXSCALARS];
// #endif /* #ifdef MAXSCALARS */
//} * FluxList;

#ifdef RESIDUAL_DISTRIBUTION

#if !defined(TWODIMS)
#error "The current residual-distribution solver is implemented only for TWODIMS."
#endif

#if !defined(VORONOI_STATIC_MESH)
#error "The current residual-distribution baseline requires VORONOI_STATIC_MESH."
#endif

#if !defined(FORCE_EQUAL_TIMESTEPS) && !defined(RD_HIERARCHICAL_TIMESTEPS)
#error "The current residual-distribution baseline requires FORCE_EQUAL_TIMESTEPS."
#endif

#ifdef RD_HIERARCHICAL_TIMESTEPS
#if !defined(RD_RK2_TOTAL_RESIDUAL) || (!defined(N_SCHEME) && !defined(LDA_SCHEME))
#error "RD_HIERARCHICAL_TIMESTEPS currently requires RD_RK2_TOTAL_RESIDUAL with N_SCHEME or LDA_SCHEME."
#endif
#if defined(RD_RK2_COHERENT_BETA_N) || defined(RD_RK2_COHERENT_BETA_STAR)
#error "The first hierarchical LDA+F1 experiment supports only the existing mixed stage-beta convention."
#endif
#ifdef LDA_SCHEME
#define RD_RK2_STAGE_BETA_LABEL "two-call-LDA-F1-frozen"
#else
#define RD_RK2_STAGE_BETA_LABEL "two-call-N-lumped"
#endif
#endif

#if defined(RD_HIERARCHICAL_TEST_PATTERN) && !defined(RD_HIERARCHICAL_TIMESTEPS)
#error "RD_HIERARCHICAL_TEST_PATTERN is only valid for the experimental RD hierarchy."
#endif

#if defined(RD_RK2_TOTAL_RESIDUAL) && !defined(RD_HIERARCHICAL_TIMESTEPS)
#define RD_RK2_INTERNAL_LOOP
#endif

#if(defined(LDA_SCHEME) + defined(N_SCHEME) + defined(B_SCHEME)) != 1
#error "Select exactly one residual-distribution scheme: LDA_SCHEME, N_SCHEME, or B_SCHEME."
#endif

#if defined(RD_RK2_TOTAL_RESIDUAL) && defined(B_SCHEME) && defined(RD_HIERARCHICAL_TIMESTEPS)
#error "RD_RK2_TOTAL_RESIDUAL with B_SCHEME is an equal-bin experiment; the hierarchy has only been derived for the N and LDA temporal terms."
#endif

#if defined(RD_RK2_COHERENT_BETA_N) && defined(RD_RK2_COHERENT_BETA_STAR)
#error "Select at most one coherent stage-beta experiment."
#endif

#if defined(RD_RK2_RATE_CONSISTENT_HEUN) && \
    (!defined(RD_RK2_TOTAL_RESIDUAL) || !defined(LDA_SCHEME) || defined(RD_HIERARCHICAL_TIMESTEPS))
#error "RD_RK2_RATE_CONSISTENT_HEUN is an equal-bin LDA+F1 experiment and requires RD_RK2_TOTAL_RESIDUAL."
#endif

#if defined(RD_RK2_RATE_CONSISTENT_HEUN) && \
    (defined(RD_RK2_COHERENT_BETA_N) || defined(RD_RK2_COHERENT_BETA_STAR))
#error "The rate-consistent Heun experiment is distinct from the stage-beta experiments."
#endif

#if(defined(RD_RK2_COHERENT_BETA_N) || defined(RD_RK2_COHERENT_BETA_STAR)) && \
    (!defined(RD_RK2_TOTAL_RESIDUAL) || !defined(LDA_SCHEME))
#error "The coherent stage-beta experiments require LDA_SCHEME and RD_RK2_TOTAL_RESIDUAL."
#endif

#if defined(RD_RK2_RATE_CONSISTENT_HEUN)
#define RD_RK2_STAGE_BETA_LABEL "rate-consistent-LDA-F1-Heun"
#define RD_UPWIND_NRHS 3
#elif defined(RD_HIERARCHICAL_TIMESTEPS)
#define RD_UPWIND_NRHS 3
#elif defined(RD_RK2_COHERENT_BETA_N)
#define RD_RK2_STAGE_BETA_LABEL "coherent-beta-n"
#define RD_UPWIND_NRHS 7 /* Phi, N inflow, F1 target, and four identity columns for beta^n */
#elif defined(RD_RK2_COHERENT_BETA_STAR)
#define RD_RK2_STAGE_BETA_LABEL "coherent-beta-star"
#define RD_UPWIND_NRHS 4 /* Phi(U*), N inflow, F1 target, and saved Phi(U^n) */
#elif defined(B_SCHEME)
#define RD_RK2_STAGE_BETA_LABEL "coherent-total-B"
#define RD_UPWIND_NRHS 3
#else
#define RD_RK2_STAGE_BETA_LABEL "mixed"
#define RD_UPWIND_NRHS 3
#endif

static struct FluxRD_list_data
{
  int task, index;
  double dMass_Dual;
  double dMomentum_Dual[3];
  double dEnergy_Dual;
#ifdef RD_HIERARCHICAL_TIMESTEPS
  double dPredictor[4]; /* full-weight integrated predictor; zero in the corrector call */
#endif

} *FluxRD_list;

static struct DualArea_list_data
{
  int task, index;
  double DualArea;
} *DualArea_list;

static int N_DualArea_export, Max_N_FluxRD_export, N_FluxRD_export;
struct triangle_normals *tri_normals_list;
extern struct primexch *PrimExch;
extern struct grad_data *GradExch;

static int rd_triangle_is_physical(tessellation *T, int triangle_index)
{
  if(triangle_index < 0 || triangle_index >= T->Ndt)
    return 0;

  for(int vertex = 0; vertex < DIMS + 1; vertex++)
    {
      int point_index = T->DT[triangle_index].p[vertex];

      if(point_index < 0 || point_index >= T->Ndp)
        return 0;

      if(T->DP[point_index].task < 0 || T->DP[point_index].task >= NTask || T->DP[point_index].index < 0)
        return 0;
    }

  return 1;
}

static int rd_simplex_claimed(tessellation *T, int i, int use_min_bin_owner);

#ifdef RD_HIERARCHICAL_TIMESTEPS
/*! \brief Map a local primary/periodic Delaunay point to its primary gas index. */
static int rd_local_point_index(const point *dp)
{
  int index = dp->index;

  if(index >= NumGas)
    index -= NumGas;

  if(index < 0 || index >= NumGas)
    terminate_program("RD hierarchy found an invalid local Delaunay-point index");

  return index;
}

/*! \brief Read live vertex scheduling data, never the construction-time DP.timebin. */
static int rd_point_timebin(const point *dp)
{
  if(dp->task == ThisTask)
    return P[rd_local_point_index(dp)].TimeBinHydro;

  return PrimExch[dp->index].TimeBinHydro;
}

static int rd_point_star_timebin(const point *dp)
{
  if(dp->task == ThisTask)
    return SphP[rd_local_point_index(dp)].RD_StarTimeBin;

  return PrimExch[dp->index].RD_StarTimeBin;
}

static integertime rd_point_predictor_end(const point *dp)
{
  if(dp->task == ThisTask)
    return SphP[rd_local_point_index(dp)].RD_PredictorEnd;

  return PrimExch[dp->index].RD_PredictorEnd;
}

static int rd_point_stage_live(const point *dp) { return rd_point_star_timebin(dp) == rd_point_timebin(dp); }

/*! \brief Whether this build can reconstruct a genuinely partial static mesh.
 *
 * Without CREATE_FULL_MESH, a static-mesh domain decomposition rebuilds the
 * tessellation around the current active set.  A persistent static mesh built
 * at the all-active initial time remains complete even without that flag and
 * can retain activity-independent ownership.
 */
static int rd_use_min_bin_owner(void)
{
#if !defined(CREATE_FULL_MESH) && defined(VORONOI_STATIC_MESH_DO_DOMAIN_DECOMPOSITION)
  return 1;
#else
  return 0;
#endif
}

struct rd_starbin_export
{
  int task;
  int index;
  int bin;
};

static int rd_starbin_export_compare(const void *a, const void *b)
{
  const struct rd_starbin_export *ea = a;
  const struct rd_starbin_export *eb = b;

  if(ea->task < eb->task)
    return -1;
  if(ea->task > eb->task)
    return 1;
  return 0;
}

/*! \brief Construct the complete vertex-star timestep minimum on each primary.
 *
 * CREATE_FULL_MESH makes every cell participate in mesh construction, but a
 * task's local tessellation also contains ghost-boundary simplices which need
 * not be members of the globally selected triangulation.  The star therefore
 * uses exactly the same minimum-ID, globally unique owned simplex set as the
 * residual ledger. Each owner sends remote-vertex candidates back to their
 * primary owners, where a minimum is taken. The completed owner value is then
 * exchanged through PrimExch for the residual sweep.
 */
static void rd_prepare_vertex_star_context(tessellation *T)
{
  point *DP = T->DP;
  tetra *DT = T->DT;
  int nexport = 0;

  for(int i = 0; i < NumGas; i++)
    SphP[i].RD_StarTimeBin = P[i].TimeBinHydro;

  for(int triangle = 0; triangle < T->Ndt; triangle++)
    if(rd_triangle_is_physical(T, triangle) && rd_simplex_claimed(T, triangle, rd_use_min_bin_owner()))
      for(int vertex = 0; vertex < DIMS + 1; vertex++)
        if(DP[DT[triangle].p[vertex]].task != ThisTask)
          nexport++;

  struct rd_starbin_export *exports =
      (struct rd_starbin_export *)mymalloc("RDStarBinExport", nexport * sizeof(struct rd_starbin_export));
  int nexport_filled = 0;

  for(int triangle = 0; triangle < T->Ndt; triangle++)
    {
      if(!rd_triangle_is_physical(T, triangle) || !rd_simplex_claimed(T, triangle, rd_use_min_bin_owner()))
        continue;

      int triangle_bin = rd_point_timebin(&DP[DT[triangle].p[0]]);
      for(int vertex = 1; vertex < DIMS + 1; vertex++)
        triangle_bin = imin(triangle_bin, rd_point_timebin(&DP[DT[triangle].p[vertex]]));

      for(int vertex = 0; vertex < DIMS + 1; vertex++)
        {
          point *dp = &DP[DT[triangle].p[vertex]];
          if(dp->task == ThisTask)
            {
              int index = rd_local_point_index(dp);
              SphP[index].RD_StarTimeBin = imin(SphP[index].RD_StarTimeBin, triangle_bin);
            }
          else
            {
              exports[nexport_filled].task  = dp->task;
              exports[nexport_filled].index = dp->originalindex;
              exports[nexport_filled].bin   = triangle_bin;
              nexport_filled++;
            }
        }
    }

  if(nexport_filled != nexport)
    terminate_program("RD hierarchy star-bin export count mismatch");

  mysort(exports, nexport, sizeof(struct rd_starbin_export), rd_starbin_export_compare);

  for(int task = 0; task < NTask; task++)
    Send_count[task] = 0;
  for(int i = 0; i < nexport; i++)
    Send_count[exports[i].task]++;

  if(Send_count[ThisTask] != 0)
    terminate_program("RD hierarchy attempted a local star-bin export");

  MPI_Alltoall(Send_count, 1, MPI_INT, Recv_count, 1, MPI_INT, MPI_COMM_WORLD);

  int nimport = 0;
  Recv_offset[0] = Send_offset[0] = 0;
  for(int task = 0; task < NTask; task++)
    {
      nimport += Recv_count[task];
      if(task > 0)
        {
          Send_offset[task] = Send_offset[task - 1] + Send_count[task - 1];
          Recv_offset[task] = Recv_offset[task - 1] + Recv_count[task - 1];
        }
    }

  struct rd_starbin_export *imports =
      (struct rd_starbin_export *)mymalloc("RDStarBinImport", nimport * sizeof(struct rd_starbin_export));

  for(int ngrp = 0; ngrp < (1 << PTask); ngrp++)
    {
      int recvTask = ThisTask ^ ngrp;
      if(recvTask < NTask && (Send_count[recvTask] > 0 || Recv_count[recvTask] > 0))
        MPI_Sendrecv(&exports[Send_offset[recvTask]], Send_count[recvTask] * sizeof(struct rd_starbin_export), MPI_BYTE,
                     recvTask, TAG_DENS_A, &imports[Recv_offset[recvTask]],
                     Recv_count[recvTask] * sizeof(struct rd_starbin_export), MPI_BYTE, recvTask, TAG_DENS_A, MPI_COMM_WORLD,
                     MPI_STATUS_IGNORE);
    }

  for(int i = 0; i < nimport; i++)
    {
      int index = imports[i].index;
      if(index < 0 || index >= NumGas)
        terminate_program("RD hierarchy received an invalid star-bin primary index");
      SphP[index].RD_StarTimeBin = imin(SphP[index].RD_StarTimeBin, imports[i].bin);
    }

  myfree(imports);
  myfree(exports);

  for(int i = 0; i < NumGas; i++)
    if(SphP[i].RD_StarTimeBin > P[i].TimeBinHydro)
      terminate_program("RD hierarchy vertex-star bin is coarser than its vertex bin");

  /* Triangle owners need the star result even when the vertex is remote. */
  exchange_primitive_variables();
}

/*! \brief Reset only predictors whose vertex interval opens at this event. */
static void rd_open_vertex_predictors(void)
{
  for(int i = 0; i < NumGas; i++)
    {
      if(SphP[i].RD_StarTimeBin < P[i].TimeBinHydro)
        {
          for(int k = 0; k < 4; k++)
            SphP[i].RD_dU[k] = 0.0;
          SphP[i].RD_PredictorEnd = -1;
        }
      else if(TimeBinSynchronized[P[i].TimeBinHydro])
        {
          for(int k = 0; k < 4; k++)
            SphP[i].RD_dU[k] = 0.0;
          SphP[i].RD_PredictorEnd = All.Ti_Current + (((integertime)1) << P[i].TimeBinHydro);
        }
    }
}
#endif

/* Per-call diagnostics for the upwind system solve (item A4 of the report). */
static long long RD_stat_elements;         /* elements whose residual was evaluated */
static long long RD_stat_pinv_fallback;    /* elements that needed the pseudo-inverse */
static long long RD_stat_exact_singular;   /* LU factorizations with an exactly singular pivot */
static lapack_int RD_stat_min_svd_rank;    /* smallest numerical rank returned by DGELSD */
static long long RD_stat_svd_rank_count[5]; /* DGELSD calls returning each rank 0,...,4 */
static double RD_stat_min_pivot_ratio;     /* smallest min|diag(U)|/max|diag(U)| seen */
static double RD_stat_max_cons_defect_abs; /* largest raw conservation defect, absolute */
static double RD_stat_max_phi;             /* largest |phi^T| seen, for context on the absolute figure */
static double RD_stat_ever_max_cons_defect_abs; /* high-water mark across calls; NOT reset per call */
#ifdef RD_RK2_TOTAL_RESIDUAL
static long long RD_stat_f1_lumped;        /* corrector elements whose temporal term fell back to the lumped mass */
static double RD_stat_min_stage_rho;       /* smallest predictor density seen this step */
static double RD_stat_min_stage_press;     /* smallest predictor pressure seen this step */
#endif
static double RD_stat_min_dt_extrap;       /* smallest dt_Extrapolation seen this call */
static double RD_stat_max_dt_extrap;       /* largest dt_Extrapolation seen this call */
#ifdef RD_RT_FIXED_BOUNDARY
static double RD_stat_boundary_absorbed[4];     /* signed trial-stage dQ suppressed at fixed vertices */
static double RD_stat_boundary_absorbed_abs[4]; /* absolute trial-stage dQ suppressed at fixed vertices */
static double RD_boundary_q_before[4];          /* global-budget reference before the staged RD call */

static inline int rd_rt_fixed_boundary_vertex(int p)
{
  return P[p].Pos[1] < (RD_RT_FIXED_BOUNDARY) || P[p].Pos[1] >= boxSize_Y - (RD_RT_FIXED_BOUNDARY);
}

static inline void rd_rt_record_absorbed_update(double dm, double dpx, double dpy, double de)
{
  const double dq[4] = {dm, dpx, dpy, de};
  for(int k = 0; k < 4; k++)
    {
      RD_stat_boundary_absorbed[k] += dq[k];
      RD_stat_boundary_absorbed_abs[k] += fabs(dq[k]);
    }
}
#endif

#ifdef RD_DIAG_THETA
/* Distribution of the B blending parameter. The classical expectation is that
 * Theta is near zero where the solution is smooth, so that B degenerates to
 * LDA there; if it is instead O(1) or switching in smooth flow the fault is in
 * the indicator rather than in the RK staging, and no amount of restaging
 * repairs it. Index 0 is the spatial Theta of the original blend, index 1 the
 * total-residual Theta of the corrector, so the two indicators can be compared
 * on the same run. */
#define RD_THETA_BINS 8
static const double RD_theta_edges[RD_THETA_BINS - 1] = {1e-6, 1e-4, 1e-2, 0.1, 0.5, 0.9, 1.0};
static long long RD_stat_theta_hist[2][RD_THETA_BINS];
static long long RD_stat_theta_count[2];
static double RD_stat_theta_sum[2];
static double RD_stat_theta_max[2];

static void rd_record_theta(int which, double theta)
{
  int bin = 0;
  while(bin < RD_THETA_BINS - 1 && theta >= RD_theta_edges[bin])
    bin++;

  RD_stat_theta_hist[which][bin]++;
  RD_stat_theta_count[which]++;
  RD_stat_theta_sum[which] += theta;
  RD_stat_theta_max[which] = dmax(RD_stat_theta_max[which], theta);
}
#endif

static void rd_reset_solver_statistics(void)
{
  RD_stat_elements        = 0;
  RD_stat_pinv_fallback   = 0;
  RD_stat_exact_singular  = 0;
  RD_stat_min_svd_rank    = 5; /* sentinel: no DGELSD call in this solver pass */
  for(int rank = 0; rank <= 4; rank++)
    RD_stat_svd_rank_count[rank] = 0;
  RD_stat_min_pivot_ratio     = 1.0;
  RD_stat_max_cons_defect_abs = 0.0;
  RD_stat_max_phi             = 0.0;
#ifdef RD_RK2_TOTAL_RESIDUAL
  RD_stat_f1_lumped       = 0;
  RD_stat_min_stage_rho   = MAX_DOUBLE_NUMBER;
  RD_stat_min_stage_press = MAX_DOUBLE_NUMBER;
#endif
  RD_stat_min_dt_extrap   = MAX_DOUBLE_NUMBER;
  RD_stat_max_dt_extrap   = -MAX_DOUBLE_NUMBER;
#ifdef RD_RT_FIXED_BOUNDARY
  for(int k = 0; k < 4; k++)
    {
      RD_stat_boundary_absorbed[k] = 0.0;
      RD_stat_boundary_absorbed_abs[k] = 0.0;
    }
#endif
#ifdef RD_DIAG_THETA
  for(int which = 0; which < 2; which++)
    {
      RD_stat_theta_count[which] = 0;
      RD_stat_theta_sum[which]   = 0.0;
      RD_stat_theta_max[which]   = 0.0;
      for(int bin = 0; bin < RD_THETA_BINS; bin++)
        RD_stat_theta_hist[which][bin] = 0;
    }
#endif
}

/* The two compute_residuals() call sites in run.c are expected to see
 * dt_Extrapolation = 0 (before find_next_sync_point) and dt (after), which is
 * what makes the pair a two-stage update rather than two Euler steps. Recording
 * the range lets that be confirmed at runtime instead of by static reading. */
static void rd_record_dt_extrapolation(double dt_extrapolation)
{
  RD_stat_min_dt_extrap = dmin(RD_stat_min_dt_extrap, dt_extrapolation);
  RD_stat_max_dt_extrap = dmax(RD_stat_max_dt_extrap, dt_extrapolation);
}

/*! \brief Solve  S^- X = B  for the residual-distribution upwind system.
 *
 *  S^- = sum_{j in T} K_j^- is singular whenever the element is stagnant with
 *  respect to the mesh (u_n = v_n), because both stationary characteristic
 *  fields then contribute nothing to K_j^-.  The system nevertheless stays
 *  consistent, and the distributed residuals are independent of which solution
 *  is selected, so the minimum-norm least-squares solution is a valid choice.
 *  See dev_log/regularize_matrix_debug_report.md, sections 3 and 4.
 *
 *  \param[in] S Row-major 4x4 matrix S^-; left unmodified.
 *  \param[in,out] rhs Row-major 4 x nrhs right-hand sides, overwritten by X.
 *  \param[in] nrhs Number of right-hand sides.
 *  \param[out] rank Numerical rank of S^-: 4 on the LU path, because the
 *         pivot-ratio trigger did not fire and no direction is numerically
 *         unresolvable; the rank DGELSD reports on the SVD path; and -1 if the
 *         solve failed, so a caller that ignores `info` still cannot mistake a
 *         failure for a full-rank result.
 *
 *         A caller whose formulation needs beta_i to be defined must branch on
 *         this and not on whether the SVD path was taken.  The pivot ratio is
 *         only a solver-selection trigger: it routes numerically full-rank
 *         matrices through DGELSD as well, and DGELSD then reports rank 4 for
 *         them.  Treating "used the SVD" as "rank deficient" silently degrades
 *         those elements.
 *
 *  \return LAPACK info of the step that produced the returned solution.
 */
static lapack_int rd_solve_upwind_system(const double S[4][4], double *rhs, lapack_int nrhs, lapack_int *rank)
{
  double A[16];
  lapack_int ipiv[4];
  int use_pseudo_inverse = 0;

  *rank = -1;

  memcpy(A, &S[0][0], sizeof(A));

#ifdef RD_ALWAYS_PSEUDOINVERSE
  /* Reference path: skip the LU shortcut entirely and always take the
   * minimum-norm solution. Slower, but free of the pivot-ratio branch, so the
   * result is independent of the domain decomposition. Use it to confirm that
   * the fast path below has not changed the answer. */
  lapack_int info    = 0;
  use_pseudo_inverse = 1;
#else
  lapack_int info = LAPACKE_dgetrf(LAPACK_ROW_MAJOR, 4, 4, A, 4, ipiv);

  if(info != 0)
    {
      use_pseudo_inverse          = 1; /* exactly singular pivot */
      RD_stat_exact_singular++;
      RD_stat_min_pivot_ratio = 0.0;
    }
  else
    {
      /* The spread of the diagonal pivots of U is a cheap scale-free trigger,
       * not a condition-number estimate and not the authoritative rank test.
       * A backward-stable LU can return a small residual while producing a
       * solution whose near-null-space component is enormous, so DGELSD is
       * asked to determine the numerical rank when this proxy is small. */
      double pivot_max = fabs(A[0]);
      double pivot_min = fabs(A[0]);

      for(int n = 1; n < 4; n++)
        {
          double pivot = fabs(A[n * 4 + n]);
          pivot_max    = dmax(pivot_max, pivot);
          pivot_min    = dmin(pivot_min, pivot);
        }

      double ratio = (pivot_max > 0.0) ? pivot_min / pivot_max : 0.0;

      if(ratio < RD_stat_min_pivot_ratio)
        RD_stat_min_pivot_ratio = ratio;

      if(!(ratio >= RD_LU_FALLBACK_PIVOT_RATIO))
        use_pseudo_inverse = 1;
    }
#endif /* #ifdef RD_ALWAYS_PSEUDOINVERSE */

  if(!use_pseudo_inverse)
    {
      lapack_int trs_info = LAPACKE_dgetrs(LAPACK_ROW_MAJOR, 'N', 4, nrhs, A, 4, ipiv, rhs, nrhs);

      if(trs_info == 0)
        *rank = 4;

      return trs_info;
    }

  /* Minimum-norm least-squares solution.  RD_SVD_RCOND=-1 asks DGELSD to use
   * its machine-precision cut-off.  The LU threshold above selects the solver;
   * it must not also discard a resolvable singular direction. */
  double singular_values[4];
  lapack_int svd_rank;

  memcpy(A, &S[0][0], sizeof(A));
  info = LAPACKE_dgelsd(LAPACK_ROW_MAJOR, 4, 4, nrhs, A, 4, rhs, nrhs, singular_values, RD_SVD_RCOND, &svd_rank);

  RD_stat_pinv_fallback++;
  if(info == 0)
    {
      *rank = svd_rank;

      if(svd_rank < RD_stat_min_svd_rank)
        RD_stat_min_svd_rank = svd_rank;
      if(svd_rank >= 0 && svd_rank <= 4)
        RD_stat_svd_rank_count[svd_rank]++;
    }

  return info;
}

/*! \brief Check the raw identity sum_{i in T} phi_i = phi^T.
 *
 *  LDA, N, and therefore B satisfy this identity without a correction.  This
 *  routine deliberately never modifies flux: an excessive defect must expose
 *  a broken solve, distribution, or data path instead of being hidden by a
 *  conservation rebalance.
 *
 *  \param[in] flux Distributed residuals, flux[variable][vertex].
 *  \param[in] Phi Element residual phi^T.
 *  \param[in] roundoff_scale Maximum, over the four equations, of |phi^T| plus
 *  the absolute matrix-vector products accumulated before cancellation.
 */
static void rd_check_conservation(const double flux[4][3], const double Phi[4], double roundoff_scale, int triangle_index,
                                  const char *label)
{
  double defect = 0.0, phi_max = 0.0;
  double sum_flux[4];

  for(int k = 0; k < 4; k++)
    {
      sum_flux[k] = flux[k][0] + flux[k][1] + flux[k][2];

      defect  = dmax(defect, fabs(Phi[k] - sum_flux[k]));
      phi_max = dmax(phi_max, fabs(Phi[k]));
    }

  RD_stat_max_cons_defect_abs = dmax(RD_stat_max_cons_defect_abs, defect);
  RD_stat_max_phi             = dmax(RD_stat_max_phi, phi_max);

#ifdef RD_DEBUG_ASSERTS
  if(defect > RD_stat_ever_max_cons_defect_abs)
    {
      RD_stat_ever_max_cons_defect_abs = defect;

      printf("RD-WORST task=%d %s triangle=%d abs=%.3e |phi^T|max=%.3e roundoff_scale=%.3e\n", ThisTask, label,
             triangle_index, defect, phi_max, roundoff_scale);
      for(int k = 0; k < 4; k++)
        printf("           k=%d  phi^T=% .6e  phi_0=% .6e  phi_1=% .6e  phi_2=% .6e  sum=% .6e  diff=% .3e\n", k, Phi[k],
               flux[k][0], flux[k][1], flux[k][2], sum_flux[k], Phi[k] - sum_flux[k]);
    }

  double tolerance = RD_CONSERVATION_ROUNDOFF_FACTOR * DBL_EPSILON * roundoff_scale;
  if(defect > tolerance)
    {
      printf("RD assertion A2 failed: task=%d %s triangle=%d defect=%.17g tolerance=%.17g roundoff_scale=%.17g\n",
             ThisTask, label, triangle_index, defect, tolerance, roundoff_scale);
      terminate_program("RD assertion A2: raw sum_i phi_i != phi^T within round-off");
    }
#else
  (void)roundoff_scale;
#endif
}

#ifdef RD_DEBUG_ASSERTS
/*! \brief Assertion A1:  sum_{i in T} K_i = 0.
 *
 *  This follows from sum_i n_i = 0 together with K_i^+ + K_i^- = K_i, and each
 *  entry of K_i is linear in the eigenvalues, so the identity must hold to
 *  round-off.  Failure indicates a broken triangle orientation, an
 *  inconsistent normal/magnitude convention, or a faulty eigenvalue splitting.
 */
static void rd_assert_K_sum_vanishes(double Kmatrix[4][4][3][3], int kfull, int triangle_index)
{
  double sum_max = 0.0, entry_max = 0.0;

  for(int k = 0; k < 4; k++)
    for(int p = 0; p < 4; p++)
      {
        double sum = 0.0;

        for(int j = 0; j < 3; j++)
          {
            sum       = sum + Kmatrix[k][p][j][kfull];
            entry_max = dmax(entry_max, fabs(Kmatrix[k][p][j][kfull]));
          }

        sum_max = dmax(sum_max, fabs(sum));
      }

  if(entry_max > 0.0 && sum_max > 1e-10 * entry_max)
    {
      printf("RD assertion A1 failed: task=%d triangle=%d ||sum_i K_i||=%g max|K|=%g ratio=%g\n", ThisTask, triangle_index,
             sum_max, entry_max, sum_max / entry_max);
      terminate_program("RD assertion A1: sum_i K_i != 0");
    }
}
#endif /* #ifdef RD_DEBUG_ASSERTS */

/*! \brief Compute residuals of triangles/tetrahedra and distribute them.
 *  This function is used for Residual Distribution hydrodynamics method, which is equivalent to
 *  compute_interface_fluxes() in the original AREPO's Finite Volume approach.
 *
 *  \param[in] T Pointer to tessellation.
 *
 *  \return void
 */

/*! \brief The set of Delaunay elements this task owns.
 *
 *  Two notions are deliberately kept distinct here.
 *
 *  1. The **physical owned set available in this mesh**,
 *     `element[0 .. n-1]`. With a persistent/full mesh this is complete. With
 *     an active-only rebuild it contains the due simplices around active
 *     primaries. The static median DualArea is initialized separately from an
 *     all-active mesh and must never be rebuilt from this partial set.
 *  2. The **active subset**, marked by `active[]`, whose residuals are
 *     advanced on the current step.
 *
 *  The two coincide under `FORCE_EQUAL_TIMESTEPS`, which the compile-time
 *  guards currently enforce, but they will not once hierarchical time bins
 *  are enabled. Collapsing them would silently build the wrong dual volume
 *  for that extension.
 */
struct rd_element_set
{
  int *element;
  char *active;
  struct triangle_normals *normals;
  int n;
  int n_active;
};

/*! \brief Minimum-ID ownership: does this task claim this simplex instance?
 *
 *  The owner of a physical simplex is the task holding, as a local primary
 *  point, the vertex with the globally smallest (ID, task) key. The claim is
 *  made only on the simplex instance in which that vertex appears as the
 *  primary copy (`DP index` in `[0, NumGas)`), never on a periodic-image
 *  instance. This gives, per physical simplex, exactly one claiming task and
 *  exactly one claimed instance on it:
 *
 *  - every task holding a copy sees the same vertex IDs, so all agree on the
 *    owner key;
 *  - the winning vertex is a local primary on exactly one task;
 *  - on that task, the Delaunay star of a primary point contains each
 *    physical simplex incident to it exactly once, so among the periodic
 *    images of the simplex exactly one has the winning vertex as the primary
 *    copy.
 *
 *  This replaces the previous majority-task rule plus O(n^2) sorted-ID
 *  deduplication. Unlike the majority rule it has no ties (IDs are globally
 *  unique; `task` is only a tie-break for reflective copies, which share the
 *  ID of their source), and the loop is over `DIMS + 1` vertices, so the same
 *  code covers triangles and tetrahedra.
 *
 *  A persistent/full mesh uses the activity-independent minimum over all
 *  vertices. A genuinely active-only static rebuild instead takes the minimum
 *  only over vertices in the triangle's finest bin. Those vertices are active
 *  whenever the triangle is due, so the winning primary owns a constructed
 *  star. Remote bins come from live PrimExch data, never DP[].timebin, which is
 *  only a construction stamp and is especially meaningless after the
 *  CREATE_FULL_MESH temporary bin 0.
 */
static int rd_simplex_claimed(tessellation *T, int i, int use_min_bin_owner)
{
  point *DP = T->DP;
  tetra *DT = T->DT;

  MyIDType min_id = 0;
  int min_task = -1, triangle_bin = TIMEBINS;
  int j;

  if(use_min_bin_owner)
    {
#ifdef RD_HIERARCHICAL_TIMESTEPS
      triangle_bin = rd_point_timebin(&DP[DT[i].p[0]]);
      for(j = 1; j < DIMS + 1; j++)
        triangle_bin = imin(triangle_bin, rd_point_timebin(&DP[DT[i].p[j]]));
#else
      terminate_program("minimum-bin simplex ownership requires the RD hierarchy");
#endif
    }

  for(j = 0; j < DIMS + 1; j++)
    {
#ifdef RD_HIERARCHICAL_TIMESTEPS
      if(use_min_bin_owner && rd_point_timebin(&DP[DT[i].p[j]]) != triangle_bin)
        continue;
#endif

      MyIDType id = DP[DT[i].p[j]].ID;
      int task = DP[DT[i].p[j]].task;

      if(min_task < 0 || id < min_id || (id == min_id && task < min_task))
        {
          min_id   = id;
          min_task = task;
        }
    }

  /* Claim if the winning vertex appears in this instance as a local primary
   * copy. The "exists" form (rather than testing the single minimising entry)
   * makes the degenerate case of a vertex meeting its own periodic image in
   * one simplex resolve in favour of the primary copy. */
  for(j = 0; j < DIMS + 1; j++)
    {
      int pt = DT[i].p[j];

      if(DP[pt].ID == min_id && DP[pt].task == ThisTask && DP[pt].task == min_task && DP[pt].index >= 0 &&
         DP[pt].index < NumGas)
        return 1;
    }

  return 0;
}

/*! \brief Collect, in one pass, the elements this task owns.
 *
 *  Replaces the two near-identical classification passes that previously ran
 *  in `reset_dualarea()` and `compute_residuals()`, and the majority-rule
 *  responsibility plus duplicate removal they relied on. The activity test
 *  that used to filter the classification is recorded in `active[]` rather
 *  than removing elements from the set.
 */
static void rd_build_element_set(tessellation *T, struct rd_element_set *set, int classify_activity)
{
  point *DP = T->DP;
  tetra *DT = T->DT;
  int Ndt   = T->Ndt;
  int i, j;
  int use_min_bin_owner = 0;

#ifdef RD_HIERARCHICAL_TIMESTEPS
  use_min_bin_owner = classify_activity && rd_use_min_bin_owner();
#endif

  int n = 0;
  for(i = 0; i < Ndt; i++)
    if(rd_triangle_is_physical(T, i) && rd_simplex_claimed(T, i, use_min_bin_owner))
      n += 1;

  set->n       = n;
  set->element = (int *)mymalloc_movable(&set->element, "RD_elements", set->n * sizeof(int));
  set->active  = (char *)mymalloc_movable(&set->active, "RD_element_active", set->n * sizeof(char));

  for(i = 0, n = 0; i < Ndt; i++)
    if(rd_triangle_is_physical(T, i) && rd_simplex_claimed(T, i, use_min_bin_owner))
      set->element[n++] = i;

  set->normals =
      (struct triangle_normals *)mymalloc_movable(&set->normals, "RD_normals", set->n * sizeof(struct triangle_normals));

  set->n_active = 0;

  for(i = 0; i < set->n; i++)
    {
#ifdef TWODIMS
      triangle_get_normals_area(T, set->element[i], &set->normals[i]);
#endif

      char is_active = 0;

      if(!classify_activity)
        {
          set->active[i] = 0;
          continue;
        }

#ifdef RD_HIERARCHICAL_TIMESTEPS
      /* The triangle clock is the finest of all three live vertex clocks.
       * The fixed owner need not own (or itself be) the active driver. */
      int triangle_bin = rd_point_timebin(&DP[DT[set->element[i]].p[0]]);
      for(j = 1; j < DIMS + 1; j++)
        triangle_bin = imin(triangle_bin, rd_point_timebin(&DP[DT[set->element[i]].p[j]]));
      is_active = TimeBinSynchronized[triangle_bin];
#else
      /* Equal-step baseline: a synchronized local original marks the element. */
      for(j = 0; j < DIMS + 1; j++)
        {
          int pt = DT[set->element[i]].p[j];

          if(DP[pt].task == ThisTask && DP[pt].index >= 0 && DP[pt].index < NumGas &&
             TimeBinSynchronized[P[DP[pt].index].TimeBinHydro])
            {
              is_active = 1;
              break;
            }
        }
#endif

      set->active[i] = is_active;
      set->n_active += is_active;
    }
}

static void rd_free_element_set(struct rd_element_set *set)
{
  myfree_movable(set->normals);
  myfree_movable(set->active);
  myfree_movable(set->element);
}

/*! \brief Accumulate the median dual area over the complete physical set.
 *
 *  Uses every owned element, active or not, because the control area is a
 *  geometric property of the tessellation.
 */
static void rd_accumulate_dual_area(tessellation *T, const struct rd_element_set *set)
{
  point *DP = T->DP;
  tetra *DT = T->DT;
  int i, j, k;

  for(i = 0; i < NumGas; i++)
    SphP[i].DualArea = 0.0;

  N_DualArea_export = 0;

  for(i = 0; i < set->n; i++)
    for(j = 0; j < DIMS + 1; j++)
      {
        int pt = DT[set->element[i]].p[j];

        if(DP[pt].task == ThisTask)
          {
            int SphP_index = DP[pt].index;

            if(SphP_index >= NumGas)
              SphP_index -= NumGas;

            SphP[SphP_index].DualArea += set->normals[i].area / (DIMS + 1);
          }
        else
          N_DualArea_export += 1;
      }

  DualArea_list = (struct DualArea_list_data *)mymalloc_movable(&DualArea_list, "DualArea_list",
                                                                N_DualArea_export * sizeof(struct DualArea_list_data));
  k = 0;

  for(i = 0; i < set->n; i++)
    for(j = 0; j < DIMS + 1; j++)
      {
        int pt = DT[set->element[i]].p[j];

        if(DP[pt].task != ThisTask)
          {
            DualArea_list[k].task     = DP[pt].task;
            DualArea_list[k].index    = DP[pt].originalindex;
            DualArea_list[k].DualArea = set->normals[i].area / (DIMS + 1);
            k += 1;
          }
      }

  apply_DualArea_list();

  myfree_movable(DualArea_list);

#ifdef RD_DEBUG_ASSERTS
  /* Coverage audit for the ownership rule. Every physical simplex must be
   * claimed exactly once globally; each claim deposits its full area |T|
   * (split as |T|/3 per vertex), and the periodic tessellation tiles the box,
   * so the global dual area must equal the box area. A double claim or a
   * missed simplex shifts this sum by O(|T|) and is caught immediately. */
  {
    double local_area = 0.0, global_area;

    for(i = 0; i < NumGas; i++)
      local_area += SphP[i].DualArea;

    MPI_Allreduce(&local_area, &global_area, 1, MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);

    double box_area = boxSize_X * boxSize_Y;

    if(fabs(global_area - box_area) > 1.0e-10 * box_area)
      {
        printf("RD coverage audit failed: task=%d sum(DualArea)=%.17g box=%.17g rel=%.3e\n", ThisTask, global_area,
               box_area, fabs(global_area - box_area) / box_area);
        terminate_program("RD coverage audit: global dual area != box area");
      }
  }
#endif /* #ifdef RD_DEBUG_ASSERTS */
}

void reset_dualarea(tessellation *T)
{
  struct rd_element_set set;

  rd_build_element_set(T, &set, 0);
  rd_accumulate_dual_area(T, &set);
  rd_free_element_set(&set);
}

#ifdef RD_RK2_INTERNAL_LOOP
/*! \brief Snapshot the intensive nodal state U^n before the predictor sweep. */
static void rd_rk2_save_stage0(void)
{
  for(int i = 0; i < NumGas; i++)
    {
      double inv_area = 1.0 / SphP[i].DualArea;

      SphP[i].RD_Ustage0[0] = P[i].Mass * inv_area;
      SphP[i].RD_Ustage0[1] = SphP[i].Momentum[0] * inv_area;
      SphP[i].RD_Ustage0[2] = SphP[i].Momentum[1] * inv_area;
      SphP[i].RD_Ustage0[3] = SphP[i].Energy * inv_area;

      for(int k = 0; k < 4; k++)
        SphP[i].RD_dU[k] = 0.0;
    }
}

#ifdef RD_RK2_RATE_CONSISTENT_HEUN
/*! \brief Prepare the nodal data between the four rate-consistent sweeps.
 *
 *  The semi-discrete LDA+F1 operator is
 *
 *      k(U) = 2 v(U) - S^-1 M(U) v(U),
 *
 *  where S is the diagonal median-dual area, v is the LDA spatial rate, and
 *  M is the F1 mass matrix.  Each Heun stage is therefore one spatial sweep
 *  followed by one mass-apply sweep.  Conserved Q is also the accumulator:
 *
 *    pass 0: Q = Qn + 2 dt S v0
 *    pass 1: Q = Qn + dt S k0 = Q*
 *    pass 2: Q = (Qn+Q*)/2 + dt S v*
 *    pass 3: Q = Qn + dt (S k0 + S k*)/2.
 *
 *  RD_dU carries v0/v* into the mass sweeps. Between passes 1 and 2 it
 *  temporarily carries U*-Un so the midpoint accumulator can be formed.
 */
static void rd_rate_consistent_prepare_pass(int pass)
{
  if(pass < 1 || pass > 3)
    terminate_program("invalid rate-consistent RD pass transition");

  for(int i = 0; i < NumGas; i++)
    {
      double area = SphP[i].DualArea;
      double dt   = (((integertime)1) << P[i].TimeBinHydro) * All.Timebase_interval;
      double u[4] = {P[i].Mass / area, SphP[i].Momentum[0] / area, SphP[i].Momentum[1] / area,
                     SphP[i].Energy / area};

      if(pass == 1)
        {
          /* The first spatial sweep used weight 2 dt. Recover v(U^n) while
           * leaving both Q and the stage-n primitives untouched. */
          for(int k = 0; k < 4; k++)
            SphP[i].RD_dU[k] = (u[k] - SphP[i].RD_Ustage0[k]) / (2.0 * dt);
        }
      else if(pass == 2)
        {
          /* The first mass sweep closed k0, so Q now is the physical Heun
           * predictor. Recover W*, retain U*-Un, and reset Q to the midpoint
           * accumulator before evaluating v(U*). */
          for(int k = 0; k < 4; k++)
            SphP[i].RD_dU[k] = u[k] - SphP[i].RD_Ustage0[k];

          double rho   = u[0];
          double velx  = u[1] / rho;
          double vely  = u[2] / rho;
          double egy   = u[3] / rho - 0.5 * (velx * velx + vely * vely);
          double press = GAMMA_MINUS1 * rho * egy;

          if(!isfinite(rho) || !isfinite(press) || rho <= 0.0 || press <= 0.0)
            {
              printf("RD rate-consistent predictor invalid: task=%d i=%d ID=%llu rho=%.17g press=%.17g\n", ThisTask, i,
                     (unsigned long long)P[i].ID, rho, press);
              terminate_program("RD rate-consistent Heun produced a non-physical predictor");
            }

          RD_stat_min_stage_rho   = dmin(RD_stat_min_stage_rho, rho);
          RD_stat_min_stage_press = dmin(RD_stat_min_stage_press, press);

          SphP[i].Density  = rho;
          P[i].Vel[0]      = velx;
          P[i].Vel[1]      = vely;
          SphP[i].Utherm   = egy;
          SphP[i].Pressure = press;
#ifdef TREE_BASED_TIMESTEPS
          SphP[i].Csnd = sqrt(GAMMA * press / rho);
#endif

          P[i].Mass              = area * (SphP[i].RD_Ustage0[0] + 0.5 * SphP[i].RD_dU[0]);
          SphP[i].Momentum[0]    = area * (SphP[i].RD_Ustage0[1] + 0.5 * SphP[i].RD_dU[1]);
          SphP[i].Momentum[1]    = area * (SphP[i].RD_Ustage0[2] + 0.5 * SphP[i].RD_dU[2]);
          SphP[i].Energy         = area * (SphP[i].RD_Ustage0[3] + 0.5 * SphP[i].RD_dU[3]);
        }
      else
        {
          /* Q is midpoint + dt v*. RD_dU still contains U*-Un here. */
          for(int k = 0; k < 4; k++)
            {
              double midpoint = SphP[i].RD_Ustage0[k] + 0.5 * SphP[i].RD_dU[k];
              SphP[i].RD_dU[k] = (u[k] - midpoint) / dt;
            }
        }
    }
}
#endif /* RD_RK2_RATE_CONSISTENT_HEUN */

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
 *  added here, before the corrector sweep contributes the element sums. The
 *  The coherent-beta* experiment instead redistributes saved element Phi(U^n)
 *  with beta(U*) inside that sweep. B similarly needs the saved old N and LDA
 *  pieces so one total-residual theta can blend both stages. In either case
 *  the assembled shortcut has discarded information the corrector needs.
 */
static void rd_rk2_prepare_corrector(void)
{
  for(int i = 0; i < NumGas; i++)
    {
      double inv_area = 1.0 / SphP[i].DualArea;

      double u0 = P[i].Mass * inv_area;
      double u1 = SphP[i].Momentum[0] * inv_area;
      double u2 = SphP[i].Momentum[1] * inv_area;
      double u3 = SphP[i].Energy * inv_area;

      SphP[i].RD_dU[0] = u0 - SphP[i].RD_Ustage0[0];
      SphP[i].RD_dU[1] = u1 - SphP[i].RD_Ustage0[1];
      SphP[i].RD_dU[2] = u2 - SphP[i].RD_Ustage0[2];
      SphP[i].RD_dU[3] = u3 - SphP[i].RD_Ustage0[3];

      double rho   = u0;
      double velx  = u1 / u0;
      double vely  = u2 / u0;
      double egy   = u3 / u0 - 0.5 * (velx * velx + vely * vely);
      double press = GAMMA_MINUS1 * rho * egy;

      if(!isfinite(rho) || !isfinite(press) || rho <= 0 || press <= 0)
        {
          printf("RD predictor state invalid: task=%d i=%d ID=%llu rho=%g press=%g pos=%g|%g\n", ThisTask, i,
                 (unsigned long long)P[i].ID, rho, press, P[i].Pos[0], P[i].Pos[1]);
          terminate_program("RD predictor produced a non-physical state");
        }

      RD_stat_min_stage_rho   = dmin(RD_stat_min_stage_rho, rho);
      RD_stat_min_stage_press = dmin(RD_stat_min_stage_press, press);

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
      SphP[i].Utherm   = egy;
      SphP[i].Pressure = press;
#ifdef TREE_BASED_TIMESTEPS
      SphP[i].Csnd = sqrt(GAMMA * press / rho);
#endif

#if !defined(RD_DIAG_NO_KICK) && !defined(RD_RK2_COHERENT_BETA_STAR) && !defined(B_SCHEME)
      /* the local +1/2 (Q* - Q^n) part of the corrector */
      P[i].Mass += 0.5 * SphP[i].DualArea * SphP[i].RD_dU[0];
      SphP[i].Momentum[0] += 0.5 * SphP[i].DualArea * SphP[i].RD_dU[1];
      SphP[i].Momentum[1] += 0.5 * SphP[i].DualArea * SphP[i].RD_dU[2];
      SphP[i].Energy += 0.5 * SphP[i].DualArea * SphP[i].RD_dU[3];
#endif
    }
}
#endif /* #ifdef RD_RK2_INTERNAL_LOOP */

#ifdef RD_HIERARCHICAL_TIMESTEPS
void compute_residuals(tessellation *T, int rd_stage)
#else
void compute_residuals(tessellation *T)
#endif
{
#ifdef NOHYDRO
  return;
#endif /* #ifdef NOHYDRO */
  TIMER_START(CPU_RESIDUAL_DISTRIBUTION);

  rd_reset_solver_statistics();

#ifdef RD_RT_FIXED_BOUNDARY
  for(int component = 0; component < 4; component++)
    RD_boundary_q_before[component] = 0.0;
  for(int q_index = 0; q_index < NumGas; q_index++)
    {
      RD_boundary_q_before[0] += P[q_index].Mass;
      RD_boundary_q_before[1] += SphP[q_index].Momentum[0];
      RD_boundary_q_before[2] += SphP[q_index].Momentum[1];
      RD_boundary_q_before[3] += SphP[q_index].Energy;
    }
#endif

#ifdef RD_HIERARCHICAL_TIMESTEPS
  if(rd_stage != RD_RK_STAGE_PREDICTOR && rd_stage != RD_RK_STAGE_CORRECTOR)
    terminate_program("invalid RD hierarchical RK stage");
#endif

  point *DP = T->DP;
  tetra *DT = T->DT;
  int i, j = 0, k = 0, p;

  /* One classification per step, shared by the dual-area accumulation and the
   * residual sweep. The set carries the complete physical owned elements; the
   * active subset is marked rather than filtered out, so that the control area
   * stays a property of the tessellation. */
  struct rd_element_set set;
  rd_build_element_set(T, &set, 1);
#ifndef RD_HIERARCHICAL_TIMESTEPS
  rd_accumulate_dual_area(T, &set);
#else
  /* Static RD control areas are initialized once from the all-active mesh and
   * migrate with SphP. Recomputing them from a fine-only tessellation would
   * replace the median dual cell by an incomplete active-star fragment. */
  for(int area_index = 0; area_index < NumGas; area_index++)
    if(!isfinite(SphP[area_index].DualArea) || SphP[area_index].DualArea <= 0.0)
      terminate_program("RD hierarchy lost its persistent static DualArea");

#ifdef RD_DEBUG_ASSERTS
  /* Domain decomposition migrates the complete SphP record, including the
   * persistent static DualArea. Check that repeated active-only rebuilds have
   * neither lost nor duplicated any part of the median-dual partition. */
  {
    double local_area = 0.0, global_area;

    for(int area_index = 0; area_index < NumGas; area_index++)
      local_area += SphP[area_index].DualArea;

    MPI_Allreduce(&local_area, &global_area, 1, MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);

    double box_area = boxSize_X * boxSize_Y;

    if(fabs(global_area - box_area) > 1.0e-10 * box_area)
      terminate_program("RD hierarchy persistent DualArea coverage changed after domain decomposition");
  }
#endif /* #ifdef RD_DEBUG_ASSERTS */
#endif

#ifdef RD_HIERARCHICAL_TIMESTEPS
  if(rd_stage == RD_RK_STAGE_PREDICTOR)
    {
      rd_prepare_vertex_star_context(T);
      rd_open_vertex_predictors();
    }

  /* Hierarchical stages use synchronized or assembled predictor states, not
   * the legacy primitive-variable Taylor extrapolation. */
  rd_record_dt_extrapolation(0.0);
#endif

  int Ndt_thistask        = set.n;
  int *thistask_triangles = set.element;
  tri_normals_list        = set.normals;

#ifdef RD_RK2_COHERENT_BETA_N
  /* The stage-0 distribution matrix is indexed by the persistent element-set
   * slot, which is identical in both sweeps of this static-mesh experiment. */
  double(*rd_beta_stage0)[3][4][4] =
      (double(*)[3][4][4])mymalloc("RD_BetaStage0", Ndt_thistask * sizeof(*rd_beta_stage0));
#endif
#ifdef RD_RK2_COHERENT_BETA_STAR
  /* beta(U*) must redistribute the old element residual explicitly; the
   * assembled +dU/2 shortcut irreversibly carries beta(U^n). */
  double(*rd_phi_stage0)[4] = (double(*)[4])mymalloc("RD_PhiStage0", Ndt_thistask * sizeof(*rd_phi_stage0));
#endif
#if defined(B_SCHEME) && defined(RD_RK2_INTERNAL_LOOP)
  /* A total-B corrector needs both spatial-stage distributions. The equal-bin
   * static element set has the same persistent ordering in both sweeps. */
  double(*rd_b_flux_n_stage0)[4][3] =
      (double(*)[4][3])mymalloc("RD_BFluxNStage0", Ndt_thistask * sizeof(*rd_b_flux_n_stage0));
  double(*rd_b_flux_lda_stage0)[4][3] =
      (double(*)[4][3])mymalloc("RD_BFluxLDAStage0", Ndt_thistask * sizeof(*rd_b_flux_lda_stage0));
  double(*rd_b_phi_stage0)[4] =
      (double(*)[4])mymalloc("RD_BPhiStage0", Ndt_thistask * sizeof(*rd_b_phi_stage0));
#endif

  Max_N_FluxRD_export = 0;
  for(i = 0; i < Ndt_thistask; i++)
    for(j = 0; j < DIMS + 1; j++)
      if(DP[DT[thistask_triangles[i]].p[j]].task != ThisTask)
        Max_N_FluxRD_export++;

#ifdef RD_RK2_INTERNAL_LOOP
  /* Two-stage GL+F1 total-residual step (analysis document sections 1, 9,
   * 10): stage 0 is the RD predictor U* = U^n - (dt/|S_i|) sum phi_i(U^n),
   * stage 1 the corrector distributing the total residual. Both stages use
   * the FULL timestep; the half-step convention of the baseline pair is
   * unreachable on this path. */
  int rd_stage;
#ifdef RD_RK2_RATE_CONSISTENT_HEUN
  const int rd_number_of_passes = 4;
#else
  const int rd_number_of_passes = 2;
#endif
  for(rd_stage = 0; rd_stage < rd_number_of_passes; rd_stage++)
    {
      if(rd_stage == 0)
        rd_rk2_save_stage0();
      else
        {
#ifdef RD_RK2_RATE_CONSISTENT_HEUN
          rd_rate_consistent_prepare_pass(rd_stage);
          /* Passes 1 and 3 need the nodal rate; pass 2 needs W*. Sending both
           * fields at every transition keeps the ghost contract simple. */
          exchange_primitive_variables();
#else
#ifdef RD_DIAG_PREDICTOR_ONLY /* diagnostic only: stop after the predictor stage */
          break;
#endif /* RD_DIAG_PREDICTOR_ONLY */
#ifndef RD_DIAG_SKIP_PREPARE /* diagnostic only: run stage 1 on the stage-0 inputs */
          rd_rk2_prepare_corrector();
          exchange_primitive_variables(); /* ghosts receive W* and RD_dU */
#endif
#endif /* RD_RK2_RATE_CONSISTENT_HEUN */
        }

#ifdef RD_DEBUG_ASSERTS
      /* Stage-boundary checksums: locate, not merely detect, any
       * decomposition dependence. Printed at full precision. */
      {
        double loc[4] = {0, 0, 0, 0}, glob[4];

        for(int ck = 0; ck < NumGas; ck++)
          {
            loc[0] += P[ck].Mass;
            loc[1] += SphP[ck].Energy;
            loc[2] += fabs(SphP[ck].RD_dU[0]) + fabs(SphP[ck].RD_dU[3]);
            loc[3] += fabs(SphP[ck].Density) + fabs(SphP[ck].Pressure);
          }
        MPI_Reduce(loc, glob, 4, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);
        if(ThisTask == 0)
          printf("RD-CKSUM stage=%d mass=%.17g energy=%.17g sum|dU|=%.17g sum|prim|=%.17g\n", rd_stage, glob[0], glob[1],
                 glob[2], glob[3]);
      }
#endif

      rd_record_dt_extrapolation(0.0); /* no Taylor extrapolation on this path */
#endif

  N_FluxRD_export     = 0;
  FluxRD_list =
      (struct FluxRD_list_data *)mymalloc_movable(&FluxRD_list, "FluxRD_list", Max_N_FluxRD_export * sizeof(struct FluxRD_list_data));

  // main loop through triangles this task responsible for
  for(i = 0; i < Ndt_thistask; i++)
    {
      /* The set holds every owned physical element so that the dual area is
       * complete; only the active subset is advanced. This is the criterion
       * that previously filtered the classification: at least one vertex that
       * is a local original point is synchronized. */
      if(!set.active[i])
        continue;

      // get triangle timebin/timestep
      int timebin_vertices[DIMS + 1];
      for(j = 0; j < DIMS + 1; j++)
        {
          if(DP[DT[thistask_triangles[i]].p[j]].task == ThisTask)
            {
              int SphP_index = DP[DT[thistask_triangles[i]].p[j]].index;
              if(SphP_index >= NumGas)
                SphP_index -= NumGas;

              timebin_vertices[j] = P[SphP_index].TimeBinHydro;
            }
          else
            {
              int PrimExch_index  = DP[DT[thistask_triangles[i]].p[j]].index;
              timebin_vertices[j] = PrimExch[PrimExch_index].TimeBinHydro;
            }
        }

      int timebin_this_triangle = timebin_vertices[0];

      for(j = 0; j < DIMS + 1; j++)
        if(timebin_vertices[j] < timebin_this_triangle)
          timebin_this_triangle = timebin_vertices[j];

      double full_triangle_dt = (((integertime)1) << timebin_this_triangle) * All.Timebase_interval;
      double triangle_dt      = full_triangle_dt;

#ifdef RD_RK2_RATE_CONSISTENT_HEUN
      /* Spatial/mass weights for k=2v-S^-1Mv and the Heun average. */
      const double rd_pass_weight[4] = {2.0, 1.0, 1.0, 0.5};
      triangle_dt *= rd_pass_weight[rd_stage];
#elif !defined(RD_RK2_INTERNAL_LOOP)
      triangle_dt *= 0.5; /* the baseline applies two half-weight Heun calls per step */
#endif

      // compute residual: set up initial states
      double U_fluid[DIMS + 1][DIMS + 2];  // specific conserved fluid variables
      double C_sound[DIMS + 1];
      double Pressure[DIMS + 1];

      double Velvertex_avg[3];  // moving mesh: average mesh velocity
      for(j = 0; j < 3; j++)
        {
          Velvertex_avg[j] = 0.0;
        }

#ifdef RD_RK2_TOTAL_RESIDUAL
      double dU_vertex[DIMS + 1][4]; /* intensive nodal U* - U^n per vertex; corrector stage only */
#endif

      for(j = 0; j < DIMS + 1; j++)  // loop through vertices of this triangle
        {
          if(DP[DT[thistask_triangles[i]].p[j]].task == ThisTask)
            {
              int SphP_index = DP[DT[thistask_triangles[i]].p[j]].index;
              if(SphP_index >= NumGas)
                SphP_index -= NumGas;

              // extrapolation to current time
              struct grad_data *grad = &SphP[SphP_index].Grad;

              struct state_primitive vertex_state;
              struct state_primitive delta_time;
              vertex_state.rho   = SphP[SphP_index].Density;
              vertex_state.press = SphP[SphP_index].Pressure;
              vertex_state.velx  = P[SphP_index].Vel[0];
              vertex_state.vely  = P[SphP_index].Vel[1];
              vertex_state.velz  = P[SphP_index].Vel[2];

#ifdef RD_RK2_TOTAL_RESIDUAL
              /* The stage states are exact: W^n before the predictor, the
               * recovered W* before the corrector. No Taylor extrapolation. */
              (void)grad;
              (void)delta_time;
              if(rd_stage == 1
#ifdef RD_RK2_RATE_CONSISTENT_HEUN
                 || rd_stage == 3
#endif
              )
                for(k = 0; k < 4; k++)
                  dU_vertex[j][k] = SphP[SphP_index].RD_dU[k];
#else
              double dt_Extrapolation = All.Time - SphP[SphP_index].TimeLastPrimUpdate;
              rd_record_dt_extrapolation(dt_Extrapolation);

              vertex_state.velx -= SphP[SphP_index].VelVertex[0];
              vertex_state.vely -= SphP[SphP_index].VelVertex[1];
              vertex_state.velz -= SphP[SphP_index].VelVertex[2];
              triangle_vertex_do_time_extrapolation(&delta_time, &vertex_state, grad, dt_Extrapolation);
              triangle_vertex_add_extrapolation(&delta_time, &vertex_state);
              vertex_state.velx += SphP[SphP_index].VelVertex[0];
              vertex_state.vely += SphP[SphP_index].VelVertex[1];
              vertex_state.velz += SphP[SphP_index].VelVertex[2];
#endif

              Velvertex_avg[0] += SphP[SphP_index].VelVertex[0];
              Velvertex_avg[1] += SphP[SphP_index].VelVertex[1];
              Velvertex_avg[2] += SphP[SphP_index].VelVertex[2];

#ifdef TWODIMS
              U_fluid[j][0]         = vertex_state.rho;
              U_fluid[j][1]         = U_fluid[j][0] * vertex_state.velx;
              U_fluid[j][2]         = U_fluid[j][0] * vertex_state.vely;
              Pressure[j]           = vertex_state.press;
              double kinetic_energy = 0.0;
              kinetic_energy += pow(vertex_state.velx, 2) + pow(vertex_state.vely, 2);
              kinetic_energy *= 0.5 * U_fluid[j][0];
              U_fluid[j][DIMS + 1] = kinetic_energy + Pressure[j] / (GAMMA_MINUS1);
#endif
              if(U_fluid[j][DIMS + 1] <= 0)
                {
                  printf(
                      "Energy <= 0 error: Task = %d, Triangle index = %d, SphP index = %d, ID = %d  \n Coordinates = %f, %f, %f, "
                      "Energies:  %f  %f  %f  %f\n",
                      ThisTask, thistask_triangles[i], SphP_index, P[SphP_index].ID, P[SphP_index].Pos[0], P[SphP_index].Pos[1],
                      P[SphP_index].Pos[2], U_fluid[j][DIMS + 1], SphP[SphP_index].Energy, kinetic_energy, Pressure[j]);

                  printf("print info for this particle:  %f %f %f    %f %f %f     %f   %f\n", P[SphP_index].Vel[0],
                         P[SphP_index].Vel[1], P[SphP_index].Vel[2], vertex_state.velx, vertex_state.vely, vertex_state.velz,
                         vertex_state.rho, kinetic_energy);

                  printf("density:  %f \n", SphP[SphP_index].Density);

                  terminate_program("Energy <= 0 error.");
                }

#ifdef TREE_BASED_TIMESTEPS
              C_sound[j] = SphP[SphP_index].Csnd;
#else
              C_sound[j] = get_sound_speed(SphP_index);
#endif
              if(C_sound[j] <= 0)
                {
                  terminate_program("sph Cs <= 0 error!");
                }
            }
          else
            {
              int PrimExch_index = DP[DT[thistask_triangles[i]].p[j]].index;

              struct grad_data *grad = &GradExch[PrimExch_index];
              struct state_primitive vertex_state;
              struct state_primitive delta_time;

              vertex_state.rho        = PrimExch[PrimExch_index].Density;
              vertex_state.press      = PrimExch[PrimExch_index].Pressure;
              vertex_state.velx       = PrimExch[PrimExch_index].VelGas[0];
              vertex_state.vely       = PrimExch[PrimExch_index].VelGas[1];
              vertex_state.velz       = PrimExch[PrimExch_index].VelGas[2];
#ifdef RD_RK2_TOTAL_RESIDUAL
              (void)grad;
              (void)delta_time;
              if(rd_stage == 1
#ifdef RD_RK2_RATE_CONSISTENT_HEUN
                 || rd_stage == 3
#endif
              )
                for(k = 0; k < 4; k++)
                  dU_vertex[j][k] = PrimExch[PrimExch_index].RD_dU[k];
#else
              double dt_Extrapolation = All.Time - PrimExch[PrimExch_index].TimeLastPrimUpdate;
              rd_record_dt_extrapolation(dt_Extrapolation);

              vertex_state.velx -= PrimExch[PrimExch_index].VelVertex[0];
              vertex_state.vely -= PrimExch[PrimExch_index].VelVertex[1];
              vertex_state.velz -= PrimExch[PrimExch_index].VelVertex[2];
              triangle_vertex_do_time_extrapolation(&delta_time, &vertex_state, grad, dt_Extrapolation);
              triangle_vertex_add_extrapolation(&delta_time, &vertex_state);
              vertex_state.velx += PrimExch[PrimExch_index].VelVertex[0];
              vertex_state.vely += PrimExch[PrimExch_index].VelVertex[1];
              vertex_state.velz += PrimExch[PrimExch_index].VelVertex[2];
#endif

              Velvertex_avg[0] += PrimExch[PrimExch_index].VelVertex[0];
              Velvertex_avg[1] += PrimExch[PrimExch_index].VelVertex[1];
              Velvertex_avg[2] += PrimExch[PrimExch_index].VelVertex[2];

              /*we should only use primitive variables to get U_fluid*/

#ifdef TWODIMS
              U_fluid[j][0]         = vertex_state.rho;
              U_fluid[j][1]         = U_fluid[j][0] * vertex_state.velx;
              U_fluid[j][2]         = U_fluid[j][0] * vertex_state.vely;
              Pressure[j]           = vertex_state.press;
              double kinetic_energy = 0.0;
              kinetic_energy += pow(vertex_state.velx, 2) + pow(vertex_state.vely, 2);
              kinetic_energy *= 0.5 * U_fluid[j][0];
              U_fluid[j][DIMS + 1] = kinetic_energy + Pressure[j] / (GAMMA_MINUS1);
#endif

              C_sound[j] = PrimExch[PrimExch_index].Csnd;

              if(C_sound[j] <= 0)
                {
                  terminate_program("primexch Cs <= 0 error!");
                }
              if(U_fluid[j][DIMS + 1] <= 0)
                {
                  printf("primexch energy <= 0 error %d %d  %d %d %d    %f  %f\n", ThisTask, DT[thistask_triangles[i]].p[j],
                         DP[DT[thistask_triangles[i]].p[j]].task, DP[DT[thistask_triangles[i]].p[j]].originalindex,
                         DP[DT[thistask_triangles[i]].p[j]].ID, U_fluid[j][DIMS + 1], PrimExch[PrimExch_index].Energy);
                  terminate_program("primexch energy <= 0 error.");
                }
            }
#ifdef RD_HIERARCHICAL_TIMESTEPS
          if(rd_stage == RD_RK_STAGE_CORRECTOR)
            {
              point *stage_point = &DP[DT[thistask_triangles[i]].p[j]];

              if(rd_point_stage_live(stage_point))
                {
                  if(rd_point_predictor_end(stage_point) != All.Ti_Current)
                    {
                      printf("RD predictor endpoint mismatch: task=%d triangle=%d ID=%llu expected=%lld got=%lld\n", ThisTask,
                             thistask_triangles[i], (unsigned long long)stage_point->ID, (long long)All.Ti_Current,
                             (long long)rd_point_predictor_end(stage_point));
                      terminate_program("RD hierarchy consumed a stale or missing predictor");
                    }

                  for(k = 0; k < 4; k++)
                    U_fluid[j][k] += dU_vertex[j][k];
                }

              double stage_rho = U_fluid[j][0];
              double stage_mom2 = U_fluid[j][1] * U_fluid[j][1] + U_fluid[j][2] * U_fluid[j][2];
              double stage_press = GAMMA_MINUS1 * (U_fluid[j][3] - 0.5 * stage_mom2 / stage_rho);

              if(!isfinite(stage_rho) || !isfinite(stage_press) || stage_rho <= 0.0 || stage_press <= 0.0)
                {
                  printf("RD hierarchy predictor invalid: task=%d triangle=%d ID=%llu rho=%.17g press=%.17g live=%d\n", ThisTask,
                         thistask_triangles[i], (unsigned long long)stage_point->ID, stage_rho, stage_press,
                         rd_point_stage_live(stage_point));
                  terminate_program("RD hierarchy produced a non-physical stage state");
                }

              Pressure[j] = stage_press;
              C_sound[j]  = sqrt(GAMMA * stage_press / stage_rho);
              RD_stat_min_stage_rho   = dmin(RD_stat_min_stage_rho, stage_rho);
              RD_stat_min_stage_press = dmin(RD_stat_min_stage_press, stage_press);
            }
#endif
        }  // for(j = 0; j < DIMS + 1; j++) get fluid state for each vertex of this triangle

      Velvertex_avg[0] /= (DIMS + 1);
      Velvertex_avg[1] /= (DIMS + 1);
      Velvertex_avg[2] /= (DIMS + 1);

      // compute residuals: Roe Vector Z, Modified fluid state U_hat = \frac{ \partial{U(Z_avg)}}{ \partial Z} * Z
#ifdef TWODIMS  // for now we only consider 2D. 3D case needs to be included in the future
      double Z_Roe[3][4];
      double Z_avg[4];
      double Enthalpy[DIMS + 1];
      double N_X[3], N_Y[3], Mag[3];
      double U_hat[4][3];  // notice: now U_hat[4][3] and Z_Roe[3][4] We may unify their formats in the future

      for(j = 0; j < 3; j++)
        {
          Z_Roe[j][0] = sqrt(U_fluid[j][0]);
          Z_Roe[j][1] = U_fluid[j][1] / Z_Roe[j][0];
          Z_Roe[j][2] = U_fluid[j][2] / Z_Roe[j][0];
          Z_Roe[j][3] = (U_fluid[j][3] + Pressure[j]) / Z_Roe[j][0];

          N_X[j]      = tri_normals_list[i].normal[j][0];
          N_Y[j]      = tri_normals_list[i].normal[j][1];
          Mag[j]      = tri_normals_list[i].mag[j];
          Enthalpy[j] = (U_fluid[j][DIMS + 1] + Pressure[j]) / U_fluid[j][0];  // specific enthalpy = (rho E + p)/rho
        }

      for(k = 0; k < 4; k++)
        Z_avg[k] = (Z_Roe[0][k] + Z_Roe[1][k] + Z_Roe[2][k]) / 3.0;

      for(j = 0; j < 3; j++)
        {
          U_hat[0][j] = 2.0 * Z_avg[0] * Z_Roe[j][0];
          U_hat[1][j] = Z_avg[1] * Z_Roe[j][0] + Z_avg[0] * Z_Roe[j][1];
          U_hat[2][j] = Z_avg[2] * Z_Roe[j][0] + Z_avg[0] * Z_Roe[j][2];
          U_hat[3][j] = (Z_avg[3] * Z_Roe[j][0] + GAMMA_MINUS1 * Z_avg[1] * Z_Roe[j][1] + GAMMA_MINUS1 * Z_avg[2] * Z_Roe[j][2] +
                         Z_avg[0] * Z_Roe[j][3]) /
                        (GAMMA);
        }

      // compute residual: Construct average state for element
      double sum_sqrt_rho = sqrt(U_fluid[0][0]) + sqrt(U_fluid[1][0]) + sqrt(U_fluid[2][0]);
      double rho_avg      = pow(sum_sqrt_rho / 3.0, 2);
      double velx_avg = 0, vely_avg = 0, h_avg = 0;
      for(j = 0; j < 3; j++)
        {
          velx_avg += sqrt(U_fluid[j][0]) * U_fluid[j][1] / U_fluid[j][0];
          vely_avg += sqrt(U_fluid[j][0]) * U_fluid[j][2] / U_fluid[j][0];
          h_avg += sqrt(U_fluid[j][0]) * Enthalpy[j];
        }
      velx_avg /= sum_sqrt_rho;
      vely_avg /= sum_sqrt_rho;
      h_avg /= sum_sqrt_rho;

      double Cs_avg = sqrt(GAMMA_MINUS1 * (h_avg - (velx_avg * velx_avg + vely_avg * vely_avg) / 2.0));

      /* Every entry of K is divided by Cs_avg, so Cs_avg == 0 poisons the
       * matrix with infinities without ever producing a NaN here; isnan()
       * alone therefore lets the failure through to LAPACK, which reports it
       * as the opaque "illegal argument 5" of its own non-finite input check.
       * Guard the whole element state instead, and report the vertex that
       * caused it -- on this path the usual cause is a predictor state that is
       * admissible per cell but not as a Roe average. */
      if(!(Cs_avg > 0) || !isfinite(Cs_avg))
        {
#ifdef RD_RK2_TOTAL_RESIDUAL
          int rd_bad_stage = rd_stage;
#else
          int rd_bad_stage = -1;
#endif
          printf(
              "RD element state invalid: task=%d triangle=%d stage=%d Cs_avg=%.17g h_avg=%.17g velx_avg=%.17g vely_avg=%.17g\n",
              ThisTask, thistask_triangles[i], rd_bad_stage, Cs_avg, h_avg, velx_avg, vely_avg);
          for(j = 0; j < DIMS + 1; j++)
            {
              int pt = DT[thistask_triangles[i]].p[j];
              printf("  vertex %d ID=%llu rho=%.17g p=%.17g H=%.17g vx=%.17g vy=%.17g x=%.17g y=%.17g task=%d\n", j,
                     (unsigned long long)DP[pt].ID, U_fluid[j][0], Pressure[j], Enthalpy[j], U_fluid[j][1] / U_fluid[j][0],
                     U_fluid[j][2] / U_fluid[j][0], DP[pt].x, DP[pt].y, DP[pt].task);
            }
          terminate_program("RD element Roe average is not a valid state");
        }

      // compute residual: Reassign variables to local equivalents
      double velx_c  = velx_avg / Cs_avg;
      double vely_c  = vely_avg / Cs_avg;
      double h_c     = h_avg / Cs_avg;
      double alpha   = GAMMA_MINUS1 * (velx_avg * velx_avg + vely_avg * vely_avg) / 2.0;
      double alpha_c = alpha / Cs_avg;

      // compute residual: Calculate K+,K- and K matrices for each vertex
      double vel_dot_n, velvertex_dot_n;
      double Lambda[3][4], Lambda_plus[3][4], Lambda_minus[3][4];
      double Value1, Value2, Value3, Value4, Value12, Value123;
      double Kmatrix[4][4][3][3];  // Kmatrix[4][4][j=0,1,2(vertices)][p=0(K+),1(K-),2(K)]
      int kfull = 2, kplus = 0, kminus = 1;

      // moving mesh

      for(j = 0; j < 3; j++)
        {
          vel_dot_n       = velx_avg * N_X[j] + vely_avg * N_Y[j];
          velvertex_dot_n = Velvertex_avg[0] * N_X[j] + Velvertex_avg[1] * N_Y[j];

          Lambda[j][0] = vel_dot_n + Cs_avg - velvertex_dot_n;
          Lambda[j][1] = vel_dot_n - Cs_avg - velvertex_dot_n;
          Lambda[j][2] = vel_dot_n - velvertex_dot_n;
          Lambda[j][3] = vel_dot_n - velvertex_dot_n;

          for(k = 0; k < 4; k++)
            {
              Lambda_plus[j][k]  = dmax(0.0, Lambda[j][k]);
              Lambda_minus[j][k] = dmin(0.0, Lambda[j][k]);
            }
          // fill in Kmatrix[4][4][j][p]
          for(p = 0; p < 3; p++)
            {
              if(p == 0)
                {  // Identify and select positive eigenvalues
                  Value1 = Lambda_plus[j][0];
                  Value2 = Lambda_plus[j][1];
                  Value3 = Lambda_plus[j][2];
                  Value4 = Lambda_plus[j][3];
                }
              else if(p == 1)
                {  // Identify and select negative eigenvalues
                  Value1 = Lambda_minus[j][0];
                  Value2 = Lambda_minus[j][1];
                  Value3 = Lambda_minus[j][2];
                  Value4 = Lambda_minus[j][3];
                }
              else
                {  // Select all eigenvalues
                  Value1 = Lambda[j][0];
                  Value2 = Lambda[j][1];
                  Value3 = Lambda[j][2];
                  Value4 = Lambda[j][3];
                }

              Value12  = (Value1 - Value2) / 2.0;
              Value123 = (Value1 + Value2 - 2.0 * Value3) / 2.0;

              Kmatrix[0][0][j][p] = 0.5 * Mag[j] * (alpha_c * Value123 / Cs_avg - vel_dot_n * Value12 / Cs_avg + Value3);
              Kmatrix[0][1][j][p] = 0.5 * Mag[j] * (-1.0 * GAMMA_MINUS1 * velx_c * Value123 / Cs_avg + N_X[j] * Value12 / Cs_avg);
              Kmatrix[0][2][j][p] = 0.5 * Mag[j] * (-1.0 * GAMMA_MINUS1 * vely_c * Value123 / Cs_avg + N_Y[j] * Value12 / Cs_avg);
              Kmatrix[0][3][j][p] = 0.5 * Mag[j] * (GAMMA_MINUS1 * Value123 / (Cs_avg * Cs_avg));

              Kmatrix[1][0][j][p] =
                  0.5 * Mag[j] *
                  ((alpha_c * velx_c - vel_dot_n * N_X[j]) * Value123 + (alpha_c * N_X[j] - velx_c * vel_dot_n) * Value12);
              Kmatrix[1][1][j][p] = 0.5 * Mag[j] *
                                    ((N_X[j] * N_X[j] - GAMMA_MINUS1 * velx_c * velx_c) * Value123 -
                                     ((GAMMA - 2.0) * velx_c * N_X[j] * Value12) + Value3);
              Kmatrix[1][2][j][p] = 0.5 * Mag[j] *
                                    ((N_X[j] * N_Y[j] - GAMMA_MINUS1 * velx_c * vely_c) * Value123 +
                                     (velx_c * N_Y[j] - GAMMA_MINUS1 * vely_c * N_X[j]) * Value12);
              Kmatrix[1][3][j][p] =
                  0.5 * Mag[j] * (GAMMA_MINUS1 * velx_c * Value123 / Cs_avg + GAMMA_MINUS1 * N_X[j] * Value12 / Cs_avg);

              Kmatrix[2][0][j][p] =
                  0.5 * Mag[j] *
                  ((alpha_c * vely_c - vel_dot_n * N_Y[j]) * Value123 + (alpha_c * N_Y[j] - vely_c * vel_dot_n) * Value12);
              Kmatrix[2][1][j][p] = 0.5 * Mag[j] *
                                    ((N_X[j] * N_Y[j] - GAMMA_MINUS1 * velx_c * vely_c) * Value123 +
                                     (vely_c * N_X[j] - GAMMA_MINUS1 * velx_c * N_Y[j]) * Value12);
              Kmatrix[2][2][j][p] = 0.5 * Mag[j] *
                                    ((N_Y[j] * N_Y[j] - GAMMA_MINUS1 * vely_c * vely_c) * Value123 -
                                     ((GAMMA - 2.0) * vely_c * N_Y[j] * Value12) + Value3);
              Kmatrix[2][3][j][p] =
                  0.5 * Mag[j] * (GAMMA_MINUS1 * vely_c * Value123 / Cs_avg + GAMMA_MINUS1 * N_Y[j] * Value12 / Cs_avg);

              Kmatrix[3][0][j][p] =
                  0.5 * Mag[j] * ((alpha_c * h_c - vel_dot_n * vel_dot_n) * Value123 + vel_dot_n * (alpha_c - h_c) * Value12);
              Kmatrix[3][1][j][p] = 0.5 * Mag[j] *
                                    ((vel_dot_n * N_X[j] - velx_avg - alpha_c * velx_c) * Value123 +
                                     (h_c * N_X[j] - GAMMA_MINUS1 * velx_c * vel_dot_n) * Value12);
              Kmatrix[3][2][j][p] = 0.5 * Mag[j] *
                                    ((vel_dot_n * N_Y[j] - vely_avg - alpha_c * vely_c) * Value123 +
                                     (h_c * N_Y[j] - GAMMA_MINUS1 * vely_c * vel_dot_n) * Value12);
              Kmatrix[3][3][j][p] =
                  0.5 * Mag[j] * (GAMMA_MINUS1 * h_c * Value123 / Cs_avg + GAMMA_MINUS1 * vel_dot_n * Value12 / Cs_avg + Value3);
            }
        }

      // compute residual: get residual Phi
      /* phi_scale is the pre-cancellation magnitude of Phi's own assembly.
       * In a quiet element the exact residual is zero and Phi is cancellation
       * noise of O(1) products, so any conservation identity involving it can
       * only hold to eps * phi_scale. Omitting this floor made A2 compare
       * noise against noise and fire on the uniform test at defect ~1e-33 --
       * the third instance of a quiet-element diagnostic without an absolute
       * floor. */
      double Phi[4];
      double phi_scale = 0.0;
      for(k = 0; k < 4; k++)
        {
          Phi[k] = 0.0;
          for(j = 0; j < 3; j++)
            {
              Phi[k] += Kmatrix[k][0][j][kfull] * U_hat[0][j] + Kmatrix[k][1][j][kfull] * U_hat[1][j] +
                        Kmatrix[k][2][j][kfull] * U_hat[2][j] + Kmatrix[k][3][j][kfull] * U_hat[3][j];

              for(p = 0; p < 4; p++)
                phi_scale += fabs(Kmatrix[k][p][j][kfull]) * fabs(U_hat[p][j]);
            }

#ifdef RD_RK2_COHERENT_BETA_STAR
          if(rd_stage == 0)
            rd_phi_stage0[i][k] = Phi[k];
#endif
        }

      /* S^- = sum_{j in T} K_j^-  (thesis notation, chapter 3) */
      double Sminus[4][4];

      for(k = 0; k < 4; k++)
        {
          for(p = 0; p < 4; p++)
            {
              Sminus[k][p] = 0.0;
              for(j = 0; j < 3; j++)
                {
                  Sminus[k][p] += Kmatrix[k][p][j][kminus];
                }
            }
        }

#ifdef RD_DEBUG_ASSERTS
      rd_assert_K_sum_vanishes(Kmatrix, kfull, thistask_triangles[i]);
#endif

      /* Solve the upwind system instead of forming (S^-)^-1 explicitly.
       * Both schemes need a solve against the same matrix:
       *   LDA:  x = (S^-)^dagger phi^T
       *   N:    y = (S^-)^dagger b,   b = sum_j K_j^- Uhat_j
       * One factorisation therefore serves both, and no regularisation of
       * S^- is required.  See dev_log/regularize_matrix_debug_report.md. */
      /* The row stride must equal the LAPACK ldb/RD_UPWIND_NRHS. The default
       * path has the historical three columns. Coherent beta^n appends an
       * identity to construct beta explicitly at stage 0; coherent beta*
       * appends saved Phi(U^n) at stage 1. */
      double rhs[4][RD_UPWIND_NRHS];

      for(k = 0; k < 4; k++)
        {
          for(int column = 0; column < RD_UPWIND_NRHS; column++)
            rhs[k][column] = 0.0;

          rhs[k][0] = Phi[k];

          for(j = 0; j < 3; j++)
            {
              rhs[k][1] += Kmatrix[k][0][j][kminus] * U_hat[0][j] + Kmatrix[k][1][j][kminus] * U_hat[1][j] +
                           Kmatrix[k][2][j][kminus] * U_hat[2][j] + Kmatrix[k][3][j][kminus] * U_hat[3][j];
            }

#ifdef RD_RK2_COHERENT_BETA_N
          for(int column = 0; column < 4; column++)
            rhs[k][3 + column] = (k == column) ? 1.0 : 0.0;
#endif
#ifdef RD_RK2_COHERENT_BETA_STAR
          if(rd_stage == 1)
            rhs[k][3] = rd_phi_stage0[i][k];
#endif
        }

#if defined(RD_RK2_TOTAL_RESIDUAL) && (defined(LDA_SCHEME) || defined(B_SCHEME))
      /* Third right-hand side: the F1 temporal target (|T|/3) sum_j dU_j/dt.
       * beta_i only ever multiplies a vector, so T_i = -K_i^+ z with
       * S^- z = target reuses the factorisation (one extra back-substitution,
       * no beta tensor) and inherits the rank policy (Kimi amendment 2). */
      if(rd_stage == 1
#ifdef RD_RK2_RATE_CONSISTENT_HEUN
         || rd_stage == 3
#endif
      )
        {
#ifdef RD_RK2_RATE_CONSISTENT_HEUN
          /* RD_dU is already the nodal spatial rate v for a mass-apply pass. */
          for(k = 0; k < 4; k++)
            rhs[k][2] =
                (tri_normals_list[i].area / 3.0) * (dU_vertex[0][k] + dU_vertex[1][k] + dU_vertex[2][k]);
#else
          double f1_interval = triangle_dt;
#ifdef RD_HIERARCHICAL_TIMESTEPS
          /* The ledger call carries half weight, but dU is the predictor over
           * the complete triangle interval h_T. */
          f1_interval = full_triangle_dt;
#endif
          for(k = 0; k < 4; k++)
            rhs[k][2] =
                (tri_normals_list[i].area / 3.0) * (dU_vertex[0][k] + dU_vertex[1][k] + dU_vertex[2][k]) / f1_interval;
#endif
        }
#endif

#ifdef RD_DIAG_TRACE_ELEMENT
      /* diagnostic only: full-precision dump of one element's inputs/outputs */
      int rd_trace = 0;
      for(j = 0; j < DIMS + 1; j++)
        if(DP[DT[thistask_triangles[i]].p[j]].ID == 1908)
          rd_trace = 1;
      if(rd_trace)
        {
          printf("RD-TRACE stage=%d elem_minid: ", rd_stage);
          for(j = 0; j < DIMS + 1; j++)
            printf("[ID=%llu rho=%.17g p=%.17g u=%.17g cs=%.17g] ", (unsigned long long)DP[DT[thistask_triangles[i]].p[j]].ID,
                   U_fluid[j][0], Pressure[j], U_fluid[j][1] / U_fluid[j][0], C_sound[j]);
          printf("Phi0=%.17g Phi3=%.17g dt=%.17g\n", Phi[0], Phi[3], triangle_dt);
          for(j = 0; j < DIMS + 1; j++)
            {
              int pt = DT[thistask_triangles[i]].p[j];
              printf("RD-TRACE-V stage=%d ID=%llu v=%.17g dU0=%.17g dU1=%.17g dU3=%.17g x=%.17g y=%.17g task=%d idx=%d\n",
                     rd_stage, (unsigned long long)DP[pt].ID, U_fluid[j][2] / U_fluid[j][0],
#ifdef RD_RK2_TOTAL_RESIDUAL
                     (rd_stage == 1) ? dU_vertex[j][0] : 0.0, (rd_stage == 1) ? dU_vertex[j][1] : 0.0,
                     (rd_stage == 1) ? dU_vertex[j][3] : 0.0,
#else
                     0.0, 0.0, 0.0,
#endif
                     DP[pt].x, DP[pt].y, DP[pt].task, DP[pt].index);
            }
          printf("RD-TRACE-VV stage=%d velvtx=%.17g %.17g\n", rd_stage, Velvertex_avg[0], Velvertex_avg[1]);
        }
#endif
      lapack_int solve_rank = -1;
      lapack_int solve_info = rd_solve_upwind_system(Sminus, &rhs[0][0], RD_UPWIND_NRHS, &solve_rank);
      (void)solve_rank;

      if(solve_info != 0)
        {
          printf("RD upwind solve failed on task %d, triangle %d, LAPACK info %d\n", ThisTask, thistask_triangles[i],
                 (int)solve_info);
          /* A negative info is LAPACKE rejecting an argument; for DGELSD,
           * info = -5 is its own non-finite check on the matrix. Dump every
           * input that feeds S^-, so the failure names its own cause instead
           * of being reported as an opaque illegal argument. */
          printf("  Cs_avg=%.17g h_avg=%.17g vel_avg=%.17g %.17g velvertex_avg=%.17g %.17g\n", Cs_avg, h_avg, velx_avg, vely_avg,
                 Velvertex_avg[0], Velvertex_avg[1]);
          for(int jj = 0; jj < DIMS + 1; jj++)
            {
              int pt = DT[thistask_triangles[i]].p[jj];
              printf("  vertex %d ID=%llu rho=%.17g p=%.17g H=%.17g mag=%.17g n=%.17g %.17g lam=%.17g %.17g %.17g x=%.17g "
                     "y=%.17g task=%d\n",
                     jj, (unsigned long long)DP[pt].ID, U_fluid[jj][0], Pressure[jj], Enthalpy[jj], Mag[jj], N_X[jj], N_Y[jj],
                     Lambda[jj][0], Lambda[jj][1], Lambda[jj][2], DP[pt].x, DP[pt].y, DP[pt].task);
            }
          for(int r = 0; r < 4; r++)
            printf("  Sminus[%d] = %.17g %.17g %.17g %.17g\n", r, Sminus[r][0], Sminus[r][1], Sminus[r][2], Sminus[r][3]);
          terminate_program("RD upwind solve failed");
        }

#ifdef RD_RK2_COHERENT_BETA_N
      if(rd_stage == 0)
        {
          if(solve_rank != 4)
            {
              printf("RD coherent beta^n undefined: task=%d triangle=%d numerical_rank=%d\n", ThisTask, thistask_triangles[i],
                     (int)solve_rank);
              terminate_program("RD coherent beta^n experiment requires full-rank S^- at stage 0");
            }

          /* beta_i = -K_i^+ (S^-)^-1. Identity columns 3,...,6 of rhs now
           * contain (S^-)^-1, so save the complete operator for stage 1. */
          for(j = 0; j < 3; j++)
            for(k = 0; k < 4; k++)
              for(int column = 0; column < 4; column++)
                {
                  rd_beta_stage0[i][j][k][column] = 0.0;
                  for(p = 0; p < 4; p++)
                    rd_beta_stage0[i][j][k][column] -= Kmatrix[k][p][j][kplus] * rhs[p][3 + column];
                }
        }
#endif

      RD_stat_elements++;

#if(defined(LDA_SCHEME) || defined(B_SCHEME))
      double X_lda[4]; /* x = (S^-)^dagger phi^T */
      for(k = 0; k < 4; k++)
        X_lda[k] = rhs[k][0];
#endif

#if(defined(N_SCHEME) || defined(B_SCHEME))
      double Y_in[4]; /* y = (S^-)^dagger b, the N-scheme inflow state Uhat_in^T */
      for(k = 0; k < 4; k++)
        Y_in[k] = rhs[k][1];
#endif

      double Flux_RD[4][3];
#ifdef B_SCHEME
      double Flux_LDA[4][3], Flux_N[4][3];
#endif

#if(defined(LDA_SCHEME) || defined(B_SCHEME))
      /* phi_i^{LDA,T} = -K_i^+ x,  with x = (S^-)^dagger phi^T.  This is the
       * same operator as beta_i^{LDA,T} phi^T = -K_i^+ (S^-)^-1 phi^T, but it
       * never forms the inverse, so it stays well defined when S^- is
       * singular. */
      double LDA_roundoff_scale = 0.0;
      for(k = 0; k < 4; k++)
        {
          double equation_scale = fabs(Phi[k]);

          for(j = 0; j < 3; j++)
            {
              for(p = 0; p < 4; p++)
                equation_scale += fabs(Kmatrix[k][p][j][kplus]) * fabs(X_lda[p]);

              double flux_lda = -1.0 * (Kmatrix[k][0][j][kplus] * X_lda[0] + Kmatrix[k][1][j][kplus] * X_lda[1] +
                                        Kmatrix[k][2][j][kplus] * X_lda[2] + Kmatrix[k][3][j][kplus] * X_lda[3]);
#ifdef LDA_SCHEME
              Flux_RD[k][j] = flux_lda;
#else
              Flux_LDA[k][j] = flux_lda;
#endif
            }

          LDA_roundoff_scale = dmax(LDA_roundoff_scale, equation_scale);
        }

#ifdef LDA_SCHEME
      rd_check_conservation(Flux_RD, Phi, LDA_roundoff_scale + phi_scale, thistask_triangles[i], "LDA");
#else
      rd_check_conservation(Flux_LDA, Phi, LDA_roundoff_scale + phi_scale, thistask_triangles[i], "LDA");
#endif

#endif  // LDA scheme or B scheme

#if(defined(N_SCHEME) || defined(B_SCHEME))

      double Bracket[4][3];
      double N_roundoff_scale = 0.0;

      for(k = 0; k < 4; k++)
        {
          for(j = 0; j < 3; j++)
            {
              Bracket[k][j] = U_hat[k][j] - Y_in[k];
            }
        }

      for(k = 0; k < 4; k++)
        {
          double equation_scale = fabs(Phi[k]);

          for(j = 0; j < 3; j++)
            {
              for(p = 0; p < 4; p++)
                equation_scale +=
                    fabs(Kmatrix[k][p][j][kplus]) * (fabs(U_hat[p][j]) + fabs(Y_in[p]));

#ifdef N_SCHEME
              Flux_RD[k][j] = Kmatrix[k][0][j][kplus] * Bracket[0][j] + Kmatrix[k][1][j][kplus] * Bracket[1][j] +
                              Kmatrix[k][2][j][kplus] * Bracket[2][j] + Kmatrix[k][3][j][kplus] * Bracket[3][j];
#else
              Flux_N[k][j] = Kmatrix[k][0][j][kplus] * Bracket[0][j] + Kmatrix[k][1][j][kplus] * Bracket[1][j] +
                             Kmatrix[k][2][j][kplus] * Bracket[2][j] + Kmatrix[k][3][j][kplus] * Bracket[3][j];
#endif
              // #ifdef N_SCHEME
              //               Flux_RD[k][j] = Kmatrix[k][0][j][kplus] * UminusX[0][j] + Kmatrix[k][1][j][kplus] * UminusX[1][j] +
              //                               Kmatrix[k][2][j][kplus] * UminusX[2][j] + Kmatrix[k][3][j][kplus] * UminusX[3][j];
              // #else
              //               Flux_N[k][j] = Kmatrix[k][0][j][kplus] * UminusX[0][j] + Kmatrix[k][1][j][kplus] * UminusX[1][j] +
              //                              Kmatrix[k][2][j][kplus] * UminusX[2][j] + Kmatrix[k][3][j][kplus] * UminusX[3][j];
              // #endif
            }

          N_roundoff_scale = dmax(N_roundoff_scale, equation_scale);
        }

#ifdef N_SCHEME
      rd_check_conservation(Flux_RD, Phi, N_roundoff_scale + phi_scale, thistask_triangles[i], "N");
#else
      rd_check_conservation(Flux_N, Phi, N_roundoff_scale + phi_scale, thistask_triangles[i], "N");
#endif

#endif  // N scheme or B scheme

#ifdef B_SCHEME
      double Sum_Flux_N[4];
      double Theta_E[4];
      double B_roundoff_scale = 0.0;

      for(k = 0; k < 4; k++)
        {
          Sum_Flux_N[k] = fabs(Flux_N[k][0]) + fabs(Flux_N[k][1]) + fabs(Flux_N[k][2]);
          if(Sum_Flux_N[k] == 0)
            {
              Theta_E[k] = 0.0;
            }
          else
            {
              Theta_E[k] = dmin(1.0, fabs(Phi[k]) / Sum_Flux_N[k]);
            }
#ifdef RD_DIAG_THETA
          rd_record_theta(0, Theta_E[k]);
#endif

          double equation_scale = fabs(Phi[k]);
          for(j = 0; j < 3; j++)
            equation_scale +=
                fabs(Theta_E[k] * Flux_N[k][j]) + fabs((1.0 - Theta_E[k]) * Flux_LDA[k][j]);

          Flux_RD[k][0] = Theta_E[k] * Flux_N[k][0] + (1.0 - Theta_E[k]) * Flux_LDA[k][0];
          Flux_RD[k][1] = Theta_E[k] * Flux_N[k][1] + (1.0 - Theta_E[k]) * Flux_LDA[k][1];
          Flux_RD[k][2] = Theta_E[k] * Flux_N[k][2] + (1.0 - Theta_E[k]) * Flux_LDA[k][2];

          B_roundoff_scale = dmax(B_roundoff_scale, equation_scale);
        }

      B_roundoff_scale = dmax(B_roundoff_scale, dmax(LDA_roundoff_scale, N_roundoff_scale));
      rd_check_conservation(Flux_RD, Phi, B_roundoff_scale + phi_scale, thistask_triangles[i], "B");

#ifdef RD_RK2_INTERNAL_LOOP
      if(rd_stage == 0)
        {
          /* Preserve the undisguised N and LDA pieces. Once the predictor has
           * been assembled, the nodal dU shortcut cannot reconstruct these
           * element-local stage-0 distributions. */
          memcpy(rd_b_flux_n_stage0[i], Flux_N, sizeof(rd_b_flux_n_stage0[i]));
          memcpy(rd_b_flux_lda_stage0[i], Flux_LDA, sizeof(rd_b_flux_lda_stage0[i]));
          memcpy(rd_b_phi_stage0[i], Phi, sizeof(rd_b_phi_stage0[i]));
        }
#endif

#endif  // B scheme

#ifdef RD_RK2_RATE_CONSISTENT_HEUN
      if(rd_stage == 1 || rd_stage == 3)
        {
          /* Replace the spatial LDA distribution by M(U)v. The solved third
           * column is (S^-)^-1 [(|T|/3) sum_j v_j], so -K_i^+ times it is the
           * F1 mass-matrix action. A rank-deficient element uses the same
           * conservative lumped fallback as the total-residual path. */
          double mass_target[4];
          double mass_scale = 0.0;

          for(k = 0; k < 4; k++)
            mass_target[k] =
                (tri_normals_list[i].area / 3.0) * (dU_vertex[0][k] + dU_vertex[1][k] + dU_vertex[2][k]);

          if(solve_rank == 4)
            {
              for(k = 0; k < 4; k++)
                for(j = 0; j < 3; j++)
                  {
                    Flux_RD[k][j] = -1.0 * (Kmatrix[k][0][j][kplus] * rhs[0][2] + Kmatrix[k][1][j][kplus] * rhs[1][2] +
                                             Kmatrix[k][2][j][kplus] * rhs[2][2] + Kmatrix[k][3][j][kplus] * rhs[3][2]);
                    for(p = 0; p < 4; p++)
                      mass_scale += fabs(Kmatrix[k][p][j][kplus]) * fabs(rhs[p][2]);
                  }
            }
          else
            {
              RD_stat_f1_lumped++;
              for(k = 0; k < 4; k++)
                for(j = 0; j < 3; j++)
                  Flux_RD[k][j] = (tri_normals_list[i].area / 3.0) * dU_vertex[j][k];
            }

          for(k = 0; k < 4; k++)
            mass_scale += fabs(mass_target[k]);

          /* On a quiescent element the nodal rates, mass target and solved
           * F1 action can all cancel down to near-zero-scale noise.  Scaling
           * A2 by that cancelled result made its tolerance collapse to
           * O(1e-47) in the Sod gate even though the defect was only O(1e-36).
           * phi_scale is assembled from the uncancelled spatial products on
           * this same element, so it supplies a unit-consistent absolute
           * round-off floor without weakening the check at ordinary scale. */
          mass_scale = dmax(mass_scale, phi_scale);
          rd_check_conservation(Flux_RD, mass_target, mass_scale, thistask_triangles[i], "LDA-F1-mass-apply");
        }
#endif

#if defined(RD_RK2_INTERNAL_LOOP) && !defined(RD_RK2_RATE_CONSISTENT_HEUN)
      if(rd_stage == 1)
        {
          /* Corrector: replace the spatial distribution by the total nodal
           * residual. The LDA mixed and coherent-beta^n paths use the local
           * +dU/2 shortcut for the old spatial half; coherent-beta* and B
           * suppress it and add the old element residual explicitly. */
          double T_time[4][3];
          double T_target[4];
#ifdef RD_RK2_COHERENT_BETA_STAR
          double Phi_old_time[4][3];
#endif
          double rk2_scale = 0.0;

          for(k = 0; k < 4; k++)
            T_target[k] =
                (tri_normals_list[i].area / 3.0) * (dU_vertex[0][k] + dU_vertex[1][k] + dU_vertex[2][k]) / triangle_dt;

#ifdef LDA_SCHEME
          /* Global Lumping is the first Neumann truncation of the mass-matrix
           * inverse: with M = S(I + X), lumping gives u_dot = v, this scheme
           * gives u_dot = (I - X) v, and the consistent mass matrix would give
           * (I + X)^{-1} v. The truncated term X^2 v is O(h) rather than O(h^2)
           * wherever the median-dual patch asymmetry varies on the mesh scale,
           * which makes the scheme asymptotically first order for unsteady flow
           * on an irregular mesh. Measured: second order to n = 256 on a regular
           * triangular lattice, 1.48 at n = 384 on a glass, 0.99 at n = 256 on a
           * jittered Cartesian mesh.
           *
           * A glass is good enough at the resolutions currently in use. The
           * derivation, the measurements, the alternatives (iterating the
           * Neumann series to a tolerance; Selective Lumping; F2) and what does
           * *not* work are in dev_log/mass_matrix_order_analysis.md. Not a
           * current priority. */
#ifdef RD_RK2_COHERENT_BETA_N
          /* Freeze the complete distribution operator from stage 0. This
           * applies beta^n consistently to Phi(U*), the F1 target, and (via
           * the predictor identity/+dU/2) Phi(U^n). */
          for(k = 0; k < 4; k++)
            for(j = 0; j < 3; j++)
              {
                Flux_RD[k][j] = 0.0;
                T_time[k][j]  = 0.0;
                for(p = 0; p < 4; p++)
                  {
                    Flux_RD[k][j] += rd_beta_stage0[i][j][k][p] * Phi[p];
                    T_time[k][j] += rd_beta_stage0[i][j][k][p] * T_target[p];
                    rk2_scale += fabs(rd_beta_stage0[i][j][k][p]) * (fabs(Phi[p]) + fabs(T_target[p]));
                  }
              }
#else
#ifdef RD_RK2_COHERENT_BETA_STAR
          if(solve_rank != 4)
            {
              printf("RD coherent beta* undefined: task=%d triangle=%d numerical_rank=%d\n", ThisTask, thistask_triangles[i],
                     (int)solve_rank);
              terminate_program("RD coherent beta* experiment requires full-rank S^- at stage 1");
            }
#endif
          if(solve_rank == 4)
            {
              /* F1 mass matrix through the third right-hand side:
               * T_i = -K_i^+ z with S^- z = T_target. Conservation is the
               * identity sum_i K_i^+ = -S^- plus the solve residual. */
              double Z_f1[4];
              for(k = 0; k < 4; k++)
                Z_f1[k] = rhs[k][2];

              for(k = 0; k < 4; k++)
                for(j = 0; j < 3; j++)
                  {
                    T_time[k][j] = -1.0 * (Kmatrix[k][0][j][kplus] * Z_f1[0] + Kmatrix[k][1][j][kplus] * Z_f1[1] +
                                           Kmatrix[k][2][j][kplus] * Z_f1[2] + Kmatrix[k][3][j][kplus] * Z_f1[3]);

                    for(p = 0; p < 4; p++)
                      rk2_scale += fabs(Kmatrix[k][p][j][kplus]) * fabs(Z_f1[p]);
                  }

#ifdef RD_RK2_COHERENT_BETA_STAR
              /* Fourth solve column is (S^-*)^-1 Phi(U^n). Apply -K_i^+*
               * explicitly: the old residual must not enter through +dU/2,
               * which is the already assembled beta^n distribution. */
              double Z_old[4];
              for(k = 0; k < 4; k++)
                Z_old[k] = rhs[k][3];

              for(k = 0; k < 4; k++)
                for(j = 0; j < 3; j++)
                  {
                    Phi_old_time[k][j] =
                        -1.0 * (Kmatrix[k][0][j][kplus] * Z_old[0] + Kmatrix[k][1][j][kplus] * Z_old[1] +
                                Kmatrix[k][2][j][kplus] * Z_old[2] + Kmatrix[k][3][j][kplus] * Z_old[3]);

                    for(p = 0; p < 4; p++)
                      rk2_scale += 0.5 * fabs(Kmatrix[k][p][j][kplus]) * fabs(Z_old[p]);
                  }
#endif
            }
          else
            {
              /* Genuinely rank-deficient element (DGELSD resolved fewer than
               * four directions): beta_i is undefined there. The F1 temporal
               * target is an arbitrary vector, unprotected by Lemma 1, so
               * S^- z = T_target need not even be consistent, and no
               * generalized inverse can restore sum_i beta_i = I on a singular
               * S^-. The lumped mass is the unique conservative element-local
               * choice, so fall back to it and count the event.
               *
               * Rank, not "the SVD path was taken", is the criterion. Consistency
               * of S^- z = T_target is what is actually required and is stricter
               * still; rank < 4 approximates it from the safe side. */
              RD_stat_f1_lumped++;

              for(k = 0; k < 4; k++)
                for(j = 0; j < 3; j++)
                  T_time[k][j] = (tri_normals_list[i].area / 3.0) * dU_vertex[j][k] / triangle_dt;
            }
#endif /* !RD_RK2_COHERENT_BETA_N */
#elif defined(B_SCHEME)
          /* Blended mass matrix, Arpaia & Ricchiuto (2015) eqs. 43-44:
           *
           *     m_ij^B = (1 - l) m_ij^{LDA} + l (|T|/3) delta_ij ,
           *
           * with one blending parameter formed from the complete RK2 total
           * residual. The F1 term belongs to the LDA branch and the lumped
           * term to the N branch. The old and new spatial N/LDA distributions
           * are kept separately, so the same theta acts on every term.
           *
           * Each branch sums to
           *
           *   T_target + [Phi(U^n) + Phi(U*)]/2,
           *
           * so their convex blend is conservative for every theta. The
           * spatial-only B blend above remains the predictor distribution; it
           * is intentionally overwritten here for the corrector. */
          double T_f1[4][3], T_lumped[4][3];

          for(k = 0; k < 4; k++)
            for(j = 0; j < 3; j++)
              T_lumped[k][j] = (tri_normals_list[i].area / 3.0) * dU_vertex[j][k] / triangle_dt;

          if(solve_rank == 4)
            {
              double Z_f1[4];
              for(k = 0; k < 4; k++)
                Z_f1[k] = rhs[k][2];

              for(k = 0; k < 4; k++)
                for(j = 0; j < 3; j++)
                  {
                    T_f1[k][j] = -1.0 * (Kmatrix[k][0][j][kplus] * Z_f1[0] + Kmatrix[k][1][j][kplus] * Z_f1[1] +
                                         Kmatrix[k][2][j][kplus] * Z_f1[2] + Kmatrix[k][3][j][kplus] * Z_f1[3]);

                    for(p = 0; p < 4; p++)
                      rk2_scale += fabs(Kmatrix[k][p][j][kplus]) * fabs(Z_f1[p]);
                  }
            }
          else
            {
              /* beta_i is undefined, so the LDA half of the blend falls back to
               * the lumped mass -- the same conservative choice the LDA path
               * makes, and it leaves the blend well defined rather than
               * disabling it. */
              RD_stat_f1_lumped++;
              memcpy(T_f1, T_lumped, sizeof(T_f1));
            }

          for(k = 0; k < 4; k++)
            {
#ifdef RD_B_FROZEN_THETA
              /* Freeze the blending parameter within the step: build it from
               * stage-0 quantities only. T_target is (|T|/3) sum_j v_j and
               * Phi(U^n) is a stage-0 residual, so neither depends on dt, and
               * the discrete map becomes a smooth function of dt. The measured
               * Theta is a correct O(h) indicator (2026-08-03 entry); the
               * obstacle to a Richardson gate is only that recomputing it from
               * U* makes the blend coefficient dt dependent. A limiter's job is
               * to locate a discontinuity, which does not move appreciably in
               * one step, so freezing costs nothing it was providing. */
              double total_k = T_target[k] + rd_b_phi_stage0[i][k];
              double sum_n_tot = 0.0;

              for(j = 0; j < 3; j++)
                sum_n_tot += fabs(T_lumped[k][j] + rd_b_flux_n_stage0[i][k][j]);
#else
              double total_k = T_target[k] + 0.5 * (rd_b_phi_stage0[i][k] + Phi[k]);
              double sum_n_tot = 0.0;

              for(j = 0; j < 3; j++)
                sum_n_tot +=
                    fabs(T_lumped[k][j] + 0.5 * (rd_b_flux_n_stage0[i][k][j] + Flux_N[k][j]));
#endif

              double theta = (sum_n_tot == 0.0) ? 0.0 : dmin(1.0, fabs(total_k) / sum_n_tot);
#ifdef RD_DIAG_THETA
              rd_record_theta(1, theta);
#endif

              for(j = 0; j < 3; j++)
                {
                  T_time[k][j]  = theta * T_lumped[k][j] + (1.0 - theta) * T_f1[k][j];
                  Flux_RD[k][j] =
                      theta * (rd_b_flux_n_stage0[i][k][j] + Flux_N[k][j]) +
                      (1.0 - theta) * (rd_b_flux_lda_stage0[i][k][j] + Flux_LDA[k][j]);

                  rk2_scale += fabs(T_time[k][j]) + 0.5 * fabs(Flux_RD[k][j]);
                }
            }
#else /* N_SCHEME: the lumped mass IS the thesis choice m^N = (|T|/3) delta_ij */
          for(k = 0; k < 4; k++)
            for(j = 0; j < 3; j++)
              T_time[k][j] = (tri_normals_list[i].area / 3.0) * dU_vertex[j][k] / triangle_dt;
#endif

#ifdef RD_DIAG_ZERO_TEMPORAL /* diagnostic only: isolate the temporal term's contribution */
          for(k = 0; k < 4; k++)
            {
              T_target[k] = 0.0;
              for(j = 0; j < 3; j++)
                T_time[k][j] = 0.0;
            }
#endif
          double total_target[4];
          for(k = 0; k < 4; k++)
            {
              total_target[k] = T_target[k] + 0.5 * Phi[k];
#ifdef RD_RK2_COHERENT_BETA_STAR
              total_target[k] += 0.5 * rd_phi_stage0[i][k];
#endif
#ifdef B_SCHEME
              total_target[k] += 0.5 * rd_b_phi_stage0[i][k];
#endif

              rk2_scale += fabs(total_target[k]);
              for(j = 0; j < 3; j++)
                {
                  rk2_scale += fabs(T_time[k][j]);
                  Flux_RD[k][j] = T_time[k][j] + 0.5 * Flux_RD[k][j];
#ifdef RD_RK2_COHERENT_BETA_STAR
                  Flux_RD[k][j] += 0.5 * Phi_old_time[k][j];
#endif
                }
            }

#ifdef LDA_SCHEME
          rk2_scale += 0.5 * LDA_roundoff_scale;
#elif defined(B_SCHEME)
          rk2_scale += 0.5 * dmax(LDA_roundoff_scale, N_roundoff_scale);
#else
          rk2_scale += 0.5 * N_roundoff_scale;
#endif

          rd_check_conservation(Flux_RD, total_target, rk2_scale + 0.5 * phi_scale, thistask_triangles[i], "RK2-total");
        }
#endif /* RD_RK2_INTERNAL_LOOP && !RD_RK2_RATE_CONSISTENT_HEUN */

#if defined(RD_HIERARCHICAL_TIMESTEPS) && defined(LDA_SCHEME)
      if(rd_stage == RD_RK_STAGE_CORRECTOR)
        {
          /* Frozen-dU multirate F1 experiment.
           *
           * The opening call has already applied -h_T phi_i(U^n)/2 and
           * assembled the full vertex predictor dU.  To reproduce the
           * concentrated mixed-beta LDA+F1 corrector when all bins are equal,
           * the closing ledger contribution is
           *
           *   |T| dU_i/3 - h_T beta_i^* [ |T| sum_j dU_j/(3 h_T) ]
           *                    - h_T phi_i(U*)/2.
           *
           * Since the common ledger multiplier below is -h_T/2, add
           * 2 (T_i^F1 - |T| dU_i/(3 h_T)) to the spatial residual. Frozen
           * vertices have dU_i=0 by Construction A. Summing over i cancels
           * the two temporal terms element by element, so the correction does
           * not alter the element's conserved total. */
          double T_time[4][3];
          double rk2_scale = 0.0;

          if(solve_rank == 4)
            {
              double Z_f1[4];
              for(k = 0; k < 4; k++)
                Z_f1[k] = rhs[k][2];

              for(k = 0; k < 4; k++)
                for(j = 0; j < 3; j++)
                  {
                    T_time[k][j] = -1.0 * (Kmatrix[k][0][j][kplus] * Z_f1[0] + Kmatrix[k][1][j][kplus] * Z_f1[1] +
                                             Kmatrix[k][2][j][kplus] * Z_f1[2] + Kmatrix[k][3][j][kplus] * Z_f1[3]);

                    for(p = 0; p < 4; p++)
                      rk2_scale += fabs(Kmatrix[k][p][j][kplus]) * fabs(Z_f1[p]);
                  }
            }
          else
            {
              /* The bare beta_i acting on the arbitrary F1 target is not
               * defined for rank-deficient S^-. Retain the existing
               * conservative element-local lumped fallback. */
              RD_stat_f1_lumped++;

              for(k = 0; k < 4; k++)
                for(j = 0; j < 3; j++)
                  T_time[k][j] = (tri_normals_list[i].area / 3.0) * dU_vertex[j][k] / full_triangle_dt;
            }

          for(k = 0; k < 4; k++)
            for(j = 0; j < 3; j++)
              {
                double T_lumped = (tri_normals_list[i].area / 3.0) * dU_vertex[j][k] / full_triangle_dt;
                rk2_scale += 2.0 * (fabs(T_time[k][j]) + fabs(T_lumped));
                Flux_RD[k][j] += 2.0 * (T_time[k][j] - T_lumped);
              }

          rd_check_conservation(Flux_RD, Phi, rk2_scale + LDA_roundoff_scale + phi_scale, thistask_triangles[i],
                                "RK2-hier-LDA-F1");
        }
#endif

#ifdef RD_DIAG_TRACE_ELEMENT
      if(rd_trace)
        printf("RD-TRACE-OUT stage=%d flux00=%.17g flux30=%.17g flux01=%.17g flux31=%.17g\n", rd_stage, Flux_RD[0][0],
               Flux_RD[3][0], Flux_RD[0][1], Flux_RD[3][1]);
#endif

      /*use residuals to update fluid state of local points or export to other tasks*/

      for(j = 0; j < 3; j++)
        {
          if(DP[DT[thistask_triangles[i]].p[j]].task == ThisTask)
            {
              int SphP_index = DP[DT[thistask_triangles[i]].p[j]].index;
              //              if(SphP_index < 0)
              //                continue;   not necessary here, since the triangles we selected should not contain external points
              if(SphP_index >= NumGas)
                SphP_index -= NumGas;

              int P_index = SphP_index;

#ifdef RD_RT_FIXED_BOUNDARY
              if(rd_rt_fixed_boundary_vertex(P_index))
                {
                  rd_rt_record_absorbed_update((-1.0) * triangle_dt * Flux_RD[0][j],
                                               (-1.0) * triangle_dt * Flux_RD[1][j],
                                               (-1.0) * triangle_dt * Flux_RD[2][j],
                                               (-1.0) * triangle_dt * Flux_RD[3][j]);
                  continue;
                }
#endif
              P[P_index].Mass += (-1.0) * triangle_dt * Flux_RD[0][j];
              SphP[SphP_index].Momentum[0] += (-1.0) * triangle_dt * Flux_RD[1][j];
              SphP[SphP_index].Momentum[1] += (-1.0) * triangle_dt * Flux_RD[2][j];
              SphP[SphP_index].Energy += (-1.0) * triangle_dt * Flux_RD[3][j];
#ifdef RD_HIERARCHICAL_TIMESTEPS
              if(rd_stage == RD_RK_STAGE_PREDICTOR &&
                 rd_point_stage_live(&DP[DT[thistask_triangles[i]].p[j]]))
                {
                  SphP[SphP_index].RD_dU[0] += (-1.0) * full_triangle_dt * Flux_RD[0][j];
                  SphP[SphP_index].RD_dU[1] += (-1.0) * full_triangle_dt * Flux_RD[1][j];
                  SphP[SphP_index].RD_dU[2] += (-1.0) * full_triangle_dt * Flux_RD[2][j];
                  SphP[SphP_index].RD_dU[3] += (-1.0) * full_triangle_dt * Flux_RD[3][j];
                }
#endif
            }
          else
            {
              if(N_FluxRD_export >= Max_N_FluxRD_export)
                terminate_program("FluxRD_list capacity exceeded");

              FluxRD_list[N_FluxRD_export].task  = DP[DT[thistask_triangles[i]].p[j]].task;
              FluxRD_list[N_FluxRD_export].index = DP[DT[thistask_triangles[i]].p[j]].originalindex;

              FluxRD_list[N_FluxRD_export].dMass_Dual        = (-1.0) * triangle_dt * Flux_RD[0][j];
              FluxRD_list[N_FluxRD_export].dMomentum_Dual[0] = (-1.0) * triangle_dt * Flux_RD[1][j];
              FluxRD_list[N_FluxRD_export].dMomentum_Dual[1] = (-1.0) * triangle_dt * Flux_RD[2][j];
              FluxRD_list[N_FluxRD_export].dMomentum_Dual[2] = 0.0;
              FluxRD_list[N_FluxRD_export].dEnergy_Dual      = (-1.0) * triangle_dt * Flux_RD[3][j];
#ifdef RD_HIERARCHICAL_TIMESTEPS
              for(k = 0; k < 4; k++)
                FluxRD_list[N_FluxRD_export].dPredictor[k] = 0.0;

              if(rd_stage == RD_RK_STAGE_PREDICTOR &&
                 rd_point_stage_live(&DP[DT[thistask_triangles[i]].p[j]]))
                {
                  FluxRD_list[N_FluxRD_export].dPredictor[0] = (-1.0) * full_triangle_dt * Flux_RD[0][j];
                  FluxRD_list[N_FluxRD_export].dPredictor[1] = (-1.0) * full_triangle_dt * Flux_RD[1][j];
                  FluxRD_list[N_FluxRD_export].dPredictor[2] = (-1.0) * full_triangle_dt * Flux_RD[2][j];
                  FluxRD_list[N_FluxRD_export].dPredictor[3] = (-1.0) * full_triangle_dt * Flux_RD[3][j];
                }
#endif

              N_FluxRD_export += 1;
            }
        }
#endif  // TWO_DIMS
    }   // for loop of triangles, i= 0~ Ndt_thistask

  apply_FluxRD_list();

#ifdef RD_HIERARCHICAL_TIMESTEPS
  if(rd_stage == RD_RK_STAGE_PREDICTOR)
    {
      long long local_counts[2] = {0, 0}, global_counts[2];
      int local_max_ratio = 1, global_max_ratio;

      for(i = 0; i < NumGas; i++)
        {
          if(SphP[i].RD_StarTimeBin == P[i].TimeBinHydro)
            {
              local_counts[0]++;
              if(TimeBinSynchronized[P[i].TimeBinHydro])
                {
                  for(k = 0; k < 4; k++)
                    SphP[i].RD_dU[k] /= SphP[i].DualArea;

                  double u0 = SphP[i].Density + SphP[i].RD_dU[0];
                  double u1 = SphP[i].Density * P[i].Vel[0] + SphP[i].RD_dU[1];
                  double u2 = SphP[i].Density * P[i].Vel[1] + SphP[i].RD_dU[2];
                  double u3 = SphP[i].Pressure / GAMMA_MINUS1 +
                              0.5 * SphP[i].Density *
                                  (P[i].Vel[0] * P[i].Vel[0] + P[i].Vel[1] * P[i].Vel[1]) +
                              SphP[i].RD_dU[3];
                  double predictor_press = GAMMA_MINUS1 * (u3 - 0.5 * (u1 * u1 + u2 * u2) / u0);

                  if(!isfinite(u0) || !isfinite(predictor_press) || u0 <= 0.0 || predictor_press <= 0.0)
                    {
                      printf("RD hierarchy predictor invalid after assembly: task=%d i=%d ID=%llu rho=%.17g press=%.17g\n",
                             ThisTask, i, (unsigned long long)P[i].ID, u0, predictor_press);
                      terminate_program("RD hierarchy produced a non-physical assembled predictor");
                    }

                  RD_stat_min_stage_rho   = dmin(RD_stat_min_stage_rho, u0);
                  RD_stat_min_stage_press = dmin(RD_stat_min_stage_press, predictor_press);
                }
            }
          else
            {
              local_counts[1]++;
              int ratio = 1 << (P[i].TimeBinHydro - SphP[i].RD_StarTimeBin);
              local_max_ratio = imax(local_max_ratio, ratio);
            }
        }

      MPI_Reduce(local_counts, global_counts, 2, MPI_LONG_LONG, MPI_SUM, 0, MPI_COMM_WORLD);
      MPI_Reduce(&local_max_ratio, &global_max_ratio, 1, MPI_INT, MPI_MAX, 0, MPI_COMM_WORLD);
      if(ThisTask == 0)
        printf("RD-HIER time=%.8g stage=open live_vertices=%lld frozen_vertices=%lld max_ratio=%d\n", All.Time,
               global_counts[0], global_counts[1], global_max_ratio);
    }
#endif

#ifdef RD_RK2_INTERNAL_LOOP
      myfree_movable(FluxRD_list);
    } /* stage loop */

  FluxRD_list = NULL; /* freed inside the stage loop */
#endif /* RD_RK2_INTERNAL_LOOP */

#ifdef RD_RT_FIXED_BOUNDARY
  {
    double local[12], global[12], q_after[4] = {0.0, 0.0, 0.0, 0.0};
    for(int q_index = 0; q_index < NumGas; q_index++)
      {
        q_after[0] += P[q_index].Mass;
        q_after[1] += SphP[q_index].Momentum[0];
        q_after[2] += SphP[q_index].Momentum[1];
        q_after[3] += SphP[q_index].Energy;
      }
    for(int component = 0; component < 4; component++)
      {
        /* The fixed boundary turns the domain into an open system.  The
         * reservoir exchange that closes the committed hydro update is the
         * negative change of the actually stored global Q.  Raw suppressed
         * increments are also useful, but they include temporary RK trial
         * stages and therefore must not be summed as a physical budget. */
        local[component] = RD_boundary_q_before[component] - q_after[component];
        local[4 + component] = RD_stat_boundary_absorbed[component];
        local[8 + component] = RD_stat_boundary_absorbed_abs[component];
      }
    MPI_Reduce(local, global, 12, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);
    if(ThisTask == 0)
      printf("RD-RT-BOUNDARY time=%.8g exchange=[%.6e,%.6e,%.6e,%.6e] "
             "stage_suppressed=[%.6e,%.6e,%.6e,%.6e] stage_abs=[%.6e,%.6e,%.6e,%.6e]\n",
             All.Time, global[0], global[1], global[2], global[3], global[4], global[5], global[6], global[7], global[8],
             global[9], global[10], global[11]);
  }
#endif

#ifdef RD_DEBUG_ASSERTS
  /* Item A4: instrumentation, not an assertion.  Reports how often the
   * upwind system used DGELSD, how often LU found an exact singularity, the
   * smallest DGELSD rank, and the largest raw conservation defect. */
  {
    long long stat_counts[4] = {RD_stat_elements, RD_stat_pinv_fallback, RD_stat_exact_singular, RD_stat_min_svd_rank};
    long long stat_totals[3], stat_min_rank;
    long long stat_rank_counts[5];
    double stat_mins[2] = {RD_stat_min_pivot_ratio, RD_stat_min_dt_extrap};
    double stat_maxs[3] = {RD_stat_max_cons_defect_abs, RD_stat_max_dt_extrap, RD_stat_max_phi};
    double stat_min_out[2], stat_max_out[3];

    MPI_Reduce(stat_counts, stat_totals, 3, MPI_LONG_LONG, MPI_SUM, 0, MPI_COMM_WORLD);
    MPI_Reduce(&stat_counts[3], &stat_min_rank, 1, MPI_LONG_LONG, MPI_MIN, 0, MPI_COMM_WORLD);
    MPI_Reduce(RD_stat_svd_rank_count, stat_rank_counts, 5, MPI_LONG_LONG, MPI_SUM, 0, MPI_COMM_WORLD);
    MPI_Reduce(stat_mins, stat_min_out, 2, MPI_DOUBLE, MPI_MIN, 0, MPI_COMM_WORLD);
    MPI_Reduce(stat_maxs, stat_max_out, 3, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);

#ifdef RD_DIAG_THETA
    {
      long long hist[2][RD_THETA_BINS], count[2];
      double sum[2], maxv[2];

      MPI_Reduce(RD_stat_theta_hist, hist, 2 * RD_THETA_BINS, MPI_LONG_LONG, MPI_SUM, 0, MPI_COMM_WORLD);
      MPI_Reduce(RD_stat_theta_count, count, 2, MPI_LONG_LONG, MPI_SUM, 0, MPI_COMM_WORLD);
      MPI_Reduce(RD_stat_theta_sum, sum, 2, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);
      MPI_Reduce(RD_stat_theta_max, maxv, 2, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);

      if(ThisTask == 0)
        for(int which = 0; which < 2; which++)
          if(count[which] > 0)
            {
              printf("RD-THETA time=%.8g kind=%s n=%lld mean=%.6e max=%.6e hist=[", All.Time,
                     (which == 0) ? "spatial" : "total", count[which], sum[which] / count[which], maxv[which]);
              for(int bin = 0; bin < RD_THETA_BINS; bin++)
                printf("%s%.4f", bin ? "," : "", (double)hist[which][bin] / (double)count[which]);
              printf("] edges=[1e-6,1e-4,1e-2,0.1,0.5,0.9,1]\n");
            }
    }
#endif

    if(ThisTask == 0)
      printf(
          "RD-DIAG time=%.8g elements=%lld svd_fallback=%lld (%.3g%%) exact_singular=%lld "
          "svd_rcond=%.3e rank_counts=[%lld,%lld,%lld,%lld,%lld] min_svd_rank=%lld "
          "min_pivot_ratio=%.3e cons_defect_abs=%.3e max_phi=%.3e cons_defect_rel=%.3e dt_extrap=[%.6e,%.6e]\n",
          All.Time, stat_totals[0], stat_totals[1],
          (stat_totals[0] > 0) ? 100.0 * (double)stat_totals[1] / (double)stat_totals[0] : 0.0, stat_totals[2],
          (double)RD_SVD_RCOND, stat_rank_counts[0], stat_rank_counts[1], stat_rank_counts[2], stat_rank_counts[3],
          stat_rank_counts[4], (stat_totals[1] > 0) ? stat_min_rank : -1, stat_min_out[0], stat_max_out[0], stat_max_out[2],
          (stat_max_out[2] > 0.0) ? stat_max_out[0] / stat_max_out[2] : 0.0, stat_min_out[1], stat_max_out[1]);

#ifdef RD_RK2_TOTAL_RESIDUAL
    long long f1_lumped_total;
    double stage_mins[2] = {RD_stat_min_stage_rho, RD_stat_min_stage_press};
    double stage_min_out[2];

    MPI_Reduce(&RD_stat_f1_lumped, &f1_lumped_total, 1, MPI_LONG_LONG, MPI_SUM, 0, MPI_COMM_WORLD);
    MPI_Reduce(stage_mins, stage_min_out, 2, MPI_DOUBLE, MPI_MIN, 0, MPI_COMM_WORLD);

    if(ThisTask == 0)
      printf("RD-RK2 time=%.8g f1_lumped=%lld predictor_min_rho=%.6e predictor_min_press=%.6e stage_beta=%s\n", All.Time,
             f1_lumped_total, stage_min_out[0], stage_min_out[1], RD_RK2_STAGE_BETA_LABEL);
#endif
  }
#endif /* #ifdef RD_DEBUG_ASSERTS */

#ifndef RD_RK2_INTERNAL_LOOP
  myfree_movable(FluxRD_list);
#endif
#ifdef RD_RK2_COHERENT_BETA_N
  myfree(rd_beta_stage0);
#endif
#ifdef RD_RK2_COHERENT_BETA_STAR
  myfree(rd_phi_stage0);
#endif
#if defined(B_SCHEME) && defined(RD_RK2_INTERNAL_LOOP)
  myfree(rd_b_phi_stage0);
  myfree(rd_b_flux_lda_stage0);
  myfree(rd_b_flux_n_stage0);
#endif
  rd_free_element_set(&set);

  TIMER_STOP(CPU_RESIDUAL_DISTRIBUTION);
}

/* The majority-task responsibility rule and the sorted-ID duplicate scan
 * that lived here were replaced by the minimum-ID ownership rule in
 * rd_simplex_claimed(); see dev_log/RD_DEVELOPMENT_LOG.md, entry
 * "deferred MPI simplex-responsibility redesign", for the failure mode of
 * the old rule under partial activation. */


void triangle_vertex_do_time_extrapolation(struct state_primitive *delta, struct state_primitive *st, struct grad_data *grad, double dt_Extrapolation)
{
  if(st->rho <= 0)
    return;

  delta->rho = -dt_Extrapolation * (st->velx * grad->drho[0] + st->rho * grad->dvel[0][0] + st->vely * grad->drho[1] +
                                    st->rho * grad->dvel[1][1] + st->velz * grad->drho[2] + st->rho * grad->dvel[2][2]);

  delta->velx = -dt_Extrapolation * (1.0 / st->rho * grad->dpress[0] + st->velx * grad->dvel[0][0] + st->vely * grad->dvel[0][1] +
                                     st->velz * grad->dvel[0][2]);

  delta->vely = -dt_Extrapolation * (1.0 / st->rho * grad->dpress[1] + st->velx * grad->dvel[1][0] + st->vely * grad->dvel[1][1] +
                                     st->velz * grad->dvel[1][2]);

  delta->velz = -dt_Extrapolation * (1.0 / st->rho * grad->dpress[2] + st->velx * grad->dvel[2][0] + st->vely * grad->dvel[2][1] +
                                     st->velz * grad->dvel[2][2]);

  delta->press = -dt_Extrapolation * (GAMMA * st->press * (grad->dvel[0][0] + grad->dvel[1][1] + grad->dvel[2][2]) +
                                      st->velx * grad->dpress[0] + st->vely * grad->dpress[1] + st->velz * grad->dpress[2]);
}

void triangle_vertex_add_extrapolation(struct state_primitive *delta_time, struct state_primitive *st)
{
  if(st->rho <= 0)
    return;

  if(st->rho + delta_time->rho <= 0 || st->press + delta_time->press <= 0)
    return;

  st->rho += delta_time->rho;
  st->velx += delta_time->velx;
  st->vely += delta_time->vely;
  st->velz += delta_time->velz;
  st->press += delta_time->press;
}

void apply_FluxRD_list(void)
{
  int i, j, p, nimport, ngrp, recvTask;

  /* now exchange the flux-list and apply it when needed */

  mysort(FluxRD_list, N_FluxRD_export, sizeof(struct FluxRD_list_data), FluxRD_list_data_compare);

  for(j = 0; j < NTask; j++)
    Send_count[j] = 0;

  for(i = 0; i < N_FluxRD_export; i++)
    Send_count[FluxRD_list[i].task]++;

  if(Send_count[ThisTask] > 0)
    terminate_program("Send_count[ThisTask]");

  MPI_Alltoall(Send_count, 1, MPI_INT, Recv_count, 1, MPI_INT, MPI_COMM_WORLD);

  for(j = 0, nimport = 0, Recv_offset[0] = 0, Send_offset[0] = 0; j < NTask; j++)
    {
      nimport += Recv_count[j];

      if(j > 0)
        {
          Send_offset[j] = Send_offset[j - 1] + Send_count[j - 1];
          Recv_offset[j] = Recv_offset[j - 1] + Recv_count[j - 1];
        }
    }

  struct FluxRD_list_data *FluxListGet = (struct FluxRD_list_data *)mymalloc("FluxListGet", nimport * sizeof(struct FluxRD_list_data));

  /* exchange particle data */
  for(ngrp = 0; ngrp < (1 << PTask); ngrp++)
    {
      recvTask = ThisTask ^ ngrp;

      if(recvTask < NTask)
        {
          if(Send_count[recvTask] > 0 || Recv_count[recvTask] > 0)
            {
              /* get the particles */
              MPI_Sendrecv(&FluxRD_list[Send_offset[recvTask]], Send_count[recvTask] * sizeof(struct FluxRD_list_data), MPI_BYTE,
                           recvTask, TAG_DENS_A, &FluxListGet[Recv_offset[recvTask]],
                           Recv_count[recvTask] * sizeof(struct FluxRD_list_data), MPI_BYTE, recvTask, TAG_DENS_A, MPI_COMM_WORLD,
                           MPI_STATUS_IGNORE);
            }
        }
    }

  /* apply the fluxes */

  for(i = 0; i < nimport; i++)
    {
      p = FluxListGet[i].index;

#ifdef RD_RT_FIXED_BOUNDARY
      if(rd_rt_fixed_boundary_vertex(p))
        {
          rd_rt_record_absorbed_update(FluxListGet[i].dMass_Dual, FluxListGet[i].dMomentum_Dual[0],
                                       FluxListGet[i].dMomentum_Dual[1], FluxListGet[i].dEnergy_Dual);
          continue;
        }
#endif
      P[p].Mass += FluxListGet[i].dMass_Dual;
      SphP[p].Momentum[0] += FluxListGet[i].dMomentum_Dual[0];
      SphP[p].Momentum[1] += FluxListGet[i].dMomentum_Dual[1];
      SphP[p].Momentum[2] += FluxListGet[i].dMomentum_Dual[2];
      SphP[p].Energy += FluxListGet[i].dEnergy_Dual;
#ifdef RD_HIERARCHICAL_TIMESTEPS
      for(int component = 0; component < 4; component++)
        SphP[p].RD_dU[component] += FluxListGet[i].dPredictor[component];
#endif
    }
  myfree(FluxListGet);
}

int FluxRD_list_data_compare(const void *a, const void *b)
{
  if(((struct FluxRD_list_data *)a)->task < (((struct FluxRD_list_data *)b)->task))
    return -1;

  if(((struct FluxRD_list_data *)a)->task > (((struct FluxRD_list_data *)b)->task))
    return +1;

  return 0;
}

void apply_DualArea_list(void)
{
  int i, j, p, nimport, ngrp, recvTask;
#if defined(MAXSCALARS)
  int k;
#endif /* #if defined(MAXSCALARS) */

  /* now exchange the flux-list and apply it when needed */

  mysort(DualArea_list, N_DualArea_export, sizeof(struct DualArea_list_data), DualArea_list_data_compare);

  for(j = 0; j < NTask; j++)
    Send_count[j] = 0;

  for(i = 0; i < N_DualArea_export; i++)
    {
      Send_count[DualArea_list[i].task]++;
      if(DualArea_list[i].task == ThisTask)
        {
          printf("bug: thistask, i_inDualAreaList %d %d %d\n", ThisTask, i, N_DualArea_export);
          printf("DualArea_list[i].task: %d\n", DualArea_list[i].task);
        }
    }

  if(Send_count[ThisTask] > 0)
    terminate_program("Send_count[ThisTask]");

  MPI_Alltoall(Send_count, 1, MPI_INT, Recv_count, 1, MPI_INT, MPI_COMM_WORLD);

  for(j = 0, nimport = 0, Recv_offset[0] = 0, Send_offset[0] = 0; j < NTask; j++)
    {
      nimport += Recv_count[j];

      if(j > 0)
        {
          Send_offset[j] = Send_offset[j - 1] + Send_count[j - 1];
          Recv_offset[j] = Recv_offset[j - 1] + Recv_count[j - 1];
        }
    }

  struct DualArea_list_data *DualAreaListGet =
      (struct DualArea_list_data *)mymalloc("DualAreaListGet", nimport * sizeof(struct DualArea_list_data));

  /* exchange particle data */
  for(ngrp = 0; ngrp < (1 << PTask); ngrp++)
    {
      recvTask = ThisTask ^ ngrp;

      if(recvTask < NTask)
        {
          if(Send_count[recvTask] > 0 || Recv_count[recvTask] > 0)
            {
              /* get the particles */
              MPI_Sendrecv(&DualArea_list[Send_offset[recvTask]], Send_count[recvTask] * sizeof(struct DualArea_list_data), MPI_BYTE,
                           recvTask, TAG_DENS_A, &DualAreaListGet[Recv_offset[recvTask]],
                           Recv_count[recvTask] * sizeof(struct DualArea_list_data), MPI_BYTE, recvTask, TAG_DENS_A, MPI_COMM_WORLD,
                           MPI_STATUS_IGNORE);
            }
        }
    }

  for(i = 0; i < nimport; i++)
    {
      p = DualAreaListGet[i].index;
      SphP[p].DualArea += DualAreaListGet[i].DualArea;
    }

  myfree(DualAreaListGet);
}

int DualArea_list_data_compare(const void *a, const void *b)
{
  if(((struct DualArea_list_data *)a)->task < (((struct DualArea_list_data *)b)->task))
    return -1;

  if(((struct DualArea_list_data *)a)->task > (((struct DualArea_list_data *)b)->task))
    return +1;

  return 0;
}

lapack_int mat_inv(double *A, unsigned n)
{
  lapack_int ipiv[n];
  lapack_int ret;

  ret = LAPACKE_dgetrf(LAPACK_ROW_MAJOR, n, n, A, n, ipiv);

  if(ret != 0)
    return ret;

  return LAPACKE_dgetri(LAPACK_ROW_MAJOR, n, A, n, ipiv);
}

lapack_int solve_system(int n, double *A, double *b)
{
  lapack_int nrhs  = 1;
  lapack_int *ipiv = (lapack_int *)malloc(n * sizeof(lapack_int));

  // Solve the system
  lapack_int info = LAPACKE_dgesv(LAPACK_ROW_MAJOR, n, nrhs, A, n, ipiv, b, n);

  free(ipiv);
  if(info != 0)
    {
      mpi_printf("solution failed.\n");
    }

  // Return the status code
  return info;
}

/* needs_regularization() and regularize_matrix() were removed here.  They
 * added an absolute shift REGULARIZATION_CONSTANT to the diagonal of S^-
 * whenever any entry fell below an absolute threshold.  That test is not a
 * conditioning test, the constants are dimensional, and the shift breaks the
 * identity sum_i K_i^+ = -S^- on which the conservation of both the LDA and
 * the N distribution rests.  See dev_log/regularize_matrix_debug_report.md; the
 * previous behaviour is preserved in git at commit ebe1be2. */

#endif  // #ifdef RESIDUAL_DISTRIBUTION
