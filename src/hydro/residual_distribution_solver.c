
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
#include "../mesh/rd_ale_geometry.h"
#include "../mesh/rd_simplex_geometry.h"
#include "../mesh/voronoi/voronoi.h"
#include "rd_euler.h"
#include "rd_linalg.h"
#include "rd_state.h"
#include "rd_timestep.h"

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

#if defined(RD_RUSANOV_LOW_ORDER) || defined(RD_LDA_RUSANOV_BLEND)
#include "rd_rusanov.h"
#ifdef RD_RUSANOV_LOW_ORDER
#if !defined(N_SCHEME) || !defined(RD_RK2_TOTAL_RESIDUAL) || \
    (!defined(FORCE_EQUAL_TIMESTEPS) && !defined(RD_ALE_INTERVAL_HIERARCHY)) || !defined(CREATE_FULL_MESH) || \
    !defined(TREE_BASED_TIMESTEPS)
#error "RD_RUSANOV_LOW_ORDER requires full-mesh, equal-step (or interval-hierarchy) N/lumped RK2 and tree timesteps."
#endif
#if (defined(RD_HIERARCHICAL_TIMESTEPS) && !defined(RD_ALE_INTERVAL_HIERARCHY)) || defined(RD_ELEMENT_COMOVING_FRAME) || \
    defined(RD_ALE_CONTOUR_RESIDUAL) || \
    defined(RD_DIAG_NO_KICK) || \
    defined(RD_RT_FIXED_BOUNDARY) || defined(SELFGRAVITY) || defined(EXTERNALGRAVITY) || defined(MHD) || \
    defined(PASSIVE_SCALARS) || defined(REFINEMENT) || defined(REFINEMENT_HIGH_RES_GAS) || \
    defined(EXACT_GRAVITY_FOR_PARTICLE_TYPE) || defined(REFLECTIVE_X) || defined(REFLECTIVE_Y) || defined(REFLECTIVE_Z)
#error "RD_RUSANOV_LOW_ORDER is periodic, hydro-only, lab-frame static or Arpaia/Campoli ALE."
#endif
#if defined(RD_ALE_CAMPOLI_MASS) && !defined(RD_ALE_EQUALSTEP) && !defined(RD_ALE_INTERVAL_HIERARCHY)
#error "RD_RUSANOV_LOW_ORDER with Campoli mass is an equal-step or interval-hierarchy ALE option."
#endif
#ifdef RD_LOW_ORDER_HLLC
/* Replaces only the element kernel and its per-vertex stage coefficient;
 * geometry, lumped RK2 stages and all stage checks are the Rusanov path's. */
#include "rd_hllc.h"
#endif
#endif
#if defined(RD_LOW_ORDER_HLLC) && !defined(RD_RUSANOV_LOW_ORDER)
#error "RD_LOW_ORDER_HLLC is a kernel option of RD_RUSANOV_LOW_ORDER."
#endif

#ifdef RD_LDA_RUSANOV_B_SENSOR
#if !defined(RD_LDA_RUSANOV_BLEND) || RD_LDA_RUSANOV_BLEND != 1
#error "RD_LDA_RUSANOV_B_SENSOR requires the static positive blend, RD_LDA_RUSANOV_BLEND=1."
#endif
#if RD_LDA_RUSANOV_B_SENSOR != 1 && RD_LDA_RUSANOV_B_SENSOR != 2
#error "Use B_SENSOR=1 for component ratios or 2 for scalar Bmax."
#endif
#endif

#ifdef RD_LDA_RUSANOV_BLEND
#include "rd_lda_rusanov.h"
#ifdef RD_BLEND_LOW_HLLC
/* Moving-mesh variant: the low-order endpoint is the edge-HLLC kernel plus
 * the half-split Gauss3 edge terms, so its element total is LDA's Gauss3
 * contour.  Equal-step ALE runs both RK sweeps in one call, hence SPLIT. */
#include "rd_hllc.h"
#if !defined(RD_ALE_EQUALSTEP) || !defined(RD_ALE_CONTOUR_RESIDUAL) || !defined(LDA_SCHEME) || \
    !defined(RD_RK2_TOTAL_RESIDUAL) || !defined(RD_RK2_SPLIT_STAGES) || !defined(FORCE_EQUAL_TIMESTEPS) || \
    !defined(CREATE_FULL_MESH) || !defined(TREE_BASED_TIMESTEPS) || !defined(RD_ALE_CONTOUR_GAUSS) || \
    RD_ALE_CONTOUR_GAUSS != 3
#error "LDA/HLLC blend requires equal-step ALE LDA/F1 with the Gauss3 contour residual."
#endif
#if defined(RD_RUSANOV_LOW_ORDER) || defined(RD_LDA_RUSANOV_B_SENSOR) || defined(RD_HIERARCHICAL_TIMESTEPS) || \
    defined(RD_RK2_RATE_CONSISTENT_HEUN) || defined(RD_ELEMENT_COMOVING_FRAME) || \
    defined(RD_ALE_SPLIT_MESH_VELOCITY) || defined(RD_ALE_TOPOLOGY_REPAIR_DIAGNOSTIC) || defined(RD_DIAG_NO_KICK) || \
    defined(RD_RT_FIXED_BOUNDARY) || defined(SELFGRAVITY) || defined(EXTERNALGRAVITY) || defined(MHD) || \
    defined(PASSIVE_SCALARS) || defined(REFINEMENT) || defined(REFINEMENT_HIGH_RES_GAS) || \
    defined(EXACT_GRAVITY_FOR_PARTICLE_TYPE) || defined(REFLECTIVE_X) || defined(REFLECTIVE_Y) || defined(REFLECTIVE_Z)
#error "LDA/HLLC blend supports lab-frame periodic source-free equal-step ALE hydro only."
#endif
/* Campoli: the low corrector keeps the Rusanov/HLLC form (a-.5)U^n + b[...],
 * with a = temporal mass (A_old+A_new)/6 summed over the star / divisor S^{n+1}
 * and b = 3/2 - a; the convex-weight check below covers both mass variants. */
#else
#if !defined(VORONOI_STATIC_MESH) || !defined(LDA_SCHEME) || !defined(RD_RK2_TOTAL_RESIDUAL) || \
    !defined(FORCE_EQUAL_TIMESTEPS) || !defined(CREATE_FULL_MESH) || !defined(TREE_BASED_TIMESTEPS) || \
    !defined(RD_ALE_CONTOUR_GAUSS) || RD_ALE_CONTOUR_GAUSS != 3
#error "LDA/Rusanov research requires static full-mesh equal-step LDA/F1/Gauss3 and tree timesteps."
#endif
#if defined(RD_RUSANOV_LOW_ORDER) || defined(RD_RK2_SPLIT_STAGES) || defined(RD_HIERARCHICAL_TIMESTEPS) || \
    defined(RD_RK2_RATE_CONSISTENT_HEUN) || defined(RD_ELEMENT_COMOVING_FRAME) || defined(RD_DIAG_NO_KICK) || \
    defined(RD_RT_FIXED_BOUNDARY) || defined(SELFGRAVITY) || defined(EXTERNALGRAVITY) || defined(MHD) || \
    defined(PASSIVE_SCALARS) || defined(REFINEMENT) || defined(REFINEMENT_HIGH_RES_GAS) || \
    defined(EXACT_GRAVITY_FOR_PARTICLE_TYPE) || defined(REFLECTIVE_X) || defined(REFLECTIVE_Y) || defined(REFLECTIVE_Z)
#error "LDA/Rusanov research supports unsplit static periodic source-free hydro only."
#endif
#endif /* RD_BLEND_LOW_HLLC */
#if RD_LDA_RUSANOV_BLEND != 0 && RD_LDA_RUSANOV_BLEND != 1
#error "Use RD_LDA_RUSANOV_BLEND=0 for the low-order control, or 1 for limiting."
#endif
#endif
#if(defined(RD_BLEND_LOW_HLLC) || defined(RD_BLEND_LOCAL_BOUNDS)) && !defined(RD_LDA_RUSANOV_BLEND)
#error "RD_BLEND_LOW_HLLC and RD_BLEND_LOCAL_BOUNDS are options of RD_LDA_RUSANOV_BLEND."
#endif

static int rd_rusanov_local_index(const point *dp)
{
  int index = dp->index;
  if(index >= NumGas)
    index -= NumGas;
  if(NTask != 1 || dp->task != ThisTask || index < 0 || index >= NumGas)
    terminate_program("RD_RUSANOV_LOW_ORDER v1 requires one MPI rank and local gas vertices");
  return index;
}
#endif

/* Standard static LDA/F1 retains its mixed-stage baseline. A common
 * interval-opening distribution is an explicit comparison option only.
 * Moving geometry, N/B, and four-pass rate-Heun have separate definitions. */
#if defined(RD_LDA_COMMON_OPENING_BETA) || defined(RD_LDA_MIXED_STAGE_BETA)
#if !defined(VORONOI_STATIC_MESH) || !defined(LDA_SCHEME) || !defined(RD_RK2_TOTAL_RESIDUAL) || \
    defined(RD_RK2_RATE_CONSISTENT_HEUN)
#error "LDA beta comparison options require standard static LDA/F1."
#endif
#if defined(RD_LDA_COMMON_OPENING_BETA) && defined(RD_LDA_MIXED_STAGE_BETA)
#error "Select only one LDA beta comparison option."
#endif
#ifdef RD_LDA_COMMON_OPENING_BETA
#define RD_LDA_COMMON_BETA
#endif
#endif

/* Static full-mesh LDA uses the same P1-U edge states, including the
 * synchronized/frozen predictor states already exchanged by the hierarchy.
 * Quadrature adds no topology state or MPI payload. Keep the moving-hierarchy
 * and active-mesh extensions guarded until separately validated. Equal-step
 * ALE N may also use Gauss3 with the existing conservative N correction;
 * this does not extend the standard scalar N positivity result. */
#if defined(RD_ALE_CONTOUR_GAUSS) &&                                                            \
    (!defined(RD_ALE_CONTOUR_RESIDUAL) ||                                                      \
     !((defined(LDA_SCHEME) &&                                                                \
        (defined(RD_ALE_EQUALSTEP) ||                                                         \
         (defined(VORONOI_STATIC_MESH) && defined(CREATE_FULL_MESH) && defined(RD_RK2_TOTAL_RESIDUAL)))) || \
       (defined(N_SCHEME) && defined(RD_ALE_EQUALSTEP) && RD_ALE_CONTOUR_GAUSS == 3)))
#error "RD_ALE_CONTOUR_GAUSS requires ALE LDA, experimental equal-step ALE N/Gauss3, or static full-mesh RK2 LDA."
#endif
#if defined(RD_ALE_CONTOUR_GAUSS) && (RD_ALE_CONTOUR_GAUSS != 3 && RD_ALE_CONTOUR_GAUSS != 5)
#error "RD_ALE_CONTOUR_GAUSS must be 3 or 5 quadrature points."
#endif
#ifdef RD_ALE_CONTOUR_GAUSS
#include "rd_contour_quadrature.h"
#endif

#if !defined(TWODIMS)
#if !defined(RD_3D_STATIC) || !defined(VORONOI_STATIC_MESH) || (!defined(N_SCHEME) && !defined(LDA_SCHEME)) || \
    !defined(RD_RK2_TOTAL_RESIDUAL) || !defined(CREATE_FULL_MESH) || !defined(FORCE_EQUAL_TIMESTEPS) || \
    !defined(TREE_BASED_TIMESTEPS)
#error "3D RD requires explicit RD_3D_STATIC: static full-mesh, equal-step N/lumped or LDA/F1 RK2 with tree timesteps."
#endif
#if defined(RD_HIERARCHICAL_TIMESTEPS) || defined(RD_RK2_SPLIT_STAGES) || defined(RD_LDA_COMMON_BETA) || defined(RD_ELEMENT_COMOVING_FRAME) || \
    defined(RD_ALE_CONTOUR_RESIDUAL) || defined(RD_ALE_ENTROPY_DISSIPATION) || defined(RD_ALE_SHEAR_EIGENVALUE_FLOOR) || \
    defined(RD_RUSANOV_LOW_ORDER) || defined(RD_LDA_RUSANOV_BLEND) || defined(RD_ALE_CONDITION_DIAGNOSTIC) || \
    defined(RD_ALE_CFL_DIAGNOSTIC) || defined(RD_DIAG_NO_KICK) || defined(RD_DIAG_PREDICTOR_ONLY) || \
    defined(RD_DIAG_SKIP_PREPARE) || defined(RD_RT_FIXED_BOUNDARY) || defined(SELFGRAVITY) || \
    defined(EXTERNALGRAVITY) || defined(EXACT_GRAVITY_FOR_PARTICLE_TYPE) || defined(MHD) || defined(PASSIVE_SCALARS) || \
    defined(REFINEMENT) || defined(REFINEMENT_HIGH_RES_GAS) || defined(REFLECTIVE_X) || defined(REFLECTIVE_Y) || \
    defined(REFLECTIVE_Z) || defined(COOLING) || defined(ONEDIMS)
#error "RD_3D_STATIC supports periodic source-free N/LDA hydro without stage-altering diagnostics."
#endif
#elif defined(RD_3D_STATIC)
#error "RD_3D_STATIC must not be combined with TWODIMS."
#endif

#if !defined(VORONOI_STATIC_MESH) && !defined(RD_ALE_EQUALSTEP) && !defined(RD_ALE_HIERARCHICAL)
#error "Moving-mesh RD requires RD_ALE_EQUALSTEP or the restricted RD_ALE_HIERARCHICAL prototype."
#endif

#if !defined(FORCE_EQUAL_TIMESTEPS) && !defined(RD_HIERARCHICAL_TIMESTEPS)
#error "The current residual-distribution baseline requires FORCE_EQUAL_TIMESTEPS."
#endif

#ifdef RD_ALE_EQUALSTEP
#if defined(VORONOI_STATIC_MESH) || !defined(FORCE_EQUAL_TIMESTEPS) || !defined(RD_RK2_TOTAL_RESIDUAL)
#error "RD_ALE_EQUALSTEP requires a moving mesh, equal timesteps and the total-residual RK2 path."
#endif

#if defined(RD_ALE_CONDITION_DIAGNOSTIC) && !defined(LDA_SCHEME)
#error "RD_ALE_CONDITION_DIAGNOSTIC currently diagnoses the LDA distribution only."
#endif

#if defined(RD_ALE_CFL_DIAGNOSTIC) && !defined(RD_ALE_EQUALSTEP)
#error "RD_ALE_CFL_DIAGNOSTIC requires the equal-step ALE prototype."
#endif
#if defined(RD_ALE_TOPOLOGY_REPAIR_DIAGNOSTIC) && !defined(RD_ALE_EQUALSTEP)
#error "RD_ALE_TOPOLOGY_REPAIR_DIAGNOSTIC requires RD_ALE_EQUALSTEP."
#endif
#if defined(RD_ALE_EXACT_PATCH_DIAGNOSTIC) && !defined(RD_ALE_TOPOLOGY_REPAIR_DIAGNOSTIC)
#error "RD_ALE_EXACT_PATCH_DIAGNOSTIC requires RD_ALE_TOPOLOGY_REPAIR_DIAGNOSTIC."
#endif
#if defined(RD_ALE_FLIP_TRANSFER) && !defined(RD_ALE_EQUALSTEP)
#error "RD_ALE_FLIP_TRANSFER requires RD_ALE_EQUALSTEP; the moving hierarchy uses its own interval transfer."
#endif
#if defined(RD_ALE_FLIP_TRANSFER) && defined(RD_ALE_TOPOLOGY_REPAIR_DIAGNOSTIC)
#error "Use the flip-element transfer or the old uniform-shift repair, not both."
#endif
#ifdef RD_ALE_FLIP_TRANSFER
/* Flip element (dev_log/RD_FLIP_ELEMENT_AND_MOVING_HIERARCHY_DESIGN_20261008.md).
 * FLOOR_FRACTION: rho and internal energy may not fall below this fraction of
 * the cavity input minima; DMP_RELAX < 0 disables the relaxed density hull;
 * ENTROPY_BOUND requests K = p/rho^gamma >= the cavity minimum. */
#include "rd_flip_transfer.h"
#ifndef RD_FLIP_FLOOR_FRACTION
#define RD_FLIP_FLOOR_FRACTION 0.5
#endif
#ifndef RD_FLIP_DMP_RELAX
#define RD_FLIP_DMP_RELAX (-1.0)
#endif
#ifndef RD_FLIP_ENTROPY_BOUND
#define RD_FLIP_ENTROPY_BOUND 0
#endif
#ifndef RD_FLIP_HIGH_MODE
/* 1 (receiver-only) since 2026-10-09: same conservation and accuracy as the
 * uniform shift in Yee/Sod/Sedov, no KH entropy excursion (results report
 * §3.4). Frozen archives before this date used 0 unless their Config says 1. */
#define RD_FLIP_HIGH_MODE 1
#endif
#endif
#if defined(RD_ALE_CFL_TIMESTEP) && (!defined(RD_ALE_EQUALSTEP) || !defined(TREE_BASED_TIMESTEPS))
#error "RD_ALE_CFL_TIMESTEP currently requires RD_ALE_EQUALSTEP and TREE_BASED_TIMESTEPS."
#endif
#if defined(RD_ALE_SHEAR_EIGENVALUE_FLOOR) && \
    (!defined(RD_ALE_EQUALSTEP) || (!defined(N_SCHEME) && !defined(LDA_SCHEME)) || !defined(RD_ALE_CFL_TIMESTEP))
#error "RD_ALE_SHEAR_EIGENVALUE_FLOOR is an N/LDA ALE experiment and requires RD_ALE_EQUALSTEP plus RD_ALE_CFL_TIMESTEP."
#endif
#if defined(RD_ALE_SHEAR_EIGENVALUE_FLOOR) && defined(RD_ALE_ENTROPY_DISSIPATION)
#error "Test the shear eigenvalue floor separately from RD_ALE_ENTROPY_DISSIPATION."
#endif
#if !defined(N_SCHEME) && !defined(LDA_SCHEME) && !defined(B_SCHEME)
#error "RD_ALE_EQUALSTEP supports N/lumped, LDA/F1 and their conservative B blend."
#endif
#if defined(RD_HIERARCHICAL_TIMESTEPS) || defined(REFINEMENT) || defined(REFINEMENT_HIGH_RES_GAS) || defined(MHD) || \
    defined(PASSIVE_SCALARS)
#error "RD_ALE_EQUALSTEP v1 excludes hierarchy, refinement, MHD and passive scalars."
#endif
#if defined(SELFGRAVITY) || defined(EXTERNALGRAVITY) || defined(EXACT_GRAVITY_FOR_PARTICLE_TYPE)
#error "RD_ALE_EQUALSTEP v1 excludes gravity."
#endif
#if defined(REFLECTIVE_X) || defined(REFLECTIVE_Y) || defined(REFLECTIVE_Z)
#error "RD_ALE_EQUALSTEP v1 requires periodic boundaries."
#endif
#endif

/* The element frame covers N, LDA and the conservative N/LDA B blend in the
 * equal-step path, and N in the concentrated moving hierarchy.  G(b_T) is a
 * similarity of the ALE operator.  In the concentrated hierarchy predictor
 * and corrector are consecutive after one rebuild, so their pulled-back
 * geometry and b_T are identical; this is not true of the older two-call
 * static-hierarchy path, which remains excluded. */
#if defined(RD_ELEMENT_COMOVING_FRAME) &&                                                        \
    ((!defined(RD_ALE_EQUALSTEP) && !defined(RD_ALE_HIERARCHICAL)) ||                            \
     (!defined(LDA_SCHEME) && !defined(N_SCHEME) && !defined(B_SCHEME)) ||                       \
     defined(RD_RK2_RATE_CONSISTENT_HEUN) ||                                                     \
     (defined(RD_HIERARCHICAL_TIMESTEPS) && !defined(RD_ALE_HIERARCHICAL)))
#error "RD_ELEMENT_COMOVING_FRAME requires the equal-step ALE path or the concentrated moving hierarchy."
#endif
#if defined(RD_ELEMENT_COMOVING_FRAME) && defined(RD_ALE_CONDITION_DIAGNOSTIC)
#error "Use separate builds for RD_ELEMENT_COMOVING_FRAME and the lab-vs-frame diagnostic."
#endif
#if defined(RD_ALE_CONTOUR_RESIDUAL) &&                                                          \
    ((!defined(RD_ALE_EQUALSTEP) && !defined(RD_ALE_HIERARCHICAL) &&                            \
      !(defined(VORONOI_STATIC_MESH) && defined(CREATE_FULL_MESH) &&                            \
        defined(LDA_SCHEME) && defined(RD_RK2_TOTAL_RESIDUAL))) ||                              \
     (!defined(LDA_SCHEME) && !defined(N_SCHEME) && !defined(B_SCHEME)))
#error "RD_ALE_CONTOUR_RESIDUAL requires equal-step ALE, concentrated moving hierarchy, or static full-mesh RK2 LDA."
#endif
/* N's contour reconciliation is covariant too: it distributes
 * (Phi_contour - sum_i phi_i^N)/3, and G is linear, so both totals transform
 * under G, their difference transforms under G, and division by three commutes
 * with it. */

#ifdef RD_ALE_HIERARCHICAL
#if defined(VORONOI_STATIC_MESH) || !defined(RD_HIERARCHICAL_TIMESTEPS) || !defined(RD_RK2_TOTAL_RESIDUAL) || \
    !(defined(N_SCHEME) || ((defined(LDA_SCHEME) || defined(B_SCHEME)) && defined(RD_ALE_INTERVAL_HIERARCHY))) || \
    !defined(CREATE_FULL_MESH)
#error "RD_ALE_HIERARCHICAL v1 requires moving mesh, CREATE_FULL_MESH, hierarchy, total-residual RK2 and N (LDA: interval mode)."
#endif
#if(defined(RD_ALE_CAMPOLI_MASS) + defined(RD_ALE_HIERARCHICAL_ARPAIA)) != 1
#error "RD_ALE_HIERARCHICAL requires exactly one temporal mass pair: Campoli or experimental Arpaia."
#endif
#if defined(FORCE_EQUAL_TIMESTEPS) && defined(RD_HIERARCHICAL_TEST_PATTERN)
#error "Use either the equal-bin degeneration or RD_HIERARCHICAL_TEST_PATTERN, not both."
#endif
#if defined(REFINEMENT) || defined(REFINEMENT_HIGH_RES_GAS) || defined(MHD) || defined(PASSIVE_SCALARS)
#error "RD_ALE_HIERARCHICAL v1 excludes refinement, MHD and passive scalars."
#endif
#if defined(SELFGRAVITY) || defined(EXTERNALGRAVITY) || defined(EXACT_GRAVITY_FOR_PARTICLE_TYPE)
#error "RD_ALE_HIERARCHICAL v1 excludes gravity."
#endif
#if defined(REFLECTIVE_X) || defined(REFLECTIVE_Y) || defined(REFLECTIVE_Z)
#error "RD_ALE_HIERARCHICAL v1 requires periodic boundaries."
#endif
#endif

#ifdef RD_ALE_INTERVAL_HIERARCHY
#if !defined(RD_ALE_HIERARCHICAL) || !defined(RD_ALE_CAMPOLI_MASS) || defined(RD_ALE_HIERARCHICAL_ARPAIA) || \
    !(defined(N_SCHEME) || defined(LDA_SCHEME) || defined(B_SCHEME)) || \
    !(defined(RD_ALE_CONTOUR_RESIDUAL) || defined(RD_RUSANOV_LOW_ORDER))
#error "RD_ALE_INTERVAL_HIERARCHY requires the Campoli RD_ALE_HIERARCHICAL N/LDA path with a conservative contour residual."
#endif
#include "rd_flip_transfer.h"
#ifndef RD_FLIP_FLOOR_FRACTION
#define RD_FLIP_FLOOR_FRACTION 0.5
#endif
#ifndef RD_FLIP_DMP_RELAX
#define RD_FLIP_DMP_RELAX (-1.0)
#endif
#ifndef RD_FLIP_ENTROPY_BOUND
#define RD_FLIP_ENTROPY_BOUND 0
#endif
#ifndef RD_FLIP_HIGH_MODE
/* 1 (receiver-only) since 2026-10-09: same conservation and accuracy as the
 * uniform shift in Yee/Sod/Sedov, no KH entropy excursion (results report
 * §3.4). Frozen archives before this date used 0 unless their Config says 1. */
#define RD_FLIP_HIGH_MODE 1
#endif
#ifndef RD_CFL_LEDGER_LIMIT
/* Frozen-vertex positivity: sum (h/2)(c0+c1) since the last refresh must not
 * exceed RD_CFL_LEDGER_LIMIT times the refreshed mass (the sufficient condition
 * is 1).  Smaller values only serve a controlled-overrun test of the check. */
#define RD_CFL_LEDGER_LIMIT 1.0
#endif
#endif
#ifdef RD_ALE_LAZY_FLIP
#ifndef RD_ALE_INTERVAL_HIERARCHY
#error "RD_ALE_LAZY_FLIP adopts registry changes and requires RD_ALE_INTERVAL_HIERARCHY."
#endif
#ifndef RD_LAZY_MIN_ANGLE
#define RD_LAZY_MIN_ANGLE 15.0 /* degrees: adopt a cavity once an old triangle is this thin */
#endif
#ifndef RD_LAZY_DELAUNAY_EXCESS
#define RD_LAZY_DELAUNAY_EXCESS 20.0 /* degrees: ... or an old edge violates Delaunay by this much */
#endif
#endif
#if defined(RD_ALE_INTERVAL_NO_TRANSFER) && !defined(RD_ALE_INTERVAL_HIERARCHY)
#error "RD_ALE_INTERVAL_NO_TRANSFER is a negative control of RD_ALE_INTERVAL_HIERARCHY."
#endif

#ifdef RD_HIERARCHICAL_TIMESTEPS
#if !defined(RD_RK2_TOTAL_RESIDUAL) || \
    (!defined(N_SCHEME) && !defined(LDA_SCHEME) && !(defined(B_SCHEME) && defined(RD_ALE_INTERVAL_HIERARCHY)))
#error "RD_HIERARCHICAL_TIMESTEPS requires RD_RK2_TOTAL_RESIDUAL with N or LDA (B: interval hierarchy only)."
#endif
#if defined(RD_ALE_HIERARCHICAL) && defined(RD_ALE_HIERARCHICAL_ARPAIA)
#define RD_RK2_STAGE_BETA_LABEL "concentrated-ALE-hierarchy-N-Arpaia"
#elif defined(RD_ALE_INTERVAL_HIERARCHY) && defined(LDA_SCHEME)
#define RD_RK2_STAGE_BETA_LABEL "interval-ALE-hierarchy-LDA-F1-Campoli"
#elif defined(RD_ALE_INTERVAL_HIERARCHY) && defined(B_SCHEME)
#define RD_RK2_STAGE_BETA_LABEL "interval-ALE-hierarchy-B-total-theta-Campoli"
#elif defined(RD_ALE_INTERVAL_HIERARCHY)
#define RD_RK2_STAGE_BETA_LABEL "interval-ALE-hierarchy-N-Campoli"
#elif defined(RD_ALE_HIERARCHICAL)
#define RD_RK2_STAGE_BETA_LABEL "concentrated-ALE-hierarchy-N-Campoli"
#elif defined(LDA_SCHEME)
#ifdef RD_LDA_COMMON_BETA
#define RD_RK2_STAGE_BETA_LABEL "two-call-LDA-F1-common-opening"
#else
#define RD_RK2_STAGE_BETA_LABEL "two-call-LDA-F1-frozen"
#endif
#else
#define RD_RK2_STAGE_BETA_LABEL "two-call-N-lumped"
#endif
#endif

#if defined(RD_HIERARCHICAL_TEST_PATTERN) && !defined(RD_HIERARCHICAL_TIMESTEPS)
#error "RD_HIERARCHICAL_TEST_PATTERN is only valid for the experimental RD hierarchy."
#endif

#if defined(RD_RK2_TOTAL_RESIDUAL) && !defined(RD_HIERARCHICAL_TIMESTEPS)
#define RD_RK2_EQUALSTEP
#endif

#ifdef RD_RK2_SPLIT_STAGES
#if !defined(RESIDUAL_DISTRIBUTION) || (!defined(VORONOI_STATIC_MESH) && !defined(RD_ALE_EQUALSTEP)) || !defined(FORCE_EQUAL_TIMESTEPS) || \
    !defined(RD_RK2_EQUALSTEP) || (!defined(N_SCHEME) && !defined(LDA_SCHEME)) || defined(RD_RK2_RATE_CONSISTENT_HEUN)
#error "RD_RK2_SPLIT_STAGES requires static or ALE equal-timestep N/LDA with standard total-residual RK2."
#endif
#if defined(REFINEMENT) || defined(REFINEMENT_HIGH_RES_GAS) || defined(MHD) || defined(PASSIVE_SCALARS) || \
    defined(SELFGRAVITY) || defined(EXTERNALGRAVITY) || defined(EXACT_GRAVITY_FOR_PARTICLE_TYPE) || defined(COOLING) || \
    defined(RD_RT_FIXED_BOUNDARY) || defined(RD_DIAG_PREDICTOR_ONLY) || defined(RD_DIAG_SKIP_PREPARE) || defined(RD_DIAG_NO_KICK)
#error "RD_RK2_SPLIT_STAGES supports source-free hydro without refinement or stage-altering diagnostics."
#endif
#endif

#if defined(RD_ALE_APOSTERIORI_FALLBACK) && \
    (!defined(RD_ALE_EQUALSTEP) || !defined(RD_RK2_EQUALSTEP) || !defined(B_SCHEME) || defined(RD_RK2_RATE_CONSISTENT_HEUN))
#error "RD_ALE_APOSTERIORI_FALLBACK is the equal-step two-pass B-engine diagnostic (binary LDA/N only)."
#endif

#if(defined(LDA_SCHEME) + defined(N_SCHEME) + defined(B_SCHEME)) != 1
#error "Select exactly one residual-distribution scheme: LDA_SCHEME, N_SCHEME, or B_SCHEME."
#endif

#if defined(RD_RK2_TOTAL_RESIDUAL) && defined(B_SCHEME) && defined(RD_HIERARCHICAL_TIMESTEPS) && \
    !defined(RD_ALE_INTERVAL_HIERARCHY)
#error "RD_RK2_TOTAL_RESIDUAL with B_SCHEME in a hierarchy is derived only for the interval moving hierarchy."
#endif

#if defined(RD_RK2_RATE_CONSISTENT_HEUN) && \
    (!defined(RD_RK2_TOTAL_RESIDUAL) || !defined(LDA_SCHEME) || defined(RD_HIERARCHICAL_TIMESTEPS))
#error "RD_RK2_RATE_CONSISTENT_HEUN is an equal-bin LDA+F1 experiment and requires RD_RK2_TOTAL_RESIDUAL."
#endif

#if defined(RD_RK2_RATE_CONSISTENT_HEUN)
#define RD_RK2_STAGE_BETA_LABEL "rate-consistent-LDA-F1-Heun"
#define RD_UPWIND_NRHS 3
#elif defined(RD_HIERARCHICAL_TIMESTEPS)
#define RD_UPWIND_NRHS 3
#elif defined(B_SCHEME) && defined(RD_ALE_APOSTERIORI_FALLBACK)
#define RD_RK2_STAGE_BETA_LABEL "a-posteriori-LDA-N"
#define RD_UPWIND_NRHS 3
#elif defined(B_SCHEME)
#define RD_RK2_STAGE_BETA_LABEL "coherent-total-B"
#define RD_UPWIND_NRHS 3
#else
#ifdef RD_LDA_COMMON_BETA
#define RD_RK2_STAGE_BETA_LABEL "common-opening"
#else
#define RD_RK2_STAGE_BETA_LABEL "mixed"
#endif
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

#ifndef TWODIMS
  if(T->DT[triangle_index].t[0] < 0) /* 3D flip deletion leaves stale vertex slots. */
    return 0;
#endif

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

#ifdef RD_ALE_INTERVAL_HIERARCHY
/* Per-event interval-hierarchy views, owned by rd_ale_interval_event(). */
static char *RdIntervalLive = NULL;  /* local index -> predictor live (whole star due, one start) */
static double *RdIntervalDt = NULL;  /* synthetic element -> its actual interval h_T */
#ifdef B_SCHEME
/* Stage-0 N and LDA distributions, the applied stage-0 blend and Phi(U^n),
 * kept from the predictor to the corrector call of the same event. */
struct rd_interval_b_stage0
{
  double n[4][3], lda[4][3], applied[4][3], phi[4];
};
static struct rd_interval_b_stage0 *RdIntervalB = NULL;
#endif
static int RdIntervalN = 0;
static int rd_point_stage_live(const point *dp) { return RdIntervalLive[rd_local_point_index(dp)]; }
#else
static int rd_point_stage_live(const point *dp) { return rd_point_star_timebin(dp) == rd_point_timebin(dp); }
#endif

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
#ifdef RD_ALE_INTERVAL_HIERARCHY
  for(int i = 0; i < NumGas; i++)
    {
      for(int k = 0; k < 4; k++)
        SphP[i].RD_dU[k] = 0.0;
      SphP[i].RD_PredictorEnd = RdIntervalLive[i] ? All.Ti_Current : -1;
    }
  return;
#endif
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
#ifdef RD_ALE_HIERARCHICAL
          SphP[i].RD_PredictorEnd = All.Ti_Current;
#else
          SphP[i].RD_PredictorEnd = All.Ti_Current + (((integertime)1) << P[i].TimeBinHydro);
#endif
        }
    }
}
#endif

/* Per-call diagnostics for the upwind system solve (item A4 of the report). */
static long long RD_stat_elements;         /* elements whose residual was evaluated */
static long long RD_stat_pinv_fallback;    /* elements that needed the pseudo-inverse */
static long long RD_stat_exact_singular;   /* LU factorizations with an exactly singular pivot */
static lapack_int RD_stat_min_svd_rank;    /* smallest numerical rank returned by DGELSD */
static long long RD_stat_svd_rank_count[DIMS + 3]; /* DGELSD calls returning each rank 0,...,DIMS+2 */
static double RD_stat_min_pivot_ratio;     /* smallest min|diag(U)|/max|diag(U)| seen */
static double RD_stat_max_cons_defect_abs; /* largest raw conservation defect, absolute */
static double RD_stat_max_phi;             /* largest |phi^T| seen, for context on the absolute figure */
static double RD_stat_ever_max_cons_defect_abs; /* high-water mark across calls; NOT reset per call */
#ifdef RD_ALE_CONDITION_DIAGNOSTIC
static double RD_stat_max_condition_lab;
static double RD_stat_shift_condition_at_lab_max;
static double RD_stat_max_backward_error_lab;
static double RD_stat_max_backward_error_shift;
static double RD_stat_max_shift_a2_defect;
static lapack_int RD_stat_min_shift_rank;
#endif
#ifdef RD_ELEMENT_COMOVING_FRAME
static double RD_stat_max_comoving_correction_covariance;
static double RD_stat_max_comoving_phi_covariance;
static double RD_stat_max_comoving_phi_covariance_relative;
#endif
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

#ifdef RD_DIAG_THETA_MAP
/* Final-step, element-local B diagnostic.  This deliberately records only
 * quantities already computed by the corrector: it does not participate in
 * the residual or alter the update.  One file per MPI task avoids a gather
 * proportional to the number of triangles. */
static FILE *rd_theta_map_open(void)
{
  char filename[MAXLEN_PATH + 64];
  snprintf(filename, sizeof(filename), "%srd_theta_map_task%03d.csv", All.OutputDir, ThisTask);

  FILE *stream = fopen(filename, "w");
  if(stream == NULL)
    terminate_program("could not open RD theta-map diagnostic output");

  fprintf(stream,
          "triangle_slot,triangle_index,id0,id1,id2,cx,cy,area,"
          "theta_rho,theta_px,theta_py,theta_energy,"
          "nlda_gap_rho,nlda_gap_energy,b_blend_rho,b_blend_energy\n");
  return stream;
}
#endif

