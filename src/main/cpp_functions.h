//
//
//

#ifndef AREPO_CPP_FUNCTIONS_H
#define AREPO_CPP_FUNCTIONS_H

#ifdef __cplusplus
extern "C"{
#endif

#ifdef RESIDUAL_DISTRIBUTION
// functions defined in residual_distribution_solver.c, which may be used in other C files
void reset_dualarea(tessellation *T);
void rd_step_begin(tessellation *T);
void rd_step_end(tessellation *T);
#if defined(RD_ALE_EXACT_PATCH_DIAGNOSTIC) || defined(RD_ALE_FLIP_TRANSFER)
void rd_ale_topology_capture_old_mesh(tessellation *T);
#endif
#if defined(RD_HIERARCHICAL_TIMESTEPS) || (defined(RD_RK2_SPLIT_STAGES) && !defined(RD_ALE_EQUALSTEP))
#define RD_RK_STAGE_PREDICTOR 0
#define RD_RK_STAGE_CORRECTOR 1
void compute_residuals(tessellation *, int);
#else
void compute_residuals(tessellation *);
#endif
void triangle_vertex_do_time_extrapolation(struct state_primitive *delta, struct state_primitive *st,struct grad_data *grad, double dt_Extrapolation);
void triangle_vertex_add_extrapolation(struct state_primitive *delta, struct state_primitive *st);
void apply_FluxRD_list(void);
int FluxRD_list_data_compare(const void *, const void *);
void apply_DualArea_list(void);
int DualArea_list_data_compare(const void *, const void *);
#endif


#ifdef __cplusplus
}
#endif






#endif  // AREPO_CPP_FUNCTIONS_H
