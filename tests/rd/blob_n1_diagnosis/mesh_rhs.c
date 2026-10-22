#include <math.h>
#include <string.h>
#include "rd_euler.h"
#include "rd_simplex_geometry.h"
int mesh_geometry(int nt, const double *x, double *normal, double *area, double *vol) {
  for(int t=0;t<nt;t++) {
    if(rd_simplex_geometry(3,x+12*t,vol+t,normal+12*t,area+4*t)) return t+1;
    vol[t]=fabs(vol[t]);
  }
  return 0;
}
int mesh_rhs(int nv, int nt, const int *ids, const double *normal, const double *area,
             const double *u, double *rhs, double *svd_count) {
  memset(rhs,0,nv*5*sizeof(double)); *svd_count=0;
  for(int t=0;t<nt;t++) {
    double state[20], phi[5], nodal[20]; struct rd_n_diagnostics d;
    for(int i=0;i<4;i++) memcpy(state+5*i,u+5*ids[4*t+i],5*sizeof(double));
    int status=rd_euler_n_residual(3,state,normal+12*t,area+4*t,5./3.,-1.,0,phi,nodal,&d);
    if(status) return t+1;
    *svd_count+=d.solve.used_svd;
    for(int i=0;i<4;i++) for(int k=0;k<5;k++) rhs[5*ids[4*t+i]+k]-=nodal[5*i+k];
  }
  return 0;
}
