/* Pure geometry/registry used by the diagnostic-only moving 3D pilot.
 * No particle state, mesh mutation, timestep selection or MPI. */
#ifndef RD_SIMPLEX_REGISTRY_H
#define RD_SIMPLEX_REGISTRY_H
#include <stdint.h>

struct rd_tetra_record
{
  uint64_t id[4];
  int32_t image[4][3]; /* relative to the smallest-ID vertex, in OLD primary coordinates */
  int32_t orientation; /* canonical ordering's sign at the snapshot's own time */
  double x[4][3], w[4][3]; /* coherently unfolded, anchor in OLD primary image */
};

struct rd_tetra_metric
{
  double v0, vmid, v1, vmin, smin, error;
  double q0, qmid, q1, ratio, midpoint_defect, gcl_defect, mean_normal_correction;
  int negative0, negative1, negative_interval, uncertain, changed;
};

struct rd_cavity_metric
{
  uint64_t min_id;
  int vertices, removed, inserted, winding, invalid_old, invalid_new;
  double volume_defect0, volume_defect1, moment_defect0, moment_defect1;
};

struct rd_registry_summary
{
  int old_count, new_count, removed, inserted, cavities, changed_vertices, max_vertices;
  int winding_cavities, id_alias_old, id_alias_new, reversed_common;
  int old_endpoint_negative, old_interval_negative, old_uncertain;
  int new_pullback_negative, new_mid_negative, new_interval_negative, new_uncertain;
  double coverage0, coverage1, old_forward_coverage, new_pullback_coverage;
  double min_old_interval, min_new_interval, min_pullback_ratio;
  double min_q0, min_qmid, min_q1;
  double max_cavity_volume_defect, max_cavity_moment_defect;
  double max_midpoint_gcl_defect, max_gauss_gcl_defect, max_mean_normal_correction;
};

/* Sort vertices and normalize a whole-box image translation. Incoming image
 * offsets are absolute relative to the opening primary positions. */
void rd_tetra_canonicalize(struct rd_tetra_record *r, const double box[3]);
int rd_registry_prepare(struct rd_tetra_record *r, int n, int *id_aliases);
void rd_tetra_interval(const struct rd_tetra_record *r, double h, int closing, struct rd_tetra_metric *m);
double rd_tetra_signed_volume(const double x[4][3]);
/* Buffers: old/new metrics of lengths no/nn, cavities at least no+nn entries.
 * -1 invalid input, -2 duplicate complete key, -3 inconsistent unchanged
 * geometry, -4 allocation failure. ID aliases with different images are valid. */
int rd_registry_compare(const struct rd_tetra_record *old, int no, const struct rd_tetra_record *fresh, int nn,
                        double h, const double box[3], struct rd_registry_summary *summary,
                        struct rd_tetra_metric *om, struct rd_tetra_metric *nm, struct rd_cavity_metric *cav);
#endif