static void rd_reset_solver_statistics(void)
{
  RD_stat_elements        = 0;
  RD_stat_pinv_fallback   = 0;
  RD_stat_exact_singular  = 0;
  RD_stat_min_svd_rank    = DIMS + 3; /* sentinel: no DGELSD call in this solver pass */
  for(int rank = 0; rank <= DIMS + 2; rank++)
    RD_stat_svd_rank_count[rank] = 0;
  RD_stat_min_pivot_ratio     = 1.0;
  RD_stat_max_cons_defect_abs = 0.0;
  RD_stat_max_phi             = 0.0;
#ifdef RD_ALE_CONDITION_DIAGNOSTIC
  RD_stat_max_condition_lab          = 0.0;
  RD_stat_shift_condition_at_lab_max = 0.0;
  RD_stat_max_backward_error_lab     = 0.0;
  RD_stat_max_backward_error_shift   = 0.0;
  RD_stat_max_shift_a2_defect        = 0.0;
  RD_stat_min_shift_rank             = 5;
#endif
#ifdef RD_ELEMENT_COMOVING_FRAME
  RD_stat_max_comoving_correction_covariance = 0.0;
  RD_stat_max_comoving_phi_covariance = 0.0;
  RD_stat_max_comoving_phi_covariance_relative = 0.0;
#endif
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

/*! Build K_i^+, K_i^- and K_i in an explicitly chosen inertial frame.
 *  Keeping this algebra in one routine lets the boost diagnostic construct
 *  the operator directly in co-moving variables, rather than obtaining it by
 *  an ill-conditioned similarity transform of the laboratory matrix. */
static void rd_build_characteristic_matrices(double velx, double vely, double enthalpy, double cs,
                                             double mesh_velx, double mesh_vely, const double normal_x[3],
                                             const double normal_y[3], const double magnitude[3],
                                             double lambda[3][4], double Kmatrix[4][4][3][3])
{
  for(int vertex = 0; vertex < 3; vertex++)
    {
      double vel_dot_n = velx * normal_x[vertex] + vely * normal_y[vertex];
      double mesh_dot_n = mesh_velx * normal_x[vertex] + mesh_vely * normal_y[vertex];
      lambda[vertex][0] = vel_dot_n + cs - mesh_dot_n;
      lambda[vertex][1] = vel_dot_n - cs - mesh_dot_n;
      lambda[vertex][2] = vel_dot_n - mesh_dot_n;
      lambda[vertex][3] = vel_dot_n - mesh_dot_n;

      for(int split = 0; split < 3; split++)
        {
          double value1, value2, value3;
          if(split == 0)
            {
              value1 = dmax(0.0, lambda[vertex][0]);
              value2 = dmax(0.0, lambda[vertex][1]);
              value3 = dmax(0.0, lambda[vertex][2]);
            }
          else if(split == 1)
            {
              value1 = dmin(0.0, lambda[vertex][0]);
              value2 = dmin(0.0, lambda[vertex][1]);
              value3 = dmin(0.0, lambda[vertex][2]);
            }
          else
            {
              value1 = lambda[vertex][0];
              value2 = lambda[vertex][1];
              value3 = lambda[vertex][2];
            }

          const double velocity[2] = {velx, vely};
          const double normal[2] = {normal_x[vertex], normal_y[vertex]};
          const double eigenvalues[3] = {value1, value2, value3};
          double matrix[4][4];
          if(rd_euler_spectral_matrix(2, velocity, enthalpy, cs, GAMMA, normal, magnitude[vertex],
                                      eigenvalues, &matrix[0][0]) != 0)
            terminate_program("Invalid RD characteristic matrix input");
          for(int row = 0; row < 4; row++)
            for(int col = 0; col < 4; col++)
              Kmatrix[row][col][vertex][split] = matrix[row][col];
        }
    }
}

#ifdef RD_ALE_ENTROPY_DISSIPATION
/*! \brief Restore the entropy-mode dissipation a Lagrangian mesh loses.
 *
 *  Derivation and the meaning of every symbol: dev_log/RD_ALE_entropy_dissipation.md.
 *
 *  A_sigma(n) = A(n) - (sigma.n)I differs from A(n) by a multiple of the
 *  identity, so the two share eigenvectors and the ALE eigenvalues are
 *  u.n - sigma.n, twice, and u.n - sigma.n +- c.  The entropy right eigenvector
 *  r_e = (1, u, v, |q|^2/2) is the SAME for every direction, while the shear
 *  eigenvector rotates with the tangent.  At sigma = u the intersection of the
 *  three face kernels of an element is therefore exactly span{r_e}: the entropy
 *  mode gets no upwind dissipation on any face, and S^- is singular along it.
 *
 *  This adds  eta_j P_e  to K_j^+ and subtracts it from K_j^-, with
 *  P_e = r_e l_e^T the spectral projector and
 *
 *      eta_j = (1/2) |n_j| max(0, eps c - |u - sigmabar_T|).
 *
 *  Three properties, all proved in the derivation:
 *    - K^+ + K^- = K is untouched, so sum_i phi_i = Phi and conservation are
 *      exact.  The term changes only the dissipation, never the flux.
 *    - sum_i K_i^+ = -S^- survives, so sum_i beta_i = I exactly and LDA stays
 *      linearity-preserving, hence formally second order.
 *    - the eigenvalues and r_e are Galilean covariant, so G(b_T) still gives a
 *      similarity and the element-frame covariance is unchanged.
 *
 *  The gate is the ELEMENT relative speed, not the per-face one: w_j vanishes
 *  on any face whose normal is perpendicular to the flow, which happens
 *  routinely on a static mesh, so a per-face gate would fire there and change
 *  every validated static-mesh result.
 *
 *  \param velx,vely,enthalpy,cs  element-average state in the frame Kmatrix
 *         was assembled in.
 *  \param rel_velx,rel_vely  u - sigmabar_T in that same frame.  In the element
 *         co-moving frame this is just (velx, vely), since sigma' has zero mean.
 */
static void rd_add_entropy_dissipation(double velx, double vely, double enthalpy, double cs,
                                       double rel_velx, double rel_vely, const double magnitude[3],
                                       int kplus, int kminus, double Kmatrix[4][4][3][3])
{
  const double relative_speed = sqrt(rel_velx * rel_velx + rel_vely * rel_vely);
  const double floor_speed    = RD_ALE_ENTROPY_DISSIPATION * cs;
  const double deficit        = floor_speed - relative_speed;
  if(!(deficit > 0.0))
    return; /* the mesh is far enough from Lagrangian: exactly no change */

  const double q2 = velx * velx + vely * vely;
  const double r_e[4] = {1.0, velx, vely, 0.5 * q2};
  const double l_e[4] = {1.0 - GAMMA_MINUS1 * q2 / (2.0 * cs * cs), GAMMA_MINUS1 * velx / (cs * cs),
                         GAMMA_MINUS1 * vely / (cs * cs), -GAMMA_MINUS1 / (cs * cs)};
  (void)enthalpy;

  for(int vertex = 0; vertex < 3; vertex++)
    {
      const double eta = 0.5 * magnitude[vertex] * deficit;
      for(int row = 0; row < 4; row++)
        for(int col = 0; col < 4; col++)
          {
            const double d = eta * r_e[row] * l_e[col];
            Kmatrix[row][col][vertex][kplus] += d;
            Kmatrix[row][col][vertex][kminus] -= d;
          }
    }
}
#endif
#ifdef RD_ALE_SHEAR_EIGENVALUE_FLOOR
/*! \brief Diagnostic Harten-type modulus floor for the ALE shear field.
 *
 *  The unmodified shear eigenvalue on face j is
 *
 *      lambda_s,j = (u - sigmabar_T) . n_hat_j.
 *
 *  If the element is near Lagrangian, |u-sigmabar_T| < eps_s c, replace only
 *  its shear modulus by d_s,j=max(|lambda_s,j|,eps_s c) in the conservative
 *  split lambda_s^{+/-*}=0.5(lambda_s,j +/- d_s,j).  The corresponding change
 *  to the already assembled face matrices is
 *
 *      K_j^{+*} = K_j^+ + |n_j|(d_s,j-|lambda_s,j|) P_s,j / 4,
 *      K_j^{-*} = K_j^- - |n_j|(d_s,j-|lambda_s,j|) P_s,j / 4.
 *
 *  Thus K_j^{+*}+K_j^{-*}=K_j exactly: this changes dissipation but neither
 *  the ALE flux nor the element total residual.  P_s,j=r_s,j l_s,j^T uses
 *
 *      t_j=(-n_y,n_x),  r_s=(0,t_x,t_y,u.t)^T,
 *      l_s=(-u.t,t_x,t_y,0),
 *
 *  so l_s r_s=1 and P_s annihilates the entropy and acoustic eigenvectors.
 *  Unlike RD_ALE_ENTROPY_DISSIPATION, the deficit is evaluated per face and
 *  contains the factor 1/2 from the conservative eigenvalue split.
 */
static void rd_apply_shear_eigenvalue_floor(double velx, double vely, double cs,
                                            double rel_velx, double rel_vely,
                                            const double normal_x[3], const double normal_y[3],
                                            const double magnitude[3], int kplus, int kminus,
                                            double Kmatrix[4][4][3][3])
{
  const double epsilon = RD_ALE_SHEAR_EIGENVALUE_FLOOR;
  if(!(epsilon > 0.0) || !(epsilon < 1.0) || !isfinite(epsilon))
    terminate_program("RD_ALE_SHEAR_EIGENVALUE_FLOOR must satisfy 0 < epsilon < 1");

  const double relative_speed = sqrt(rel_velx * rel_velx + rel_vely * rel_vely);
  const double floor_speed = epsilon * cs;
  if(!(relative_speed < floor_speed))
    return;

  for(int vertex = 0; vertex < 3; vertex++)
    {
      const double lambda_s = rel_velx * normal_x[vertex] + rel_vely * normal_y[vertex];
      const double deficit = floor_speed - fabs(lambda_s);
      if(!(deficit > 0.0))
        continue;

      const double tangent_x = -normal_y[vertex];
      const double tangent_y = normal_x[vertex];
      const double velocity_tangent = velx * tangent_x + vely * tangent_y;
      const double r_s[4] = {0.0, tangent_x, tangent_y, velocity_tangent};
      const double l_s[4] = {-velocity_tangent, tangent_x, tangent_y, 0.0};
      const double eta = 0.25 * magnitude[vertex] * deficit;

      for(int row = 0; row < 4; row++)
        for(int col = 0; col < 4; col++)
          {
            const double correction = eta * r_s[row] * l_s[col];
            Kmatrix[row][col][vertex][kplus] += correction;
            Kmatrix[row][col][vertex][kminus] -= correction;
          }
    }
}
#endif

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
  struct rd_solve_info result;
#ifdef RD_ALWAYS_PSEUDOINVERSE
  const int always_svd = 1;
#else
  const int always_svd = 0;
#endif
  const int info = rd_upwind_solve(4, &S[0][0], rhs, nrhs, RD_SVD_RCOND, always_svd, &result);
  *rank = result.rank;
  RD_stat_exact_singular += result.exact_singular;
  RD_stat_min_pivot_ratio = dmin(RD_stat_min_pivot_ratio, result.pivot_ratio);
  RD_stat_pinv_fallback += result.used_svd;
  if(result.used_svd && info == 0)
    {
      RD_stat_min_svd_rank = imin(RD_stat_min_svd_rank, result.rank);
      RD_stat_svd_rank_count[result.rank]++;
    }
  return info;
}

#ifdef RD_ALE_CONDITION_DIAGNOSTIC
static void rd_matmul4(const double A[4][4], const double B[4][4], double C[4][4])
{
  for(int i = 0; i < 4; i++)
    for(int j = 0; j < 4; j++)
      {
        C[i][j] = 0.0;
        for(int k = 0; k < 4; k++)
          C[i][j] += A[i][k] * B[k][j];
      }
}

static void rd_matvec4(const double A[4][4], const double x[4], double y[4])
{
  for(int i = 0; i < 4; i++)
    {
      y[i] = 0.0;
      for(int k = 0; k < 4; k++)
        y[i] += A[i][k] * x[k];
    }
}

static int rd_singular_values4(const double matrix[4][4], double singular[4])
{
  double A[16], U[16], VT[16], superb[3];
  memcpy(A, &matrix[0][0], sizeof(A));
  return (int)LAPACKE_dgesvd(LAPACK_ROW_MAJOR, 'A', 'A', 4, 4, A, 4, singular, U, 4, VT, 4, superb);
}

static double rd_backward_error4(const double A[4][4], const double x[4], const double b[4])
{
  long double residual_norm = 0.0L, matrix_norm = 0.0L, x_norm = 0.0L, b_norm = 0.0L;

  for(int i = 0; i < 4; i++)
    {
      long double row_sum = 0.0L, ax = 0.0L;
      x_norm = fmaxl(x_norm, fabsl((long double)x[i]));
      b_norm = fmaxl(b_norm, fabsl((long double)b[i]));
      for(int j = 0; j < 4; j++)
        {
          row_sum += fabsl((long double)A[i][j]);
          ax += (long double)A[i][j] * (long double)x[j];
        }
      matrix_norm = fmaxl(matrix_norm, row_sum);
      residual_norm = fmaxl(residual_norm, fabsl((long double)b[i] - ax));
    }

  long double denominator = b_norm + matrix_norm * x_norm;
  return (denominator > 0.0L) ? (double)(residual_norm / denominator) : (double)residual_norm;
}

/*! Compare the LDA solve in laboratory conserved variables with the same
 *  algebra after a Galilean change of conservative coordinates.  This is
 *  diagnostic only: Flux_RD remains the unmodified production result.
 *
 *  For frame velocity b,
 *    U' = G(b) U = (rho, m-rho b, E-b.m+rho|b|^2/2),
 *  and the identical linear map is S' = G S G^{-1}.  A large reduction in
 *  condition number or A2 defect therefore identifies coordinate scaling,
 *  rather than a physical loss of rank, as the boosted failure mechanism. */
static void rd_diagnose_lda_condition(const double S[4][4], int kplus, const double Phi[4],
                                      const double X_lab[4], const double Flux_lab[4][3],
                                      const double frame_velocity[3], double velx_avg, double vely_avg, double h_avg,
                                      double cs_avg, const double normal_x[3], const double normal_y[3],
                                      const double magnitude[3], double roundoff_scale, int triangle_index)
{
  double b0 = frame_velocity[0], b1 = frame_velocity[1], b2 = b0 * b0 + b1 * b1;
  double G[4][4] = {{1.0, 0.0, 0.0, 0.0},
                    {-b0, 1.0, 0.0, 0.0},
                    {-b1, 0.0, 1.0, 0.0},
                    {0.5 * b2, -b0, -b1, 1.0}};
  double Ginv[4][4] = {{1.0, 0.0, 0.0, 0.0},
                       {b0, 1.0, 0.0, 0.0},
                       {b1, 0.0, 1.0, 0.0},
                       {0.5 * b2, b0, b1, 1.0}};
  double work[4][4], S_similarity[4][4];
  rd_matmul4(G, S, work);
  rd_matmul4(work, Ginv, S_similarity);

  double velx_shift = velx_avg - b0, vely_shift = vely_avg - b1;
  double h_shift = h_avg - b0 * velx_avg - b1 * vely_avg + 0.5 * b2;
  double lambda_shift[3][4], K_shift[4][4][3][3], S_shift[4][4];
  rd_build_characteristic_matrices(velx_shift, vely_shift, h_shift, cs_avg, 0.0, 0.0,
                                   normal_x, normal_y, magnitude, lambda_shift, K_shift);
  for(int row = 0; row < 4; row++)
    for(int col = 0; col < 4; col++)
      {
        S_shift[row][col] = 0.0;
        for(int vertex = 0; vertex < 3; vertex++)
          S_shift[row][col] += K_shift[row][col][vertex][1];
      }

  double similarity_gap = 0.0, direct_scale = 0.0;
  for(int row = 0; row < 4; row++)
    for(int col = 0; col < 4; col++)
      {
        similarity_gap = dmax(similarity_gap, fabs(S_similarity[row][col] - S_shift[row][col]));
        direct_scale = dmax(direct_scale, fabs(S_shift[row][col]));
      }
  if(direct_scale > 0.0)
    similarity_gap /= direct_scale;

  double singular_lab[4], singular_shift[4];
  int svd_info_lab = rd_singular_values4(S, singular_lab);
  int svd_info_shift = rd_singular_values4(S_shift, singular_shift);
  if(svd_info_lab != 0 || svd_info_shift != 0)
    return;

  double condition_lab = (singular_lab[3] > 0.0) ? singular_lab[0] / singular_lab[3] : INFINITY;
  double condition_shift = (singular_shift[3] > 0.0) ? singular_shift[0] / singular_shift[3] : INFINITY;
  double eta_lab = rd_backward_error4(S, X_lab, Phi);

  double Phi_shift[4];
  rd_matvec4(G, Phi, Phi_shift);
  double X_shift[4] = {Phi_shift[0], Phi_shift[1], Phi_shift[2], Phi_shift[3]};
  double A_shift[16], solve_singular[4];
  lapack_int rank_shift = -1;
  memcpy(A_shift, &S_shift[0][0], sizeof(A_shift));
  lapack_int solve_info = LAPACKE_dgelsd(LAPACK_ROW_MAJOR, 4, 4, 1, A_shift, 4, X_shift, 1, solve_singular,
                                         RD_SVD_RCOND, &rank_shift);
  if(solve_info != 0)
    return;

  double eta_shift = rd_backward_error4(S_shift, X_shift, Phi_shift);
  double Flux_shift[4][3], Flux_shift_back[4][3];
  for(int vertex = 0; vertex < 3; vertex++)
    {
      double Kplus_shift[4][4], flux_prime[4], flux_back[4];
      for(int row = 0; row < 4; row++)
        for(int col = 0; col < 4; col++)
          Kplus_shift[row][col] = K_shift[row][col][vertex][kplus];
      rd_matvec4(Kplus_shift, X_shift, flux_prime);
      for(int row = 0; row < 4; row++)
        {
          flux_prime[row] = -flux_prime[row];
          Flux_shift[row][vertex] = flux_prime[row];
        }
      rd_matvec4(Ginv, flux_prime, flux_back);
      for(int row = 0; row < 4; row++)
        Flux_shift_back[row][vertex] = flux_back[row];
    }

  double a2_lab = 0.0, a2_shift = 0.0, a2_shift_coordinates = 0.0;
  for(int row = 0; row < 4; row++)
    {
      double sum_lab = 0.0, sum_shift = 0.0, sum_shift_coordinates = 0.0;
      for(int vertex = 0; vertex < 3; vertex++)
        {
          sum_lab += Flux_lab[row][vertex];
          sum_shift += Flux_shift_back[row][vertex];
          sum_shift_coordinates += Flux_shift[row][vertex];
        }
      a2_lab = dmax(a2_lab, fabs(Phi[row] - sum_lab));
      a2_shift = dmax(a2_shift, fabs(Phi[row] - sum_shift));
      a2_shift_coordinates = dmax(a2_shift_coordinates, fabs(Phi_shift[row] - sum_shift_coordinates));
    }

  if(condition_lab > RD_stat_max_condition_lab)
    {
      RD_stat_max_condition_lab = condition_lab;
      RD_stat_shift_condition_at_lab_max = condition_shift;
    }
  RD_stat_max_backward_error_lab = dmax(RD_stat_max_backward_error_lab, eta_lab);
  RD_stat_max_backward_error_shift = dmax(RD_stat_max_backward_error_shift, eta_shift);
  RD_stat_max_shift_a2_defect = dmax(RD_stat_max_shift_a2_defect, a2_shift);
  RD_stat_min_shift_rank = imin(RD_stat_min_shift_rank, rank_shift);

  double tolerance = RD_CONSERVATION_ROUNDOFF_FACTOR * DBL_EPSILON * roundoff_scale;
  if(a2_lab > 0.5 * tolerance)
    printf("RD-COND task=%d triangle=%d frame=[%.17g,%.17g] "
           "s_lab=[%.6e,%.6e,%.6e,%.6e] cond_lab=%.6e eta_lab=%.6e a2_lab=%.6e "
           "s_shift=[%.6e,%.6e,%.6e,%.6e] cond_shift=%.6e rank_shift=%d eta_shift=%.6e "
           "similarity_gap=%.6e a2_shift_coord=%.6e a2_shift_back=%.6e tol=%.6e\n",
           ThisTask, triangle_index, b0, b1, singular_lab[0], singular_lab[1], singular_lab[2], singular_lab[3],
           condition_lab, eta_lab, a2_lab, singular_shift[0], singular_shift[1], singular_shift[2], singular_shift[3],
           condition_shift, (int)rank_shift, eta_shift, similarity_gap, a2_shift_coordinates, a2_shift, tolerance);
}
#endif

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

#ifdef RD_LDA_COMMON_BETA
/*! Extend the singular spatial distribution to arbitrary stage residuals:
 * beta_i = -K_i^+ S^dagger + (I - S S^dagger)/3, S=sum K^-.
 * The unresolved component is shared equally. This is an explicit numerical
 * choice, needed because phi(U*) need not belong to range(S(U^n)); it is not
 * a tolerance change or a full-rank conservation repair. Compatible targets
 * retain the original upwind distribution. The temporal rank fallback is
 * still lumped. */
static void rd_common_beta_unresolved(const double S[4][4], const double x[4], const double target[4],
                                      double projected[4], double share[4])
{
  for(int k = 0; k < 4; k++)
    {
      projected[k] = 0.0;
      for(int p = 0; p < 4; p++)
        projected[k] += S[k][p] * x[p];
      share[k] = (target[k] - projected[k]) / 3.0;
    }
}
#endif

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
#ifdef RD_ALE_EQUALSTEP
  struct rd_ale_triangle_geometry *ale_geometry;
  double *ale_endpoint_area;
#if defined(RD_ALE_TOPOLOGY_REPAIR_DIAGNOSTIC) || defined(RD_ALE_FLIP_TRANSFER)
  double *ale_pullback_area;
#endif
  double *ale_divisor;
#ifdef RD_ALE_CFL_DIAGNOSTIC
  double *ale_cfl_alpha_sum;
#endif
  double(*ale_uold)[4];
  double ale_old_total[4];
  double ale_dt;
  int ale_uniform_initial;
#endif
#ifdef RD_ALE_HIERARCHICAL
  double *ale_hier_divisor_element_area;
  double *ale_hier_endpoint_area;
#ifdef RD_ALE_HIERARCHICAL_ARPAIA
  double *ale_hier_divisor;
#endif
#endif
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
#ifdef RD_3D_STATIC
  if(NumPart != NumGas || All.ComovingIntegrationOn)
    terminate_program("RD_3D_STATIC requires gas only and non-comoving integration");
#endif
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
#ifdef RD_ALE_EQUALSTEP
  set->ale_geometry = NULL;
  set->ale_endpoint_area = NULL;
  set->ale_divisor = NULL;
#if defined(RD_ALE_TOPOLOGY_REPAIR_DIAGNOSTIC) || defined(RD_ALE_FLIP_TRANSFER)
  set->ale_pullback_area = NULL;
#endif
#ifdef RD_ALE_CFL_DIAGNOSTIC
  set->ale_cfl_alpha_sum = NULL;
#endif
  set->ale_uold = NULL;
  set->ale_dt = 0.0;
  set->ale_uniform_initial = 0;
  for(int component = 0; component < 4; component++)
    set->ale_old_total[component] = 0.0;
#endif
#ifdef RD_ALE_HIERARCHICAL
  set->ale_hier_divisor_element_area = NULL;
  set->ale_hier_endpoint_area = NULL;
#ifdef RD_ALE_HIERARCHICAL_ARPAIA
  set->ale_hier_divisor = NULL;
#endif
#endif

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
#else
      double x[4][3], signed_volume = NAN;
      for(int vertex = 0; vertex < 4; vertex++)
        {
          const point *dp = &DP[DT[set->element[i]].p[vertex]];
          /* Use AREPO's already unfolded periodic images, not wrapped P.Pos. */
          x[vertex][0] = dp->x;
          x[vertex][1] = dp->y;
          x[vertex][2] = dp->z;
        }
      if(rd_simplex_geometry(3, &x[0][0], &signed_volume, &set->normals[i].normal[0][0],
                              set->normals[i].mag) != 0 || !(signed_volume > 0.0))
        terminate_program("RD tetra geometry invalid: tetra=%d signed_volume=%.17g", set->element[i], signed_volume);
      set->normals[i].area = signed_volume; /* legacy field name; 3D stores true volume */
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
#ifdef RD_ALE_EQUALSTEP
  if(set->ale_uold != NULL)
    myfree(set->ale_uold);
#ifdef RD_ALE_CFL_DIAGNOSTIC
  if(set->ale_cfl_alpha_sum != NULL)
    myfree(set->ale_cfl_alpha_sum);
#endif
  if(set->ale_divisor != NULL)
    myfree(set->ale_divisor);
#if defined(RD_ALE_TOPOLOGY_REPAIR_DIAGNOSTIC) || defined(RD_ALE_FLIP_TRANSFER)
  if(set->ale_pullback_area != NULL)
    myfree(set->ale_pullback_area);
#endif
  if(set->ale_endpoint_area != NULL)
    myfree(set->ale_endpoint_area);
  if(set->ale_geometry != NULL)
    myfree_movable(set->ale_geometry);
#endif
#ifdef RD_ALE_HIERARCHICAL
#ifdef RD_ALE_HIERARCHICAL_ARPAIA
  if(set->ale_hier_divisor != NULL)
    myfree(set->ale_hier_divisor);
#endif
  if(set->ale_hier_endpoint_area != NULL)
    myfree(set->ale_hier_endpoint_area);
  if(set->ale_hier_divisor_element_area != NULL)
    myfree(set->ale_hier_divisor_element_area);
#endif
  myfree_movable(set->normals);
  myfree_movable(set->active);
  myfree_movable(set->element);
}

#ifdef RD_ALE_EQUALSTEP
static int rd_ale_local_point_index(const point *dp)
{
  if(dp->task != ThisTask)
    terminate_program("RD_ALE_EQUALSTEP v1 encountered a remote vertex despite its one-rank guard");

  int index = dp->index;
  if(index >= NumGas)
    index -= NumGas;
  if(index < 0 || index >= NumGas)
    terminate_program("RD_ALE_EQUALSTEP could not map a periodic image to its primary generator");
  return index;
}

#if defined(RD_ALE_EXACT_PATCH_DIAGNOSTIC) || defined(RD_ALE_FLIP_TRANSFER)
/*! A physical triangle key for the deliberately one-rank diagnostic.
 *
 * Sorted particle IDs are sufficient unless the same three particles form
 * more than one distinct torus triangle. Both snapshots are checked for
 * duplicate keys and abort in that exceptional small-box case; this is safer
 * than inferring periodic winding numbers from floating-point coordinates.
 */
struct rd_ale_exact_triangle_record
{
  MyIDType id[3];
  double area_third;
};

static struct rd_ale_exact_triangle_record *rd_ale_exact_old_triangle = NULL;
static int rd_ale_exact_old_triangle_count = 0;
static int rd_ale_exact_old_snapshot_valid = 0;

static int rd_ale_exact_triangle_compare(const void *a, const void *b)
{
  const struct rd_ale_exact_triangle_record *ta = a;
  const struct rd_ale_exact_triangle_record *tb = b;
  for(int vertex = 0; vertex < 3; vertex++)
    {
      if(ta->id[vertex] < tb->id[vertex])
        return -1;
      if(ta->id[vertex] > tb->id[vertex])
        return 1;
    }
  return 0;
}

static int rd_ale_exact_key_equal(const struct rd_ale_exact_triangle_record *a,
                                  const struct rd_ale_exact_triangle_record *b)
{
  return a->id[0] == b->id[0] && a->id[1] == b->id[1] && a->id[2] == b->id[2];
}

static void rd_ale_exact_make_record(tessellation *T, int triangle, double area,
                                     struct rd_ale_exact_triangle_record *record)
{
  for(int vertex = 0; vertex < 3; vertex++)
    record->id[vertex] = T->DP[T->DT[triangle].p[vertex]].ID;

  for(int a = 0; a < 2; a++)
    for(int b = a + 1; b < 3; b++)
      if(record->id[b] < record->id[a])
        {
          MyIDType tmp = record->id[a];
          record->id[a] = record->id[b];
          record->id[b] = tmp;
        }

  if(record->id[0] == record->id[1] || record->id[1] == record->id[2])
    terminate_program("RD exact-patch diagnostic found a triangle with repeated particle IDs");
  if(!(area > 0.0) || !isfinite(area))
    terminate_program("RD exact-patch diagnostic found a non-positive triangle area");
  record->area_third = area / 3.0;
}

static void rd_ale_exact_assert_unique_keys(struct rd_ale_exact_triangle_record *record, int count,
                                            const char *which)
{
  for(int i = 1; i < count; i++)
    if(rd_ale_exact_key_equal(&record[i - 1], &record[i]))
      {
        printf("RD-TOPO-EXACT duplicate-%s-key IDs=[%llu %llu %llu]\n", which,
               (unsigned long long)record[i].id[0], (unsigned long long)record[i].id[1],
               (unsigned long long)record[i].id[2]);
        terminate_program("RD exact-patch ID-only key is ambiguous; periodic winding metadata is required");
      }
}

/*! Snapshot the current owned physical triangulation immediately before the
 * mesh is freed. The snapshot contains no fluid state and survives only to
 * the next equal-step rebuild, where it is compared with the pulled-back new
 * connectivity. It therefore cannot alter the numerical solution.
 */
void rd_ale_topology_capture_old_mesh(tessellation *T)
{
  if(NTask != 1)
    terminate_program("RD exact-patch diagnostic is initially restricted to one MPI rank");

  struct rd_element_set set;
  rd_build_element_set(T, &set, 0);

  if(rd_ale_exact_old_triangle != NULL)
    free(rd_ale_exact_old_triangle);
  rd_ale_exact_old_triangle_count = set.n;
  rd_ale_exact_old_triangle = (struct rd_ale_exact_triangle_record *)malloc(
      rd_ale_exact_old_triangle_count * sizeof(*rd_ale_exact_old_triangle));
  if(rd_ale_exact_old_triangle == NULL)
    terminate_program("RD exact-patch diagnostic could not allocate its persistent old triangle snapshot");

  for(int slot = 0; slot < set.n; slot++)
    rd_ale_exact_make_record(T, set.element[slot], set.normals[slot].area,
                             &rd_ale_exact_old_triangle[slot]);

  qsort(rd_ale_exact_old_triangle, rd_ale_exact_old_triangle_count,
        sizeof(*rd_ale_exact_old_triangle), rd_ale_exact_triangle_compare);
  rd_ale_exact_assert_unique_keys(rd_ale_exact_old_triangle, rd_ale_exact_old_triangle_count, "old");
  rd_ale_exact_old_snapshot_valid = 1;

  mpi_printf("RD-TOPO-EXACT-SNAPSHOT triangles=%d\n", rd_ale_exact_old_triangle_count);
  rd_free_element_set(&set);
}
#endif

static void rd_ale_q_from_particle(int i, double q[4])
{
  q[0] = P[i].Mass;
  q[1] = SphP[i].Momentum[0];
  q[2] = SphP[i].Momentum[1];
  q[3] = SphP[i].Energy;
}

static void rd_ale_set_particle_q(int i, double area, const double u[4])
{
  P[i].Mass = area * u[0];
  SphP[i].Momentum[0] = area * u[1];
  SphP[i].Momentum[1] = area * u[2];
  SphP[i].Energy = area * u[3];

  /* The first prototype excludes a dynamically relevant third momentum, but
   * preserve a zero/non-zero passive value through the storage rebase. */
  if(SphP[i].DualArea > 0.0)
    SphP[i].Momentum[2] *= area / SphP[i].DualArea;
}

#if defined(RD_ALE_TOPOLOGY_REPAIR_DIAGNOSTIC) || defined(RD_ALE_FLIP_TRANSFER)
/* After a connectivity transfer the stage-0 residual reads SphP/P primitives,
 * while RD_Ustage0 is recovered later from Q/DualArea.  Set the primitives
 * from the transferred conservative density so both use the same state.
 * No floors; the mesh velocity of this interval is left unchanged. */
static void rd_ale_refresh_primitives(int i, const double u[4])
{
  const double internal = u[3] - 0.5 * (u[1] * u[1] + u[2] * u[2]) / u[0];
  if(!(u[0] > 0.0) || !(internal > 0.0) || !isfinite(internal))
    terminate_program("RD topology transfer produced an inadmissible state: ID=%llu rho=%g e=%g",
                      (unsigned long long)P[i].ID, u[0], internal);
  SphP[i].Density = u[0];
  P[i].Vel[0] = u[1] / u[0];
  P[i].Vel[1] = u[2] / u[0];
  SphP[i].Utherm = internal / u[0];
  SphP[i].Pressure = GAMMA_MINUS1 * internal;
  SphP[i].Csnd = sqrt(GAMMA * SphP[i].Pressure / u[0]);
}
#endif
#ifdef RD_ALE_TOPOLOGY_REPAIR_DIAGNOSTIC
#define RD_ALE_TOPOLOGY_SUPPORT_FACTOR 65536.0
#define RD_ALE_TOPOLOGY_AUDIT_FACTOR 262144.0

static int rd_ale_topology_find(int *parent, int i)
{
  int root = i;
  while(parent[root] != root)
    root = parent[root];

  while(parent[i] != i)
    {
      int next = parent[i];
      parent[i] = root;
      i = next;
    }
  return root;
}

static void rd_ale_topology_union(int *parent, int a, int b)
{
  int root_a = rd_ale_topology_find(parent, a);
  int root_b = rd_ale_topology_find(parent, b);
  if(root_a != root_b)
    parent[root_b] = root_a;
}

#ifdef RD_ALE_EXACT_PATCH_DIAGNOSTIC
struct rd_ale_exact_changed_triangle
{
  struct rd_ale_exact_triangle_record triangle;
  int side; /* -1: removed old triangle, +1: inserted pulled-back triangle */
};

struct rd_ale_exact_id_index
{
  MyIDType id;
  int index;
};

static int rd_ale_exact_id_index_compare(const void *a, const void *b)
{
  const struct rd_ale_exact_id_index *ia = a;
  const struct rd_ale_exact_id_index *ib = b;
  if(ia->id < ib->id)
    return -1;
  if(ia->id > ib->id)
    return 1;
  return 0;
}

static int rd_ale_exact_lookup_index(const struct rd_ale_exact_id_index *map, int count, MyIDType id)
{
  int lo = 0, hi = count;
  while(lo < hi)
    {
      int mid = lo + (hi - lo) / 2;
      if(map[mid].id < id)
        lo = mid + 1;
      else
        hi = mid;
    }
  if(lo >= count || map[lo].id != id)
    terminate_program("RD exact-patch diagnostic could not map a triangle ID to a local particle");
  return map[lo].index;
}

static int rd_ale_exact_triangles_share_edge(const struct rd_ale_exact_triangle_record *a,
                                             const struct rd_ale_exact_triangle_record *b)
{
  int common = 0;
  for(int i = 0; i < 3; i++)
    for(int j = 0; j < 3; j++)
      common += a->id[i] == b->id[j];
  return common >= 2;
}

static double rd_ale_exact_wrap(double x, double box)
{
  x = fmod(x, box);
  if(x < 0.0)
    x += box;
  if(x >= box)
    x -= box;
  return x;
}

/*! Compare the exact endpoint symmetric difference with the provisional
 * non-zero-dm support patches. Both exact correction candidates are formed
 * in scratch arrays only; the applied state remains the support repair below.
 */
