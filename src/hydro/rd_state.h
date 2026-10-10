#ifndef RD_STATE_H
#define RD_STATE_H

/* Equal-step AREPO stage transitions; state vector size follows rd_dimensions.
 * Corrector recovery rejects inadmissible states without applying floors.
 * The caller owns the minimum-state diagnostic accumulators. */
void rd_rk2_save_stage0(void);
void rd_rk2_prepare_corrector(double *min_rho, double *min_pressure);
void rd_static_validate_stage(int stage, int elements);

#endif
