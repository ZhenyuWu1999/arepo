#include <cmath>
#include <fstream>
#include "vertex3D.h"
VERTEX setup_vertex(double,double,double);
int main(int argc,char **argv) {
  if(argc!=3) return 2;
  std::ifstream in(argv[1],std::ios::binary); std::ofstream out(argv[2],std::ios::binary);
  int n;in.read(reinterpret_cast<char *>(&n),sizeof(n));
  for(int i=0;i<n;i++) {
    double x[3];in.read(reinterpret_cast<char *>(x),sizeof(x));
    VERTEX v=setup_vertex(x[0],x[1],x[2]);
    double a[5]={v.get_u0(),v.get_u1(),v.get_u2(),v.get_u3(),v.get_u4()};
    out.write(reinterpret_cast<char *>(a),sizeof(a));
  }
}