static void rd_ale_exact_patch_diagnostic(tessellation *T, struct rd_element_set *set,
                                          const unsigned char *affected, int *support_parent,
                                          const int *support_root_to_patch, int support_patch_count)
{
  if(!rd_ale_exact_old_snapshot_valid)
    {
      mpi_printf("RD-TOPO-EXACT time=%.8g unavailable=1 reason=no-old-snapshot\n", All.Time);
      return;
    }

  struct rd_ale_exact_triangle_record *new_triangle =
      (struct rd_ale_exact_triangle_record *)mymalloc(
          "RDExactNewTriangles", set->n * sizeof(*new_triangle));
  for(int slot = 0; slot < set->n; slot++)
    {
      int triangle = set->element[slot];
      rd_ale_exact_make_record(T, triangle,
                               set->ale_geometry[slot].normals[RD_ALE_OLD].area,
                               &new_triangle[slot]);
    }
  qsort(new_triangle, set->n, sizeof(*new_triangle), rd_ale_exact_triangle_compare);
  rd_ale_exact_assert_unique_keys(new_triangle, set->n, "new");

  int changed_capacity = rd_ale_exact_old_triangle_count + set->n;
  struct rd_ale_exact_changed_triangle *changed =
      (struct rd_ale_exact_changed_triangle *)mymalloc(
          "RDExactChangedTriangles", changed_capacity * sizeof(*changed));

  int old_cursor = 0, new_cursor = 0, changed_count = 0;
  int unchanged_count = 0, removed_count = 0, inserted_count = 0;
  double max_unchanged_area_error = 0.0;
  while(old_cursor < rd_ale_exact_old_triangle_count || new_cursor < set->n)
    {
      int comparison;
      if(old_cursor >= rd_ale_exact_old_triangle_count)
        comparison = 1;
      else if(new_cursor >= set->n)
        comparison = -1;
      else
        comparison = rd_ale_exact_triangle_compare(&rd_ale_exact_old_triangle[old_cursor],
                                                   &new_triangle[new_cursor]);

      if(comparison == 0)
        {
          max_unchanged_area_error =
              dmax(max_unchanged_area_error,
                   fabs(rd_ale_exact_old_triangle[old_cursor].area_third -
                        new_triangle[new_cursor].area_third));
          unchanged_count++;
          old_cursor++;
          new_cursor++;
        }
      else if(comparison < 0)
        {
          changed[changed_count].triangle = rd_ale_exact_old_triangle[old_cursor++];
          changed[changed_count++].side = -1;
          removed_count++;
        }
      else
        {
          changed[changed_count].triangle = new_triangle[new_cursor++];
          changed[changed_count++].side = 1;
          inserted_count++;
        }
    }

  if(changed_count == 0)
    {
      mpi_printf("RD-TOPO-EXACT time=%.8g old=%d new=%d unchanged=%d removed=0 inserted=0 "
                 "exact=0 support=%d split=0 merged_support=0 exact_in_merges=0 max_merge=0 "
                 "max_nodes=0 max_diameter=0.000e+00 zero_rel=0.000e+00 first_rel=0.000e+00 "
                 "dm_match_rel=0.000e+00 unchanged_area=%.3e dU_full=0.000e+00 "
                 "dU_patch=0.000e+00 bad_full=0 bad_patch=0\n",
                 All.Time, rd_ale_exact_old_triangle_count, set->n, unchanged_count,
                 support_patch_count, max_unchanged_area_error);
      myfree(changed);
      myfree(new_triangle);
      return;
    }

  int *changed_parent =
      (int *)mymalloc("RDExactChangedParent", changed_count * sizeof(*changed_parent));
  int *root_to_exact =
      (int *)mymalloc("RDExactRootPatch", changed_count * sizeof(*root_to_exact));
  for(int i = 0; i < changed_count; i++)
    {
      changed_parent[i] = i;
      root_to_exact[i] = -1;
    }
  for(int i = 0; i < changed_count; i++)
    for(int j = i + 1; j < changed_count; j++)
      if(rd_ale_exact_triangles_share_edge(&changed[i].triangle, &changed[j].triangle))
        rd_ale_topology_union(changed_parent, i, j);

  int exact_patch_count = 0;
  for(int i = 0; i < changed_count; i++)
    {
      int root = rd_ale_topology_find(changed_parent, i);
      if(root_to_exact[root] < 0)
        root_to_exact[root] = exact_patch_count++;
    }

  struct rd_ale_exact_id_index *id_map =
      (struct rd_ale_exact_id_index *)mymalloc("RDExactIDMap", NumGas * sizeof(*id_map));
  for(int i = 0; i < NumGas; i++)
    {
      id_map[i].id = P[i].ID;
      id_map[i].index = i;
    }
  qsort(id_map, NumGas, sizeof(*id_map), rd_ale_exact_id_index_compare);
  for(int i = 1; i < NumGas; i++)
    if(id_map[i - 1].id == id_map[i].id)
      terminate_program("RD exact-patch diagnostic requires unique local particle IDs");

  size_t patch_node_count = (size_t)exact_patch_count * (size_t)NumGas;
  double *old_patch_mass =
      (double *)mymalloc("RDExactOldPatchMass", patch_node_count * sizeof(*old_patch_mass));
  double *new_patch_mass =
      (double *)mymalloc("RDExactNewPatchMass", patch_node_count * sizeof(*new_patch_mass));
  memset(old_patch_mass, 0, patch_node_count * sizeof(*old_patch_mass));
  memset(new_patch_mass, 0, patch_node_count * sizeof(*new_patch_mass));

  int *old_triangles =
      (int *)mymalloc("RDExactOldPatchTriangles", exact_patch_count * sizeof(*old_triangles));
  int *new_triangles =
      (int *)mymalloc("RDExactNewPatchTriangles", exact_patch_count * sizeof(*new_triangles));
  memset(old_triangles, 0, exact_patch_count * sizeof(*old_triangles));
  memset(new_triangles, 0, exact_patch_count * sizeof(*new_triangles));

  for(int triangle = 0; triangle < changed_count; triangle++)
    {
      int patch = root_to_exact[rd_ale_topology_find(changed_parent, triangle)];
      if(changed[triangle].side < 0)
        old_triangles[patch]++;
      else
        new_triangles[patch]++;
      for(int vertex = 0; vertex < 3; vertex++)
        {
          int index = rd_ale_exact_lookup_index(id_map, NumGas,
                                                changed[triangle].triangle.id[vertex]);
          size_t offset = (size_t)patch * NumGas + index;
          if(changed[triangle].side < 0)
            old_patch_mass[offset] += changed[triangle].triangle.area_third;
          else
            new_patch_mass[offset] += changed[triangle].triangle.area_third;
        }
    }

  double(*delta_full)[4] =
      (double(*)[4])mymalloc("RDExactDeltaFull", NumGas * sizeof(*delta_full));
  double(*delta_patch)[4] =
      (double(*)[4])mymalloc("RDExactDeltaPatch", NumGas * sizeof(*delta_patch));
  memset(delta_full, 0, NumGas * sizeof(*delta_full));
  memset(delta_patch, 0, NumGas * sizeof(*delta_patch));
  double *reconstructed_dm =
      (double *)mymalloc("RDExactReconstructedDM", NumGas * sizeof(*reconstructed_dm));
  memset(reconstructed_dm, 0, NumGas * sizeof(*reconstructed_dm));

  int support_storage_count = imax(1, support_patch_count);
  int *support_exact_count =
      (int *)mymalloc("RDExactSupportCount", support_storage_count * sizeof(*support_exact_count));
  memset(support_exact_count, 0, support_storage_count * sizeof(*support_exact_count));

  const double mean_area = boxSize_X * boxSize_Y / NumGas;
  const double box_length = dmax(boxSize_X, boxSize_Y);
  double max_zero_relative = 0.0, max_first_relative = 0.0;
  double max_patch_diameter = 0.0;
  int max_patch_nodes = 0, split_exact = 0, unmapped_exact = 0;
  int integrity_fail = 0;

  for(int patch = 0; patch < exact_patch_count; patch++)
    {
      if(old_triangles[patch] == 0 || new_triangles[patch] == 0)
        integrity_fail = 1;

      int node_count = 0, anchor = -1, support_label = -1, patch_split = 0;
      double patch_dm = 0.0, patch_abs_dm = 0.0;
      double full_weight_sum = 0.0, patch_weight_sum = 0.0;
      double defect[4] = {0.0, 0.0, 0.0, 0.0};

      for(int i = 0; i < NumGas; i++)
        {
          size_t offset = (size_t)patch * NumGas + i;
          double old_mass = old_patch_mass[offset];
          double new_mass = new_patch_mass[offset];
          if(old_mass == 0.0 && new_mass == 0.0)
            continue;
          node_count++;
          if(anchor < 0 || P[i].ID < P[anchor].ID)
            anchor = i;
          double dm = new_mass - old_mass;
          reconstructed_dm[i] += dm;
          patch_dm += dm;
          patch_abs_dm += fabs(dm);
          full_weight_sum += set->ale_pullback_area[i];
          patch_weight_sum += new_mass;
          for(int component = 0; component < 4; component++)
            defect[component] += dm * set->ale_uold[i][component];

          double support_tolerance =
              RD_ALE_TOPOLOGY_SUPPORT_FACTOR * DBL_EPSILON *
              dmax(mean_area, dmax(fabs(old_mass), fabs(new_mass)));
          if(fabs(dm) > support_tolerance)
            {
              if(!affected[i])
                integrity_fail = 1;
              else
                {
                  int label = support_root_to_patch[rd_ale_topology_find(support_parent, i)];
                  if(support_label < 0)
                    support_label = label;
                  else if(label != support_label)
                    patch_split = 1;
                }
            }
        }

      max_patch_nodes = imax(max_patch_nodes, node_count);
      if(anchor < 0 || !(full_weight_sum > 0.0) || !(patch_weight_sum > 0.0))
        integrity_fail = 1;

      double anchor_x = rd_ale_exact_wrap(P[anchor].Pos[0] - set->ale_dt * SphP[anchor].VelVertex[0], boxSize_X);
      double anchor_y = rd_ale_exact_wrap(P[anchor].Pos[1] - set->ale_dt * SphP[anchor].VelVertex[1], boxSize_Y);
      double first[2] = {0.0, 0.0};
      for(int i = 0; i < NumGas; i++)
        {
          size_t offset = (size_t)patch * NumGas + i;
          if(old_patch_mass[offset] == 0.0 && new_patch_mass[offset] == 0.0)
            continue;
          double dm = new_patch_mass[offset] - old_patch_mass[offset];
          double x = rd_ale_exact_wrap(P[i].Pos[0] - set->ale_dt * SphP[i].VelVertex[0], boxSize_X);
          double y = rd_ale_exact_wrap(P[i].Pos[1] - set->ale_dt * SphP[i].VelVertex[1], boxSize_Y);
          double dx = nearest_x(x - anchor_x);
          double dy = nearest_y(y - anchor_y);
          first[0] += dm * (anchor_x + dx);
          first[1] += dm * (anchor_y + dy);
          max_patch_diameter = dmax(max_patch_diameter, sqrt(dx * dx + dy * dy));

          double full_weight = set->ale_pullback_area[i] / full_weight_sum;
          double patch_weight = new_patch_mass[offset] / patch_weight_sum;
          for(int component = 0; component < 4; component++)
            {
              delta_full[i][component] -= full_weight * defect[component] / set->ale_pullback_area[i];
              delta_patch[i][component] -= patch_weight * defect[component] / set->ale_pullback_area[i];
            }
        }

      double zero_scale = dmax(mean_area, patch_abs_dm);
      double first_scale = zero_scale * box_length;
      max_zero_relative = dmax(max_zero_relative, fabs(patch_dm) / zero_scale);
      max_first_relative =
          dmax(max_first_relative, dmax(fabs(first[0]), fabs(first[1])) / first_scale);
      if(fabs(patch_dm) > 1.0e-9 * mean_area || fabs(first[0]) > 1.0e-9 * mean_area * box_length ||
         fabs(first[1]) > 1.0e-9 * mean_area * box_length)
        integrity_fail = 1;

      split_exact += patch_split;
      if(support_label >= 0 && !patch_split)
        support_exact_count[support_label]++;
      else
        unmapped_exact++;
    }

  int merged_support = 0, exact_in_merges = 0, max_merge = 0, support_unmapped = 0;
  for(int patch = 0; patch < support_patch_count; patch++)
    {
      if(support_exact_count[patch] > 1)
        {
          merged_support++;
          exact_in_merges += support_exact_count[patch];
        }
      if(support_exact_count[patch] == 0)
        support_unmapped++;
      max_merge = imax(max_merge, support_exact_count[patch]);
    }

  double max_dm_match_relative = 0.0;
  for(int i = 0; i < NumGas; i++)
    {
      double actual_dm = set->ale_pullback_area[i] - SphP[i].DualArea;
      double scale = dmax(mean_area, dmax(fabs(actual_dm), fabs(reconstructed_dm[i])));
      max_dm_match_relative =
          dmax(max_dm_match_relative, fabs(reconstructed_dm[i] - actual_dm) / scale);
    }
  if(max_dm_match_relative > 1.0e-9)
    integrity_fail = 1;

  double max_full_change = 0.0, max_patch_change = 0.0;
  int bad_full = 0, bad_patch = 0;
  for(int i = 0; i < NumGas; i++)
    {
      for(int component = 0; component < 4; component++)
        {
          max_full_change = dmax(max_full_change, fabs(delta_full[i][component]));
          max_patch_change = dmax(max_patch_change, fabs(delta_patch[i][component]));
        }
      double rho_full = set->ale_uold[i][0] + delta_full[i][0];
      double rho_patch = set->ale_uold[i][0] + delta_patch[i][0];
      double mx_full = set->ale_uold[i][1] + delta_full[i][1];
      double my_full = set->ale_uold[i][2] + delta_full[i][2];
      double energy_full = set->ale_uold[i][3] + delta_full[i][3];
      double mx_patch = set->ale_uold[i][1] + delta_patch[i][1];
      double my_patch = set->ale_uold[i][2] + delta_patch[i][2];
      double energy_patch = set->ale_uold[i][3] + delta_patch[i][3];
      double press_full = (isfinite(rho_full) && rho_full > 0.0)
                              ? GAMMA_MINUS1 * (energy_full - 0.5 * (mx_full * mx_full + my_full * my_full) / rho_full)
                              : NAN;
      double press_patch = (isfinite(rho_patch) && rho_patch > 0.0)
                               ? GAMMA_MINUS1 * (energy_patch - 0.5 * (mx_patch * mx_patch + my_patch * my_patch) / rho_patch)
                               : NAN;
      bad_full += !isfinite(rho_full) || !isfinite(press_full) || rho_full <= 0.0 || press_full <= 0.0;
      bad_patch += !isfinite(rho_patch) || !isfinite(press_patch) || rho_patch <= 0.0 || press_patch <= 0.0;
    }

  mpi_printf("RD-TOPO-EXACT time=%.8g old=%d new=%d unchanged=%d removed=%d inserted=%d "
             "exact=%d support=%d split=%d unmapped_exact=%d merged_support=%d exact_in_merges=%d "
             "support_unmapped=%d max_merge=%d max_nodes=%d max_diameter=%.3e zero_rel=%.3e "
             "first_rel=%.3e dm_match_rel=%.3e unchanged_area=%.3e dU_full=%.3e dU_patch=%.3e "
             "bad_full=%d bad_patch=%d integrity_fail=%d\n",
             All.Time, rd_ale_exact_old_triangle_count, set->n, unchanged_count, removed_count,
             inserted_count, exact_patch_count, support_patch_count, split_exact, unmapped_exact,
             merged_support, exact_in_merges, support_unmapped, max_merge, max_patch_nodes,
             max_patch_diameter, max_zero_relative, max_first_relative, max_dm_match_relative,
             max_unchanged_area_error, max_full_change, max_patch_change, bad_full, bad_patch,
             integrity_fail);

  myfree(support_exact_count);
  myfree(reconstructed_dm);
  myfree(delta_patch);
  myfree(delta_full);
  myfree(new_triangles);
  myfree(old_triangles);
  myfree(new_patch_mass);
  myfree(old_patch_mass);
  myfree(id_map);
  myfree(root_to_exact);
  myfree(changed_parent);
  myfree(changed);
  myfree(new_triangle);

  if(integrity_fail)
    terminate_program("RD exact-patch diagnostic failed its reconstruction gates");
}
#endif

/*! Apply a conservative representation transfer from the actual old P1 basis
 *  to the new connectivity pulled back to the old physical time.
 *
 *  This first online diagnostic deliberately avoids retaining the old triangle
 *  list. A vertex is marked when its pulled-back new-connectivity lumped mass
 *  differs from the persistent old DualArea by more than a round-off envelope.
 *  Marked vertices are connected through the new triangulation. Offline tests
 *  in log section 69 found that this may merge neighbouring exact flip patches
 *  but never splits one, and every resulting component retains zero total dm.
 *
 *  For each component P,
 *
 *      D_P       = sum_i dm_i U_i,
 *      Q_i^plus  = Q_i^minus + dm_i U_i - w_i D_P,
 *
 *  with non-negative full pulled-back nodal-mass weights. Full nodal masses are
 *  a diagnostic substitute for exact new patch masses; conservation and
 *  uniform/linear exactness need only sum_i w_i=1. The final weight is formed
 *  as one minus the preceding sum so conservation does not rely on a second
 *  floating-point normalization.
 */
static void rd_ale_apply_topology_repair(tessellation *T, struct rd_element_set *set)
{
  point *DP = T->DP;
  tetra *DT = T->DT;
  const double box_area = boxSize_X * boxSize_Y;
  const double mean_area = box_area / NumGas;

  int *parent = (int *)mymalloc("RDTopologyParent", NumGas * sizeof(*parent));
  int *root_to_patch = (int *)mymalloc("RDTopologyRootPatch", NumGas * sizeof(*root_to_patch));
  unsigned char *affected =
      (unsigned char *)mymalloc("RDTopologyAffected", NumGas * sizeof(*affected));

  int affected_count = 0;
  double total_dm = 0.0, total_abs_dm = 0.0, max_relative_dm = 0.0;
  for(int i = 0; i < NumGas; i++)
    {
      const double old_area = SphP[i].DualArea;
      const double pullback_area = set->ale_pullback_area[i];
      if(!(pullback_area > 0.0) || !isfinite(pullback_area))
        terminate_program("RD topology repair found a non-positive pulled-back nodal mass");

      const double dm = pullback_area - old_area;
      const double scale = dmax(mean_area, dmax(fabs(old_area), fabs(pullback_area)));
      const double tolerance = RD_ALE_TOPOLOGY_SUPPORT_FACTOR * DBL_EPSILON * scale;
      affected[i] = fabs(dm) > tolerance;
      parent[i] = affected[i] ? i : -1;
      root_to_patch[i] = -1;
      affected_count += affected[i] != 0;
      total_dm += dm;
      total_abs_dm += fabs(dm);
      max_relative_dm = dmax(max_relative_dm, fabs(dm) / old_area);
    }

  const double total_dm_tolerance =
      RD_ALE_TOPOLOGY_AUDIT_FACTOR * DBL_EPSILON * dmax(box_area, total_abs_dm);
  if(fabs(total_dm) > total_dm_tolerance)
    {
      printf("RD-TOPO-FAIL time=%.17g total_dm=%.17g tolerance=%.17g\n",
             All.Time, total_dm, total_dm_tolerance);
      terminate_program("RD topology repair: pulled-back and old meshes cover different areas");
    }

  for(int slot = 0; slot < set->n; slot++)
    {
      int triangle = set->element[slot];
      int first = -1;
      for(int vertex = 0; vertex < DIMS + 1; vertex++)
        {
          int index = rd_ale_local_point_index(&DP[DT[triangle].p[vertex]]);
          if(!affected[index])
            continue;
          if(first < 0)
            first = index;
          else
            rd_ale_topology_union(parent, first, index);
        }
    }

  int patch_count = 0;
  for(int i = 0; i < NumGas; i++)
    if(affected[i])
      {
        int root = rd_ale_topology_find(parent, i);
        if(root_to_patch[root] < 0)
          root_to_patch[root] = patch_count++;
      }

#ifdef RD_ALE_EXACT_PATCH_DIAGNOSTIC
  rd_ale_exact_patch_diagnostic(T, set, affected, parent, root_to_patch,
                                patch_count);
#endif

  if(patch_count == 0)
    {
      mpi_printf("RD-TOPO-REPAIR time=%.8g affected=0 patches=0 "
                 "max_dm_rel=%.3e max_patch_zero_rel=0.000e+00 max_dU=0.000e+00 "
                 "raw=[+0.000000e+00 +0.000000e+00 +0.000000e+00 +0.000000e+00] "
                 "repaired=[+0.000000e+00 +0.000000e+00 +0.000000e+00 +0.000000e+00]\n",
                 All.Time, max_relative_dm);
      myfree(affected);
      myfree(root_to_patch);
      myfree(parent);
      return;
    }

  double *patch_weight =
      (double *)mymalloc("RDTopologyPatchWeight", patch_count * sizeof(*patch_weight));
  double *patch_dm =
      (double *)mymalloc("RDTopologyPatchDM", patch_count * sizeof(*patch_dm));
  double *patch_abs_dm =
      (double *)mymalloc("RDTopologyPatchAbsDM", patch_count * sizeof(*patch_abs_dm));
  double *weight_used =
      (double *)mymalloc("RDTopologyWeightUsed", patch_count * sizeof(*weight_used));
  int *anchor = (int *)mymalloc("RDTopologyAnchor", patch_count * sizeof(*anchor));
  double(*defect)[4] =
      (double(*)[4])mymalloc("RDTopologyDefect", patch_count * sizeof(*defect));

  memset(patch_weight, 0, patch_count * sizeof(*patch_weight));
  memset(patch_dm, 0, patch_count * sizeof(*patch_dm));
  memset(patch_abs_dm, 0, patch_count * sizeof(*patch_abs_dm));
  memset(weight_used, 0, patch_count * sizeof(*weight_used));
  memset(defect, 0, patch_count * sizeof(*defect));
  for(int patch = 0; patch < patch_count; patch++)
    anchor[patch] = -1;

  double raw_defect[4] = {0.0, 0.0, 0.0, 0.0};
  for(int i = 0; i < NumGas; i++)
    if(affected[i])
      {
        int patch = root_to_patch[rd_ale_topology_find(parent, i)];
        const double dm = set->ale_pullback_area[i] - SphP[i].DualArea;
        patch_weight[patch] += set->ale_pullback_area[i];
        patch_dm[patch] += dm;
        patch_abs_dm[patch] += fabs(dm);
        anchor[patch] = i;
        for(int component = 0; component < 4; component++)
          {
            const double contribution = dm * set->ale_uold[i][component];
            defect[patch][component] += contribution;
            raw_defect[component] += contribution;
          }
      }

  double max_patch_zero_relative = 0.0;
  for(int patch = 0; patch < patch_count; patch++)
    {
      if(!(patch_weight[patch] > 0.0) || anchor[patch] < 0)
        terminate_program("RD topology repair constructed an empty patch");

      const double zero_scale = dmax(mean_area, patch_abs_dm[patch]);
      const double zero_tolerance =
          RD_ALE_TOPOLOGY_AUDIT_FACTOR * DBL_EPSILON * zero_scale;
      max_patch_zero_relative =
          dmax(max_patch_zero_relative, fabs(patch_dm[patch]) / zero_scale);
      if(fabs(patch_dm[patch]) > zero_tolerance)
        {
          printf("RD-TOPO-FAIL time=%.17g patch=%d dm=%.17g abs_dm=%.17g "
                 "tolerance=%.17g anchor_id=%llu\n",
                 All.Time, patch, patch_dm[patch], patch_abs_dm[patch],
                 zero_tolerance, (unsigned long long)P[anchor[patch]].ID);
          terminate_program("RD topology repair support component violates the zeroth moment");
        }
    }

  double max_state_change = 0.0, state_scale = 1.0;
  int bad_nodes = 0;

  /* Apply every non-anchor weight first. */
  for(int i = 0; i < NumGas; i++)
    if(affected[i])
      {
        int patch = root_to_patch[rd_ale_topology_find(parent, i)];
        if(i == anchor[patch])
          continue;

        const double weight = set->ale_pullback_area[i] / patch_weight[patch];
        const double dm = set->ale_pullback_area[i] - SphP[i].DualArea;
        double unew[4];
        for(int component = 0; component < 4; component++)
          {
            const double uold = set->ale_uold[i][component];
            const double qnew =
                SphP[i].DualArea * uold + dm * uold - weight * defect[patch][component];
            unew[component] = qnew / set->ale_pullback_area[i];
            max_state_change = dmax(max_state_change, fabs(unew[component] - uold));
            state_scale = dmax(state_scale, fabs(uold));
          }

        const double rho = unew[0];
        const double press =
            (isfinite(rho) && rho > 0.0)
                ? GAMMA_MINUS1 *
                      (unew[3] - 0.5 * (unew[1] * unew[1] + unew[2] * unew[2]) / rho)
                : NAN;
        if(!isfinite(rho) || !isfinite(press) || rho <= 0.0 || press <= 0.0)
          {
            bad_nodes++;
            printf("RD-TOPO-BAD time=%.17g patch=%d ID=%llu rho=%.17g "
                   "press=%.17g dm=%.17g weight=%.17g D=[%.17g %.17g %.17g %.17g]\n",
                   All.Time, patch, (unsigned long long)P[i].ID, rho, press, dm,
                   weight, defect[patch][0], defect[patch][1],
                   defect[patch][2], defect[patch][3]);
          }
        for(int component = 0; component < 4; component++)
          set->ale_uold[i][component] = unew[component];
        weight_used[patch] += weight;
      }

  /* The anchor receives the exact remaining correction weight. */
  for(int patch = 0; patch < patch_count; patch++)
    {
      int i = anchor[patch];
      const double weight = 1.0 - weight_used[patch];
      const double dm = set->ale_pullback_area[i] - SphP[i].DualArea;
      double unew[4];
      for(int component = 0; component < 4; component++)
        {
          const double uold = set->ale_uold[i][component];
          const double qnew =
              SphP[i].DualArea * uold + dm * uold - weight * defect[patch][component];
          unew[component] = qnew / set->ale_pullback_area[i];
          max_state_change = dmax(max_state_change, fabs(unew[component] - uold));
          state_scale = dmax(state_scale, fabs(uold));
        }

      const double rho = unew[0];
      const double press =
          (isfinite(rho) && rho > 0.0)
              ? GAMMA_MINUS1 *
                    (unew[3] - 0.5 * (unew[1] * unew[1] + unew[2] * unew[2]) / rho)
              : NAN;
      if(!isfinite(rho) || !isfinite(press) || rho <= 0.0 || press <= 0.0)
        {
          bad_nodes++;
          printf("RD-TOPO-BAD time=%.17g patch=%d ID=%llu rho=%.17g "
                 "press=%.17g dm=%.17g weight=%.17g D=[%.17g %.17g %.17g %.17g]\n",
                 All.Time, patch, (unsigned long long)P[i].ID, rho, press, dm,
                 weight, defect[patch][0], defect[patch][1],
                 defect[patch][2], defect[patch][3]);
        }
      for(int component = 0; component < 4; component++)
        set->ale_uold[i][component] = unew[component];
    }

  if(bad_nodes > 0)
    terminate_program("RD topology repair produced an inadmissible high-order state");

  double repaired_change[4] = {0.0, 0.0, 0.0, 0.0};
  double conservation_scale = 1.0;
  for(int i = 0; i < NumGas; i++)
    for(int component = 0; component < 4; component++)
      repaired_change[component] +=
          set->ale_pullback_area[i] * set->ale_uold[i][component];

  for(int component = 0; component < 4; component++)
    {
      repaired_change[component] -= set->ale_old_total[component];
      conservation_scale =
          dmax(conservation_scale, fabs(set->ale_old_total[component]));
    }

  const double conservation_tolerance =
      RD_ALE_TOPOLOGY_AUDIT_FACTOR * DBL_EPSILON * conservation_scale;
  for(int component = 0; component < 4; component++)
    if(fabs(repaired_change[component]) > conservation_tolerance)
      terminate_program("RD topology repair failed its global conservation audit");

  if(set->ale_uniform_initial)
    {
      const double state_tolerance =
          RD_ALE_TOPOLOGY_AUDIT_FACTOR * DBL_EPSILON * state_scale;
      if(max_state_change > state_tolerance)
        terminate_program("RD topology repair changed a uniform state");
    }

  mpi_printf("RD-TOPO-REPAIR time=%.8g affected=%d patches=%d "
             "max_dm_rel=%.3e max_patch_zero_rel=%.3e max_dU=%.3e "
             "raw=[%+.6e %+.6e %+.6e %+.6e] "
             "repaired=[%+.6e %+.6e %+.6e %+.6e]\n",
             All.Time, affected_count, patch_count, max_relative_dm,
             max_patch_zero_relative, max_state_change,
             raw_defect[0], raw_defect[1], raw_defect[2], raw_defect[3],
             repaired_change[0], repaired_change[1],
             repaired_change[2], repaired_change[3]);

  myfree(defect);
  myfree(anchor);
  myfree(weight_used);
  myfree(patch_abs_dm);
  myfree(patch_dm);
  myfree(patch_weight);
  myfree(affected);
  myfree(root_to_patch);
  myfree(parent);
}
#endif

/*! Construct the post-rebuild new-connectivity geometry and switch the
 *  temporary AREPO storage from endpoint Q=m_old U_old to Qbar=mbar U_old. */
#ifdef RD_ALE_FLIP_TRANSFER
struct rd_flip_id_index
{
  MyIDType id;
  int index;
};

static int rd_flip_id_index_compare(const void *a, const void *b)
{
  const MyIDType x = ((const struct rd_flip_id_index *)a)->id, y = ((const struct rd_flip_id_index *)b)->id;
  return (x > y) - (x < y);
}

static int rd_flip_index_of(const struct rd_flip_id_index *map, MyIDType id)
{
  int lo = 0, hi = NumGas - 1;
  while(lo <= hi)
    {
      const int mid = (lo + hi) / 2;
      if(map[mid].id == id)
        return map[mid].index;
      if(map[mid].id < id)
        lo = mid + 1;
      else
        hi = mid - 1;
    }
  terminate_program("RD flip transfer: old triangle vertex ID=%llu is not a local gas particle", (unsigned long long)id);
  return -1;
}

static int rd_flip_find(int *parent, int i)
{
  while(parent[i] != i)
    {
      parent[i] = parent[parent[i]];
      i = parent[i];
    }
  return i;
}

/*! Flip element at the old time t^n (equal-step, one rank).
 *
 * The old triangles are the keys captured from the live mesh before it was
 * freed (Delaunay of x^n, areas at x^n).  The new triangles are this step's
 * connectivity pulled back to x^n.  Every connected component of the symmetric
 * difference is a changed cavity C.  With old full nodal masses g_i (the stored
 * endpoint DualArea) and new pulled-back masses g_i^+, the cavity residual is
 * D_C = sum_C (g_i^+ - g_i) U_i; rd_flip_transfer distributes it so that
 * sum_C g_i^+ U_i^+ = sum_C g_i U_i exactly and every state stays admissible.
 * Vertices outside cavities keep U; their g^+ - g is round-off, which is
 * asserted.  Primitives of changed vertices are refreshed. */
static void rd_ale_apply_flip_transfer(tessellation *T, struct rd_element_set *set)
{
  if(NTask != 1)
    terminate_program("RD_ALE_FLIP_TRANSFER is restricted to one MPI rank");
  if(!rd_ale_exact_old_snapshot_valid)
    terminate_program("RD_ALE_FLIP_TRANSFER found no old triangle snapshot");

  /* New triangle keys with pulled-back (old-position) areas. */
  struct rd_ale_exact_triangle_record *fresh =
      (struct rd_ale_exact_triangle_record *)malloc((set->n > 0 ? set->n : 1) * sizeof(*fresh));
  struct rd_flip_id_index *map = (struct rd_flip_id_index *)malloc(NumGas * sizeof(*map));
  int *parent = (int *)malloc(NumGas * sizeof(int));
  if(fresh == NULL || map == NULL || parent == NULL)
    terminate_program("RD flip transfer: allocation failed");
  for(int slot = 0; slot < set->n; slot++)
    rd_ale_exact_make_record(T, set->element[slot], set->ale_geometry[slot].normals[RD_ALE_OLD].area, &fresh[slot]);
  qsort(fresh, set->n, sizeof(*fresh), rd_ale_exact_triangle_compare);
  rd_ale_exact_assert_unique_keys(fresh, set->n, "new");

  for(int i = 0; i < NumGas; i++)
    {
      map[i].id = P[i].ID;
      map[i].index = i;
      parent[i] = -1; /* not in a cavity */
    }
  qsort(map, NumGas, sizeof(*map), rd_flip_id_index_compare);
  for(int i = 1; i < NumGas; i++)
    if(map[i].id == map[i - 1].id)
      terminate_program("RD flip transfer requires unique particle IDs");

  /* Sort-merge the two key lists; union the vertices of every changed triangle. */
  int removed = 0, inserted = 0, a = 0, b = 0;
  const int n_old = rd_ale_exact_old_triangle_count, n_new = set->n;
  while(a < n_old || b < n_new)
    {
      const struct rd_ale_exact_triangle_record *changed = NULL;
      int cmp = a >= n_old ? 1 : (b >= n_new ? -1 : rd_ale_exact_triangle_compare(&rd_ale_exact_old_triangle[a], &fresh[b]));
      if(cmp == 0)
        {
          a++;
          b++;
          continue;
        }
      if(cmp < 0)
        {
          changed = &rd_ale_exact_old_triangle[a++];
          removed++;
        }
      else
        {
          changed = &fresh[b++];
          inserted++;
        }
      int v[3];
      for(int k = 0; k < 3; k++)
        {
          v[k] = rd_flip_index_of(map, changed->id[k]);
          if(parent[v[k]] < 0)
            parent[v[k]] = v[k];
        }
      for(int k = 1; k < 3; k++)
        {
          int r0 = rd_flip_find(parent, v[0]), rk = rd_flip_find(parent, v[k]);
          if(r0 != rk)
            parent[rk] = r0;
        }
    }

  /* Group cavity vertices by root (CSR). */
  int *start = (int *)calloc(NumGas + 1, sizeof(int));
  int *member = (int *)malloc(NumGas * sizeof(int));
  if(start == NULL || member == NULL)
    terminate_program("RD flip transfer: allocation failed");
  int n_cavity_vertices = 0;
  for(int i = 0; i < NumGas; i++)
    if(parent[i] >= 0)
      {
        start[rd_flip_find(parent, i) + 1]++;
        n_cavity_vertices++;
      }
  for(int i = 0; i < NumGas; i++)
    start[i + 1] += start[i];
  int *fill = (int *)malloc((NumGas + 1) * sizeof(int));
  memcpy(fill, start, (NumGas + 1) * sizeof(int));
  for(int i = 0; i < NumGas; i++)
    if(parent[i] >= 0)
      member[fill[rd_flip_find(parent, i)]++] = i;
  free(fill);

  /* Vertices outside the cavities must have unchanged nodal masses. */
  double outside_dm = 0.0;
  for(int i = 0; i < NumGas; i++)
    if(parent[i] < 0)
      outside_dm = dmax(outside_dm, fabs(set->ale_pullback_area[i] - SphP[i].DualArea) / SphP[i].DualArea);
  if(outside_dm > 1e-10)
    terminate_program("RD flip transfer: nodal mass changed outside every cavity (rel %g)", outside_dm);

  int max_n = 1;
  for(int root = 0; root < NumGas; root++)
    max_n = imax(max_n, start[root + 1] - start[root]);
  double *g = (double *)malloc(max_n * sizeof(double)), *dm = (double *)malloc(max_n * sizeof(double));
  double(*u)[4] = malloc(max_n * sizeof(*u)), (*ul)[4] = malloc(max_n * sizeof(*ul)), (*uh)[4] = malloc(max_n * sizeof(*uh));
  double(*work)[4] = malloc(max_n * sizeof(*work)), (*uout)[4] = malloc(max_n * sizeof(*uout));
  if(!g || !dm || !u || !ul || !uh || !work || !uout)
    terminate_program("RD flip transfer: allocation failed");

  struct rd_flip_options options = {GAMMA, RD_FLIP_FLOOR_FRACTION, RD_FLIP_DMP_RELAX, RD_FLIP_ENTROPY_BOUND,
                                    RD_FLIP_HIGH_MODE};
  int cavities = 0, limited = 0, low_only = 0;
  double theta_min = 1.0, theta_sum = 0.0, max_defect = 0.0, max_change = 0.0;
  double before[4] = {0, 0, 0, 0}, after[4] = {0, 0, 0, 0}, scale[4] = {0, 0, 0, 0};
  for(int root = 0; root < NumGas; root++)
    {
      const int n = start[root + 1] - start[root];
      if(n == 0)
        continue;
      for(int k = 0; k < n; k++)
        {
          const int i = member[start[root] + k];
          g[k] = SphP[i].DualArea;
          dm[k] = set->ale_pullback_area[i] - SphP[i].DualArea;
          for(int c = 0; c < 4; c++)
            u[k][c] = set->ale_uold[i][c];
        }
      struct rd_flip_diagnostics diag;
      int status = rd_flip_transfer(n, g, dm, (const double(*)[4])u, &options, ul, uh, work, uout, &diag);
      if(status != RD_FLIP_OK)
        terminate_program("RD flip transfer failed with status %d on a cavity of %d vertices (first ID=%llu)", status, n,
                          (unsigned long long)P[member[start[root]]].ID);
      for(int k = 0; k < n; k++)
        {
          const int i = member[start[root] + k];
          for(int c = 0; c < 4; c++)
            {
              before[c] += g[k] * u[k][c];
              after[c] += (g[k] + dm[k]) * uout[k][c];
              scale[c] += g[k] * fabs(u[k][c]);
              set->ale_uold[i][c] = uout[k][c];
            }
          rd_ale_refresh_primitives(i, set->ale_uold[i]);
        }
      cavities++;
      limited += diag.theta < 1.0;
      low_only += diag.theta == 0.0;
      theta_min = dmin(theta_min, diag.theta);
      theta_sum += diag.theta;
      max_defect = dmax(max_defect, diag.defect_scale);
      max_change = dmax(max_change, diag.max_change);
    }

  double transfer_rel = 0.0;
  for(int c = 0; c < 4; c++)
    if(scale[c] > 0.0)
      transfer_rel = dmax(transfer_rel, fabs(after[c] - before[c]) / scale[c]);
  if(transfer_rel > 1e-12)
    terminate_program("RD flip transfer lost conservation within the cavities (rel %g)", transfer_rel);

  mpi_printf("RD-FLIP time=%.8g removed=%d inserted=%d cavities=%d vertices=%d max_cavity=%d limited=%d low_only=%d "
             "theta_min=%.6g theta_mean=%.6g max_defect=%.3e max_dU=%.3e transfer_rel=%.3e outside_dm=%.3e\n",
             All.Time, removed, inserted, cavities, n_cavity_vertices, cavities ? max_n : 0, limited, low_only, theta_min,
             cavities ? theta_sum / cavities : 1.0, max_defect, max_change, transfer_rel, outside_dm);

  free(uout); free(work); free(uh); free(ul); free(u); free(dm); free(g);
  free(member); free(start); free(parent); free(map); free(fresh);
}
#endif

