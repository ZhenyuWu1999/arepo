#include "rd_element.h"

#include <math.h>
#include <string.h>

int rd_element_roe_residual(const struct rd_element_input *input, enum rd_element_scheme scheme,
                            double gamma, double rcond, int always_svd, const double *temporal_target,
                            struct rd_element_output *output, struct rd_n_diagnostics *diagnostics)
{
  if(!diagnostics)
    return -1;
  memset(diagnostics, 0, sizeof(*diagnostics));
  if(!input || !output || !input->conserved || !input->geometry.unit_normal ||
     !input->geometry.face_measure || !output->total || !output->spatial ||
     (input->geometry.ndim != 2 && input->geometry.ndim != 3) ||
     !(input->geometry.measure > 0.0) || !isfinite(input->geometry.measure) ||
     (scheme != RD_ELEMENT_N && scheme != RD_ELEMENT_LDA) ||
     (temporal_target && (scheme != RD_ELEMENT_LDA || !output->temporal)))
    return -1;

  const int ndim = input->geometry.ndim, nvert = ndim + 1, nvar = ndim + 2;
  double spatial[20], temporal[20]; /* compact vertex-major kernel buffers */
  int info;
  if(scheme == RD_ELEMENT_N)
    info = rd_euler_n_residual(ndim, input->conserved, input->geometry.unit_normal,
                               input->geometry.face_measure, gamma, rcond, always_svd,
                               output->total, spatial, diagnostics);
  else
    info = rd_euler_lda_residual(ndim, input->conserved, input->geometry.unit_normal,
                                 input->geometry.face_measure, gamma, rcond, always_svd,
                                 temporal_target, output->total, spatial,
                                 temporal_target ? temporal : NULL, diagnostics);
  if(info != 0)
    return info;

  for(int vertex = 0; vertex < nvert; vertex++)
    for(int component = 0; component < nvar; component++)
      {
        output->spatial[component * nvert + vertex] = spatial[vertex * nvar + component];
        if(temporal_target)
          output->temporal[component * nvert + vertex] = temporal[vertex * nvar + component];
      }
  return 0;
}
