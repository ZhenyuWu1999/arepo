#include <cmath>
#include <string>
#include <vector>
#include <iostream>
#include <fstream>
#include <iomanip>
// Diagnostic visibility only; the included numerical methods are unchanged.
#define private public
#include "triangle3D.h"
#undef private
extern "C" {
#include "rd_euler.h"
#include "rd_simplex_geometry.h"
}

int main(int argc, char **argv) {
  if (argc != 3) return 2;
  std::ifstream input(argv[1], std::ios::binary);
  std::ofstream output(argv[2], std::ios::binary);
  int count; input.read(reinterpret_cast<char *>(&count), sizeof(count));
  for (int sample=0; sample<count; ++sample) {
    double x[12], u[20], old[20], residual[20], phi[5], vol[1], normal[12], area[4];
    input.read(reinterpret_cast<char *>(x), sizeof(x));
    input.read(reinterpret_cast<char *>(u), sizeof(u));
    if (!input) return 3;
    VERTEX v[4]; TRIANGLE t;
    for (int j=0; j<4; ++j) {
      v[j].set_id(j); v[j].set_x(x[3*j]); v[j].set_y(x[3*j+1]); v[j].set_z(x[3*j+2]);
      v[j].set_dual(0);
      for (int k=0; k<5; ++k) v[j].U_VARIABLES[k]=u[j*5+k];
      v[j].con_to_prim(); v[j].reset_u_half(); v[j].reset_du(); v[j].reset_du_half();
    }
    t.set_id(sample); t.set_boundary(0); t.set_tbin(1);
    t.set_vertex_0(v); t.set_vertex_1(v+1); t.set_vertex_2(v+2); t.set_vertex_3(v+3);
    t.setup_normals();
    t.calculate_first_half(0, 1.);
    for (int j=0; j<4; ++j) for (int k=0; k<5; ++k) old[j*5+k]=t.FLUC_N[k][j];
    rd_n_diagnostics diagnostic;
    int status=rd_simplex_geometry(3,x,vol,normal,area);
    if (status) return 4;
    status=rd_euler_n_residual(3,u,normal,area,GAMMA,-1.,0,phi,residual,&diagnostic);
    if (status) return 5;
    // Records: old/current residual, phi, native old phi/2, geometry errors,
    // rank/pivot diagnostics, all stored as doubles.
    output.write(reinterpret_cast<char *>(old),sizeof(old));
    output.write(reinterpret_cast<char *>(residual),sizeof(residual));
    output.write(reinterpret_cast<char *>(phi),sizeof(phi));
    for (double p:t.PHI) { p*=.5; output.write(reinterpret_cast<char *>(&p),sizeof(p)); }
    double metrics[5]={std::abs(t.VOLUME/std::abs(vol[0])-1),0,0,
                       double(diagnostic.solve.used_svd),diagnostic.solve.pivot_ratio};
    for(int j=0;j<4;++j) {
      metrics[1]=std::max(metrics[1],std::abs(t.MAG[j]/(2*area[j])-1));
      for(int k=0;k<3;++k) metrics[2]=std::max(metrics[2],std::abs(t.NORMAL[j][k]-normal[j*3+k]));
    }
    output.write(reinterpret_cast<char *>(metrics),sizeof(metrics));
  }
  std::cout << "Completed " << count << " actual predecessor/current element comparisons\n";
}