static void rd_ale_prepare_step(tessellation *T, struct rd_element_set *set)
{
  if(NTask != 1)
    terminate_program("RD_ALE_EQUALSTEP v1 is deliberately restricted to one MPI rank");
  if(All.ComovingIntegrationOn)
    terminate_program("RD_ALE_EQUALSTEP v1 excludes comoving integration");

  integertime drift_ticks = All.Ti_Current - All.Previous_Ti_Current;
  set->ale_dt = drift_ticks * All.Timebase_interval;
  if(!(set->ale_dt > 0.0) || !isfinite(set->ale_dt))
    terminate_program("RD_ALE_EQUALSTEP received a non-positive drift interval");

  set->ale_geometry = (struct rd_ale_triangle_geometry *)mymalloc_movable(
      &set->ale_geometry, "RD_ALEGeometry", set->n * sizeof(*set->ale_geometry));
  set->ale_endpoint_area = (double *)mymalloc("RD_ALEEndpointArea", NumGas * sizeof(*set->ale_endpoint_area));
#if defined(RD_ALE_TOPOLOGY_REPAIR_DIAGNOSTIC) || defined(RD_ALE_FLIP_TRANSFER)
  set->ale_pullback_area = (double *)mymalloc("RD_ALEPullbackArea", NumGas * sizeof(*set->ale_pullback_area));
#endif
  set->ale_divisor = (double *)mymalloc("RD_ALEDivisor", NumGas * sizeof(*set->ale_divisor));
#ifdef RD_ALE_CFL_DIAGNOSTIC
  set->ale_cfl_alpha_sum = (double *)mymalloc("RD_ALECFLAlpha", NumGas * sizeof(*set->ale_cfl_alpha_sum));
#endif
  set->ale_uold = (double(*)[4])mymalloc("RD_ALEUOld", NumGas * sizeof(*set->ale_uold));
  memset(set->ale_endpoint_area, 0, NumGas * sizeof(*set->ale_endpoint_area));
#if defined(RD_ALE_TOPOLOGY_REPAIR_DIAGNOSTIC) || defined(RD_ALE_FLIP_TRANSFER)
  memset(set->ale_pullback_area, 0, NumGas * sizeof(*set->ale_pullback_area));
#endif
  memset(set->ale_divisor, 0, NumGas * sizeof(*set->ale_divisor));
#ifdef RD_ALE_CFL_DIAGNOSTIC
  memset(set->ale_cfl_alpha_sum, 0, NumGas * sizeof(*set->ale_cfl_alpha_sum));
#endif

  double umin[4] = {DBL_MAX, DBL_MAX, DBL_MAX, DBL_MAX};
  double umax[4] = {-DBL_MAX, -DBL_MAX, -DBL_MAX, -DBL_MAX};

  for(int i = 0; i < NumGas; i++)
    {
      double old_area = SphP[i].DualArea;
      if(!(old_area > 0.0) || !isfinite(old_area))
        terminate_program("RD_ALE_EQUALSTEP lost the old endpoint median-dual area");

      double q[4];
      rd_ale_q_from_particle(i, q);
      for(int component = 0; component < 4; component++)
        {
          set->ale_uold[i][component] = q[component] / old_area;
          set->ale_old_total[component] += q[component];
          umin[component] = dmin(umin[component], set->ale_uold[i][component]);
          umax[component] = dmax(umax[component], set->ale_uold[i][component]);
        }
    }

  point *DP = T->DP;
  tetra *DT = T->DT;
  double max_delta_identity = 0.0;
  double min_old_area = DBL_MAX, min_mid_area = DBL_MAX, min_new_area = DBL_MAX;
  double max_static_geometry_difference = 0.0;
  int stationary_geometry = 1, static_geometry_bit_mismatches = 0;

  for(int slot = 0; slot < set->n; slot++)
    {
      int triangle = set->element[slot];
      double xnew[3][2], velocity[3][2];
      int triangle_stationary = 1;

      for(int vertex = 0; vertex < 3; vertex++)
        {
          const point *dp = &DP[DT[triangle].p[vertex]];
          int index = rd_ale_local_point_index(dp);
          xnew[vertex][0] = dp->x;
          xnew[vertex][1] = dp->y;
          velocity[vertex][0] = SphP[index].VelVertex[0];
          velocity[vertex][1] = SphP[index].VelVertex[1];
          if(velocity[vertex][0] != 0.0 || velocity[vertex][1] != 0.0)
            stationary_geometry = triangle_stationary = 0;
        }

      struct rd_ale_triangle_geometry *geometry = &set->ale_geometry[slot];
      rd_ale_triangle_geometry_build(xnew, velocity, set->ale_dt, geometry);

      double area_old = geometry->normals[RD_ALE_OLD].area;
      double area_mid = geometry->normals[RD_ALE_MID].area;
      double area_new = geometry->normals[RD_ALE_NEW].area;
      min_old_area = dmin(min_old_area, area_old);
      min_mid_area = dmin(min_mid_area, area_mid);
      min_new_area = dmin(min_new_area, area_new);

      if(!(area_old > 0.0) || !(area_mid > 0.0) || !(area_new > 0.0))
        {
          printf("RD-ALE invalid element: triangle=%d Aold=%.17g Amid=%.17g Anew=%.17g dt=%.17g\n", triangle,
                 area_old, area_mid, area_new, set->ale_dt);
          terminate_program("RD_ALE_EQUALSTEP found an inverted pulled-back or midpoint triangle");
        }
      for(int vertex = 0; vertex < 3; vertex++)
        if(!(geometry->normals[RD_ALE_MID].mag[vertex] > 0.0))
          terminate_program("RD_ALE_EQUALSTEP found a zero midpoint edge");

      if(triangle_stationary)
        {
          int triangle_static_mismatch = set->normals[slot].area != geometry->normals[RD_ALE_MID].area;
          max_static_geometry_difference =
              dmax(max_static_geometry_difference,
                   fabs(set->normals[slot].area - geometry->normals[RD_ALE_MID].area));
          for(int vertex = 0; vertex < 3; vertex++)
            {
              triangle_static_mismatch |= set->normals[slot].mag[vertex] != geometry->normals[RD_ALE_MID].mag[vertex];
              max_static_geometry_difference =
                  dmax(max_static_geometry_difference,
                       fabs(set->normals[slot].mag[vertex] - geometry->normals[RD_ALE_MID].mag[vertex]));
              for(int axis = 0; axis < 2; axis++)
                {
                  triangle_static_mismatch |=
                      set->normals[slot].normal[vertex][axis] != geometry->normals[RD_ALE_MID].normal[vertex][axis];
                  max_static_geometry_difference =
                      dmax(max_static_geometry_difference,
                           fabs(set->normals[slot].normal[vertex][axis] - geometry->normals[RD_ALE_MID].normal[vertex][axis]));
                }
            }
          static_geometry_bit_mismatches += triangle_static_mismatch;
        }
      set->normals[slot] = geometry->normals[RD_ALE_MID];

      /* The element geometry used by the residual is split in two: the normals
       * and their magnitudes are the midpoint ones in both candidate
       * formulations, because both evaluate the flux on T^{n+1/2}, while the
       * `area` field feeds only the lumped and F1 temporal mass -- it is never
       * used as the |T| of a gradient reconstruction, which is what makes this
       * decoupling safe.
       *
       * Log section 8.7 shows the two published forms differ by
       *     delta_T = (A_old + A_new)/2 - A_mid
       * added to both the element mass coefficient and the nodal divisor:
       *
       *   Arpaia et al. (2015), Proposition 4.1:  A_mid          and |Sbar^{n+1/2}|
       *   Campoli et al. (2017), section 2.2:     (A_old+A_new)/2 and the new median dual
       *
       * They are therefore one scheme with a second-order-small modification of
       * two scalars, and selecting between them here is the numerical check of
       * that algebra inside the fluid solver. */
#ifdef RD_ALE_CAMPOLI_MASS
      set->normals[slot].area = 0.5 * (area_old + area_new);
#endif

      double dv10x = velocity[1][0] - velocity[0][0];
      double dv10y = velocity[1][1] - velocity[0][1];
      double dv20x = velocity[2][0] - velocity[0][0];
      double dv20y = velocity[2][1] - velocity[0][1];
      double delta_velocity = 0.125 * set->ale_dt * set->ale_dt * (dv10x * dv20y - dv10y * dv20x);
      max_delta_identity = dmax(max_delta_identity, fabs(geometry->delta_area - delta_velocity));

      for(int vertex = 0; vertex < 3; vertex++)
        {
          int index = rd_ale_local_point_index(&DP[DT[triangle].p[vertex]]);
          set->ale_endpoint_area[index] += area_new / 3.0;
#if defined(RD_ALE_TOPOLOGY_REPAIR_DIAGNOSTIC) || defined(RD_ALE_FLIP_TRANSFER)
          set->ale_pullback_area[index] += area_old / 3.0;
#endif
#ifdef RD_ALE_CAMPOLI_MASS
          set->ale_divisor[index] += area_new / 3.0;
#else
          set->ale_divisor[index] += geometry->arpaia_divisor / 3.0;
#endif
        }
    }

  double endpoint_coverage = 0.0, divisor_coverage = 0.0;
  int nonpositive_divisors = 0;
  for(int i = 0; i < NumGas; i++)
    {
      endpoint_coverage += set->ale_endpoint_area[i];
      divisor_coverage += set->ale_divisor[i];
      if(!(set->ale_divisor[i] > 0.0) || !isfinite(set->ale_divisor[i]))
        nonpositive_divisors++;
    }

  double box_area = boxSize_X * boxSize_Y;
  double coverage_tolerance = 1.0e-10 * box_area;
  if(fabs(endpoint_coverage - box_area) > coverage_tolerance || fabs(divisor_coverage - box_area) > coverage_tolerance)
    {
      printf("RD-ALE coverage failure: endpoint=%.17g divisor=%.17g box=%.17g\n", endpoint_coverage, divisor_coverage,
             box_area);
      terminate_program("RD_ALE_EQUALSTEP geometry does not cover the periodic box");
    }
  if(nonpositive_divisors > 0)
    terminate_program("RD_ALE_EQUALSTEP found a non-positive modified Arpaia nodal divisor");
  if(stationary_geometry && static_geometry_bit_mismatches != 0)
    terminate_program("RD_ALE_EQUALSTEP sigma=0 geometry did not collapse bitwise to the static coefficients");

  set->ale_uniform_initial = 1;
  for(int component = 0; component < 4; component++)
    {
      double scale = dmax(1.0, dmax(fabs(umin[component]), fabs(umax[component])));
      if(umax[component] - umin[component] > 4096.0 * DBL_EPSILON * scale)
        set->ale_uniform_initial = 0;
    }
#ifdef RD_ALE_FLIP_TRANSFER
  rd_ale_apply_flip_transfer(T, set);
#endif
#ifdef RD_ALE_TOPOLOGY_REPAIR_DIAGNOSTIC
  rd_ale_apply_topology_repair(T, set);
#ifndef RD_ALE_REPAIR_STALE_PRIMITIVES
  /* The predictor residual and its saved initial state must use the same
   * repaired U, for every distribution scheme (before 2026-10-09 only the
   * Rusanov build did this; N/LDA/B evaluated the predictor from the
   * unrepaired primitives).  RD_ALE_REPAIR_STALE_PRIMITIVES reproduces the
   * old behaviour for comparison. */
  for(int i = 0; i < NumGas; i++)
    rd_ale_refresh_primitives(i, set->ale_uold[i]);
#elif defined(RD_RUSANOV_LOW_ORDER)
#error "RD_ALE_REPAIR_STALE_PRIMITIVES is a comparison switch for N/LDA/B only."
#endif
#endif


  for(int i = 0; i < NumGas; i++)
    {
      rd_ale_set_particle_q(i, set->ale_divisor[i], set->ale_uold[i]);
      SphP[i].DualArea = set->ale_divisor[i];
    }

  mpi_printf("RD-ALE-PREP time=%.8g dt=%.8g elements=%d minA=[%.3e,%.3e,%.3e] "
             "coverage=[%.17g,%.17g] delta_identity=%.3e uniform=%d stationary=%d static_bit_mismatch=%d "
             "static_max_diff=%.3e\n",
             All.Time, set->ale_dt, set->n, min_old_area, min_mid_area, min_new_area, endpoint_coverage,
             divisor_coverage, max_delta_identity, set->ale_uniform_initial, stationary_geometry,
             static_geometry_bit_mismatches, max_static_geometry_difference);
}

/*! Convert the temporary modified-midpoint ledger back to endpoint Q=m_new U
 *  and audit the declared physical endpoint totals. */
static void rd_ale_finish_step(struct rd_element_set *set)
{
  double temporary_total[4] = {0.0, 0.0, 0.0, 0.0};
  double new_total[4] = {0.0, 0.0, 0.0, 0.0}, new_abs[4] = {0.0, 0.0, 0.0, 0.0};
  double max_uniform_error = 0.0, max_uniform_scale = 1.0;

  for(int i = 0; i < NumGas; i++)
    {
      double qbar[4], unew[4];
      rd_ale_q_from_particle(i, qbar);
      for(int component = 0; component < 4; component++)
        {
          temporary_total[component] += qbar[component];
          unew[component] = qbar[component] / set->ale_divisor[i];
          max_uniform_error = dmax(max_uniform_error, fabs(unew[component] - set->ale_uold[i][component]));
          max_uniform_scale = dmax(max_uniform_scale, fabs(set->ale_uold[i][component]));
        }

      rd_ale_set_particle_q(i, set->ale_endpoint_area[i], unew);
      SphP[i].DualArea = set->ale_endpoint_area[i];

      double qnew[4];
      rd_ale_q_from_particle(i, qnew);
      for(int component = 0; component < 4; component++)
        {
          new_total[component] += qnew[component];
          new_abs[component] += fabs(qnew[component]);
        }
    }

  double max_conservation_defect = 0.0, conservation_scale = 1.0;
  double temporary_change[4], rebase_change[4], endpoint_change[4];
  for(int component = 0; component < 4; component++)
    {
      temporary_change[component] = temporary_total[component] - set->ale_old_total[component];
      rebase_change[component] = new_total[component] - temporary_total[component];
      endpoint_change[component] = new_total[component] - set->ale_old_total[component];
      max_conservation_defect = dmax(max_conservation_defect, fabs(endpoint_change[component]));
      conservation_scale = dmax(conservation_scale, fabs(set->ale_old_total[component]));
    }

#if defined(RD_ALE_FLIP_TRANSFER) && defined(RD_ALE_CAMPOLI_MASS)
  /* Campoli storage has no endpoint rebase and the flip element conserves
   * every cavity: the whole step must close to round-off for ANY state. */
  for(int component = 0; component < 4; component++)
    if(fabs(endpoint_change[component]) > 1e-11 * dmax(new_abs[component], DBL_MIN))
      terminate_program("RD flip transfer + Campoli: step conservation failed, component %d change %g (scale %g)",
                        component, endpoint_change[component], new_abs[component]);
#endif
  (void)new_abs;

  if(set->ale_uniform_initial)
    {
      double state_tolerance = 32768.0 * DBL_EPSILON * max_uniform_scale;
      double conservation_tolerance = 32768.0 * DBL_EPSILON * conservation_scale;
      if(max_uniform_error > state_tolerance)
        terminate_program("RD_ALE_EQUALSTEP failed particle-wise free-stream preservation");
      if(max_conservation_defect > conservation_tolerance)
        terminate_program("RD_ALE_EQUALSTEP failed uniform-state endpoint conservation");
    }

  mpi_printf("RD-ALE-FINISH time=%.8g uniform=%d max_dU=%.3e endpoint_cons=%.3e "
             "temporary_change=[%.6e,%.6e,%.6e,%.6e] rebase_change=[%.6e,%.6e,%.6e,%.6e] "
             "endpoint_change=[%.6e,%.6e,%.6e,%.6e] totals=[%.17g,%.17g,%.17g,%.17g]\n",
             All.Time, set->ale_uniform_initial, max_uniform_error, max_conservation_defect, temporary_change[0],
             temporary_change[1], temporary_change[2], temporary_change[3], rebase_change[0], rebase_change[1],
             rebase_change[2], rebase_change[3], endpoint_change[0], endpoint_change[1], endpoint_change[2],
             endpoint_change[3], new_total[0], new_total[1], new_total[2], new_total[3]);
}

#ifdef RD_ALE_CFL_DIAGNOSTIC
/*! Report, but do not yet enforce, the scalar ALE-RD CFL restriction
 *
 *       dt_i <= CFL mbar_i / sum_{T contains i} alpha_T,
 *       alpha_T = max_j rho(K_j) = max_{j,q} |n_j| |lambda_{jq}| / 2.
 *
 *  The existing AREPO bound is reconstructed from the same quantities used by
 *  get_timestep_hydro(), including CurrentMaxTiStep when the tree signal-speed
 *  limiter is enabled.  Keeping this diagnostic non-invasive establishes the
 *  convention and safety ratio before it is allowed to select a time bin. */
static void rd_ale_report_cfl(const struct rd_element_set *set)
{
  double rd_limit = DBL_MAX, carrier_limit = DBL_MAX;
  MyIDType rd_id = 0, carrier_id = 0;

  for(int i = 0; i < NumGas; i++)
    {
      double alpha_sum = set->ale_cfl_alpha_sum[i];
      if(alpha_sum > 0.0 && isfinite(alpha_sum))
        {
          double candidate = All.CourantFac * set->ale_divisor[i] / alpha_sum;
          if(candidate < rd_limit)
            {
              rd_limit = candidate;
              rd_id = P[i].ID;
            }
        }

      double csnd = get_sound_speed(i);
      if(!(csnd > 0.0))
        csnd = 1.0e-30;
#ifdef VORONOI_STATIC_MESH
      csnd += sqrt(P[i].Vel[0] * P[i].Vel[0] + P[i].Vel[1] * P[i].Vel[1] + P[i].Vel[2] * P[i].Vel[2]) / All.cf_atime;
#endif
      double carrier_candidate = get_cell_radius(i) / csnd;
#ifdef TREE_BASED_TIMESTEPS
      carrier_candidate = dmin(carrier_candidate, SphP[i].CurrentMaxTiStep);
#endif
      carrier_candidate *= All.CourantFac;
      if(carrier_candidate < carrier_limit)
        {
          carrier_limit = carrier_candidate;
          carrier_id = P[i].ID;
        }
    }

  if(!(rd_limit < DBL_MAX))
    terminate_program("RD ALE CFL diagnostic found no positive nodal alpha sum");

  /* With RD_ALE_CFL_TIMESTEP, CurrentMaxTiStep already carries the minimum of
   * AREPO's tree bound and the current-geometry RD predictor.  Call this the
   * carrier limit rather than incorrectly labelling it as a pure FV bound. */
  mpi_printf("RD-CFL time=%.8g selected_dt=%.8g rd_midpoint_limit=%.8g carrier_limit=%.8g "
             "rd_over_selected=%.6e rd_over_carrier=%.6e rd_id=%llu carrier_id=%llu\n",
             All.Time, set->ale_dt, rd_limit, carrier_limit, rd_limit / set->ale_dt, rd_limit / carrier_limit,
             (unsigned long long)rd_id, (unsigned long long)carrier_id);
}
#endif
#endif /* RD_ALE_EQUALSTEP */
#ifdef RD_ALE_HIERARCHICAL
#ifdef RD_ALE_HIERARCHICAL_ARPAIA
static void rd_ale_hierarchical_q_from_particle(int i, double q[4])
{
  q[0] = P[i].Mass;
  q[1] = SphP[i].Momentum[0];
  q[2] = SphP[i].Momentum[1];
  q[3] = SphP[i].Energy;
}

static void rd_ale_hierarchical_set_particle_q(int i, double area, const double u[4])
{
  P[i].Mass = area * u[0];
  SphP[i].Momentum[0] = area * u[1];
  SphP[i].Momentum[1] = area * u[2];
  SphP[i].Energy = area * u[3];
  if(SphP[i].DualArea > 0.0)
    SphP[i].Momentum[2] *= area / SphP[i].DualArea;
}
#endif

static int rd_ale_hierarchical_local_index(const point *dp)
{
  if(dp->task != ThisTask)
    terminate_program("RD_ALE_HIERARCHICAL v1 encountered a remote vertex despite its one-rank guard");

  int index = dp->index;
  if(index >= NumGas)
    index -= NumGas;
  if(index < 0 || index >= NumGas)
    terminate_program("RD_ALE_HIERARCHICAL could not map a periodic image to its primary generator");
  return index;
}

/*! Prepare one concentrated moving-mesh hierarchy sweep on the current
 * connectivity.  Every due triangle is pulled back over its own finest-bin
 * interval.  The predictor sweep advances the scalar geometric ledger and
 * closes synchronized vertices to the exact current median-dual mass; the
 * corrector sweep only reconstructs the identical midpoint geometry. */
static void rd_ale_hierarchical_prepare(tessellation *T, struct rd_element_set *set, int rd_stage)
{
  if(NTask != 1)
    terminate_program("RD_ALE_HIERARCHICAL v1 is deliberately restricted to one MPI rank");
  if(All.ComovingIntegrationOn)
    terminate_program("RD_ALE_HIERARCHICAL v1 excludes comoving integration");

  set->ale_hier_divisor_element_area =
      (double *)mymalloc("RD_ALEHierElementDivisorArea", set->n * sizeof(*set->ale_hier_divisor_element_area));
  set->ale_hier_endpoint_area =
      (double *)mymalloc("RD_ALEHierEndpointArea", NumGas * sizeof(*set->ale_hier_endpoint_area));
  memset(set->ale_hier_endpoint_area, 0, NumGas * sizeof(*set->ale_hier_endpoint_area));
#ifdef RD_ALE_HIERARCHICAL_ARPAIA
  set->ale_hier_divisor =
      (double *)mymalloc("RD_ALEHierArpaiaDivisor", NumGas * sizeof(*set->ale_hier_divisor));
  memset(set->ale_hier_divisor, 0, NumGas * sizeof(*set->ale_hier_divisor));
#endif

  point *DP = T->DP;
  tetra *DT = T->DT;
  double min_old = DBL_MAX, min_mid = DBL_MAX, min_new = DBL_MAX;
  double geometric_change[4] = {0.0, 0.0, 0.0, 0.0};
  double closing_change[4] = {0.0, 0.0, 0.0, 0.0};
  double max_close_relative = 0.0;
  int due_elements = 0, closed_vertices = 0;

  for(int slot = 0; slot < set->n; slot++)
    {
      int triangle = set->element[slot];
      double current_area = set->normals[slot].area;

      for(int vertex = 0; vertex < 3; vertex++)
        {
          int index = rd_ale_hierarchical_local_index(&DP[DT[triangle].p[vertex]]);
          set->ale_hier_endpoint_area[index] += current_area / 3.0;
        }

      if(!set->active[slot])
        continue;

      int triangle_bin = rd_point_timebin(&DP[DT[triangle].p[0]]);
      for(int vertex = 1; vertex < 3; vertex++)
        triangle_bin = imin(triangle_bin, rd_point_timebin(&DP[DT[triangle].p[vertex]]));

      double dt = (((integertime)1) << triangle_bin) * All.Timebase_interval;
      double xnew[3][2], velocity[3][2];

      for(int vertex = 0; vertex < 3; vertex++)
        {
          const point *dp = &DP[DT[triangle].p[vertex]];
          int index = rd_ale_hierarchical_local_index(dp);
          xnew[vertex][0] = dp->x;
          xnew[vertex][1] = dp->y;
          velocity[vertex][0] = SphP[index].VelVertex[0];
          velocity[vertex][1] = SphP[index].VelVertex[1];
        }

      struct rd_ale_triangle_geometry geometry;
      rd_ale_triangle_geometry_build(xnew, velocity, dt, &geometry);

      double area_old = geometry.normals[RD_ALE_OLD].area;
      double area_mid = geometry.normals[RD_ALE_MID].area;
      double area_new = geometry.normals[RD_ALE_NEW].area;
      min_old = dmin(min_old, area_old);
      min_mid = dmin(min_mid, area_mid);
      min_new = dmin(min_new, area_new);

      if(!(area_old > 0.0) || !(area_mid > 0.0) || !(area_new > 0.0))
        {
          printf("RD-ALE-HIER invalid element: triangle=%d bin=%d Aold=%.17g Amid=%.17g Anew=%.17g dt=%.17g\n",
                 triangle, triangle_bin, area_old, area_mid, area_new, dt);
          terminate_program("RD_ALE_HIERARCHICAL found an inverted pulled-back or midpoint triangle");
        }
      for(int vertex = 0; vertex < 3; vertex++)
        if(!(geometry.normals[RD_ALE_MID].mag[vertex] > 0.0))
          terminate_program("RD_ALE_HIERARCHICAL found a zero midpoint edge");

      set->normals[slot] = geometry.normals[RD_ALE_MID];
#ifdef RD_ALE_HIERARCHICAL_ARPAIA
      /* Published Arpaia pair: M_T=A_mid and
       * D_T=A_mid+(A_new-A_old)/2. D_T is a temporary RK coefficient,
       * not the physical endpoint dual area. */
      set->ale_hier_divisor_element_area[slot] = geometry.arpaia_divisor;
      for(int vertex = 0; vertex < 3; vertex++)
        {
          int index = rd_ale_hierarchical_local_index(&DP[DT[triangle].p[vertex]]);
          set->ale_hier_divisor[index] += geometry.arpaia_divisor / 3.0;
        }
#else
      set->normals[slot].area = 0.5 * (area_old + area_new);
      set->ale_hier_divisor_element_area[slot] = area_new;
#endif
      due_elements++;

      if(rd_stage == RD_RK_STAGE_PREDICTOR)
        {
          double dg = (area_new - area_old) / 3.0;

          for(int vertex = 0; vertex < 3; vertex++)
            {
              int index = rd_ale_hierarchical_local_index(&DP[DT[triangle].p[vertex]]);
              double rho = SphP[index].Density;
              double velx = P[index].Vel[0], vely = P[index].Vel[1];
              double u[4] = {rho, rho * velx, rho * vely,
                             SphP[index].Pressure / GAMMA_MINUS1 +
                                 0.5 * rho * (velx * velx + vely * vely)};

              P[index].Mass += dg * u[0];
              SphP[index].Momentum[0] += dg * u[1];
              SphP[index].Momentum[1] += dg * u[2];
              SphP[index].Energy += dg * u[3];
              SphP[index].RD_GeoLedger += dg;
              for(int component = 0; component < 4; component++)
                geometric_change[component] += dg * u[component];
            }
        }
    }

  if(rd_stage == RD_RK_STAGE_PREDICTOR)
    {
      double endpoint_coverage = 0.0;
      for(int index = 0; index < NumGas; index++)
        {
          endpoint_coverage += set->ale_hier_endpoint_area[index];
          if(!(set->ale_hier_endpoint_area[index] > 0.0) || !isfinite(set->ale_hier_endpoint_area[index]))
            terminate_program("RD_ALE_HIERARCHICAL found an incomplete current vertex star");

          if(TimeBinSynchronized[P[index].TimeBinHydro])
            {
              double rho = SphP[index].Density;
              double velx = P[index].Vel[0], vely = P[index].Vel[1];
              double u[4] = {rho, rho * velx, rho * vely,
                             SphP[index].Pressure / GAMMA_MINUS1 +
                                 0.5 * rho * (velx * velx + vely * vely)};
              double correction = set->ale_hier_endpoint_area[index] - SphP[index].RD_GeoLedger;

              P[index].Mass += correction * u[0];
              SphP[index].Momentum[0] += correction * u[1];
              SphP[index].Momentum[1] += correction * u[2];
              SphP[index].Energy += correction * u[3];
              for(int component = 0; component < 4; component++)
                closing_change[component] += correction * u[component];

              max_close_relative =
                  dmax(max_close_relative, fabs(correction) / set->ale_hier_endpoint_area[index]);
              SphP[index].RD_GeoLedger = set->ale_hier_endpoint_area[index];
              SphP[index].DualArea = set->ale_hier_endpoint_area[index];
              closed_vertices++;
            }
        }

      double box_area = boxSize_X * boxSize_Y;
      if(fabs(endpoint_coverage - box_area) > 1.0e-10 * box_area)
        terminate_program("RD_ALE_HIERARCHICAL current full mesh does not cover the periodic box");

#ifdef RD_ALE_HIERARCHICAL_ARPAIA
      double divisor_sum = 0.0, min_divisor = DBL_MAX, max_rebase_relative = 0.0;
      int rebased_vertices = 0;
      for(int index = 0; index < NumGas; index++)
        {
          divisor_sum += set->ale_hier_divisor[index];
          if(SphP[index].RD_StarTimeBin == P[index].TimeBinHydro &&
             TimeBinSynchronized[P[index].TimeBinHydro])
            {
              double divisor = set->ale_hier_divisor[index];
              if(!(divisor > 0.0) || !isfinite(divisor))
                terminate_program("RD_ALE_HIERARCHICAL_ARPAIA found a non-positive live nodal divisor");
              double q[4], u[4];
              rd_ale_hierarchical_q_from_particle(index, q);
              for(int component = 0; component < 4; component++)
                u[component] = q[component] / set->ale_hier_endpoint_area[index];
              rd_ale_hierarchical_set_particle_q(index, divisor, u);
              SphP[index].DualArea = divisor;
              min_divisor = dmin(min_divisor, divisor);
              max_rebase_relative = dmax(max_rebase_relative,
                  fabs(divisor - set->ale_hier_endpoint_area[index]) /
                  set->ale_hier_endpoint_area[index]);
              rebased_vertices++;
            }
        }
      int all_due = due_elements == set->n;
      mpi_printf("RD-ALE-HIER-ARPAIA time=%.8g stage=open live=%d all_due=%d "
                 "active_divisor_sum=%.17g box_defect_if_full=%+.6e "
                 "min_live=%.6e max_rebase_rel=%.6e\n",
                 All.Time, rebased_vertices, all_due, divisor_sum,
                 all_due ? divisor_sum - box_area : NAN, min_divisor,
                 max_rebase_relative);
#endif

      mpi_printf("RD-ALE-HIER time=%.8g stage=ledger due=%d closed=%d minA=[%.3e,%.3e,%.3e] "
                 "max_close_rel=%.3e geom=[%+.6e,%+.6e,%+.6e,%+.6e] "
                 "basis=[%+.6e,%+.6e,%+.6e,%+.6e]\n",
                 All.Time, due_elements, closed_vertices, min_old, min_mid, min_new, max_close_relative,
                 geometric_change[0], geometric_change[1], geometric_change[2], geometric_change[3],
                 closing_change[0], closing_change[1], closing_change[2], closing_change[3]);
    }

#ifdef RD_ALE_HIERARCHICAL_ARPAIA
  if(rd_stage == RD_RK_STAGE_CORRECTOR)
    for(int index = 0; index < NumGas; index++)
      if(SphP[index].RD_StarTimeBin == P[index].TimeBinHydro &&
         TimeBinSynchronized[P[index].TimeBinHydro])
        {
          double divisor = set->ale_hier_divisor[index];
          if(!(divisor > 0.0) || !isfinite(divisor))
            terminate_program("RD_ALE_HIERARCHICAL_ARPAIA lost its live nodal divisor in the corrector");
          double scale = dmax(1.0, dmax(fabs(divisor), fabs(SphP[index].DualArea)));
          if(fabs(divisor - SphP[index].DualArea) > 4096.0 * DBL_EPSILON * scale)
            terminate_program("RD_ALE_HIERARCHICAL_ARPAIA predictor/corrector divisor mismatch");
        }
#endif
}

#ifdef RD_ALE_HIERARCHICAL_ARPAIA
static void rd_ale_hierarchical_arpaia_finish(const struct rd_element_set *set)
{
  double rebase_change[4] = {0.0, 0.0, 0.0, 0.0};
  double max_rebase_relative = 0.0;
  int rebased_vertices = 0;
  for(int index = 0; index < NumGas; index++)
    if(SphP[index].RD_StarTimeBin == P[index].TimeBinHydro &&
       TimeBinSynchronized[P[index].TimeBinHydro])
      {
        double qbar[4], unew[4], qnew[4];
        rd_ale_hierarchical_q_from_particle(index, qbar);
        for(int component = 0; component < 4; component++)
          {
            unew[component] = qbar[component] / set->ale_hier_divisor[index];
            qnew[component] = set->ale_hier_endpoint_area[index] * unew[component];
            rebase_change[component] += qnew[component] - qbar[component];
          }
        rd_ale_hierarchical_set_particle_q(index, set->ale_hier_endpoint_area[index], unew);
        SphP[index].DualArea = set->ale_hier_endpoint_area[index];
        max_rebase_relative = dmax(max_rebase_relative,
            fabs(set->ale_hier_endpoint_area[index] - set->ale_hier_divisor[index]) /
            set->ale_hier_endpoint_area[index]);
        rebased_vertices++;
      }
  mpi_printf("RD-ALE-HIER-ARPAIA time=%.8g stage=commit live=%d max_rebase_rel=%.6e "
             "dQ=[%+.6e,%+.6e,%+.6e,%+.6e]\n",
             All.Time, rebased_vertices, max_rebase_relative, rebase_change[0],
             rebase_change[1], rebase_change[2], rebase_change[3]);
}
#endif
#endif

#ifdef RD_ALE_INTERVAL_HIERARCHY
/* ==========================================================================
 * Moving-mesh hierarchy with actual-interval closure (one rank, N, Campoli).
 * Design: dev_log/RD_FLIP_ELEMENT_AND_MOVING_HIERARCHY_DESIGN_20261008.md;
 * Python oracle: tests/rd/audit_euler_flip_closure.py.
 *
 * A persistent registry holds every triangle of the RD connectivity with the
 * end s_T of its last integrated interval.  At each synchronisation time t:
 *  1. the registry is compared with the new Delaunay triangulation; changed
 *     triangles form cavities (connected components of their vertices);
 *  2. the closure set C = naturally due triangles (finest vertex bin
 *     synchronised) and every registry triangle touching a cavity vertex;
 *  3. C is integrated over its own intervals [s_T, t] with the concentrated
 *     Campoli RK2 (both sweeps at t, on a synthetic tessellation of C); a
 *     vertex predictor is live iff its whole star is in C with one start;
 *  4. every vertex whose whole star was closed is refreshed (this includes
 *     all active and cavity vertices); the geometric ledger equals the star
 *     area.  Between refreshes a vertex is therefore either live for one
 *     RK2 interval or frozen throughout;
 *  5. each cavity is transferred with the flip element (rd_flip_transfer.h);
 *  6. the registry is committed: retained triangles keep s_T (= t if closed),
 *     new ones start at t.
 * An edge shared by triangles with different intervals has frozen (non-live)
 * endpoints moving linearly, so the midpoint normals integrate its flux
 * exactly on both sides: totals are conserved at every common closure.
 * ========================================================================== */
struct rd_reg_triangle
{
  MyIDType key[3]; /* sorted particle IDs: the identity of the triangle */
  MyIDType ccw[3]; /* the same IDs, counter-clockwise */
  integertime start, birth;
};

struct rd_reg_new
{
  struct rd_reg_triangle t;
  double area;
};

struct rd_reg_idmap
{
  MyIDType id;
  int index;
};

static struct rd_reg_triangle *RdReg = NULL;
static int RdRegN = 0;
static double RdRegTotal[4];
static long long RdRegWork[4]; /* element updates, forced updates, non-dyadic intervals, events */
static struct rd_reg_idmap *RdIdMap = NULL;
static int *RdIdDirect = NULL; /* id -> local index when IDs are dense (max ID <= 4 NumGas), else NULL */
static MyIDType RdIdDirectMax = 0;
static char *RdIntervalClosed = NULL; /* local index -> whole star closed in this event */

static int rd_reg_key_cmp(const MyIDType *a, const MyIDType *b)
{
  for(int k = 0; k < 3; k++)
    if(a[k] != b[k])
      return a[k] < b[k] ? -1 : 1;
  return 0;
}

static int rd_reg_new_compare(const void *a, const void *b)
{
  return rd_reg_key_cmp(((const struct rd_reg_new *)a)->t.key, ((const struct rd_reg_new *)b)->t.key);
}

static int rd_reg_idmap_compare(const void *a, const void *b)
{
  const MyIDType x = ((const struct rd_reg_idmap *)a)->id, y = ((const struct rd_reg_idmap *)b)->id;
  return (x > y) - (x < y);
}

static void rd_reg_build_idmap(void)
{
  RdIdMap = (struct rd_reg_idmap *)realloc(RdIdMap, (NumGas > 0 ? NumGas : 1) * sizeof(*RdIdMap));
  if(RdIdMap == NULL)
    terminate_program("RD interval hierarchy: ID map allocation failed");
  for(int i = 0; i < NumGas; i++)
    {
      if(P[i].Ti_Current != All.Ti_Current)
        terminate_program("RD interval hierarchy needs every vertex drifted to the current time (ID=%llu)",
                          (unsigned long long)P[i].ID);
      RdIdMap[i].id = P[i].ID;
      RdIdMap[i].index = i;
    }
  qsort(RdIdMap, NumGas, sizeof(*RdIdMap), rd_reg_idmap_compare);
  for(int i = 1; i < NumGas; i++)
    if(RdIdMap[i].id == RdIdMap[i - 1].id)
      terminate_program("RD interval hierarchy requires unique particle IDs");
  /* Dense IDs (the usual case): O(1) lookup instead of a binary search. */
  free(RdIdDirect);
  RdIdDirect = NULL;
  RdIdDirectMax = NumGas > 0 ? RdIdMap[NumGas - 1].id : 0;
  if(NumGas > 0 && RdIdDirectMax <= (MyIDType)4 * NumGas)
    {
      RdIdDirect = (int *)malloc((RdIdDirectMax + 1) * sizeof(int));
      if(RdIdDirect == NULL)
        terminate_program("RD interval hierarchy: ID table allocation failed");
      for(MyIDType id = 0; id <= RdIdDirectMax; id++)
        RdIdDirect[id] = -1;
      for(int i = 0; i < NumGas; i++)
        RdIdDirect[RdIdMap[i].id] = RdIdMap[i].index;
    }
}

static int rd_reg_index(MyIDType id)
{
  if(RdIdDirect != NULL)
    {
      if(id > RdIdDirectMax || RdIdDirect[id] < 0)
        terminate_program("RD interval hierarchy: registry vertex ID=%llu is not a local gas particle", (unsigned long long)id);
      return RdIdDirect[id];
    }
  int lo = 0, hi = NumGas - 1;
  while(lo <= hi)
    {
      const int mid = (lo + hi) / 2;
      if(RdIdMap[mid].id == id)
        return RdIdMap[mid].index;
      if(RdIdMap[mid].id < id)
        lo = mid + 1;
      else
        hi = mid - 1;
    }
  terminate_program("RD interval hierarchy: registry vertex ID=%llu is not a local gas particle", (unsigned long long)id);
  return -1;
}

static int rd_reg_find(int *parent, int i)
{
  while(parent[i] != i)
    {
      parent[i] = parent[parent[i]];
      i = parent[i];
    }
  return i;
}

static void rd_reg_union(int *parent, const MyIDType key[3])
{
  int v[3];
  for(int k = 0; k < 3; k++)
    {
      v[k] = rd_reg_index(key[k]);
      if(parent[v[k]] < 0)
        parent[v[k]] = v[k];
    }
  for(int k = 1; k < 3; k++)
    {
      const int r0 = rd_reg_find(parent, v[0]), rk = rd_reg_find(parent, v[k]);
      if(r0 != rk)
        parent[rk] = r0;
    }
}

static double rd_reg_signed_area(const double x[3][2])
{
  return 0.5 * ((x[1][0] - x[0][0]) * (x[2][1] - x[0][1]) - (x[1][1] - x[0][1]) * (x[2][0] - x[0][0]));
}

/* Current coordinates in one coherent periodic image (minimal image about the
 * first vertex).  Edges must stay far below half the box. */
static void rd_reg_coordinates(const MyIDType id[3], int index[3], double x[3][2])
{
  const double box[2] = {boxSize_X, boxSize_Y};
  for(int v = 0; v < 3; v++)
    index[v] = rd_reg_index(id[v]);
  for(int d = 0; d < 2; d++)
    {
      x[0][d] = P[index[0]].Pos[d];
      for(int v = 1; v < 3; v++)
        {
          double dx = P[index[v]].Pos[d] - x[0][d];
          dx -= box[d] * floor(dx / box[d] + 0.5);
          if(fabs(dx) > 0.25 * box[d])
            terminate_program("RD interval hierarchy: triangle edge longer than a quarter box (IDs %llu %llu %llu)",
                              (unsigned long long)id[0], (unsigned long long)id[1], (unsigned long long)id[2]);
          x[v][d] = x[0][d] + dx;
        }
    }
}

static void rd_reg_sort_key(const MyIDType id[3], MyIDType key[3])
{
  for(int k = 0; k < 3; k++)
    key[k] = id[k];
  for(int a = 0; a < 2; a++)
    for(int b = a + 1; b < 3; b++)
      if(key[b] < key[a])
        {
          MyIDType tmp = key[a];
          key[a] = key[b];
          key[b] = tmp;
        }
  if(key[0] == key[1] || key[1] == key[2])
    terminate_program("RD interval hierarchy found a triangle with repeated particle IDs");
}

/* The owned physical triangles of a live tessellation, sorted by key, with
 * counter-clockwise IDs and current (positive) areas. */
static int rd_reg_collect_mesh(tessellation *T, struct rd_reg_new **out)
{
  struct rd_element_set set;
  rd_build_element_set(T, &set, 0);
  const int n = set.n;
  struct rd_reg_new *fresh = (struct rd_reg_new *)malloc((n > 0 ? n : 1) * sizeof(*fresh));
  if(fresh == NULL)
    terminate_program("RD interval hierarchy: allocation failed");
  for(int slot = 0; slot < n; slot++)
    {
      const int triangle = set.element[slot];
      double x[3][2];
      for(int v = 0; v < 3; v++)
        {
          const point *dp = &T->DP[T->DT[triangle].p[v]];
          fresh[slot].t.ccw[v] = dp->ID;
          x[v][0] = dp->x;
          x[v][1] = dp->y;
        }
      double area = rd_reg_signed_area(x);
      if(area < 0.0)
        {
          MyIDType tmp = fresh[slot].t.ccw[1];
          fresh[slot].t.ccw[1] = fresh[slot].t.ccw[2];
          fresh[slot].t.ccw[2] = tmp;
          area = -area;
        }
      if(!(area > 0.0) || !isfinite(area))
        terminate_program("RD interval hierarchy found a degenerate Delaunay triangle");
      rd_reg_sort_key(fresh[slot].t.ccw, fresh[slot].t.key);
      fresh[slot].t.start = fresh[slot].t.birth = All.Ti_Current;
      fresh[slot].area = area;
    }
  rd_free_element_set(&set);
  qsort(fresh, n, sizeof(*fresh), rd_reg_new_compare);
  for(int k = 1; k < n; k++)
    if(rd_reg_key_cmp(fresh[k - 1].t.key, fresh[k].t.key) == 0)
      terminate_program("RD interval hierarchy: ID-only triangle key is ambiguous (periodic winding needed)");
  *out = fresh;
  return n;
}

static void rd_reg_totals(double total[4], double scale[4])
{
  for(int c = 0; c < 4; c++)
    total[c] = scale[c] = 0.0;
  for(int i = 0; i < NumGas; i++)
    {
      const double q[4] = {P[i].Mass, SphP[i].Momentum[0], SphP[i].Momentum[1], SphP[i].Energy};
      for(int c = 0; c < 4; c++)
        {
          total[c] += q[c];
          scale[c] += fabs(q[c]);
        }
    }
}

/*! Create the registry from the opening tessellation (setup time only). */
static void rd_reg_init(tessellation *T)
{
  if(NTask != 1)
    terminate_program("RD_ALE_INTERVAL_HIERARCHY is restricted to one MPI rank");
  if(All.Ti_Current != 0)
    terminate_program("RD_ALE_INTERVAL_HIERARCHY cannot restart: the triangle registry is not stored in restart files");
  rd_reg_build_idmap();
  struct rd_reg_new *fresh;
  const int n = rd_reg_collect_mesh(T, &fresh);
  if(n != 2 * NumGas)
    terminate_program("RD interval hierarchy: a periodic triangulation needs 2N triangles (%d for N=%d)", n, NumGas);
  RdReg = (struct rd_reg_triangle *)malloc(n * sizeof(*RdReg));
  if(RdReg == NULL)
    terminate_program("RD interval hierarchy: allocation failed");
  for(int k = 0; k < n; k++)
    RdReg[k] = fresh[k].t;
  RdRegN = n;
  free(fresh);
  double scale[4];
  rd_reg_totals(RdRegTotal, scale);
  for(int i = 0; i < NumGas; i++)
    SphP[i].RD_CFLLedger = 0.0;
  mpi_printf("RD-IHIER-INIT time=%.8g triangles=%d vertices=%d\n", All.Time, RdRegN, NumGas);
}

#if defined(RD_DEBUG_ASSERTS) && !defined(RD_ALE_LAZY_FLIP)
/*! At the opening hook the registry must be exactly the live connectivity. */
static void rd_reg_check_mesh(tessellation *T)
{
  rd_reg_build_idmap();
  struct rd_reg_new *fresh;
  const int n = rd_reg_collect_mesh(T, &fresh);
  if(n != RdRegN)
    terminate_program("RD interval registry has %d triangles, the live mesh %d", RdRegN, n);
  for(int k = 0; k < n; k++)
    if(rd_reg_key_cmp(fresh[k].t.key, RdReg[k].key) != 0)
      terminate_program("RD interval registry differs from the live mesh at entry %d", k);
  free(fresh);
}
#endif

static void rd_reg_trace(int i, double u[4])
{
  const double rho = SphP[i].Density, vx = P[i].Vel[0], vy = P[i].Vel[1];
  u[0] = rho;
  u[1] = rho * vx;
  u[2] = rho * vy;
  u[3] = SphP[i].Pressure / GAMMA_MINUS1 + 0.5 * rho * (vx * vx + vy * vy);
}

/* Trace refresh of an inactive (forced) vertex from its conserved state.
 * Active vertices are refreshed by update_primitive_variables(). */
static void rd_reg_set_trace(int i, const double u[4])
{
  const double internal = u[3] - 0.5 * (u[1] * u[1] + u[2] * u[2]) / u[0];
  if(!(u[0] > 0.0) || !(internal > 0.0) || !isfinite(internal))
    terminate_program("RD interval hierarchy refreshed an inadmissible state: ID=%llu rho=%g e=%g",
                      (unsigned long long)P[i].ID, u[0], internal);
  SphP[i].Density = u[0];
  P[i].Vel[0] = u[1] / u[0];
  P[i].Vel[1] = u[2] / u[0];
  SphP[i].Utherm = internal / u[0];
  SphP[i].Pressure = GAMMA_MINUS1 * internal;
  SphP[i].Csnd = sqrt(GAMMA * SphP[i].Pressure / u[0]);
}

/*! Geometry of the synthetic closure set over each triangle's own interval.
 * The predictor call deposits the exact geometric term (dA/3) U_i and
 * advances the ledger; both calls rebuild the identical midpoint geometry. */
static void rd_ale_interval_prepare(tessellation *T, struct rd_element_set *set, int rd_stage)
{
  if(set->n != RdIntervalN)
    terminate_program("RD interval hierarchy: synthetic element set has %d of %d triangles", set->n, RdIntervalN);
  set->ale_hier_divisor_element_area =
      (double *)mymalloc("RD_ALEHierElementDivisorArea", set->n * sizeof(*set->ale_hier_divisor_element_area));
  set->ale_hier_endpoint_area = (double *)mymalloc("RD_ALEHierEndpointArea", NumGas * sizeof(*set->ale_hier_endpoint_area));
  memset(set->ale_hier_endpoint_area, 0, NumGas * sizeof(*set->ale_hier_endpoint_area));

  double min_area = DBL_MAX, geometric_change[4] = {0, 0, 0, 0};
  for(int slot = 0; slot < set->n; slot++)
    {
      const int triangle = set->element[slot];
      if(triangle != slot)
        terminate_program("RD interval hierarchy: synthetic element order changed");
      set->active[slot] = 1;
      double xnew[3][2], velocity[3][2];
      int index[3];
      for(int v = 0; v < 3; v++)
        {
          const point *dp = &T->DP[T->DT[triangle].p[v]];
          index[v] = dp->index;
          xnew[v][0] = dp->x;
          xnew[v][1] = dp->y;
          velocity[v][0] = SphP[index[v]].VelVertex[0];
          velocity[v][1] = SphP[index[v]].VelVertex[1];
        }
      struct rd_ale_triangle_geometry geometry;
      rd_ale_triangle_geometry_build(xnew, velocity, RdIntervalDt[slot], &geometry);
      const double a_old = geometry.normals[RD_ALE_OLD].area, a_mid = geometry.normals[RD_ALE_MID].area,
                   a_new = geometry.normals[RD_ALE_NEW].area;
      /* Signed area is quadratic in time: check its minimum over the interval. */
      const double c2 = 2.0 * (a_new + a_old - 2.0 * a_mid), c1 = a_new - a_old - c2;
      double a_min = dmin(a_old, a_new);
      if(c2 > 0.0)
        {
          const double s = -c1 / (2.0 * c2);
          if(s > 0.0 && s < 1.0)
            a_min = dmin(a_min, a_old + c1 * s + c2 * s * s);
        }
      if(!(a_min > 0.0) || !(a_mid > 0.0))
        {
          printf("RD-IHIER invalid element: IDs=%llu,%llu,%llu Aold=%.17g Amid=%.17g Anew=%.17g Amin=%.17g h=%.17g\n",
                 (unsigned long long)T->DP[3 * slot].ID, (unsigned long long)T->DP[3 * slot + 1].ID,
                 (unsigned long long)T->DP[3 * slot + 2].ID, a_old, a_mid, a_new, a_min, RdIntervalDt[slot]);
          terminate_program("RD interval hierarchy: a triangle inverts within its interval");
        }
      for(int v = 0; v < 3; v++)
        if(!(geometry.normals[RD_ALE_MID].mag[v] > 0.0))
          terminate_program("RD interval hierarchy found a zero midpoint edge");
      min_area = dmin(min_area, a_min);

      set->normals[slot] = geometry.normals[RD_ALE_MID];
      set->normals[slot].area = 0.5 * (a_old + a_new); /* Campoli temporal mass */
      set->ale_hier_divisor_element_area[slot] = a_new;
      for(int v = 0; v < 3; v++)
        set->ale_hier_endpoint_area[index[v]] += a_new / 3.0;

      if(rd_stage == RD_RK_STAGE_PREDICTOR)
        {
          const double dg = (a_new - a_old) / 3.0;
          for(int v = 0; v < 3; v++)
            {
              double u[4];
              rd_reg_trace(index[v], u);
              P[index[v]].Mass += dg * u[0];
              SphP[index[v]].Momentum[0] += dg * u[1];
              SphP[index[v]].Momentum[1] += dg * u[2];
              SphP[index[v]].Energy += dg * u[3];
              SphP[index[v]].RD_GeoLedger += dg;
              for(int c = 0; c < 4; c++)
                geometric_change[c] += dg * u[c];
            }
        }
    }
  set->n_active = set->n;

  if(rd_stage == RD_RK_STAGE_PREDICTOR)
    {
      /* A closed star is complete: its live predictor is normalised by the
       * current median-dual mass. */
      for(int i = 0; i < NumGas; i++)
        if(RdIntervalClosed[i])
          {
            if(fabs(SphP[i].RD_GeoLedger - set->ale_hier_endpoint_area[i]) > 1e-10 * set->ale_hier_endpoint_area[i])
              terminate_program("RD interval hierarchy: closed-star ledger differs from the star area (ID=%llu)",
                                (unsigned long long)P[i].ID);
            SphP[i].DualArea = SphP[i].RD_GeoLedger;
          }
        else if(RdIntervalLive[i])
          terminate_program("RD interval hierarchy: live vertex with an open star");
      mpi_printf("RD-IHIER time=%.8g stage=prepare due=%d min_interval_area=%.3e geom=[%+.6e,%+.6e,%+.6e,%+.6e]\n",
                 All.Time, set->n, min_area, geometric_change[0], geometric_change[1], geometric_change[2],
                 geometric_change[3]);
    }
}

#ifdef RD_ALE_LAZY_FLIP
static int rd_lazy_edge_compare(const void *pa, const void *pb)
{
  const MyIDType *a = (const MyIDType *)pa, *b = (const MyIDType *)pb; /* struct starts with the two IDs */
  if(a[0] != b[0])
    return a[0] < b[0] ? -1 : 1;
  if(a[1] != b[1])
    return a[1] < b[1] ? -1 : 1;
  return 0;
}
#endif

/*! One synchronisation event of the interval hierarchy (see block comment). */
static void rd_ale_interval_event(tessellation *T)
{
  if(NTask != 1)
    terminate_program("RD_ALE_INTERVAL_HIERARCHY is restricted to one MPI rank");
  if(RdReg == NULL)
    terminate_program("RD interval hierarchy has no registry (restarts are not supported)");
  const integertime now = All.Ti_Current;
  rd_reg_build_idmap();

  /* 1. New connectivity and the changed cavities. */
  struct rd_reg_new *fresh;
  const int nf = rd_reg_collect_mesh(T, &fresh);
  int *match = (int *)malloc((nf > 0 ? nf : 1) * sizeof(int));
  char *dying = (char *)calloc(RdRegN > 0 ? RdRegN : 1, 1);
  int *parent = (int *)malloc(NumGas * sizeof(int));
  if(match == NULL || dying == NULL || parent == NULL)
    terminate_program("RD interval hierarchy: allocation failed");
  for(int i = 0; i < NumGas; i++)
    parent[i] = -1;
  int removed = 0, inserted = 0;
  for(int a = 0, b = 0; a < RdRegN || b < nf;)
    {
      const int cmp = a >= RdRegN ? 1 : (b >= nf ? -1 : rd_reg_key_cmp(RdReg[a].key, fresh[b].t.key));
      if(cmp == 0)
        match[b++] = a++;
      else if(cmp < 0)
        {
          dying[a] = 1;
          rd_reg_union(parent, RdReg[a++].key);
          removed++;
        }
      else
        {
          match[b] = -1;
          rd_reg_union(parent, fresh[b++].t.key);
          inserted++;
        }
    }
  /* keep_new[b]: the new triangle enters the registry (always, unless lazy). */
  char *keep_new = (char *)malloc(nf > 0 ? nf : 1);
  if(keep_new == NULL)
    terminate_program("RD interval hierarchy: allocation failed");
  for(int b = 0; b < nf; b++)
    keep_new[b] = 1;
  int n_adopted = 0, n_deferred = 0;
  double deferred_min_angle = 180.0, deferred_max_excess = -180.0;
#ifdef RD_ALE_LAZY_FLIP
  {
    /* Lazy flipping: a changed component (its old and new triangles tile
     * the same polygon) is adopted only once its old triangles are poor:
     * minimum angle below RD_LAZY_MIN_ANGLE or an old interior edge whose
     * opposite angles exceed pi by RD_LAZY_DELAUNAY_EXCESS.  Otherwise the
     * old, still valid connectivity is kept: no forced closure, no transfer. */
    struct rd_lazy_edge
    {
      MyIDType a, b;
      double angle;
      int root;
    } *edges = malloc((3 * removed > 0 ? 3 * removed : 1) * sizeof(*edges));
    double *root_angle = (double *)malloc(NumGas * sizeof(double)), *root_excess = (double *)malloc(NumGas * sizeof(double));
    char *adopt = (char *)calloc(NumGas, 1);
    int *croot = (int *)malloc(NumGas * sizeof(int));
    if(edges == NULL || root_angle == NULL || root_excess == NULL || adopt == NULL || croot == NULL)
      terminate_program("RD lazy flip: allocation failed");
    for(int i = 0; i < NumGas; i++)
      {
        croot[i] = parent[i] >= 0 ? rd_reg_find(parent, i) : -1;
        root_angle[i] = M_PI;
        root_excess[i] = -M_PI;
      }
    int ne = 0;
    for(int a = 0; a < RdRegN; a++)
      if(dying[a])
        {
          int index[3];
          double x[3][2];
          rd_reg_coordinates(RdReg[a].ccw, index, x);
          const int root = croot[index[0]];
          for(int v = 0; v < 3; v++)
            {
              const int v1 = (v + 1) % 3, v2 = (v + 2) % 3;
              const double ex = x[v1][0] - x[v][0], ey = x[v1][1] - x[v][1], fx = x[v2][0] - x[v][0], fy = x[v2][1] - x[v][1];
              const double angle = atan2(fabs(ex * fy - ey * fx), ex * fx + ey * fy);
              root_angle[root] = dmin(root_angle[root], angle);
              MyIDType ia = RdReg[a].ccw[v1], ib = RdReg[a].ccw[v2];
              edges[ne].a = ia < ib ? ia : ib;
              edges[ne].b = ia < ib ? ib : ia;
              edges[ne].angle = angle;
              edges[ne].root = root;
              ne++;
            }
        }
    qsort(edges, ne, sizeof(*edges), rd_lazy_edge_compare);
    for(int k = 1; k < ne; k++)
      if(edges[k].a == edges[k - 1].a && edges[k].b == edges[k - 1].b)
        root_excess[edges[k].root] = dmax(root_excess[edges[k].root], edges[k].angle + edges[k - 1].angle - M_PI);
    const double min_angle = RD_LAZY_MIN_ANGLE * M_PI / 180.0, max_excess = RD_LAZY_DELAUNAY_EXCESS * M_PI / 180.0;
    for(int i = 0; i < NumGas; i++)
      if(croot[i] == i)
        {
          adopt[i] = root_angle[i] < min_angle || root_excess[i] > max_excess;
          n_adopted += adopt[i];
          n_deferred += !adopt[i];
          if(!adopt[i])
            {
              deferred_min_angle = dmin(deferred_min_angle, root_angle[i] * 180.0 / M_PI);
              deferred_max_excess = dmax(deferred_max_excess, root_excess[i] * 180.0 / M_PI);
            }
        }
    for(int a = 0; a < RdRegN; a++)
      if(dying[a] && !adopt[croot[rd_reg_index(RdReg[a].key[0])]])
        dying[a] = 0;
    for(int b = 0; b < nf; b++)
      if(match[b] < 0 && !adopt[croot[rd_reg_index(fresh[b].t.key[0])]])
        keep_new[b] = 0;
    for(int i = 0; i < NumGas; i++)
      if(croot[i] >= 0 && !adopt[croot[i]])
        parent[i] = -1;
    free(croot); free(adopt); free(root_excess); free(root_angle); free(edges);
  }
#endif

  /* 2. Closure set, vertex stars and the live predictor mask. */
  char *due = (char *)malloc(RdRegN > 0 ? RdRegN : 1);
  int(*rindex)[3] = malloc((RdRegN > 0 ? RdRegN : 1) * sizeof(*rindex));
  int *degree = (int *)calloc(NumGas, sizeof(int)), *closed = (int *)calloc(NumGas, sizeof(int));
  integertime *smin = (integertime *)malloc(NumGas * sizeof(integertime)), *smax = (integertime *)malloc(NumGas * sizeof(integertime));
  char *live = (char *)calloc(NumGas, 1), *closed_star = (char *)calloc(NumGas, 1);
  if(due == NULL || rindex == NULL || degree == NULL || closed == NULL || smin == NULL || smax == NULL || live == NULL ||
     closed_star == NULL)
    terminate_program("RD interval hierarchy: allocation failed");
  for(int i = 0; i < NumGas; i++)
    {
      smin[i] = TIMEBASE;
      smax[i] = -1;
    }
  int n_due = 0, n_forced = 0, n_nondyadic = 0;
  for(int r = 0; r < RdRegN; r++)
    {
      int bin = TIMEBINS, forced = 0;
      for(int v = 0; v < 3; v++)
        {
          const int i = rindex[r][v] = rd_reg_index(RdReg[r].ccw[v]);
          bin = imin(bin, P[i].TimeBinHydro);
          forced |= parent[i] >= 0;
        }
      const int natural = TimeBinSynchronized[bin];
      if(RdReg[r].start > now || RdReg[r].start < RdReg[r].birth)
        terminate_program("RD interval registry has an invalid interval start");
      due[r] = natural || forced;
      if(due[r] && RdReg[r].start == now)
        terminate_program("RD interval hierarchy would close an empty interval");
      n_due += due[r];
      n_forced += due[r] && !natural;
      n_nondyadic += due[r] && (now - RdReg[r].start) != (((integertime)1) << bin);
      for(int v = 0; v < 3; v++)
        {
          const int i = rindex[r][v];
          degree[i]++;
          closed[i] += due[r];
          if(RdReg[r].start < smin[i])
            smin[i] = RdReg[r].start;
          if(RdReg[r].start > smax[i])
            smax[i] = RdReg[r].start;
        }
    }
  int n_live = 0, n_closed = 0;
  for(int i = 0; i < NumGas; i++)
    {
      if(degree[i] < 3)
        terminate_program("RD interval hierarchy: incomplete vertex star (ID=%llu degree=%d)", (unsigned long long)P[i].ID,
                          degree[i]);
      closed_star[i] = closed[i] == degree[i];
      live[i] = closed_star[i] && smin[i] == smax[i];
      n_live += live[i];
      n_closed += closed_star[i];
    }

  /* 3. Synthetic tessellation of the closure set; both concentrated sweeps. */
  tessellation synthetic;
  memset(&synthetic, 0, sizeof(synthetic));
  synthetic.Ndt = synthetic.MaxNdt = n_due;
  synthetic.Ndp = synthetic.MaxNdp = 3 * n_due;
  synthetic.DT = (tetra *)calloc(n_due > 0 ? n_due : 1, sizeof(tetra));
  synthetic.DP = (point *)calloc(3 * (n_due > 0 ? n_due : 1), sizeof(point));
  RdIntervalDt = (double *)malloc((n_due > 0 ? n_due : 1) * sizeof(double));
  if(synthetic.DT == NULL || synthetic.DP == NULL || RdIntervalDt == NULL)
    terminate_program("RD interval hierarchy: allocation failed");
  for(int r = 0, slot = 0; r < RdRegN; r++)
    if(due[r])
      {
        int index[3];
        double x[3][2];
        rd_reg_coordinates(RdReg[r].ccw, index, x);
        for(int v = 0; v < 3; v++)
          {
            point *dp = &synthetic.DP[3 * slot + v];
            dp->x = x[v][0];
            dp->y = x[v][1];
            dp->z = 0.0;
            dp->ID = RdReg[r].ccw[v];
            dp->task = ThisTask;
            dp->index = dp->originalindex = index[v];
            dp->timebin = P[index[v]].TimeBinHydro;
            synthetic.DT[slot].p[v] = 3 * slot + v;
            synthetic.DT[slot].t[v] = slot;
          }
        RdIntervalDt[slot] = (now - RdReg[r].start) * All.Timebase_interval;
        slot++;
      }
  RdIntervalN = n_due;
  RdIntervalLive = live;
  RdIntervalClosed = closed_star;
#ifdef B_SCHEME
  RdIntervalB = (struct rd_interval_b_stage0 *)malloc((n_due > 0 ? n_due : 1) * sizeof(*RdIntervalB));
  if(RdIntervalB == NULL)
    terminate_program("RD interval hierarchy: allocation failed");
#endif
  if(n_due > 0)
    {
      compute_residuals(&synthetic, RD_RK_STAGE_PREDICTOR);
      compute_residuals(&synthetic, RD_RK_STAGE_CORRECTOR);
    }
#ifdef B_SCHEME
  free(RdIntervalB);
  RdIntervalB = NULL;
#endif
  RdIntervalLive = NULL;
  RdIntervalClosed = NULL;
  free(RdIntervalDt);
  RdIntervalDt = NULL;
  free(synthetic.DP);
  free(synthetic.DT);
  for(int r = 0; r < RdRegN; r++)
    if(due[r])
      RdReg[r].start = now;

  /* 4. Star areas at t on both connectivities; ledger closure of every
   *    complete star; refresh only complete stars. */
  double *old_star = (double *)calloc(NumGas, sizeof(double)), *new_star = (double *)calloc(NumGas, sizeof(double));
  if(old_star == NULL || new_star == NULL)
    terminate_program("RD interval hierarchy: allocation failed");
  /* new_star: the next registry (kept old triangles and adopted new ones). */
  for(int r = 0; r < RdRegN; r++)
    {
      int index[3];
      double x[3][2];
      rd_reg_coordinates(RdReg[r].ccw, index, x);
      const double area = rd_reg_signed_area(x);
      if(!(area > 0.0))
        terminate_program("RD interval registry triangle is inverted at the current time");
      for(int v = 0; v < 3; v++)
        {
          old_star[index[v]] += area / 3.0;
          if(!dying[r])
            new_star[index[v]] += area / 3.0;
        }
    }
  for(int b = 0; b < nf; b++)
    if(match[b] < 0 && keep_new[b])
      for(int v = 0; v < 3; v++)
        new_star[rd_reg_index(fresh[b].t.ccw[v])] += fresh[b].area / 3.0;
  double max_ledger = 0.0, outside_dm = 0.0, max_cfl_ledger = 0.0;
  int n_refresh = 0, n_forced_refresh = 0, n_cfl_ledger_over = 0;
  for(int i = 0; i < NumGas; i++)
    {
      const int active = TimeBinSynchronized[P[i].TimeBinHydro];
      if((active || parent[i] >= 0) && !closed_star[i])
        terminate_program("RD interval hierarchy: refresh before full star closure (ID=%llu)", (unsigned long long)P[i].ID);
      if(closed_star[i])
        {
          const double rel = fabs(SphP[i].RD_GeoLedger - old_star[i]) / old_star[i];
          max_ledger = dmax(max_ledger, rel);
          if(rel > 1e-10)
            terminate_program("RD interval hierarchy: ledger %.17g differs from the star area %.17g (ID=%llu)",
                              SphP[i].RD_GeoLedger, old_star[i], (unsigned long long)P[i].ID);
          /* The ledger, not the recomputed geometry, is the divisor: Q was
           * accumulated with it, so a uniform state stays exactly uniform. */
          SphP[i].DualArea = SphP[i].RD_GeoLedger;
        }
      if(parent[i] < 0)
        outside_dm = dmax(outside_dm, fabs(new_star[i] - old_star[i]) / old_star[i]);
      if(closed_star[i])
        {
#ifdef RD_RUSANOV_LOW_ORDER
          const double ratio = SphP[i].RD_CFLLedger / SphP[i].DualArea;
          max_cfl_ledger = dmax(max_cfl_ledger, ratio);
          /* Enforced (Codex review R2): for a vertex frozen since its last
           * refresh this is the sufficient positivity condition.  Live
           * vertices are covered by the stage checks (their ratio can reach
           * 1.5 legitimately). */
          if(!isfinite(ratio) || (!live[i] && ratio > RD_CFL_LEDGER_LIMIT))
            terminate_program("RD interval hierarchy: frozen-vertex CFL ledger %.6g exceeds %.6g of its refreshed mass "
                              "(ID=%llu); positivity is no longer guaranteed",
                              ratio, (double)RD_CFL_LEDGER_LIMIT, (unsigned long long)P[i].ID);
          n_cfl_ledger_over += !live[i] && ratio > 1.0;
          SphP[i].RD_CFLLedger = 0.0;
#endif
          /* Refresh: the trace of every closed star becomes Q/ledger. Active
           * vertices are converted by update_primitive_variables(); the state
           * is checked here for all of them. */
          const double q[4] = {P[i].Mass, SphP[i].Momentum[0], SphP[i].Momentum[1], SphP[i].Energy};
          double u[4];
          for(int c = 0; c < 4; c++)
            u[c] = q[c] / SphP[i].DualArea;
          if(!rd_rusanov_admissible(u))
            terminate_program("RD interval hierarchy: inadmissible refreshed state (ID=%llu live=%d active=%d cavity=%d)",
                              (unsigned long long)P[i].ID, live[i], active, parent[i] >= 0);
          if(!active && parent[i] < 0)
            rd_reg_set_trace(i, u);
          n_refresh++;
          n_forced_refresh += !active;
        }
    }
  if(outside_dm > 1e-10)
    terminate_program("RD interval hierarchy: nodal mass changed outside every cavity (rel %g)", outside_dm);

  /* 5. Flip element on each cavity, from the refreshed states. */
  int *start = (int *)calloc(NumGas + 1, sizeof(int)), *member = (int *)malloc((NumGas > 0 ? NumGas : 1) * sizeof(int));
  if(start == NULL || member == NULL)
    terminate_program("RD interval hierarchy: allocation failed");
  int n_cavity_vertices = 0;
  for(int i = 0; i < NumGas; i++)
    if(parent[i] >= 0)
      {
        start[rd_reg_find(parent, i) + 1]++;
        n_cavity_vertices++;
      }
  for(int i = 0; i < NumGas; i++)
    start[i + 1] += start[i];
  int *fill = (int *)malloc((NumGas + 1) * sizeof(int));
  memcpy(fill, start, (NumGas + 1) * sizeof(int));
  for(int i = 0; i < NumGas; i++)
    if(parent[i] >= 0)
      member[fill[rd_reg_find(parent, i)]++] = i;
  free(fill);
  int max_n = 1;
  for(int root = 0; root < NumGas; root++)
    max_n = imax(max_n, start[root + 1] - start[root]);
  double *g = (double *)malloc(max_n * sizeof(double)), *dm = (double *)malloc(max_n * sizeof(double));
  double(*u)[4] = malloc(max_n * sizeof(*u)), (*ul)[4] = malloc(max_n * sizeof(*ul)), (*uh)[4] = malloc(max_n * sizeof(*uh));
  double(*work)[4] = malloc(max_n * sizeof(*work)), (*uout)[4] = malloc(max_n * sizeof(*uout));
  if(!g || !dm || !u || !ul || !uh || !work || !uout)
    terminate_program("RD interval hierarchy: allocation failed");
  struct rd_flip_options options = {GAMMA, RD_FLIP_FLOOR_FRACTION, RD_FLIP_DMP_RELAX, RD_FLIP_ENTROPY_BOUND,
                                    RD_FLIP_HIGH_MODE};
  int cavities = 0, limited = 0;
  double theta_min = 1.0, max_change = 0.0, before[4] = {0, 0, 0, 0}, after[4] = {0, 0, 0, 0}, scale[4] = {0, 0, 0, 0};
  for(int root = 0; root < NumGas; root++)
    {
      const int n = start[root + 1] - start[root];
      if(n == 0)
        continue;
      for(int k = 0; k < n; k++)
        {
          const int i = member[start[root] + k];
          const double q[4] = {P[i].Mass, SphP[i].Momentum[0], SphP[i].Momentum[1], SphP[i].Energy};
          g[k] = SphP[i].DualArea;
          dm[k] = new_star[i] - old_star[i];
          for(int c = 0; c < 4; c++)
            u[k][c] = q[c] / g[k];
        }
#ifdef RD_ALE_INTERVAL_NO_TRANSFER
      /* Negative control: keep U, so the totals change by the flip defect. */
      for(int k = 0; k < n; k++)
        for(int c = 0; c < 4; c++)
          uout[k][c] = u[k][c];
      struct rd_flip_diagnostics diag = {1.0, 0.0, 0.0, 1, 0, 0};
#else
      struct rd_flip_diagnostics diag;
      const int status = rd_flip_transfer(n, g, dm, (const double(*)[4])u, &options, ul, uh, work, uout, &diag);
      if(status != RD_FLIP_OK)
        terminate_program("RD interval hierarchy: flip transfer status %d on a cavity of %d vertices (ID=%llu)", status, n,
                          (unsigned long long)P[member[start[root]]].ID);
#endif
      for(int k = 0; k < n; k++)
        {
          const int i = member[start[root] + k];
          const double gnew = g[k] + dm[k];
          for(int c = 0; c < 4; c++)
            {
              before[c] += g[k] * u[k][c];
              after[c] += gnew * uout[k][c];
              scale[c] += g[k] * fabs(u[k][c]);
            }
          P[i].Mass = gnew * uout[k][0];
          SphP[i].Momentum[0] = gnew * uout[k][1];
          SphP[i].Momentum[1] = gnew * uout[k][2];
          SphP[i].Energy = gnew * uout[k][3];
          SphP[i].RD_GeoLedger = SphP[i].DualArea = gnew;
          if(!TimeBinSynchronized[P[i].TimeBinHydro])
            rd_reg_set_trace(i, uout[k]);
        }
      cavities++;
      limited += diag.theta < 1.0;
      theta_min = dmin(theta_min, diag.theta);
      max_change = dmax(max_change, diag.max_change);
    }
  double transfer_rel = 0.0;
  for(int c = 0; c < 4; c++)
    if(scale[c] > 0.0)
      transfer_rel = dmax(transfer_rel, fabs(after[c] - before[c]) / scale[c]);
#ifndef RD_ALE_INTERVAL_NO_TRANSFER
  if(transfer_rel > 1e-12)
    terminate_program("RD interval hierarchy: cavity transfer lost conservation (rel %g)", transfer_rel);
#endif

  /* 6. Commit: retained triangles keep their (possibly just closed) start. */
  int n_next = 0;
  for(int r = 0; r < RdRegN; r++)
    n_next += !dying[r];
  for(int b = 0; b < nf; b++)
    n_next += match[b] < 0 && keep_new[b];
  struct rd_reg_triangle *next = (struct rd_reg_triangle *)malloc((n_next > 0 ? n_next : 1) * sizeof(*next));
  if(next == NULL)
    terminate_program("RD interval hierarchy: allocation failed");
  int filled = 0;
  for(int a = 0, b = 0; a < RdRegN || b < nf;)
    {
      if(b < nf && (match[b] >= 0 || !keep_new[b]))
        {
          b++; /* retained twins come from the registry; deferred new triangles are dropped */
          continue;
        }
      if(a < RdRegN && dying[a])
        {
          a++;
          continue;
        }
      const int take_old = b >= nf || (a < RdRegN && rd_reg_key_cmp(RdReg[a].key, fresh[b].t.key) < 0);
      next[filled++] = take_old ? RdReg[a++] : fresh[b++].t;
    }
  if(filled != n_next || n_next != 2 * NumGas)
    terminate_program("RD interval hierarchy: committed registry has %d triangles (expected %d, 2N=%d)", filled, n_next,
                      2 * NumGas);
  free(RdReg);
  RdReg = next;
  RdRegN = n_next;

  /* Totals are meaningful when every triangle has just been closed. */
  RdRegWork[0] += n_due;
  RdRegWork[1] += n_forced;
  RdRegWork[2] += n_nondyadic;
  RdRegWork[3] += cavities;
  double cons = NAN, coverage = NAN;
  if(n_closed == NumGas)
    {
      double total[4], tscale[4];
      rd_reg_totals(total, tscale);
      cons = 0.0;
      for(int c = 0; c < 4; c++)
        if(tscale[c] > 0.0)
          cons = dmax(cons, fabs(total[c] - RdRegTotal[c]) / tscale[c]);
      double area = 0.0;
      for(int i = 0; i < NumGas; i++)
        area += SphP[i].DualArea;
      coverage = area / (boxSize_X * boxSize_Y) - 1.0;
#ifndef RD_ALE_INTERVAL_NO_TRANSFER
      if(cons > 1e-12 || fabs(coverage) > 1e-12)
        terminate_program("RD interval hierarchy lost conservation at a common closure: cons=%g coverage=%g", cons, coverage);
#endif
    }
  mpi_printf("RD-IHIER time=%.8g stage=event triangles=%d due=%d forced=%d nondyadic=%d live=%d closed=%d refresh=%d "
             "forced_refresh=%d removed=%d inserted=%d cavities=%d cavity_vertices=%d limited=%d theta_min=%.6g "
             "max_dU=%.3e transfer_rel=%.3e max_ledger=%.3e outside_dm=%.3e cons=%.3e coverage=%+.3e "
             "cfl_ledger_max=%.3f cfl_ledger_over=%d adopted=%d deferred=%d deferred_min_angle=%.2f "
             "deferred_max_excess=%.2f work=[%lld,%lld,%lld,%lld]\n",
             All.Time, RdRegN, n_due, n_forced, n_nondyadic, n_live, n_closed, n_refresh, n_forced_refresh, removed, inserted,
             cavities, n_cavity_vertices, limited, theta_min, max_change, transfer_rel, max_ledger, outside_dm, cons, coverage,
             max_cfl_ledger, n_cfl_ledger_over, n_adopted, n_deferred, deferred_min_angle, deferred_max_excess, RdRegWork[0],
             RdRegWork[1], RdRegWork[2], RdRegWork[3]);

  free(uout); free(work); free(uh); free(ul); free(u); free(dm); free(g);
  free(member); free(start); free(new_star); free(old_star);
  free(closed_star); free(live); free(smax); free(smin); free(closed); free(degree); free(rindex); free(due);
  free(parent); free(keep_new); free(dying); free(match); free(fresh);
}
#endif /* RD_ALE_INTERVAL_HIERARCHY */

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
#ifndef TWODIMS
    box_area *= boxSize_Z;
#endif

    if(fabs(global_area - box_area) > 1.0e-10 * box_area)
      {
        printf("RD coverage audit failed: task=%d sum(DualArea)=%.17g box=%.17g rel=%.3e\n", ThisTask, global_area,
               box_area, fabs(global_area - box_area) / box_area);
        terminate_program("RD coverage audit: global dual area != box area");
      }
  }
#endif /* #ifdef RD_DEBUG_ASSERTS */
}

#if defined(RD_ALE_CFL_TIMESTEP) || defined(RD_RUSANOV_LOW_ORDER) || defined(RD_LDA_RUSANOV_BLEND) || defined(RD_3D_STATIC)
/*! Add the current-mesh RD spectral restriction to CurrentMaxTiStep.
 *
 *  This function is called immediately after tree_based_timesteps(), before
 *  AREPO quantises the next equal timestep.  For each current triangle,
 *
 *      alpha_T = max_j |n_j| [c_Roe + |(u_Roe-sigma_bar).n_hat_j|] / 2,
 *
 *  and every incident node receives alpha_T.  The resulting raw (pre-Courant)
 *  bound m_i/sum alpha_T is combined with, rather than substituted for, the
 *  tree/Voronoi signal bound.  At this selection point the future midpoint
 *  mass depends on the as-yet unknown dt; the current endpoint median-dual
 *  mass is therefore the explicit prototype coefficient.  The post-drift
 *  RD_ALE_CFL_DIAGNOSTIC reports the corresponding midpoint value and checks
 *  how much this explicit estimate changed over the accepted step. */
void rd_apply_cfl_timestep_constraint(tessellation *T)
{
#ifdef RD_3D_STATIC
  exchange_primitive_variables(); /* CFL sees current primary states, including ghosts. */
  struct rd_element_set set;
  rd_build_element_set(T, &set, 0);
  rd_static_tetra_cfl(T, set.n, set.element, set.normals);
  rd_free_element_set(&set);
#else
  if(NTask != 1)
    terminate_program("RD_ALE_CFL_TIMESTEP currently supports the one-rank ALE prototype only");

  struct rd_element_set set;
  rd_build_element_set(T, &set, 0);

  double *mass = (double *)mymalloc("RD_CFLMass", NumGas * sizeof(*mass));
  double *alpha_sum = (double *)mymalloc("RD_CFLAlpha", NumGas * sizeof(*alpha_sum));
  memset(mass, 0, NumGas * sizeof(*mass));
  memset(alpha_sum, 0, NumGas * sizeof(*alpha_sum));

  point *DP = T->DP;
  tetra *DT = T->DT;

  for(int slot = 0; slot < set.n; slot++)
    {
      int triangle = set.element[slot];
#if defined(RD_RUSANOV_LOW_ORDER) || defined(RD_LDA_RUSANOV_BLEND)
      double u[3][4], n[3][2], w[2] = {0.0, 0.0}, phi[4], residual[4][3], scale;
      for(int vertex = 0; vertex < 3; vertex++)
        {
          int index = rd_rusanov_local_index(&DP[DT[triangle].p[vertex]]);
          double rho = SphP[index].Density;
          u[vertex][0] = rho;
          u[vertex][1] = rho * P[index].Vel[0];
          u[vertex][2] = rho * P[index].Vel[1];
          u[vertex][3] = SphP[index].Pressure / GAMMA_MINUS1 +
                        0.5 * rho * (P[index].Vel[0] * P[index].Vel[0] + P[index].Vel[1] * P[index].Vel[1]);
          for(int axis = 0; axis < 2; axis++)
            {
              n[vertex][axis] = set.normals[slot].mag[vertex] * set.normals[slot].normal[vertex][axis];
              w[axis] += SphP[index].VelVertex[axis] / 3.0;
            }
          mass[index] += set.normals[slot].area / 3.0;
        }
#if defined(RD_LOW_ORDER_HLLC) || defined(RD_BLEND_LOW_HLLC)
      double coeff[3];
      double alpha = rd_hllc_residual(u, n, w, GAMMA, phi, residual, coeff, &scale);
#else
      double alpha = rd_rusanov_residual(u, n, w, GAMMA, phi, residual, &scale);
#endif
#if defined(RD_LDA_RUSANOV_BLEND) && !defined(RD_BLEND_LOW_HLLC)
      double nx[3], ny[3], mag[3];
      for(int vertex = 0; vertex < 3; vertex++)
        {
          nx[vertex] = set.normals[slot].normal[vertex][0];
          ny[vertex] = set.normals[slot].normal[vertex][1];
          mag[vertex] = set.normals[slot].mag[vertex];
        }
      rd_contour_gauss_correction(u, nx, ny, mag, GAMMA, phi, &scale);
      alpha = rd_lr_low(u, n, GAMMA, phi, residual);
#endif
      if(!(alpha > 0.0))
        terminate_program("Rusanov timestep estimate found an inadmissible state or bar state");
      for(int vertex = 0; vertex < 3; vertex++)
        alpha_sum[rd_rusanov_local_index(&DP[DT[triangle].p[vertex]])] +=
#if defined(RD_LOW_ORDER_HLLC) || defined(RD_BLEND_LOW_HLLC)
            coeff[vertex];
#elif defined(RD_LDA_RUSANOV_BLEND)
            alpha;
#else
            4.0 * alpha / 3.0;
#endif
#else
      double sum_sqrt_rho = 0.0, velx_num = 0.0, vely_num = 0.0, h_num = 0.0;
      double sigma[2] = {0.0, 0.0};

      for(int vertex = 0; vertex < 3; vertex++)
        {
          int index = rd_ale_local_point_index(&DP[DT[triangle].p[vertex]]);
          double rho = SphP[index].Density;
          double sqrt_rho = sqrt(rho);
          double velx = P[index].Vel[0], vely = P[index].Vel[1];
          double enthalpy = GAMMA / GAMMA_MINUS1 * SphP[index].Pressure / rho + 0.5 * (velx * velx + vely * vely);

          sum_sqrt_rho += sqrt_rho;
          velx_num += sqrt_rho * velx;
          vely_num += sqrt_rho * vely;
          h_num += sqrt_rho * enthalpy;
          sigma[0] += SphP[index].VelVertex[0] / 3.0;
          sigma[1] += SphP[index].VelVertex[1] / 3.0;
          mass[index] += set.normals[slot].area / 3.0;
        }

      double velx_roe = velx_num / sum_sqrt_rho;
      double vely_roe = vely_num / sum_sqrt_rho;
      double h_roe = h_num / sum_sqrt_rho;
      double cs2 = GAMMA_MINUS1 * (h_roe - 0.5 * (velx_roe * velx_roe + vely_roe * vely_roe));
      if(!(cs2 > 0.0) || !isfinite(cs2))
        terminate_program("RD_ALE_CFL_TIMESTEP encountered an invalid Roe sound speed");
      double cs = sqrt(cs2);
#ifdef RD_ALE_SHEAR_EIGENVALUE_FLOOR
      const double shear_floor_epsilon = RD_ALE_SHEAR_EIGENVALUE_FLOOR;
      if(!(shear_floor_epsilon > 0.0) || !(shear_floor_epsilon < 1.0) || !isfinite(shear_floor_epsilon))
        terminate_program("RD_ALE_SHEAR_EIGENVALUE_FLOOR must satisfy 0 < epsilon < 1");
      const double relative_x = velx_roe - sigma[0];
      const double relative_y = vely_roe - sigma[1];
      const int shear_floor_active =
          sqrt(relative_x * relative_x + relative_y * relative_y) < shear_floor_epsilon * cs;
#endif

      double alpha_triangle = 0.0;
      for(int vertex = 0; vertex < 3; vertex++)
        {
          double relative_normal =
              (velx_roe - sigma[0]) * set.normals[slot].normal[vertex][0] +
              (vely_roe - sigma[1]) * set.normals[slot].normal[vertex][1];
          double alpha_speed = cs + fabs(relative_normal);
#ifdef RD_ALE_SHEAR_EIGENVALUE_FLOOR
          if(shear_floor_active)
            {
              const double shear_modulus = dmax(fabs(relative_normal), shear_floor_epsilon * cs);
              const double shear_positive = 0.5 * (relative_normal + shear_modulus);
              alpha_speed = dmax(alpha_speed, shear_positive);
            }
#endif
          double alpha_vertex = 0.5 * set.normals[slot].mag[vertex] * alpha_speed;
          alpha_triangle = dmax(alpha_triangle, alpha_vertex);
        }

      for(int vertex = 0; vertex < 3; vertex++)
        {
          int index = rd_ale_local_point_index(&DP[DT[triangle].p[vertex]]);
          alpha_sum[index] += alpha_triangle;
        }
#endif
    }

  double raw_limit = DBL_MAX;
  MyIDType limiting_id = 0;
  for(int i = 0; i < NumGas; i++)
    {
      if(!(mass[i] > 0.0) || !(alpha_sum[i] > 0.0) || !isfinite(alpha_sum[i]))
        terminate_program("RD_ALE_CFL_TIMESTEP found an invalid nodal coefficient");
      double candidate = mass[i] / alpha_sum[i];
      SphP[i].CurrentMaxTiStep = dmin(SphP[i].CurrentMaxTiStep, candidate);
      if(candidate < raw_limit)
        {
          raw_limit = candidate;
          limiting_id = P[i].ID;
        }
    }

  mpi_printf("RD-CFL-SELECT time=%.8g current_mesh_raw=%.8g courant_limit=%.8g limiting_id=%llu\n",
             All.Time, raw_limit, All.CourantFac * raw_limit, (unsigned long long)limiting_id);

  myfree(alpha_sum);
  myfree(mass);
  rd_free_element_set(&set);
#endif /* RD_3D_STATIC */
}
#endif

void reset_dualarea(tessellation *T)
{
  struct rd_element_set set;

  rd_build_element_set(T, &set, 0);
  rd_accumulate_dual_area(T, &set);
#ifdef RD_ALE_HIERARCHICAL
  for(int i = 0; i < NumGas; i++)
    SphP[i].RD_GeoLedger = SphP[i].DualArea;
#endif
  rd_free_element_set(&set);
}

#ifdef RD_ALE_APOSTERIORI_FALLBACK
/* Diagnostic, deliberately global-retry implementation of an a-posteriori
 * LDA-to-N fallback.  B_SCHEME is used only as an internal engine because it
 * already forms coherent LDA and N branches for both RK stages.  The ordinary
 * B indicator is overridden below by one binary element mask: zero is exactly
 * the LDA branch and one is exactly the N/lumped branch.
 *
 * The trial is inspected before the predictor is consumed and again before
 * the temporary Arpaia ledger is committed to endpoint storage.  A rejected
 * trial restores Q and W from ale_uold while retaining the same mesh velocity,
 * geometry and connectivity.  This is a diagnosis of whether a very local N
 * substitution can save LDA; it is not the eventual pending-ledger design. */
#define RD_ALE_APOSTERIORI_MAX_ATTEMPTS 12

struct rd_aposteriori_trial_stats
{
  int bad_nodes;
  int hard_bad_nodes;
  double min_rho;
  double min_press;
  double min_rho_ratio;
  MyIDType worst_id;
};

static void rd_aposteriori_restore_trial(const struct rd_element_set *set)
{
  for(int i = 0; i < NumGas; i++)
    {
      const double *u = set->ale_uold[i];
      double rho      = u[0];
      double velx     = u[1] / rho;
      double vely     = u[2] / rho;
      double press    = GAMMA_MINUS1 * (u[3] - 0.5 * (u[1] * u[1] + u[2] * u[2]) / rho);

      if(!isfinite(rho) || !isfinite(press) || rho <= 0.0 || press <= 0.0)
        terminate_program("a-posteriori fallback could not restore the admissible stage-0 state");

      rd_ale_set_particle_q(i, set->ale_divisor[i], u);
      SphP[i].DualArea = set->ale_divisor[i];
      SphP[i].Density  = rho;
      P[i].Vel[0]      = velx;
      P[i].Vel[1]      = vely;
      P[i].Vel[2]      = 0.0;
      SphP[i].Pressure = press;
      SphP[i].Utherm   = press / (GAMMA_MINUS1 * rho);
#ifdef TREE_BASED_TIMESTEPS
      SphP[i].Csnd = sqrt(GAMMA * press / rho);
#endif
      for(int component = 0; component < 4; component++)
        SphP[i].RD_dU[component] = 0.0;
    }
}

static struct rd_aposteriori_trial_stats rd_aposteriori_inspect_trial(const struct rd_element_set *set,
                                                                      unsigned char *bad_vertex,
                                                                      const unsigned char *relaxed_vertex)
{
  struct rd_aposteriori_trial_stats stats;
  stats.bad_nodes     = 0;
  stats.hard_bad_nodes = 0;
  stats.min_rho       = DBL_MAX;
  stats.min_press     = DBL_MAX;
  stats.min_rho_ratio = DBL_MAX;
  stats.worst_id      = 0;

  const double ratio_floor = (double)(RD_ALE_APOSTERIORI_FALLBACK);
  if(!(ratio_floor > 0.0) || !(ratio_floor < 1.0))
    terminate_program("RD_ALE_APOSTERIORI_FALLBACK must be a density-ratio floor strictly between zero and one");

  memset(bad_vertex, 0, (size_t)NumGas * sizeof(*bad_vertex));

  for(int i = 0; i < NumGas; i++)
    {
      double q[4];
      rd_ale_q_from_particle(i, q);

      double rho       = q[0] / set->ale_divisor[i];
      double press     = NAN;
      double rho_ratio = rho / set->ale_uold[i][0];
      if(isfinite(rho) && rho > 0.0)
        press = GAMMA_MINUS1 * (q[3] / set->ale_divisor[i] -
                                0.5 * (q[1] * q[1] + q[2] * q[2]) /
                                    (set->ale_divisor[i] * q[0]));

      if(isfinite(rho))
        stats.min_rho = dmin(stats.min_rho, rho);
      else
        stats.min_rho = -DBL_MAX;
      if(isfinite(press))
        stats.min_press = dmin(stats.min_press, press);
      else
        stats.min_press = -DBL_MAX;

      double ranked_ratio = isfinite(rho_ratio) ? rho_ratio : -DBL_MAX;
      if(ranked_ratio < stats.min_rho_ratio)
        {
          stats.min_rho_ratio = ranked_ratio;
          stats.worst_id      = P[i].ID;
        }

      int hard_bad = !isfinite(rho) || !isfinite(press) || !isfinite(rho_ratio) || rho <= 0.0 || press <= 0.0;
      int soft_bad = !hard_bad && rho_ratio < ratio_floor && !relaxed_vertex[i];

      if(hard_bad || soft_bad)
        {
          bad_vertex[i] = 1;
          stats.bad_nodes++;
          if(hard_bad)
            stats.hard_bad_nodes++;
        }
    }

  return stats;
}

static int rd_aposteriori_expand_star(const tessellation *T, const struct rd_element_set *set,
                                      const unsigned char *bad_vertex, unsigned char *fallback_element,
                                      int *masked_total)
{
  int added = 0;

  for(int slot = 0; slot < set->n; slot++)
    {
      if(!set->active[slot] || fallback_element[slot])
        continue;

      int triangle = set->element[slot];
      for(int vertex = 0; vertex < 3; vertex++)
        {
          int index = rd_ale_local_point_index(&T->DP[T->DT[triangle].p[vertex]]);
          if(bad_vertex[index])
            {
              fallback_element[slot] = 1;
              added++;
              break;
            }
        }
    }

  *masked_total += added;
  return added;
}
static int rd_aposteriori_expand_halo(const tessellation *T, const struct rd_element_set *set,
                                      unsigned char *fallback_element, int *masked_total)
{
  unsigned char *halo_vertex =
      (unsigned char *)mymalloc("RD_AposterioriHaloVertex", (size_t)NumGas * sizeof(*halo_vertex));
  memset(halo_vertex, 0, (size_t)NumGas * sizeof(*halo_vertex));

  for(int slot = 0; slot < set->n; slot++)
    {
      if(!set->active[slot] || !fallback_element[slot])
        continue;

      int triangle = set->element[slot];
      for(int vertex = 0; vertex < 3; vertex++)
        {
          int index = rd_ale_local_point_index(&T->DP[T->DT[triangle].p[vertex]]);
          halo_vertex[index] = 1;
        }
    }

  int added = 0;
  for(int slot = 0; slot < set->n; slot++)
    {
      if(!set->active[slot] || fallback_element[slot])
        continue;

      int triangle = set->element[slot];
      for(int vertex = 0; vertex < 3; vertex++)
        {
          int index = rd_ale_local_point_index(&T->DP[T->DT[triangle].p[vertex]]);
          if(halo_vertex[index])
            {
              fallback_element[slot] = 1;
              added++;
              break;
            }
        }
    }

  myfree(halo_vertex);
  *masked_total += added;
  return added;
}

#endif

#ifdef RD_RK2_EQUALSTEP
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
#endif /* #ifdef RD_RK2_EQUALSTEP */

/*! The two main-loop hooks describe the lifetime of an RD step, not a claim
 * that every scheme evaluates its predictor on the opening mesh. Equal ALE
 * requires the new connectivity for both sweeps; begin only records its end
 * time and leaves all node/mesh data untouched. No preview or replay is needed. */
void rd_step_begin(tessellation *T)
{
  (void)T;
#if defined(RD_ALE_EQUALSTEP) && defined(RD_RK2_SPLIT_STAGES)
  if(NTask != 1 || NumGas == 0 || NumPart != NumGas || All.ComovingIntegrationOn || All.RD_EqualStepEnd != 0)
    terminate_program("ALE begin requires a closed, one-rank, gas-only, non-comoving step");
  int bin = P[0].TimeBinHydro; /* FORCE_EQUAL_TIMESTEPS assigns the same bin to all nodes. */
  if(bin <= 0 || bin >= TIMEBINS || !TimeBinSynchronized[bin])
    terminate_program("ALE begin received an invalid equal timestep");
#ifdef RD_DEBUG_ASSERTS
  /* Check the assignment invariant at the opening hook, before recording an
   * endpoint. Keep the extra node scan out of non-debug equal-step runs. */
  for(int i = 1; i < NumGas; i++)
    if(P[i].TimeBinHydro != bin)
      terminate_program("ALE begin requires equal hydro timebins: node=%d bin=%d expected=%d", i, P[i].TimeBinHydro, bin);
#endif
  All.RD_EqualStepEnd = All.Ti_Current + (((integertime)1) << bin);
#ifdef RD_DEBUG_ASSERTS
  mpi_printf("RD-STEP time=%.8g hook=begin sweeps=0 pending_endpoint=%lld\n", All.Time, (long long)All.RD_EqualStepEnd);
#endif
#elif defined(RD_HIERARCHICAL_TIMESTEPS) || defined(RD_RK2_SPLIT_STAGES)
#ifdef RD_ALE_INTERVAL_HIERARCHY
  if(RdReg == NULL)
    rd_reg_init(T);
#if defined(RD_DEBUG_ASSERTS) && !defined(RD_ALE_LAZY_FLIP)
  else
    rd_reg_check_mesh(T);
#endif
#endif
#ifndef RD_ALE_HIERARCHICAL
  compute_residuals(T, RD_RK_STAGE_PREDICTOR);
#endif
#elif !defined(RD_RK2_TOTAL_RESIDUAL)
  compute_residuals(T);
#endif
}

void rd_step_end(tessellation *T)
{
#if defined(RD_ALE_EQUALSTEP) && defined(RD_RK2_SPLIT_STAGES)
  if(All.RD_EqualStepEnd == 0 || All.RD_EqualStepEnd != All.Ti_Current)
    terminate_program("ALE end does not match the opening hook's endpoint");
  compute_residuals(T); /* Original two sweeps, one element set and one ALE geometry. */
  All.RD_EqualStepEnd = 0;
#ifdef RD_DEBUG_ASSERTS
  mpi_printf("RD-STEP time=%.8g hook=end sweeps=2 pending_endpoint=0\n", All.Time);
#endif
#elif defined(RD_ALE_INTERVAL_HIERARCHY)
  rd_ale_interval_event(T);
#elif defined(RD_ALE_HIERARCHICAL)
  compute_residuals(T, RD_RK_STAGE_PREDICTOR);
  compute_residuals(T, RD_RK_STAGE_CORRECTOR);
#elif defined(RD_HIERARCHICAL_TIMESTEPS) || defined(RD_RK2_SPLIT_STAGES)
  compute_residuals(T, RD_RK_STAGE_CORRECTOR);
#else
  compute_residuals(T);
#endif
}

#ifdef RD_HIERARCHICAL_TIMESTEPS
void compute_residuals(tessellation *T, int rd_stage)
#elif defined(RD_RK2_SPLIT_STAGES) && !defined(RD_ALE_EQUALSTEP)
void compute_residuals(tessellation *T, int rd_requested_stage)
#else
void compute_residuals(tessellation *T)
#endif
{
#ifdef NOHYDRO
  return;
#endif /* #ifdef NOHYDRO */
  TIMER_START(CPU_RESIDUAL_DISTRIBUTION);

  rd_reset_solver_statistics();

#if defined(RD_RK2_SPLIT_STAGES) && !defined(RD_ALE_EQUALSTEP)
  integertime rd_equal_interval = 0;
  if(rd_requested_stage == RD_RK_STAGE_PREDICTOR)
    {
      if(All.RD_EqualStepEnd != 0)
        terminate_program("RD equal predictor called with an unconsumed corrector");

      /* HighestActiveTimeBin still describes the previous synchronization
       * after timestep selection. Read the newly assigned vertex bins. */
      int local_bins[2] = {TIMEBINS, 0}, global_bins[2];
      for(int bin_index = 0; bin_index < NumGas; bin_index++)
        {
          int bin = P[bin_index].TimeBinHydro;
          local_bins[0] = imin(local_bins[0], bin);
          local_bins[1] = imin(local_bins[1], -bin);
        }
      MPI_Allreduce(local_bins, global_bins, 2, MPI_INT, MPI_MIN, MPI_COMM_WORLD);
      if(global_bins[0] <= 0 || global_bins[0] >= TIMEBINS || global_bins[0] != -global_bins[1] ||
         !TimeBinSynchronized[global_bins[0]])
        terminate_program("RD split equal predictor requires one synchronized vertex bin");
      rd_equal_interval = ((integertime)1) << global_bins[0];
    }
  else if(rd_requested_stage == RD_RK_STAGE_CORRECTOR)
    {
      if(All.RD_EqualStepEnd == 0 || All.RD_EqualStepEnd != All.Ti_Current)
        terminate_program("RD equal corrector does not match a saved predictor endpoint");
    }
  else
    terminate_program("invalid RD equal RK stage");

  if(All.ComovingIntegrationOn)
    terminate_program("RD_RK2_SPLIT_STAGES has only been defined for non-comoving hydro");
#endif

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
#if defined(RD_ALE_HIERARCHICAL) && defined(RD_ALE_HIERARCHICAL_ARPAIA)
  if(rd_stage == RD_RK_STAGE_PREDICTOR)
    rd_prepare_vertex_star_context(T);
#endif
#ifdef RD_ALE_EQUALSTEP
  rd_ale_prepare_step(T, &set);
#elif defined(RD_ALE_INTERVAL_HIERARCHY)
  rd_ale_interval_prepare(T, &set, rd_stage);
#elif defined(RD_ALE_HIERARCHICAL)
  rd_ale_hierarchical_prepare(T, &set, rd_stage);
#elif defined(RD_RK2_SPLIT_STAGES)
  /* Keep the predictor's divisor through the corrector, including a domain
   * migration or restart. Only element indices/normals are rebuilt here. */
  if(rd_requested_stage == RD_RK_STAGE_PREDICTOR)
    rd_accumulate_dual_area(T, &set);
  else
    for(int area_index = 0; area_index < NumGas; area_index++)
      if(!isfinite(SphP[area_index].DualArea) || SphP[area_index].DualArea <= 0.0)
        terminate_program("RD equal corrector lost its predictor DualArea");
#elif !defined(RD_HIERARCHICAL_TIMESTEPS)
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
#if !defined(RD_ALE_HIERARCHICAL_ARPAIA) && !defined(RD_ALE_INTERVAL_HIERARCHY)
      rd_prepare_vertex_star_context(T);
#endif
      rd_open_vertex_predictors();
    }

  /* Hierarchical stages use synchronized or assembled predictor states, not
   * the legacy primitive-variable Taylor extrapolation. */
  rd_record_dt_extrapolation(0.0);
#endif

  int Ndt_thistask        = set.n;
  int *thistask_triangles = set.element;
  tri_normals_list        = set.normals;

#ifdef RD_LDA_RUSANOV_B_SENSOR
  struct rd_lr_old_residual
  {
    double low[4][3], high[4][3], accepted[4][3], dt;
  } *rd_lr_old = (struct rd_lr_old_residual *)mymalloc("RD_LROldResidual", Ndt_thistask * sizeof(*rd_lr_old));
#endif

#if defined(B_SCHEME) && defined(RD_RK2_EQUALSTEP)
  /* A total-B corrector needs both spatial-stage distributions. The equal-bin
   * static element set has the same persistent ordering in both sweeps. */
  double(*rd_b_flux_n_stage0)[4][3] =
      (double(*)[4][3])mymalloc("RD_BFluxNStage0", Ndt_thistask * sizeof(*rd_b_flux_n_stage0));
  double(*rd_b_flux_lda_stage0)[4][3] =
      (double(*)[4][3])mymalloc("RD_BFluxLDAStage0", Ndt_thistask * sizeof(*rd_b_flux_lda_stage0));
  double(*rd_b_phi_stage0)[4] =
      (double(*)[4])mymalloc("RD_BPhiStage0", Ndt_thistask * sizeof(*rd_b_phi_stage0));
#endif

#ifdef RD_ALE_APOSTERIORI_FALLBACK
  unsigned char *fallback_element =
      (unsigned char *)mymalloc("RD_AposterioriElement", (size_t)Ndt_thistask * sizeof(*fallback_element));
  unsigned char *bad_vertex =
      (unsigned char *)mymalloc("RD_AposterioriVertex", (size_t)NumGas * sizeof(*bad_vertex));
  unsigned char *relaxed_vertex =
      (unsigned char *)mymalloc("RD_AposterioriRelaxedVertex", (size_t)NumGas * sizeof(*relaxed_vertex));
  memset(fallback_element, 0, (size_t)Ndt_thistask * sizeof(*fallback_element));
  memset(bad_vertex, 0, (size_t)NumGas * sizeof(*bad_vertex));
  memset(relaxed_vertex, 0, (size_t)NumGas * sizeof(*relaxed_vertex));
#endif

  Max_N_FluxRD_export = 0;
  for(i = 0; i < Ndt_thistask; i++)
    for(j = 0; j < DIMS + 1; j++)
      if(DP[DT[thistask_triangles[i]].p[j]].task != ThisTask)
        Max_N_FluxRD_export++;

#ifdef RD_RK2_EQUALSTEP
  /* Two-stage GL+F1 total-residual step (analysis document sections 1, 9,
   * 10): stage 0 is the RD predictor U* = U^n - (dt/|S_i|) sum phi_i(U^n),
   * stage 1 the corrector distributing the total residual. Both stages use
   * the FULL timestep; the half-step convention of the baseline pair is
   * unreachable on this path. Static split hooks execute only the requested
   * sweep; equal ALE keeps both sweeps here after the single mesh rebuild. */
  int rd_stage;
#ifdef RD_RK2_RATE_CONSISTENT_HEUN
  const int rd_number_of_passes = 4;
#else
  const int rd_number_of_passes = 2;
#endif
#if defined(RD_RK2_SPLIT_STAGES) && !defined(RD_ALE_EQUALSTEP)
  const int rd_first_pass = rd_requested_stage;
  const int rd_pass_end   = rd_requested_stage + 1;
  (void)rd_number_of_passes;
#else
  const int rd_first_pass = 0;
  const int rd_pass_end   = rd_number_of_passes;
#endif
#ifdef RD_ALE_APOSTERIORI_FALLBACK
  int fallback_attempt = 0;
  int fallback_masked_total = 0;
  int fallback_retry = 0;
  const char *fallback_rejected_stage = NULL;
  struct rd_aposteriori_trial_stats fallback_rejected_stats;

  while(1)
    {
      if(fallback_attempt > 0)
        {
          rd_reset_solver_statistics();
          rd_aposteriori_restore_trial(&set);
        }
      fallback_retry = 0;
#endif
  for(rd_stage = rd_first_pass; rd_stage < rd_pass_end; rd_stage++)
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
#ifdef RD_ALE_APOSTERIORI_FALLBACK
          fallback_rejected_stats = rd_aposteriori_inspect_trial(&set, bad_vertex, relaxed_vertex);
          if(fallback_rejected_stats.bad_nodes > 0)
            {
              fallback_retry          = 1;
              fallback_rejected_stage = "predictor";
              break;
            }
#endif
#ifndef RD_DIAG_SKIP_PREPARE /* diagnostic only: run stage 1 on the stage-0 inputs */
          rd_rk2_prepare_corrector(&RD_stat_min_stage_rho, &RD_stat_min_stage_press);
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
            loc[2] += fabs(SphP[ck].RD_dU[0]) + fabs(SphP[ck].RD_dU[DIMS + 1]);
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

#if defined(RD_DIAG_THETA_MAP) && defined(B_SCHEME) && defined(RD_RK2_EQUALSTEP)
  FILE *rd_theta_map_fp = NULL;
  if(rd_stage == 1 && fabs(All.Time - All.TimeMax) <= 16.0 * DBL_EPSILON * dmax(1.0, fabs(All.TimeMax)))
    rd_theta_map_fp = rd_theta_map_open();
#endif

  N_FluxRD_export     = 0;
  FluxRD_list =
      (struct FluxRD_list_data *)mymalloc_movable(&FluxRD_list, "FluxRD_list", Max_N_FluxRD_export * sizeof(struct FluxRD_list_data));

#ifdef RD_RUSANOV_LOW_ORDER
  /* Sum the actual stage coefficients, including midpoint geometry and U*.
   * A timestep selected on the opening mesh alone is not a proof of this bound. */
  double *rd_rus_coeff = (double *)mymalloc("RD_RusanovStageCoefficients", 2 * NumGas * sizeof(double));
  memset(rd_rus_coeff, 0, 2 * NumGas * sizeof(double));
#endif

#ifdef RD_LDA_RUSANOV_BLEND
  /* Assemble an admissible low-order state first; retain complete F1
   * corrections until their common element coefficient can be bounded. */
  double(*rd_lr_correction)[4][3] =
      (double(*)[4][3])mymalloc("RD_LRCorrection", Ndt_thistask * sizeof(*rd_lr_correction));
  double *rd_lr_cfl = (double *)mymalloc("RD_LRCFL", NumGas * sizeof(double));
  int *rd_lr_degree = (int *)mymalloc("RD_LRDegree", NumGas * sizeof(int));
  memset(rd_lr_cfl, 0, NumGas * sizeof(double));
  memset(rd_lr_degree, 0, NumGas * sizeof(int));
#ifdef RD_BLEND_LOW_HLLC
  /* Sum of midpoint |T|/3: the lumped temporal mass. With the Arpaia divisor
   * it gives the ALE corrector weights a_i and b_i=3/2-a_i. */
  double *rd_lr_mass = (double *)mymalloc("RD_LRMass", NumGas * sizeof(double));
  memset(rd_lr_mass, 0, NumGas * sizeof(double));
#endif
#ifdef RD_LDA_RUSANOV_B_SENSOR
  double rd_lr_theta_sum[4] = {0}, rd_lr_theta_max = 0;
  long long rd_lr_sensor_elements = 0;
#endif
#endif

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

#ifdef RD_ALE_INTERVAL_HIERARCHY
      (void)timebin_this_triangle;
      double full_triangle_dt = RdIntervalDt[i]; /* actual interval [s_T, t], not 2^bin */
#else
      double full_triangle_dt = (((integertime)1) << timebin_this_triangle) * All.Timebase_interval;
#endif
      double triangle_dt      = full_triangle_dt;

#ifdef RD_ALE_EQUALSTEP
      if(fabs(full_triangle_dt - set.ale_dt) > 64.0 * DBL_EPSILON * dmax(full_triangle_dt, set.ale_dt))
        terminate_program("RD_ALE_EQUALSTEP residual interval differs from the mesh drift interval");
#endif

#ifdef RD_RK2_RATE_CONSISTENT_HEUN
      /* Spatial/mass weights for k=2v-S^-1Mv and the Heun average. */
      const double rd_pass_weight[4] = {2.0, 1.0, 1.0, 0.5};
      triangle_dt *= rd_pass_weight[rd_stage];
#elif !defined(RD_RK2_EQUALSTEP)
      triangle_dt *= 0.5; /* the baseline applies two half-weight Heun calls per step */
#endif

      // compute residual: set up initial states
      double U_fluid[DIMS + 1][DIMS + 2];  // specific conserved fluid variables
#ifdef RD_LDA_COMMON_BETA
      double U_beta[3][4]; /* interval-opening state; never used for phi(U*) */
#endif
      double C_sound[DIMS + 1];
      double Pressure[DIMS + 1];

      double Velvertex_avg[3];  // moving mesh: average mesh velocity
#ifdef RD_ELEMENT_COMOVING_FRAME
      double rd_frame_G[4][4], rd_frame_Ginv[4][4];
#if defined(RD_ALE_EQUALSTEP) && defined(RD_ALE_SPLIT_MESH_VELOCITY)
      /* N is assembled in primed variables until the final nodal residual is
       * mapped back below. Keep the split correction in those same
       * coordinates for its conservative 1/3 distribution. */
      double rd_frame_split_correction[4] = {0.0, 0.0, 0.0, 0.0};
#endif
#endif
      for(j = 0; j < 3; j++)
        {
          Velvertex_avg[j] = 0.0;
        }

#ifdef RD_RK2_TOTAL_RESIDUAL
      double dU_vertex[DIMS + 1][DIMS + 2]; /* intensive nodal U* - U^n per vertex; corrector stage only */
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
                for(k = 0; k < DIMS + 2; k++)
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

              U_fluid[j][0]         = vertex_state.rho;
              U_fluid[j][1]         = U_fluid[j][0] * vertex_state.velx;
              U_fluid[j][2]         = U_fluid[j][0] * vertex_state.vely;
              Pressure[j]           = vertex_state.press;
              double kinetic_energy = 0.0;
              kinetic_energy += pow(vertex_state.velx, 2) + pow(vertex_state.vely, 2);
#ifndef TWODIMS
              U_fluid[j][3] = U_fluid[j][0] * vertex_state.velz;
              kinetic_energy += pow(vertex_state.velz, 2);
#endif
              kinetic_energy *= 0.5 * U_fluid[j][0];
              U_fluid[j][DIMS + 1] = kinetic_energy + Pressure[j] / (GAMMA_MINUS1);
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
                for(k = 0; k < DIMS + 2; k++)
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

              U_fluid[j][0]         = vertex_state.rho;
              U_fluid[j][1]         = U_fluid[j][0] * vertex_state.velx;
              U_fluid[j][2]         = U_fluid[j][0] * vertex_state.vely;
              Pressure[j]           = vertex_state.press;
              double kinetic_energy = 0.0;
              kinetic_energy += pow(vertex_state.velx, 2) + pow(vertex_state.vely, 2);
#ifndef TWODIMS
              U_fluid[j][3] = U_fluid[j][0] * vertex_state.velz;
              kinetic_energy += pow(vertex_state.velz, 2);
#endif
              kinetic_energy *= 0.5 * U_fluid[j][0];
              U_fluid[j][DIMS + 1] = kinetic_energy + Pressure[j] / (GAMMA_MINUS1);

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
#ifdef RD_LDA_COMMON_BETA
          /* In the hierarchy these primitives are the interval-opening
           * states, before the live-only predictor below. In equal stepping
           * the primitives already contain U*, so undo its stored increment.
           * The existing ghost exchange supplies that increment as well. */
          for(k = 0; k < 4; k++)
            {
              U_beta[j][k] = U_fluid[j][k];
#ifndef RD_HIERARCHICAL_TIMESTEPS
              if(rd_stage == 1)
                U_beta[j][k] -= dU_vertex[j][k];
#endif
            }
#endif
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

#ifdef TWODIMS
#ifdef RD_RUSANOV_LOW_ORDER
      double Phi[4], Flux_RD[4][3], phi_scale, normal[3][2];
      for(int vertex = 0; vertex < 3; vertex++)
        for(int axis = 0; axis < 2; axis++)
          normal[vertex][axis] = tri_normals_list[i].mag[vertex] * tri_normals_list[i].normal[vertex][axis];
#ifdef RD_LOW_ORDER_HLLC
      double coeff[3];
      double alpha = rd_hllc_residual(U_fluid, normal, Velvertex_avg, GAMMA, Phi, Flux_RD, coeff, &phi_scale);
      if(!(alpha > 0.0))
        terminate_program("HLLC stage found an inadmissible input, orientation or star state");
      rd_check_conservation(Flux_RD, Phi, phi_scale, thistask_triangles[i], "HLLC");
#else
      double alpha = rd_rusanov_residual(U_fluid, normal, Velvertex_avg, GAMMA, Phi, Flux_RD, &phi_scale);
      if(!(alpha > 0.0))
        terminate_program("Rusanov stage found an inadmissible input or pair bar state");
      rd_check_conservation(Flux_RD, Phi, phi_scale, thistask_triangles[i], "Rusanov");
#endif
      double N_roundoff_scale = phi_scale;
      for(int vertex = 0; vertex < 3; vertex++)
        {
          int index = rd_rusanov_local_index(&DP[DT[thistask_triangles[i]].p[vertex]]);
#ifdef RD_LOW_ORDER_HLLC
          rd_rus_coeff[index] += triangle_dt * coeff[vertex];
#else
          rd_rus_coeff[index] += triangle_dt * 4.0 * alpha / 3.0;
#endif
          rd_rus_coeff[NumGas + index] += tri_normals_list[i].area / 3.0;
        }
#else
      // compute residuals: Roe Vector Z, Modified fluid state U_hat = \frac{ \partial{U(Z_avg)}}{ \partial Z} * Z
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

#ifdef RD_LDA_COMMON_BETA
      /* Keep K(U*) for the conservative spatial residual, but build K+/-
       * from U^n. Thus beta^n acts on phi(U*) and on F1 without an extra
       * residual sweep, factorisation, or stored per-triangle beta tensor. */
      double rd_stage_average[4] = {velx_avg, vely_avg, h_avg, Cs_avg};
      double rd_beta_average[4] = {velx_avg, vely_avg, h_avg, Cs_avg};
      if(rd_stage == 1)
        {
          double weight_sum = 0.0, vx_sum = 0.0, vy_sum = 0.0, h_sum = 0.0;
          for(j = 0; j < 3; j++)
            {
              double rho = U_beta[j][0];
              double pressure = GAMMA_MINUS1 *
                  (U_beta[j][3] - 0.5 * (U_beta[j][1] * U_beta[j][1] + U_beta[j][2] * U_beta[j][2]) / rho);
              if(!(rho > 0.0) || !(pressure > 0.0) || !isfinite(rho) || !isfinite(pressure))
                terminate_program("RD common-beta opening state is not physical");
              double weight = sqrt(rho);
              weight_sum += weight;
              vx_sum += weight * U_beta[j][1] / rho;
              vy_sum += weight * U_beta[j][2] / rho;
              h_sum += weight * ((U_beta[j][3] + pressure) / rho);
            }
          rd_beta_average[0] = vx_sum / weight_sum;
          rd_beta_average[1] = vy_sum / weight_sum;
          rd_beta_average[2] = h_sum / weight_sum;
          rd_beta_average[3] = sqrt(GAMMA_MINUS1 * (rd_beta_average[2] -
              0.5 * (rd_beta_average[0] * rd_beta_average[0] + rd_beta_average[1] * rd_beta_average[1])));
          if(!(rd_beta_average[3] > 0.0) || !isfinite(rd_beta_average[3]))
            terminate_program("RD common-beta Roe average is not physical");
        }
#endif

      // compute residual: Reassign variables to local equivalents
      // compute residual: Calculate K+,K- and K matrices for each vertex
      double vel_dot_n, velvertex_dot_n;
      double Lambda[3][4], Lambda_plus[3][4], Lambda_minus[3][4];
      double Value1, Value2, Value3;
      double Kmatrix[4][4][3][3];  // Kmatrix[4][4][j=0,1,2(vertices)][p=0(K+),1(K-),2(K)]
#if defined(RD_ALE_EQUALSTEP) && defined(RD_ALE_SPLIT_MESH_VELOCITY)
      double rd_ale_mesh_velocity_correction[4] = {0.0, 0.0, 0.0, 0.0};
#endif
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
#ifdef RD_LDA_COMMON_BETA
              /* Only the unsplit Jacobian follows the residual's stage.
               * The split pair uses one common opening-state distribution. */
              const double *average = (p == kfull) ? rd_stage_average : rd_beta_average;
              double velx_avg = average[0], vely_avg = average[1], h_avg = average[2], Cs_avg = average[3];
              double vel_dot_n = velx_avg * N_X[j] + vely_avg * N_Y[j];
              double lambda1 = vel_dot_n + Cs_avg - velvertex_dot_n;
              double lambda2 = vel_dot_n - Cs_avg - velvertex_dot_n;
              double lambda3 = vel_dot_n - velvertex_dot_n;
              Value1 = p == kplus ? dmax(0.0, lambda1) : (p == kminus ? dmin(0.0, lambda1) : lambda1);
              Value2 = p == kplus ? dmax(0.0, lambda2) : (p == kminus ? dmin(0.0, lambda2) : lambda2);
              Value3 = p == kplus ? dmax(0.0, lambda3) : (p == kminus ? dmin(0.0, lambda3) : lambda3);

#else
              if(p == 0)
                {  // Identify and select positive eigenvalues
                  Value1 = Lambda_plus[j][0];
                  Value2 = Lambda_plus[j][1];
                  Value3 = Lambda_plus[j][2];

                }
              else if(p == 1)
                {  // Identify and select negative eigenvalues
                  Value1 = Lambda_minus[j][0];
                  Value2 = Lambda_minus[j][1];
                  Value3 = Lambda_minus[j][2];

                }
              else
                {  // Select all eigenvalues
                  Value1 = Lambda[j][0];
                  Value2 = Lambda[j][1];
                  Value3 = Lambda[j][2];

                }

#endif /* RD_LDA_COMMON_BETA */
              const double velocity[2] = {velx_avg, vely_avg};
              const double normal[2] = {N_X[j], N_Y[j]};
              const double eigenvalues[3] = {Value1, Value2, Value3};
              double matrix[4][4];
              if(rd_euler_spectral_matrix(2, velocity, h_avg, Cs_avg, GAMMA, normal, Mag[j],
                                          eigenvalues, &matrix[0][0]) != 0)
                terminate_program("Invalid RD characteristic matrix input");
              for(int row = 0; row < 4; row++)
                for(int col = 0; col < 4; col++)
                  Kmatrix[row][col][j][p] = matrix[row][col];
            }
        }

#ifdef RD_ALE_CFL_DIAGNOSTIC
      if(rd_stage == 0)
        {
          double alpha_triangle = 0.0;
          for(j = 0; j < 3; j++)
            for(k = 0; k < 4; k++)
              alpha_triangle = dmax(alpha_triangle, 0.5 * Mag[j] * fabs(Lambda[j][k]));

          for(j = 0; j < 3; j++)
            {
              int index = rd_ale_local_point_index(&DP[DT[thistask_triangles[i]].p[j]]);
              set.ale_cfl_alpha_sum[index] += alpha_triangle;
            }
        }
#endif

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
#ifdef RD_DIFFERENCE_RESIDUAL
      double U_hat_mean[4];
      for(k = 0; k < 4; k++)
        U_hat_mean[k] = (U_hat[k][0] + U_hat[k][1] + U_hat[k][2]) / 3.0;
#endif

      for(k = 0; k < 4; k++)
        {
          Phi[k] = 0.0;
#if defined(RD_ALE_EQUALSTEP) && defined(RD_ALE_SPLIT_MESH_VELOCITY)
          /* Experimental: assemble the mesh-velocity part of the element
           * residual on the conservative nodal state rather than on the
           * parameter-vector linearisation.
           *
           * The endpoint ledger balances the geometric term
           * sum_i (m_new - m_old)_i U_i^n = dt * integral U_h div sigma_h
           * against the mesh-velocity part of the flux,
           * -dt * integral sigma_h . grad U_h. The two cancel through the
           * divergence theorem only if both use the same interpolant. The
           * physical flux must keep U_hat, because the conservative Roe
           * linearisation is what makes sum_j K_j U_hat_j equal to the exact
           * boundary integral of F; the mesh-velocity part must not. The
           * difference is corrected here, added to the element total so that
           * the sum_i phi_i = phi^T assertion still holds, and distributed
           * below with the lumped weight 1/3, which is the row sum of the N
           * mass matrix. It vanishes identically for a uniform state, so no
           * free-stream or DGCL property is disturbed. */
          rd_ale_mesh_velocity_correction[k] = 0.0;
          for(j = 0; j < 3; j++)
            {
              double sigma_dot_n = Velvertex_avg[0] * N_X[j] + Velvertex_avg[1] * N_Y[j];
              rd_ale_mesh_velocity_correction[k] -= 0.5 * Mag[j] * sigma_dot_n * (U_fluid[j][k] - U_hat[k][j]);
            }
          Phi[k] += rd_ale_mesh_velocity_correction[k];
#endif

          for(j = 0; j < 3; j++)
            {
#ifdef RD_DIFFERENCE_RESIDUAL
              /* sum_j K_j = 0, because sum_j n_j = 0 for a closed triangle and
               * the mesh-velocity shift is proportional to the same normals.
               * The element residual is therefore unchanged by subtracting any
               * common state, and subtracting the element mean is what makes
               * that identity hold in floating point as well as in exact
               * arithmetic.
               *
               * It matters under a Galilean boost. The entries of K grow like
               * the square of the bulk velocity through velx_c = velx_avg/c,
               * while the residual itself stays the size of the physical
               * imbalance, so the accumulation loses relative precision like
               * b^2. On a moving mesh that compounds with a near-singular S^-,
               * because sigma is approximately u makes the two advective
               * eigenvalues vanish. Assembling from differences removes the
               * common part before it is ever multiplied, so the cancellation
               * happens in one exact subtraction instead of in the sum. */
              Phi[k] += Kmatrix[k][0][j][kfull] * (U_hat[0][j] - U_hat_mean[0]) +
                        Kmatrix[k][1][j][kfull] * (U_hat[1][j] - U_hat_mean[1]) +
                        Kmatrix[k][2][j][kfull] * (U_hat[2][j] - U_hat_mean[2]) +
                        Kmatrix[k][3][j][kfull] * (U_hat[3][j] - U_hat_mean[3]);

              /* The round-off scale must stay the absolute one: the residual is
               * now accumulated from differences, but the solve and the
               * -K_i^+ z application downstream still carry the full magnitude
               * of K, so that is what bounds the error the assertion checks. */
              for(p = 0; p < 4; p++)
                phi_scale += fabs(Kmatrix[k][p][j][kfull]) * fabs(U_hat[p][j]);
#else
              Phi[k] += Kmatrix[k][0][j][kfull] * U_hat[0][j] + Kmatrix[k][1][j][kfull] * U_hat[1][j] +
                        Kmatrix[k][2][j][kfull] * U_hat[2][j] + Kmatrix[k][3][j][kfull] * U_hat[3][j];

              for(p = 0; p < 4; p++)
                phi_scale += fabs(Kmatrix[k][p][j][kfull]) * fabs(U_hat[p][j]);
#endif
            }

        }

#if defined(RD_ALE_CONTOUR_RESIDUAL) && !defined(RD_ELEMENT_COMOVING_FRAME)
      /* Laboratory-coordinate control for the element-frame experiment below.
       * Use exactly the same nodal conservative P1 contour residual, including
       * the mean mesh-advection flux, but retain the laboratory K^+/- matrices,
       * S^- solve and F1 right-hand side. Exact arithmetic makes this the
       * Galilean image of the co-moving construction; their numerical gap
       * therefore isolates coordinate conditioning from the residual choice. */
      phi_scale = 0.0;
      for(k = 0; k < 4; k++)
        Phi[k] = 0.0;
      for(j = 0; j < 3; j++)
        {
          double rho = U_fluid[j][0];
          double vx = U_fluid[j][1] / rho;
          double vy = U_fluid[j][2] / rho;
          double energy = U_fluid[j][3];
          double sigma_dot_n = Velvertex_avg[0] * N_X[j] + Velvertex_avg[1] * N_Y[j];
          double flux_x[4] = {U_fluid[j][1],
                              U_fluid[j][1] * vx + Pressure[j],
                              U_fluid[j][2] * vx,
                              (energy + Pressure[j]) * vx};
          double flux_y[4] = {U_fluid[j][2],
                              U_fluid[j][1] * vy,
                              U_fluid[j][2] * vy + Pressure[j],
                              (energy + Pressure[j]) * vy};
          for(k = 0; k < 4; k++)
            {
              double contribution =
                  0.5 * Mag[j] * (N_X[j] * flux_x[k] + N_Y[j] * flux_y[k] - sigma_dot_n * U_fluid[j][k]);
              Phi[k] += contribution;
              phi_scale += fabs(contribution);
            }
        }
#endif

#if defined(RD_ALE_CONTOUR_GAUSS) && !defined(RD_ELEMENT_COMOVING_FRAME)
      rd_contour_gauss_correction(U_fluid, N_X, N_Y, Mag, GAMMA, Phi, &phi_scale);
#endif

            /* S^- = sum_{j in T} K_j^-  (thesis notation, chapter 3) */
#ifdef RD_ALE_ENTROPY_DISSIPATION
      /* Laboratory frame: the mesh velocity is explicit, so the element
       * relative velocity is u - sigmabar_T directly. */
      rd_add_entropy_dissipation(velx_avg, vely_avg, h_avg, Cs_avg, velx_avg - Velvertex_avg[0],
                                 vely_avg - Velvertex_avg[1], Mag, kplus, kminus, Kmatrix);
#endif
#ifdef RD_ALE_SHEAR_EIGENVALUE_FLOOR
      rd_apply_shear_eigenvalue_floor(velx_avg, vely_avg, Cs_avg, velx_avg - Velvertex_avg[0],
                                      vely_avg - Velvertex_avg[1], N_X, N_Y, Mag, kplus, kminus, Kmatrix);
#endif

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
      /* The row stride must equal the LAPACK ldb/RD_UPWIND_NRHS. The three
       * columns carry the element residual, the N inflow right-hand side and
       * the LDA/F1 temporal target; unused columns remain zero in each scheme. */
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

#ifdef RD_ELEMENT_COMOVING_FRAME
      /* Change only the algebraic coordinates of this element solve.  The
       * frame is the element-average generator velocity, so the directly
       * assembled ALE operator has sigma'=0 and velocities u'=u-sigma_bar.
       * The spatial residual is reassembled in that frame, so neither the
       * laboratory K matrix nor its large common-state cancellation enters
       * the solve.  Temporal right-hand sides use the same Galilean map.  The
       * final nodal residuals are mapped back immediately before they enter
       * AREPO's laboratory-frame ledger. */
      {
        double Phi_lab_before_frame[4];
        memcpy(Phi_lab_before_frame, Phi, sizeof(Phi_lab_before_frame));

        double b0 = Velvertex_avg[0], b1 = Velvertex_avg[1], b2 = b0 * b0 + b1 * b1;
        double G_local[4][4] = {{1.0, 0.0, 0.0, 0.0},
                                {-b0, 1.0, 0.0, 0.0},
                                {-b1, 0.0, 1.0, 0.0},
                                {0.5 * b2, -b0, -b1, 1.0}};
        double Ginv_local[4][4] = {{1.0, 0.0, 0.0, 0.0},
                                   {b0, 1.0, 0.0, 0.0},
                                   {b1, 0.0, 1.0, 0.0},
                                   {0.5 * b2, b0, b1, 1.0}};
        memcpy(rd_frame_G, G_local, sizeof(rd_frame_G));
        memcpy(rd_frame_Ginv, Ginv_local, sizeof(rd_frame_Ginv));

        double velx_shift = velx_avg - b0, vely_shift = vely_avg - b1;
        double h_shift = h_avg - b0 * velx_avg - b1 * vely_avg + 0.5 * b2;
        double lambda_shift[3][4], K_shift[4][4][3][3];
        rd_build_characteristic_matrices(velx_shift, vely_shift, h_shift, Cs_avg, 0.0, 0.0,
                                         N_X, N_Y, Mag, lambda_shift, K_shift);
        memcpy(Kmatrix, K_shift, sizeof(Kmatrix));

#ifdef RD_ALE_ENTROPY_DISSIPATION
        /* Element frame: sigma' has zero element mean by construction, so the
         * relative velocity is the shifted velocity itself. */
        rd_add_entropy_dissipation(velx_shift, vely_shift, h_shift, Cs_avg, velx_shift, vely_shift, Mag,
                                   kplus, kminus, Kmatrix);
#endif
#ifdef RD_ALE_SHEAR_EIGENVALUE_FLOOR
        rd_apply_shear_eigenvalue_floor(velx_shift, vely_shift, Cs_avg, velx_shift, vely_shift,
                                        N_X, N_Y, Mag, kplus, kminus, Kmatrix);
#endif

        for(k = 0; k < 4; k++)
          for(p = 0; p < 4; p++)
            {
              Sminus[k][p] = 0.0;
              for(j = 0; j < 3; j++)
                Sminus[k][p] += Kmatrix[k][p][j][kminus];
            }

        double U_hat_shift[4][3], U_fluid_shift[4][3];
        for(j = 0; j < 3; j++)
          for(k = 0; k < 4; k++)
            {
              U_hat_shift[k][j] = 0.0;
              U_fluid_shift[k][j] = 0.0;
              for(p = 0; p < 4; p++)
                {
                  U_hat_shift[k][j] += rd_frame_G[k][p] * U_hat[p][j];
                  U_fluid_shift[k][j] += rd_frame_G[k][p] * U_fluid[j][p];
                }
            }

        /* Rebase the working Roe state, in the same way this block already
         * rebases Kmatrix and rhs.  N reads U_hat downstream of this block,
         * outside the scope of U_hat_shift, to form its inflow bracket
         * U_hat - Y_in.  Y_in is solved from the shifted rhs and is therefore
         * already in the element frame, so leaving U_hat in laboratory
         * variables would subtract a primed inflow state from an unprimed
         * nodal state and give a quantity that is neither frame's N flux.
         * That mixture, not any missing derivation, is what the N guard on
         * RD_ELEMENT_COMOVING_FRAME used to protect against.  LDA does not read
         * U_hat after this point, so the rebase changes no LDA result. */
        memcpy(U_hat, U_hat_shift, sizeof(U_hat));

        /* The direct co-moving Roe residual K'_j Uhat'_j is only the
         * transform of the Roe-linearised ALE term.  The production ALE
         * residual deliberately advects the original conservative P1 state
         * with the mesh, so the U-Uhat split correction must cross the frame
         * boundary as well:
         *
         *     C'_T = G(b_T) C_T
         *          = -1/2 sum_j |n_j| (sigma_bar.n_j)
         *                    G(b_T) (U_j-Uhat_j).
         *
         * Although sigma'=sigma_bar-b_T=0 in the characteristic operator,
         * this term does not vanish: it repairs the non-covariance introduced
         * by using the Roe parameter-vector interpolant Uhat for the physical
         * flux while the geometric transport uses the original nodal U. */
#if defined(RD_ALE_EQUALSTEP) && defined(RD_ALE_SPLIT_MESH_VELOCITY)
        double correction_expected[4] = {0.0, 0.0, 0.0, 0.0};
        double correction_covariance_scale = 0.0;

        for(j = 0; j < 3; j++)
          {
            double sigma_dot_n = Velvertex_avg[0] * N_X[j] + Velvertex_avg[1] * N_Y[j];
            for(k = 0; k < 4; k++)
              {
                double delta_shift = U_fluid_shift[k][j] - U_hat_shift[k][j];
                rd_frame_split_correction[k] -= 0.5 * Mag[j] * sigma_dot_n * delta_shift;
                correction_covariance_scale += 0.5 * Mag[j] * fabs(sigma_dot_n) * fabs(delta_shift);
              }
          }

        for(k = 0; k < 4; k++)
          for(p = 0; p < 4; p++)
            correction_expected[k] += rd_frame_G[k][p] * rd_ale_mesh_velocity_correction[p];

        double correction_covariance_defect = 0.0;
        for(k = 0; k < 4; k++)
          correction_covariance_defect = dmax(correction_covariance_defect,
                                               fabs(rd_frame_split_correction[k] - correction_expected[k]));
        RD_stat_max_comoving_correction_covariance =
            dmax(RD_stat_max_comoving_correction_covariance, correction_covariance_defect);

#ifdef RD_DEBUG_ASSERTS
        double correction_covariance_tolerance =
            RD_CONSERVATION_ROUNDOFF_FACTOR * DBL_EPSILON * dmax(1.0, correction_covariance_scale);
        if(correction_covariance_defect > correction_covariance_tolerance)
          {
            printf("RD-COMOVING-CORRECTION task=%d triangle=%d defect=%.17g tol=%.17g scale=%.17g\n",
                   ThisTask, thistask_triangles[i], correction_covariance_defect,
                   correction_covariance_tolerance, correction_covariance_scale);
            terminate_program("co-moving U-Uhat correction failed Galilean covariance gate");
          }
#endif
#endif

#ifdef RD_DIFFERENCE_RESIDUAL
        double U_hat_shift_mean[4];
        for(k = 0; k < 4; k++)
          U_hat_shift_mean[k] = (U_hat_shift[k][0] + U_hat_shift[k][1] + U_hat_shift[k][2]) / 3.0;
#endif

        phi_scale = 0.0;
#ifdef RD_ALE_CONTOUR_RESIDUAL
        /* Galilean-covariant total residual based on the same conservative P1
         * state as the moving median-dual ledger.  Interpolate the physical
         * Euler flux from its nodal values and integrate its divergence over
         * the triangle.  In the b_T=sigma_bar frame the mean mesh advection is
         * zero, so no U-Uhat correction is present.  The Roe matrices remain
         * the multidimensional upwind distribution operator; they no longer
         * define the element total. */
        for(k = 0; k < 4; k++)
          Phi[k] = 0.0;
        for(j = 0; j < 3; j++)
          {
            double rho = U_fluid_shift[0][j];
            double vx = U_fluid_shift[1][j] / rho;
            double vy = U_fluid_shift[2][j] / rho;
            double energy = U_fluid_shift[3][j];
            double flux_x[4] = {U_fluid_shift[1][j],
                                U_fluid_shift[1][j] * vx + Pressure[j],
                                U_fluid_shift[2][j] * vx,
                                (energy + Pressure[j]) * vx};
            double flux_y[4] = {U_fluid_shift[2][j],
                                U_fluid_shift[1][j] * vy,
                                U_fluid_shift[2][j] * vy + Pressure[j],
                                (energy + Pressure[j]) * vy};
            for(k = 0; k < 4; k++)
              {
                double contribution = 0.5 * Mag[j] * (N_X[j] * flux_x[k] + N_Y[j] * flux_y[k]);
                Phi[k] += contribution;
                phi_scale += fabs(contribution);
              }
          }
#ifdef RD_ALE_CONTOUR_GAUSS
        double gauss_u_shift[3][4];
        for(j = 0; j < 3; j++)
          for(k = 0; k < 4; k++) gauss_u_shift[j][k] = U_fluid_shift[k][j];
        rd_contour_gauss_correction(gauss_u_shift, N_X, N_Y, Mag, GAMMA, Phi, &phi_scale);
#endif
#else
        for(k = 0; k < 4; k++)
          {
            Phi[k] = 0.0;
#if defined(RD_ALE_EQUALSTEP) && defined(RD_ALE_SPLIT_MESH_VELOCITY)
            Phi[k] = rd_frame_split_correction[k];
            phi_scale += fabs(rd_frame_split_correction[k]);
#endif
            for(j = 0; j < 3; j++)
              for(p = 0; p < 4; p++)
                {
#ifdef RD_DIFFERENCE_RESIDUAL
                  Phi[k] += Kmatrix[k][p][j][kfull] * (U_hat_shift[p][j] - U_hat_shift_mean[p]);
#else
                  Phi[k] += Kmatrix[k][p][j][kfull] * U_hat_shift[p][j];
#endif
                  phi_scale += fabs(Kmatrix[k][p][j][kfull]) * fabs(U_hat_shift[p][j]);
                }
          }

        /* This second gate includes the characteristic operator as well as
         * the split correction.  Unlike the correction-only identity above,
         * its laboratory reference has already suffered the large-boost
         * cancellation that motivated the co-moving construction, so it is
         * diagnostic rather than a fatal assertion. */
        double Phi_frame_expected[4] = {0.0, 0.0, 0.0, 0.0};
        double phi_covariance_defect = 0.0, phi_covariance_scale = 0.0;
        for(k = 0; k < 4; k++)
          {
            for(p = 0; p < 4; p++)
              Phi_frame_expected[k] += rd_frame_G[k][p] * Phi_lab_before_frame[p];
            phi_covariance_defect = dmax(phi_covariance_defect, fabs(Phi[k] - Phi_frame_expected[k]));
            phi_covariance_scale = dmax(phi_covariance_scale, dmax(fabs(Phi[k]), fabs(Phi_frame_expected[k])));
          }
        RD_stat_max_comoving_phi_covariance = dmax(RD_stat_max_comoving_phi_covariance, phi_covariance_defect);
        RD_stat_max_comoving_phi_covariance_relative =
            dmax(RD_stat_max_comoving_phi_covariance_relative,
                 phi_covariance_defect / dmax(DBL_MIN, phi_covariance_scale));
#endif

        double rhs_shift[4][RD_UPWIND_NRHS];
        for(k = 0; k < 4; k++)
          for(int column = 0; column < RD_UPWIND_NRHS; column++)
            {
              rhs_shift[k][column] = 0.0;
              for(p = 0; p < 4; p++)
                rhs_shift[k][column] += rd_frame_G[k][p] * rhs[p][column];
            }
        memcpy(rhs, rhs_shift, sizeof(rhs));
        for(k = 0; k < 4; k++)
          {
            rhs[k][0] = Phi[k];
            rhs[k][1] = 0.0;
            for(j = 0; j < 3; j++)
              for(p = 0; p < 4; p++)
                rhs[k][1] += Kmatrix[k][p][j][kminus] * U_hat_shift[p][j];
          }

        if(rd_stage == 1)
          for(j = 0; j < 3; j++)
            {
              double shifted[4];
              for(k = 0; k < 4; k++)
                {
                  shifted[k] = 0.0;
                  for(p = 0; p < 4; p++)
                    shifted[k] += rd_frame_G[k][p] * dU_vertex[j][p];
                }
              memcpy(dU_vertex[j], shifted, sizeof(shifted));
            }

#ifdef RD_DEBUG_ASSERTS
        rd_assert_K_sum_vanishes(Kmatrix, kfull, thistask_triangles[i]);
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
#ifdef RD_LDA_COMMON_BETA
      if(solve_rank < 4)
        {
          double projected[4], share[4];
          rd_common_beta_unresolved(Sminus, X_lda, Phi, projected, share);
          /* Independently check the raw range contribution before adding the
           * defined complement; a broken K split must still fail A2. */
          rd_check_conservation(Flux_RD, projected, LDA_roundoff_scale + phi_scale,
                                thistask_triangles[i], "LDA-common-range");
          for(k = 0; k < 4; k++)
            {
              for(j = 0; j < 3; j++)
                Flux_RD[k][j] += share[k];
              LDA_roundoff_scale += 3.0 * fabs(share[k]);
            }
        }
#endif
#ifdef RD_ALE_CONDITION_DIAGNOSTIC
      rd_diagnose_lda_condition(Sminus, kplus, Phi, X_lda, Flux_RD, Velvertex_avg, velx_avg, vely_avg, h_avg,
                                Cs_avg, N_X, N_Y, Mag, LDA_roundoff_scale + phi_scale, thistask_triangles[i]);
#endif
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
            }

          N_roundoff_scale = dmax(N_roundoff_scale, equation_scale);
        }

#if defined(RD_ALE_EQUALSTEP) && defined(RD_ALE_SPLIT_MESH_VELOCITY) && !defined(RD_ALE_CONTOUR_RESIDUAL)
      /* Outside the component loop, and with its own indices: reusing k or j
       * here would terminate the enclosing loop early.
       *
       * Suppressed under the contour residual: there the element total is
       * rebuilt from nodal conservative states, so the U-Uhat correction has
       * already been discarded from Phi and adding it to the nodal fluxes alone
       * would break sum_i phi_i = Phi. */
      for(int corr_k = 0; corr_k < 4; corr_k++)
        for(int corr_j = 0; corr_j < 3; corr_j++)
#ifdef B_SCHEME
#ifdef RD_ELEMENT_COMOVING_FRAME
          Flux_N[corr_k][corr_j] += rd_frame_split_correction[corr_k] / 3.0;
#else
          Flux_N[corr_k][corr_j] += rd_ale_mesh_velocity_correction[corr_k] / 3.0;
#endif
#else
#ifdef RD_ELEMENT_COMOVING_FRAME
          Flux_RD[corr_k][corr_j] += rd_frame_split_correction[corr_k] / 3.0;
#else
          Flux_RD[corr_k][corr_j] += rd_ale_mesh_velocity_correction[corr_k] / 3.0;
#endif
#endif
#endif

#if (defined(N_SCHEME) || defined(B_SCHEME)) && defined(RD_ALE_CONTOUR_RESIDUAL)
      /* Reconcile the N distribution with the contour element total.
       *
       * N does not distribute Phi. Its nodal flux is K_i^+(U_i - U_in), and the
       * identity sum_i phi_i^N = sum_j K_j Uhat_j holds by construction of the
       * inflow state. The contour residual replaces the element total by the
       * divergence of the interpolated physical flux, which is a different
       * quantity, so that identity no longer closes and assertion A2 would fire
       * on the first step.
       *
       * The difference is distributed with the row sum of N's mass matrix,
       * which for the lumped mass is 1/3 at each vertex. This is the same
       * construction used for the split correction above and for the geometric
       * residual of the development log. It is conservative by construction,
       * leaves the upwind character of K_i^+ untouched, and vanishes
       * identically when the two totals agree, so it is inert wherever the
       * contour and Roe totals coincide.
       *
       * This is a scheme design choice, not an algebraic identity: it fixes how
       * a first-order monotone distribution is reconciled with a total it did
       * not generate, and its accuracy and positivity are what the campaign in
       * RD_ALE_FORM_SELECTION.md measures. */
      for(int corr_k = 0; corr_k < 4; corr_k++)
        {
#ifdef B_SCHEME
          double distributed = Flux_N[corr_k][0] + Flux_N[corr_k][1] + Flux_N[corr_k][2];
#else
          double distributed = Flux_RD[corr_k][0] + Flux_RD[corr_k][1] + Flux_RD[corr_k][2];
#endif
          double residue     = (Phi[corr_k] - distributed) / 3.0;

          for(int corr_j = 0; corr_j < 3; corr_j++)
#ifdef B_SCHEME
            Flux_N[corr_k][corr_j] += residue;
#else
            Flux_RD[corr_k][corr_j] += residue;
#endif
        }
#endif

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
        }

#ifdef RD_B_SCALAR_THETA
      /* A component-wise blend can combine the density residual of one
       * branch with momentum and energy residuals of another, so it has no
       * invariant-domain interpretation even when the N update is admissible.
       * Use the most dissipative component as one element-local scalar.  This
       * preserves the full conservative-state coupling and makes every
       * component the same convex blend of the N and LDA distributions. */
      double theta_scalar = 0.0;
      for(k = 0; k < 4; k++)
        theta_scalar = dmax(theta_scalar, Theta_E[k]);
      for(k = 0; k < 4; k++)
        Theta_E[k] = theta_scalar;
#endif

#ifdef RD_ALE_APOSTERIORI_FALLBACK
      /* The classical B sensor is intentionally bypassed: this experiment is
       * pure LDA except on stars rejected by the complete candidate update. */
      for(k = 0; k < 4; k++)
        Theta_E[k] = fallback_element[i] ? 1.0 : 0.0;
#endif

      for(k = 0; k < 4; k++)
        {
#ifdef RD_DIAG_THETA
          rd_record_theta(0, Theta_E[k]);
#endif

          double equation_scale = fabs(Phi[k]);
          for(j = 0; j < 3; j++)
            {
              equation_scale +=
                  fabs(Theta_E[k] * Flux_N[k][j]) + fabs((1.0 - Theta_E[k]) * Flux_LDA[k][j]);
              Flux_RD[k][j] = Theta_E[k] * Flux_N[k][j] + (1.0 - Theta_E[k]) * Flux_LDA[k][j];
            }

          B_roundoff_scale = dmax(B_roundoff_scale, equation_scale);
        }

      B_roundoff_scale = dmax(B_roundoff_scale, dmax(LDA_roundoff_scale, N_roundoff_scale));
      rd_check_conservation(Flux_RD, Phi, B_roundoff_scale + phi_scale, thistask_triangles[i], "B");

#ifdef RD_ALE_INTERVAL_HIERARCHY
      if(rd_stage == RD_RK_STAGE_PREDICTOR)
        {
          memcpy(RdIntervalB[i].n, Flux_N, sizeof(RdIntervalB[i].n));
          memcpy(RdIntervalB[i].lda, Flux_LDA, sizeof(RdIntervalB[i].lda));
          memcpy(RdIntervalB[i].applied, Flux_RD, sizeof(RdIntervalB[i].applied));
          memcpy(RdIntervalB[i].phi, Phi, sizeof(RdIntervalB[i].phi));
        }
      else
        {
          /* Interval total-theta B (Arpaia & Ricchiuto 2015, eqs. 43-45) for the
           * two-call hierarchy.  The predictor call already applied
           * -(h/2) b^0 with the spatial stage-0 blend b^0.  The complete
           * interval update is
           *   -(h) { T + [theta (N^0+N^1) + (1-theta)(L^0+L^1)]/2 },
           *   T = theta T_lumped + (1-theta) T_F1,
           * and the lumped T is the base the deposits already contain, so the
           * corrector (multiplier -h/2) applies
           *   theta (N^0+N^1) + (1-theta)(L^0+L^1) - b^0 + 2 (1-theta)(T_F1 - T_lumped).
           * Its element total is Phi(U*): conservative for every theta. */
          /* After the solve rhs[.][2] holds z (S^- z = target), not the target. */
          double T_lumped[4][3], T_f1[4][3], T_target[4], theta[4], scale = 0.0;
          for(k = 0; k < 4; k++)
            {
              T_target[k] = 0.0;
              for(j = 0; j < 3; j++)
                {
                  T_lumped[k][j] = (tri_normals_list[i].area / 3.0) * dU_vertex[j][k] / full_triangle_dt;
                  T_target[k] += T_lumped[k][j];
                }
            }
          if(solve_rank == 4)
            {
              for(k = 0; k < 4; k++)
                for(j = 0; j < 3; j++)
                  {
                    T_f1[k][j] = 0.0;
                    for(p = 0; p < 4; p++)
                      {
                        T_f1[k][j] -= Kmatrix[k][p][j][kplus] * rhs[p][2];
                        scale += fabs(Kmatrix[k][p][j][kplus]) * fabs(rhs[p][2]);
                      }
                  }
            }
          else
            {
              RD_stat_f1_lumped++;
              memcpy(T_f1, T_lumped, sizeof(T_f1));
            }
          for(k = 0; k < 4; k++)
            {
#ifdef RD_B_FROZEN_THETA
              double theta_num = T_target[k] + RdIntervalB[i].phi[k], sum_n = 0.0;
              for(j = 0; j < 3; j++)
                sum_n += fabs(T_lumped[k][j] + RdIntervalB[i].n[k][j]);
#else
              double theta_num = T_target[k] + 0.5 * (RdIntervalB[i].phi[k] + Phi[k]), sum_n = 0.0;
              for(j = 0; j < 3; j++)
                sum_n += fabs(T_lumped[k][j] + 0.5 * (RdIntervalB[i].n[k][j] + Flux_N[k][j]));
#endif
              theta[k] = sum_n == 0.0 ? 0.0 : dmin(1.0, fabs(theta_num) / sum_n);
            }
#ifdef RD_B_SCALAR_THETA
          double theta_max = 0.0;
          for(k = 0; k < 4; k++)
            theta_max = dmax(theta_max, theta[k]);
          for(k = 0; k < 4; k++)
            theta[k] = theta_max;
#endif
          for(k = 0; k < 4; k++)
            for(j = 0; j < 3; j++)
              {
#ifdef RD_DIAG_THETA
                if(j == 0)
                  rd_record_theta(1, theta[k]);
#endif
                Flux_RD[k][j] = theta[k] * (RdIntervalB[i].n[k][j] + Flux_N[k][j]) +
                                (1.0 - theta[k]) * (RdIntervalB[i].lda[k][j] + Flux_LDA[k][j]) - RdIntervalB[i].applied[k][j] +
                                2.0 * (1.0 - theta[k]) * (T_f1[k][j] - T_lumped[k][j]);
                scale += fabs(RdIntervalB[i].n[k][j]) + fabs(Flux_N[k][j]) + fabs(RdIntervalB[i].lda[k][j]) +
                         fabs(Flux_LDA[k][j]) + fabs(RdIntervalB[i].applied[k][j]) + 2.0 * fabs(T_lumped[k][j]);
              }
          rd_check_conservation(Flux_RD, Phi, scale + B_roundoff_scale + phi_scale, thistask_triangles[i], "B-interval");
        }
#endif
#ifdef RD_RK2_EQUALSTEP
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
#endif  // RD_RUSANOV_LOW_ORDER: bypass Roe matrices and distribute trapezoidal flux

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

#if defined(RD_RK2_EQUALSTEP) && !defined(RD_RK2_RATE_CONSISTENT_HEUN)
      if(rd_stage == 1)
        {
          /* Corrector: replace the stage-1 spatial distribution by the total
           * nodal residual. LDA and N already carry the old spatial half through
           * the local +dU/2 predictor increment; B stores and adds its separate
           * stage-0 N/LDA distributions explicitly. */
          double T_time[4][3];
          double T_target[4];
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

            }
          else
            {
              /* Genuinely rank-deficient element (DGELSD resolved fewer than
               * four directions): beta_i is undefined there. The F1 temporal
               * target is an arbitrary vector, unprotected by Lemma 1, so
               * S^- z = T_target need not even be consistent, and no
               * bare generalized inverse restores sum_i beta_i = I on a
               * singular S^-. Retain the conservative lumped temporal policy
               * and count the event, including under common-beta spatial
               * range completion. Other conservative extensions are possible.
               *
               * Rank, not "the SVD path was taken", is the criterion. Consistency
               * of S^- z = T_target is what is actually required and is stricter
               * still; rank < 4 approximates it from the safe side. */
              RD_stat_f1_lumped++;

              for(k = 0; k < 4; k++)
                for(j = 0; j < 3; j++)
                  T_time[k][j] = (tri_normals_list[i].area / 3.0) * dU_vertex[j][k] / triangle_dt;
            }
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
          double Theta_total[4];
#ifdef RD_DIAG_THETA_MAP
          double theta_map[4] = {0.0, 0.0, 0.0, 0.0};
          double nlda_gap_map[4] = {0.0, 0.0, 0.0, 0.0};
#endif

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
              /* Two independent choices in the indicator, both of which leave
               * conservation untouched because it holds for any Theta.
               *
               * RD_B_SPATIAL_THETA: whether the temporal term enters at all.
               * Absent, the whole residual is used, which is eq. 44-45 of
               * Arpaia & Ricchiuto (2015) and is what a time-dependent problem
               * requires -- the spatial residual alone is a *steady-state*
               * smoothness detector and measures 0.46 to 0.52 in a perfectly
               * smooth vortex. Present, the steady form of their eq. 42 is
               * used instead, retained as the control that establishes this.
               *
               * RD_B_FROZEN_THETA: which quadrature of the interval residual.
               * The same paper notes that eqs. 44-45 are "somewhat unclear
               * since the meaning of d u_h / d t needs to be made more
               * precise", and never fixes it. Frozen is the left-endpoint rule
               * and uses stage-0 data only; unfrozen is the trapezoid and is
               * the higher-order estimator but reads the predictor state,
               * which near a discontinuity is the oscillatory intermediate.
               * Frozen is additionally the only form computable at the opening
               * call of the two-call hierarchy. */
#ifdef RD_B_SPATIAL_THETA
              double theta_num = 0.0;
#else
              double theta_num = T_target[k];
#endif
#ifdef RD_B_FROZEN_THETA
              theta_num += rd_b_phi_stage0[i][k];
#else
              theta_num += 0.5 * (rd_b_phi_stage0[i][k] + Phi[k]);
#endif

              double sum_n_tot = 0.0;

              for(j = 0; j < 3; j++)
                {
#ifdef RD_B_SPATIAL_THETA
                  double contrib = 0.0;
#else
                  double contrib = T_lumped[k][j];
#endif
#ifdef RD_B_FROZEN_THETA
                  contrib += rd_b_flux_n_stage0[i][k][j];
#else
                  contrib += 0.5 * (rd_b_flux_n_stage0[i][k][j] + Flux_N[k][j]);
#endif
                  sum_n_tot += fabs(contrib);
                }

              double total_k = theta_num;

              Theta_total[k] = (sum_n_tot == 0.0) ? 0.0 : dmin(1.0, fabs(total_k) / sum_n_tot);
            }

#ifdef RD_B_SCALAR_THETA
          double theta_total_scalar = 0.0;
          for(k = 0; k < 4; k++)
            theta_total_scalar = dmax(theta_total_scalar, Theta_total[k]);
          for(k = 0; k < 4; k++)
            Theta_total[k] = theta_total_scalar;
#endif

#ifdef RD_ALE_APOSTERIORI_FALLBACK
          for(k = 0; k < 4; k++)
            Theta_total[k] = fallback_element[i] ? 1.0 : 0.0;
#endif

          for(k = 0; k < 4; k++)
            {
              double theta = Theta_total[k];
#ifdef RD_DIAG_THETA
              rd_record_theta(1, theta);
#endif
#ifdef RD_DIAG_THETA_MAP
              theta_map[k] = theta;
#endif

              for(j = 0; j < 3; j++)
                {
#ifdef RD_DIAG_THETA_MAP
                  double n_branch = T_lumped[k][j] +
                                    0.5 * (rd_b_flux_n_stage0[i][k][j] + Flux_N[k][j]);
                  double lda_branch = T_f1[k][j] +
                                      0.5 * (rd_b_flux_lda_stage0[i][k][j] + Flux_LDA[k][j]);
                  nlda_gap_map[k] += fabs(n_branch - lda_branch);
#endif
                  T_time[k][j]  = theta * T_lumped[k][j] + (1.0 - theta) * T_f1[k][j];
                  Flux_RD[k][j] =
                      theta * (rd_b_flux_n_stage0[i][k][j] + Flux_N[k][j]) +
                      (1.0 - theta) * (rd_b_flux_lda_stage0[i][k][j] + Flux_LDA[k][j]);

                  rk2_scale += fabs(T_time[k][j]) + 0.5 * fabs(Flux_RD[k][j]);
                }
            }
#ifdef RD_DIAG_THETA_MAP
          if(rd_theta_map_fp != NULL)
            {
              int diag_pt[3];
              double cx = 0.0, cy = 0.0;
              for(j = 0; j < 3; j++)
                {
                  diag_pt[j] = DT[thistask_triangles[i]].p[j];
                  cx += DP[diag_pt[j]].x / 3.0;
                  cy += DP[diag_pt[j]].y / 3.0;
                }
              cx = fmod(cx, boxSize_X);
              cy = fmod(cy, boxSize_Y);
              if(cx < 0.0)
                cx += boxSize_X;
              if(cy < 0.0)
                cy += boxSize_Y;

              fprintf(rd_theta_map_fp,
                      "%d,%d,%llu,%llu,%llu,%.17g,%.17g,%.17g,"
                      "%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g\n",
                      i, thistask_triangles[i],
                      (unsigned long long)DP[diag_pt[0]].ID,
                      (unsigned long long)DP[diag_pt[1]].ID,
                      (unsigned long long)DP[diag_pt[2]].ID,
                      cx, cy, tri_normals_list[i].area,
                      theta_map[0], theta_map[1], theta_map[2], theta_map[3],
                      triangle_dt * nlda_gap_map[0], triangle_dt * nlda_gap_map[3],
                      triangle_dt * theta_map[0] * nlda_gap_map[0],
                      triangle_dt * theta_map[3] * nlda_gap_map[3]);
            }
#endif
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
#ifdef B_SCHEME
              total_target[k] += 0.5 * rd_b_phi_stage0[i][k];
#endif

              rk2_scale += fabs(total_target[k]);
              for(j = 0; j < 3; j++)
                {
                  rk2_scale += fabs(T_time[k][j]);
                  Flux_RD[k][j] = T_time[k][j] + 0.5 * Flux_RD[k][j];
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
#endif /* RD_RK2_EQUALSTEP && !RD_RK2_RATE_CONSISTENT_HEUN */

#if defined(RD_HIERARCHICAL_TIMESTEPS) && defined(LDA_SCHEME)
      if(rd_stage == RD_RK_STAGE_CORRECTOR)
        {
          /* Frozen-dU multirate F1 experiment.
           *
           * The opening call has already applied -h_T phi_i(U^n)/2 and
           * assembled the full vertex predictor dU.  To reproduce the
           * concentrated LDA+F1 corrector when all bins are equal,
           * the closing ledger contribution is
           *
           *   |T| dU_i/3 - h_T beta_i [ |T| sum_j dU_j/(3 h_T) ]
           *                    - h_T phi_i(U*)/2.
           *
           * beta is the predicted-state matrix by default, or the opening
           * matrix with RD_LDA_COMMON_OPENING_BETA. Since the common ledger
           * multiplier below is -h_T/2, add
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

#if defined(RD_ALE_HIERARCHICAL) && (defined(N_SCHEME) || defined(RD_ALE_INTERVAL_HIERARCHY))
      if(rd_stage == RD_RK_STAGE_CORRECTOR)
        {
          /* For LDA (interval mode) this mass-variant term is lumped and is
           * added on top of the F1 swap of the M_T temporal term above.
           * The concentrated two-half-call hierarchy has no explicit
           * total-residual temporal sweep. Let D_T/3 contribute to the common
           * two-stage nodal divisor and M_T/3 be the lumped temporal mass.
           * The equal-step algebra leaves
           *
           *     Delta Q_i^mass = (D_T - M_T) dU_i / 3.
           *
           * Campoli uses (D_T,M_T)=(A_new,(A_old+A_new)/2); Arpaia uses
           * (A_mid+(A_new-A_old)/2,A_mid). */
          double area_gap =
              (set.ale_hier_divisor_element_area[i] - tri_normals_list[i].area) / 3.0;

          for(k = 0; k < 4; k++)
            for(j = 0; j < 3; j++)
              {
                double q_correction = area_gap * dU_vertex[j][k];
                Flux_RD[k][j] -= q_correction / triangle_dt;
              }
        }
#endif

#ifdef RD_ELEMENT_COMOVING_FRAME
      for(j = 0; j < 3; j++)
        {
          double lab_flux[4];
          for(k = 0; k < 4; k++)
            {
              lab_flux[k] = 0.0;
              for(p = 0; p < 4; p++)
                lab_flux[k] += rd_frame_Ginv[k][p] * Flux_RD[p][j];
            }
          for(k = 0; k < 4; k++)
            Flux_RD[k][j] = lab_flux[k];
        }
#endif

#ifdef RD_DIAG_TRACE_ELEMENT
      if(rd_trace)
        printf("RD-TRACE-OUT stage=%d flux00=%.17g flux30=%.17g flux01=%.17g flux31=%.17g\n", rd_stage, Flux_RD[0][0],
               Flux_RD[3][0], Flux_RD[0][1], Flux_RD[3][1]);
#endif

      /*use residuals to update fluid state of local points or export to other tasks*/

#ifdef RD_LDA_RUSANOV_BLEND
      {
        double normals[3][2], low[4][3];
        for(int v = 0; v < 3; v++)
          for(int d = 0; d < 2; d++)
            normals[v][d] = tri_normals_list[i].mag[v] * tri_normals_list[i].normal[v][d];
#ifdef RD_BLEND_LOW_HLLC
        double coeff[3], low_phi[4], low_scale = 0, nx[3], ny[3], mag[3];
        double alpha = rd_hllc_residual(U_fluid, normals, Velvertex_avg, GAMMA, low_phi, low, coeff, &low_scale);
        if(!(alpha > 0)) terminate_program("LDA/HLLC low-order stage found an inadmissible or star state");
        for(int v = 0; v < 3; v++)
          {
            nx[v] = tri_normals_list[i].normal[v][0];
            ny[v] = tri_normals_list[i].normal[v][1];
            mag[v] = tri_normals_list[i].mag[v];
          }
        rd_hllc_gauss_edge_split(U_fluid, nx, ny, mag, GAMMA, low, low_phi, &low_scale);
        /* Both endpoints must now share LDA's Gauss3 element total. */
        for(int k = 0; k < 4; k++)
          if(fabs(low_phi[k] - Phi[k]) > 1e-10 * (low_scale + phi_scale + DBL_MIN))
            terminate_program("LDA/HLLC element totals differ: k=%d low=%.17g LDA=%.17g", k, low_phi[k], Phi[k]);
#else
        double alpha = rd_lr_low(U_fluid, normals, GAMMA, Phi, low);
        if(!(alpha > 0)) terminate_program("LDA/Rusanov common-total inflow is inadmissible");
#endif
#ifdef RD_LDA_RUSANOV_B_SENSOR
        double sensor_low[4][3], theta[4];
        if(rd_stage == 0)
          {
            memcpy(rd_lr_old[i].low, low, sizeof(low));
            memcpy(rd_lr_old[i].high, Flux_RD, sizeof(low));
            rd_lr_old[i].dt = triangle_dt;
          }
        else if(triangle_dt != rd_lr_old[i].dt)
          terminate_program("RD B sensor requires identical predictor/corrector intervals");
        for(int k = 0; k < 4; k++)
          for(int v = 0; v < 3; v++)
            sensor_low[k][v] = rd_stage == 0 ? low[k][v] :
                tri_normals_list[i].area/3 * dU_vertex[v][k]/triangle_dt +
                .5*(rd_lr_old[i].low[k][v]+low[k][v]);
        rd_lr_b_sensor(sensor_low, RD_LDA_RUSANOV_B_SENSOR, theta);
        for(int k = 0; k < 4; k++)
          {
            rd_lr_theta_sum[k] += theta[k];
            rd_lr_theta_max = dmax(rd_lr_theta_max, theta[k]);
          }
        rd_lr_sensor_elements++;
#endif
        for(int v = 0; v < 3; v++)
          {
            int index = rd_rusanov_local_index(&DP[DT[thistask_triangles[i]].p[v]]);
#ifdef RD_BLEND_LOW_HLLC
            rd_lr_cfl[index] += triangle_dt * coeff[v] / SphP[index].DualArea;
            rd_lr_mass[index] += tri_normals_list[i].area / 3.0;
#else
            rd_lr_cfl[index] += triangle_dt * alpha / SphP[index].DualArea;
#endif
            rd_lr_degree[index]++;
            for(int k = 0; k < 4; k++)
              {
                if(rd_stage == 1)
                  low[k][v] = tri_normals_list[i].area/3 * dU_vertex[v][k]/triangle_dt + .5*low[k][v];
                rd_lr_correction[i][k][v] = -triangle_dt * (Flux_RD[k][v]-low[k][v]);
#ifdef RD_LDA_RUSANOV_B_SENSOR
                if(rd_stage == 0)
                  rd_lr_correction[i][k][v] *= 1-theta[k];
                else
                  rd_lr_correction[i][k][v] = -triangle_dt * rd_lr_b_difference(
                      Flux_RD[k][v], low[k][v], rd_lr_old[i].high[k][v], rd_lr_old[i].low[k][v],
                      rd_lr_old[i].accepted[k][v], theta[k]);
#endif
                Flux_RD[k][v] = low[k][v];
              }
          }
        /* Remove only the roundoff-level element closure defect. */
        for(int k = 0; k < 4; k++)
          {
            double closure = (rd_lr_correction[i][k][0]+rd_lr_correction[i][k][1]+rd_lr_correction[i][k][2])/3;
            for(int v = 0; v < 3; v++) rd_lr_correction[i][k][v] -= closure;
            rd_lr_correction[i][k][2] = -rd_lr_correction[i][k][0]-rd_lr_correction[i][k][1];
          }
      }
#endif

#else /* static tetra distributions; common stages and particle update below */
      double Phi[5], nodal[4][5], Flux_RD[5][4];
      struct rd_n_diagnostics diagnostic;
#ifdef RD_ALWAYS_PSEUDOINVERSE
      const int always_svd = 1;
#else
      const int always_svd = 0;
#endif
#ifdef LDA_SCHEME
      double temporal[5] = {0}, f1[4][5];
      if(rd_stage == 1)
        for(k = 0; k < RD_NVAR; k++)
          for(j = 0; j < RD_NVERT; j++)
            temporal[k] += tri_normals_list[i].area / RD_NVERT * dU_vertex[j][k] / full_triangle_dt;
      const int info = rd_euler_lda_residual(3, &U_fluid[0][0], &tri_normals_list[i].normal[0][0],
                                            tri_normals_list[i].mag, GAMMA, RD_SVD_RCOND, always_svd,
                                            rd_stage == 1 ? temporal : NULL,
                                            Phi, &nodal[0][0], &f1[0][0], &diagnostic);
      if(rd_stage == 1 && diagnostic.solve.rank != RD_NVAR)
        {
          RD_stat_f1_lumped++;
          for(j = 0; j < RD_NVERT; j++)
            for(k = 0; k < RD_NVAR; k++)
              f1[j][k] = tri_normals_list[i].area / RD_NVERT * dU_vertex[j][k] / full_triangle_dt;
        }
#else
      const int info = rd_euler_n_residual(3, &U_fluid[0][0], &tri_normals_list[i].normal[0][0],
                                          tri_normals_list[i].mag, GAMMA, RD_SVD_RCOND, always_svd,
                                          Phi, &nodal[0][0], &diagnostic);
#endif
      if(info != 0)
        terminate_program("RD tetra distribution failed: tetra=%d stage=%d info=%d solve=%.17g conservation=%.17g scale=%.17g",
                          thistask_triangles[i], rd_stage, info, diagnostic.solve_defect,
                          diagnostic.conservation_defect, diagnostic.roundoff_scale);
      RD_stat_elements++;
      RD_stat_pinv_fallback += diagnostic.solve.used_svd;
      RD_stat_exact_singular += diagnostic.solve.exact_singular;
      RD_stat_min_pivot_ratio = dmin(RD_stat_min_pivot_ratio, diagnostic.solve.pivot_ratio);
      if(diagnostic.solve.used_svd)
        {
          RD_stat_min_svd_rank = imin(RD_stat_min_svd_rank, diagnostic.solve.rank);
          RD_stat_svd_rank_count[diagnostic.solve.rank]++;
        }
      RD_stat_max_cons_defect_abs = dmax(RD_stat_max_cons_defect_abs, diagnostic.conservation_defect);
      RD_stat_max_phi = dmax(RD_stat_max_phi, diagnostic.max_phi);
      for(j = 0; j < DIMS + 1; j++)
        for(k = 0; k < DIMS + 2; k++)
          Flux_RD[k][j] = rd_stage == 0 ? nodal[j][k] :
#ifdef LDA_SCHEME
              f1[j][k] + 0.5 * nodal[j][k];
#else
              tri_normals_list[i].area / (DIMS + 1) * dU_vertex[j][k] / triangle_dt + 0.5 * nodal[j][k];
#endif
#endif /* TWODIMS: distribution */

      for(j = 0; j < DIMS + 1; j++)
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
#ifndef TWODIMS
              SphP[SphP_index].Momentum[2] += (-1.0) * triangle_dt * Flux_RD[3][j];
#endif
              SphP[SphP_index].Energy += (-1.0) * triangle_dt * Flux_RD[DIMS + 1][j];
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
#ifdef TWODIMS
              FluxRD_list[N_FluxRD_export].dMomentum_Dual[2] = 0.0;
#else
              FluxRD_list[N_FluxRD_export].dMomentum_Dual[2] = (-1.0) * triangle_dt * Flux_RD[3][j];
#endif
              FluxRD_list[N_FluxRD_export].dEnergy_Dual      = (-1.0) * triangle_dt * Flux_RD[DIMS + 1][j];
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
    }   // for loop of triangles, i= 0~ Ndt_thistask

#if defined(RD_DIAG_THETA_MAP) && defined(B_SCHEME) && defined(RD_RK2_EQUALSTEP)
  if(rd_theta_map_fp != NULL)
    fclose(rd_theta_map_fp);
#endif

  apply_FluxRD_list();

#ifdef RD_3D_STATIC
  rd_static_validate_stage(rd_stage, set.n);
#endif

#ifdef RD_LDA_RUSANOV_BLEND
  {
    double(*q_low)[4] = (double(*)[4])mymalloc("RD_LRLowState", NumGas * sizeof(*q_low));
    double before[4] = {0}, after[4] = {0}, max_cfl = 0, ell_sum = 0, ell_min = 1;
    double min_rho = DBL_MAX, min_internal = DBL_MAX, correction_norm = 0, accepted_norm = 0, min_b = 1;
    long long limited = 0, elements = 0;
    for(int index = 0; index < NumGas; index++)
      {
        q_low[index][0] = P[index].Mass;
        q_low[index][1] = SphP[index].Momentum[0];
        q_low[index][2] = SphP[index].Momentum[1];
        q_low[index][3] = SphP[index].Energy;
#ifdef RD_BLEND_LOW_HLLC
        /* ALE lumped corrector = (a-.5)U^n + b[U* - dt/(2b) S^-1 sum phi^low(U*)]:
         * both convex weights and the rescaled stage CFL must hold. */
        const double a = rd_lr_mass[index] / SphP[index].DualArea;
        const double b = rd_stage == 0 ? 1.0 : 1.5 - a;
        rd_lr_cfl[index] *= rd_stage == 0 ? 1.0 : 0.5 / b;
        if(!(b > 0.0) || b > 1.0)
          terminate_program("LDA/HLLC low corrector weight invalid: ID=%llu a=%.17g b=%.17g",
                            (unsigned long long)P[index].ID, a, b);
        min_b = dmin(min_b, b);
#endif
        if(rd_lr_degree[index] < 1 || !rd_rusanov_admissible(q_low[index]) ||
           !isfinite(rd_lr_cfl[index]) || rd_lr_cfl[index] > 1)
          terminate_program("LDA/Rusanov low stage invalid: stage=%d ID=%llu CFL=%.17g",
                            rd_stage, (unsigned long long)P[index].ID, rd_lr_cfl[index]);
        max_cfl = dmax(max_cfl, rd_lr_cfl[index]);
        for(int k = 0; k < 4; k++) before[k] += q_low[index][k];
      }
#ifdef RD_BLEND_LOCAL_BOUNDS
    /* Bounds over the element stencil of each node (all incident triangles'
     * vertices): stage-opening U^n, the predictor U* at the corrector, and
     * the assembled low-order stage state.  Zalesak-type, not relaxed. */
    double(*bound)[3] = (double(*)[3])mymalloc("RD_LRBounds", NumGas * sizeof(*bound));
    for(int index = 0; index < NumGas; index++)
      bound[index][0] = bound[index][2] = DBL_MAX, bound[index][1] = -DBL_MAX;
    for(int slot = 0; slot < Ndt_thistask; slot++)
      {
        int ids[3];
        for(int v = 0; v < 3; v++) ids[v] = rd_rusanov_local_index(&DP[DT[thistask_triangles[slot]].p[v]]);
        for(int w = 0; w < 3; w++)
          {
            const int j = ids[w];
            double states[3][4];
            int count = 0;
            for(int k = 0; k < 4; k++)
              {
                states[0][k] = SphP[j].RD_Ustage0[k];
                states[1][k] = q_low[j][k] / SphP[j].DualArea;
                states[2][k] = SphP[j].RD_Ustage0[k] + SphP[j].RD_dU[k];
              }
            count = rd_stage == 0 ? 2 : 3;
            for(int c = 0; c < count; c++)
              for(int v = 0; v < 3; v++) rd_lr_bounds_include(bound[ids[v]], states[c], GAMMA);
          }
      }
#endif
    for(int slot = 0; slot < Ndt_thistask; slot++)
      if(set.active[slot])
        {
          int ids[3];
          double ell = 1;
          for(int v = 0; v < 3; v++)
            {
              ids[v] = rd_rusanov_local_index(&DP[DT[thistask_triangles[slot]].p[v]]);
              double dq[4];
              for(int k = 0; k < 4; k++) dq[k] = rd_lr_degree[ids[v]] * rd_lr_correction[slot][k][v];
#ifdef RD_BLEND_LOCAL_BOUNDS
              ell = dmin(ell, rd_lr_limit_bounds(q_low[ids[v]], dq, SphP[ids[v]].DualArea, bound[ids[v]], GAMMA));
#else
              ell = dmin(ell, rd_lr_limit(q_low[ids[v]], dq));
#endif
            }
          if(RD_LDA_RUSANOV_BLEND == 0) ell = 0;
          if(!(ell >= 0 && ell <= 1)) terminate_program("Invalid LDA/Rusanov limiter");
          ell_sum += ell; ell_min = dmin(ell_min, ell); elements++;
          if(ell < 1-1e-12) limited++;
          for(int v = 0; v < 3; v++)
            {
              int index = ids[v];
              P[index].Mass += ell*rd_lr_correction[slot][0][v];
              SphP[index].Momentum[0] += ell*rd_lr_correction[slot][1][v];
              SphP[index].Momentum[1] += ell*rd_lr_correction[slot][2][v];
              SphP[index].Energy += ell*rd_lr_correction[slot][3][v];
              for(int k = 0; k < 4; k++)
                {
#ifdef RD_LDA_RUSANOV_B_SENSOR
                  if(rd_stage == 0)
                    rd_lr_old[slot].accepted[k][v] = rd_lr_old[slot].low[k][v] -
                        ell*rd_lr_correction[slot][k][v]/rd_lr_old[slot].dt;
#endif
                  correction_norm += fabs(rd_lr_correction[slot][k][v]);
                  accepted_norm += ell*fabs(rd_lr_correction[slot][k][v]);
                }
            }
        }
    for(int index = 0; index < NumGas; index++)
      {
        double q[4] = {P[index].Mass, SphP[index].Momentum[0], SphP[index].Momentum[1], SphP[index].Energy};
        if(!rd_rusanov_admissible(q)) terminate_program("LDA/Rusanov limited stage is inadmissible");
        for(int k = 0; k < 4; k++) after[k] += q[k];
        min_rho = dmin(min_rho, q[0]/SphP[index].DualArea);
        min_internal = dmin(min_internal, rd_rusanov_internal(q)/SphP[index].DualArea);
      }
    double defect = 0;
    for(int k = 0; k < 4; k++)
      {
        defect = dmax(defect, fabs(after[k]-before[k]));
        if(fabs(after[k]-before[k]) > 1e-10*dmax(1, fabs(before[k])))
          terminate_program("LDA/Rusanov correction lost conservation");
      }
    mpi_printf("RD-LR time=%.17g stage=%d elements=%lld limited=%lld ell_mean=%.17g ell_min=%.17g "
               "correction_norm=%.17g accepted_norm=%.17g rho_min=%.17g internal_min=%.17g CFL_max=%.17g budget_defect=%.17g\n",
               All.Time, rd_stage, elements, limited, ell_sum/elements, ell_min, correction_norm, accepted_norm,
               min_rho, min_internal, max_cfl, defect);
#ifdef RD_BLEND_LOW_HLLC
    mpi_printf("RD-LR-HLLC time=%.17g stage=%d b_min=%.17g bounds=%d\n", All.Time, rd_stage, min_b,
#ifdef RD_BLEND_LOCAL_BOUNDS
               1);
#else
               0);
#endif
#else
    (void)min_b;
#endif
#ifdef RD_BLEND_LOCAL_BOUNDS
    myfree(bound);
#endif
    myfree(q_low);
  }
#ifdef RD_LDA_RUSANOV_B_SENSOR
  mpi_printf("RD-LR-B time=%.17g stage=%d mode=%d elements=%lld theta_rho=%.17g theta_mx=%.17g "
             "theta_my=%.17g theta_E=%.17g theta_max=%.17g\n", All.Time, rd_stage,
             RD_LDA_RUSANOV_B_SENSOR, rd_lr_sensor_elements,
             rd_lr_theta_sum[0]/rd_lr_sensor_elements, rd_lr_theta_sum[1]/rd_lr_sensor_elements,
             rd_lr_theta_sum[2]/rd_lr_sensor_elements, rd_lr_theta_sum[3]/rd_lr_sensor_elements, rd_lr_theta_max);
#endif
#ifdef RD_BLEND_LOW_HLLC
  myfree(rd_lr_mass);
#endif
  myfree(rd_lr_degree);
  myfree(rd_lr_cfl);
  myfree(rd_lr_correction);
#endif

#if defined(RD_RUSANOV_LOW_ORDER) && defined(RD_ALE_INTERVAL_HIERARCHY)
  {
    /* Interval hierarchy: every closed star is refreshed, so between two
     * refreshes a vertex is either live for one RK2 interval (the equal-step
     * convex-weight and stage-CFL checks below, with triangle_dt = h/2) or
     * frozen in every interval (positivity needs the ledger of
     * (h/2)(coeff^0+coeff^1) to stay below its refreshed mass, checked at
     * refresh).  Partial stars hold partial ledgers and are not states. */
    double max_cfl = 0.0, min_b = 1.0;
    int live_checked = 0;
    for(int index = 0; index < NumGas; index++)
      {
        SphP[index].RD_CFLLedger += rd_rus_coeff[index];
        if(!RdIntervalLive[index])
          continue;
        const double area = SphP[index].DualArea;
        const double a = rd_rus_coeff[NumGas + index] / area;
        const double b = rd_stage == RD_RK_STAGE_PREDICTOR ? 1.0 : 1.5 - a;
        const double cfl = (rd_stage == RD_RK_STAGE_PREDICTOR ? 2.0 : 1.0 / b) * rd_rus_coeff[index] / area;
        if(!(area > 0.0) || !(b > 0.0) || b > 1.0 || !isfinite(cfl) || cfl > 1.0)
          terminate_program("Interval low-order stage CFL/convex weight violated: stage=%d ID=%llu a=%.17g b=%.17g CFL=%.17g",
                            rd_stage, (unsigned long long)P[index].ID, a, b, cfl);
        max_cfl = dmax(max_cfl, cfl);
        min_b = dmin(min_b, b);
        live_checked++;
      }
    mpi_printf("RD-RUSANOV time=%.17g stage=%d interval live=%d CFL_max=%.17g b_min=%.17g\n", All.Time, rd_stage,
               live_checked, max_cfl, min_b);
  }
  myfree(rd_rus_coeff);
#elif defined(RD_RUSANOV_LOW_ORDER)
  {
    double min_rho = DBL_MAX, min_internal = DBL_MAX, max_cfl = 0.0, min_b = 1.0;
    for(int index = 0; index < NumGas; index++)
      {
        const double area = SphP[index].DualArea;
        const double a = rd_rus_coeff[NumGas + index] / area;
        /* Existing lumped corrector = (a-.5)U^n + b[U* + dt/(2b)L(U*)].
         * Static a=1. ALE needs BOTH convex weights and the rescaled stage CFL. */
        const double b = rd_stage == 0 ? 1.0 : 1.5 - a;
        const double factor = rd_stage == 0 ? 1.0 : 0.5 / b;
        const double cfl = factor * rd_rus_coeff[index] / area;
        if(!(area > 0.0) || !(b > 0.0) || b > 1.0 || !isfinite(cfl) || cfl > 1.0)
          terminate_program("Rusanov stage CFL/convex weight violated: stage=%d ID=%llu a=%.17g b=%.17g CFL=%.17g",
                            rd_stage, (unsigned long long)P[index].ID, a, b, cfl);
        double u[4] = {P[index].Mass / area, SphP[index].Momentum[0] / area,
                       SphP[index].Momentum[1] / area, SphP[index].Energy / area};
        if(!rd_rusanov_admissible(u))
          terminate_program("Rusanov produced an inadmissible stage before primitive recovery: stage=%d ID=%llu",
                            rd_stage, (unsigned long long)P[index].ID);
        min_rho = dmin(min_rho, u[0]);
        min_internal = dmin(min_internal, rd_rusanov_internal(u));
        max_cfl = dmax(max_cfl, cfl);
        min_b = dmin(min_b, b);
      }
    mpi_printf("RD-RUSANOV time=%.17g stage=%d rho_min=%.17g internal_min=%.17g CFL_max=%.17g b_min=%.17g\n",
               All.Time, rd_stage, min_rho, min_internal, max_cfl, min_b);
  }
  myfree(rd_rus_coeff);
#endif

#ifdef RD_ALE_HIERARCHICAL_ARPAIA
  if(rd_stage == RD_RK_STAGE_CORRECTOR)
    rd_ale_hierarchical_arpaia_finish(&set);
#endif

#ifdef RD_ALE_CFL_DIAGNOSTIC
  if(rd_stage == 0)
    rd_ale_report_cfl(&set);
#endif

#ifdef RD_HIERARCHICAL_TIMESTEPS
  if(rd_stage == RD_RK_STAGE_PREDICTOR)
    {
      long long local_counts[2] = {0, 0}, global_counts[2];
      int local_max_ratio = 1, global_max_ratio;

      for(i = 0; i < NumGas; i++)
        {
#ifdef RD_ALE_INTERVAL_HIERARCHY
          if(RdIntervalLive[i])
            {
              local_counts[0]++;
              {
#else
          if(SphP[i].RD_StarTimeBin == P[i].TimeBinHydro)
            {
              local_counts[0]++;
              if(TimeBinSynchronized[P[i].TimeBinHydro])
                {
#endif
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
#ifndef RD_ALE_INTERVAL_HIERARCHY
              int ratio = 1 << (P[i].TimeBinHydro - SphP[i].RD_StarTimeBin);
              local_max_ratio = imax(local_max_ratio, ratio);
#endif
            }
        }

      MPI_Reduce(local_counts, global_counts, 2, MPI_LONG_LONG, MPI_SUM, 0, MPI_COMM_WORLD);
      MPI_Reduce(&local_max_ratio, &global_max_ratio, 1, MPI_INT, MPI_MAX, 0, MPI_COMM_WORLD);
      if(ThisTask == 0)
        printf("RD-HIER time=%.8g stage=open live_vertices=%lld frozen_vertices=%lld max_ratio=%d\n", All.Time,
               global_counts[0], global_counts[1], global_max_ratio);
    }
#endif

#ifdef RD_RK2_EQUALSTEP
      myfree_movable(FluxRD_list);
    } /* stage loop */

  FluxRD_list = NULL; /* freed inside the stage loop */
#ifdef RD_ALE_APOSTERIORI_FALLBACK
      if(!fallback_retry)
        {
          fallback_rejected_stats = rd_aposteriori_inspect_trial(&set, bad_vertex, relaxed_vertex);
          if(fallback_rejected_stats.bad_nodes > 0)
            {
              fallback_retry          = 1;
              fallback_rejected_stage = "endpoint";
            }
        }

      if(!fallback_retry)
        {
          if(fallback_attempt > 0)
            mpi_printf("RD-APOSTERIORI-ACCEPT time=%.8g retries=%d masked_elements=%d/%d (%.6g%%) "
                       "rho_ratio_floor=%.6g\n",
                       All.Time, fallback_attempt, fallback_masked_total, Ndt_thistask,
                       (Ndt_thistask > 0) ? 100.0 * (double)fallback_masked_total / (double)Ndt_thistask : 0.0,
                       (double)(RD_ALE_APOSTERIORI_FALLBACK));
          break;
        }

      int fallback_added = rd_aposteriori_expand_star(T, &set, bad_vertex, fallback_element,
                                                      &fallback_masked_total);
      for(int fallback_vertex = 0; fallback_vertex < NumGas; fallback_vertex++)
        if(bad_vertex[fallback_vertex])
          relaxed_vertex[fallback_vertex] = 1;

      mpi_printf("RD-APOSTERIORI-REJECT time=%.8g attempt=%d stage=%s bad_nodes=%d hard_bad_nodes=%d worst_id=%llu "
                 "min_rho=%.6e min_press=%.6e min_rho_ratio=%.6e added_elements=%d masked=%d/%d\n",
                 All.Time, fallback_attempt, fallback_rejected_stage, fallback_rejected_stats.bad_nodes,
                 fallback_rejected_stats.hard_bad_nodes,
                 (unsigned long long)fallback_rejected_stats.worst_id, fallback_rejected_stats.min_rho,
                 fallback_rejected_stats.min_press, fallback_rejected_stats.min_rho_ratio, fallback_added,
                 fallback_masked_total, Ndt_thistask);

      if(fallback_added == 0 && fallback_rejected_stats.hard_bad_nodes > 0)
        {
          fallback_added = rd_aposteriori_expand_halo(T, &set, fallback_element, &fallback_masked_total);
          mpi_printf("RD-APOSTERIORI-HALO time=%.8g attempt=%d added_elements=%d masked=%d/%d\n", All.Time,
                     fallback_attempt, fallback_added, fallback_masked_total, Ndt_thistask);
        }

      if(fallback_added == 0)
        terminate_program("a-posteriori fallback could not enlarge the local N patch to recover hard positivity");
      if(fallback_attempt + 1 >= RD_ALE_APOSTERIORI_MAX_ATTEMPTS)
        terminate_program("a-posteriori fallback exceeded its diagnostic retry limit");

      fallback_attempt++;
    }

  myfree(relaxed_vertex);
  myfree(bad_vertex);
  myfree(fallback_element);
#endif
#endif /* RD_RK2_EQUALSTEP */

#if defined(RD_RK2_SPLIT_STAGES) && !defined(RD_ALE_EQUALSTEP)
  if(rd_requested_stage == RD_RK_STAGE_PREDICTOR)
    All.RD_EqualStepEnd = All.Ti_Current + rd_equal_interval;
  else
    All.RD_EqualStepEnd = 0;
#ifdef RD_DEBUG_ASSERTS
  mpi_printf("RD-EQUAL time=%.8g stage=%s pending_endpoint=%lld\n", All.Time,
             rd_requested_stage == RD_RK_STAGE_PREDICTOR ? "predictor" : "corrector",
             (long long)All.RD_EqualStepEnd);
#endif
#endif

#ifdef RD_ALE_EQUALSTEP
  rd_ale_finish_step(&set);
#endif

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
    long long stat_rank_counts[DIMS + 3];
    double stat_mins[2] = {RD_stat_min_pivot_ratio, RD_stat_min_dt_extrap};
    double stat_maxs[3] = {RD_stat_max_cons_defect_abs, RD_stat_max_dt_extrap, RD_stat_max_phi};
    double stat_min_out[2], stat_max_out[3];

    MPI_Reduce(stat_counts, stat_totals, 3, MPI_LONG_LONG, MPI_SUM, 0, MPI_COMM_WORLD);
    MPI_Reduce(&stat_counts[3], &stat_min_rank, 1, MPI_LONG_LONG, MPI_MIN, 0, MPI_COMM_WORLD);
    MPI_Reduce(RD_stat_svd_rank_count, stat_rank_counts, DIMS + 3, MPI_LONG_LONG, MPI_SUM, 0, MPI_COMM_WORLD);
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

#ifndef TWODIMS
    mpi_printf("RD-3D rank5_count=%lld\n", stat_rank_counts[5]);
#endif

#ifdef RD_ALE_CONDITION_DIAGNOSTIC
    if(ThisTask == 0)
      printf("RD-COND-SUMMARY time=%.8g max_cond_lab=%.6e cond_shift_at_lab_max=%.6e "
             "max_eta_lab=%.6e max_eta_shift=%.6e max_a2_shift=%.6e min_rank_shift=%d\n",
             All.Time, RD_stat_max_condition_lab, RD_stat_shift_condition_at_lab_max,
             RD_stat_max_backward_error_lab, RD_stat_max_backward_error_shift, RD_stat_max_shift_a2_defect,
             (int)RD_stat_min_shift_rank);
#endif

#ifdef RD_ELEMENT_COMOVING_FRAME
    if(ThisTask == 0)
      printf("RD-COMOVING-SUMMARY time=%.8g max_correction_covariance=%.6e "
             "max_phi_covariance=%.6e max_phi_covariance_relative=%.6e\n",
             All.Time, RD_stat_max_comoving_correction_covariance,
             RD_stat_max_comoving_phi_covariance, RD_stat_max_comoving_phi_covariance_relative);
#endif

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

#ifndef RD_RK2_EQUALSTEP
  myfree_movable(FluxRD_list);
#endif
#if defined(B_SCHEME) && defined(RD_RK2_EQUALSTEP)
  myfree(rd_b_phi_stage0);
  myfree(rd_b_flux_lda_stage0);
  myfree(rd_b_flux_n_stage0);
#endif
#ifdef RD_LDA_RUSANOV_B_SENSOR
  myfree(rd_lr_old);
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
