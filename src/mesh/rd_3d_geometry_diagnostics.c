/* Diagnostic only: consumes native FV trajectories, never writes P/SphP,
 * connectivity, bins, or timestep. Geometry is keyed by ID and periodic image. */
#include <float.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../main/allvars.h"
#include "../main/proto.h"
#include "voronoi/voronoi.h"
#include "rd_simplex_registry.h"

#ifdef RD_3D_GEOMETRY_DIAGNOSTICS
#if defined(TWODIMS) || defined(ONEDIMS) || defined(VORONOI_STATIC_MESH) || defined(RESIDUAL_DISTRIBUTION)
#error "RD_3D_GEOMETRY_DIAGNOSTICS requires standard moving 3D FV."
#endif
#if !defined(FORCE_EQUAL_TIMESTEPS) || !defined(CREATE_FULL_MESH)
#error "RD_3D_GEOMETRY_DIAGNOSTICS requires full mesh and equal steps."
#endif
#if defined(REFINEMENT) || defined(REFLECTIVE_X) || defined(REFLECTIVE_Y) || defined(REFLECTIVE_Z)
#error "RD_3D_GEOMETRY_DIAGNOSTICS requires periodic fixed-count gas."
#endif
struct geom_node {uint64_t id; double x[3], w[3];};
static struct geom_node *GeomNodes;
static struct rd_tetra_record *Old;
static int Nold, Nnodes, Ready, PairWritten;
static double OpeningTime, RegRms, RegMax, MeshRms;
static double (*Base)[3];
static FILE *Steps, *Cavities, *Invalid;

static void *alloc(size_t n)
{
  void *p=calloc(n ? n:1,1);
  if(!p) terminate_program("3D geometry diagnostic allocation failed");
  return p;
}
static int nodecmp(const void *a,const void *b)
{
  const struct geom_node *x=a,*y=b;return (x->id>y->id)-(x->id<y->id);
}
static int node(uint64_t id)
{
  int lo=0,hi=Nnodes;
  while(lo<hi) {int m=lo+(hi-lo)/2;if(GeomNodes[m].id<id) lo=m+1;else hi=m;}
  if(lo==Nnodes || GeomNodes[lo].id!=id) terminate_program("3D geometry diagnostic missing ID");
  return lo;
}
static FILE *output(const char *name,const char *mode)
{
  char path[MAXLEN_PATH];snprintf(path,sizeof(path),"%s%s",All.OutputDir,name);
  FILE *f=fopen(path,mode);
  if(!f) terminate_program("3D geometry diagnostic could not open output");
  return f;
}
static struct rd_tetra_record *capture(tessellation *T,double h,int closing,int *nr)
{
  double box[3]={boxSize_X,boxSize_Y,boxSize_Z};
  struct rd_tetra_record *r=alloc((size_t)T->Ndt*sizeof(*r));*nr=0;
  for(int t=0;t<T->Ndt;t++)
    {
      /* AREPO retains vertex slots in deleted tetrahedra; t[0], not p[0],
       * is its deletion marker. Counting those slots corrupts coverage. */
      if(T->DT[t].t[0]<0) continue;
      int valid=1,owner=-1;MyIDType minid=0;
      for(int v=0;v<4;v++)
        {
          int k=T->DT[t].p[v];
          if(k<0 || k>=T->Ndp || T->DP[k].task!=ThisTask || T->DP[k].index<0) {valid=0;break;}
          const point *p=&T->DP[k];
          if(owner<0 || p->ID<minid) {owner=v;minid=p->ID;}
        }
      if(!valid) continue;
      const point *anchor=&T->DP[T->DT[t].p[owner]];
      if(anchor->index>=NumGas) continue; /* min-ID primary claims exactly one periodic image */
      struct rd_tetra_record *a=&r[(*nr)++];
      for(int v=0;v<4;v++)
        {
          const point *p=&T->DP[T->DT[t].p[v]];int j=node(p->ID);
          a->id[v]=p->ID;double coords[3]={p->x,p->y,p->z};
          for(int d=0;d<3;d++)
            {
              double ref=GeomNodes[j].x[d]+(closing ? h*GeomNodes[j].w[d]:0);
              double image=(coords[d]-ref)/box[d];long k=lround(image);
              if(fabs(image-k)>4096*DBL_EPSILON)
                terminate_program("3D geometry diagnostic inconsistent periodic trajectory");
              a->x[v][d]=coords[d];a->w[v][d]=GeomNodes[j].w[d];a->image[v][d]=(int32_t)k;
            }
        }
      rd_tetra_canonicalize(a,box);
    }
  int aliases;
  if(rd_registry_prepare(r,*nr,&aliases)) terminate_program("3D geometry diagnostic duplicate complete key");
  return r;
}
void rd_3d_geometry_velocity_begin(void)
{
  free(Base);Base=alloc((size_t)NumGas*sizeof(*Base));
  for(int j=0;j<NumGas;j++) for(int d=0;d<3;d++) Base[j][d]=SphP[j].VelVertex[d];
}
void rd_3d_geometry_velocity_end(void)
{
  if(!Old || NumGas!=Nnodes) terminate_program("3D geometry diagnostic incomplete opening snapshot");
  RegRms=RegMax=MeshRms=0;
  for(int j=0;j<NumGas;j++)
    {
      int k=node(P[j].ID);double reg2=0,mesh2=0;
      for(int d=0;d<3;d++)
        {
          double w=SphP[j].VelVertex[d];GeomNodes[k].w[d]=w;
          reg2+=(w-Base[j][d])*(w-Base[j][d]);mesh2+=w*w;
        }
      RegRms+=reg2;MeshRms+=mesh2;RegMax=fmax(RegMax,sqrt(reg2));
    }
  RegRms=sqrt(RegRms/NumGas);MeshRms=sqrt(MeshRms/NumGas);
  for(int t=0;t<Nold;t++) for(int v=0;v<4;v++) memcpy(Old[t].w[v],GeomNodes[node(Old[t].id[v])].w,sizeof(Old[t].w[v]));
  Ready=1;free(Base);Base=NULL;
}
static int dcmp(const void *a,const void *b) {double x=*(const double*)a,y=*(const double*)b;return (x>y)-(x<y);}
static void quantiles(const char *name,const struct rd_tetra_metric *m,int n,int field)
{
  double *q=alloc(n*sizeof(*q));
  for(int i=0;i<n;i++) q[i]=field==0 ? m[i].q0:field==1 ? m[i].qmid:m[i].q1;
  qsort(q,n,sizeof(*q),dcmp);
  fprintf(Steps,",\"%s\":[%.17g,%.17g,%.17g,%.17g,%.17g]",name,q[0],q[(n-1)/100],q[(n-1)/10],q[(n-1)/2],q[n-1]);free(q);
}
static void invalid_record(const struct rd_tetra_record *r,const struct rd_tetra_metric *m,int closing)
{
  fprintf(Invalid,"{\"step\":%d,\"time\":%.17g,\"h\":%.17g,\"closing\":%d,\"orientation\":%d,\"vmin\":%.17g,\"smin\":%.17g,\"error\":%.17g,\"uncertain\":%d,\"id\":[",All.NumCurrentTiStep,All.Time,All.Time-OpeningTime,closing,r->orientation,m->vmin,m->smin,m->error,m->uncertain);
  for(int i=0;i<4;i++) fprintf(Invalid,"%s%llu",i ? ",":"",(unsigned long long)r->id[i]);
  const double (*fields[2])[3]={r->x,r->w};
  for(int k=0;k<2;k++)
    {
      fprintf(Invalid,"],\"%s\":[",k ? "w":"x");
      for(int i=0;i<4;i++) fprintf(Invalid,"%s[%.17g,%.17g,%.17g]",i ? ",":"",fields[k][i][0],fields[k][i][1],fields[k][i][2]);
    }
  fprintf(Invalid,"]}\n");
}
void rd_3d_geometry_after_mesh(tessellation *T)
{
  if(NTask!=1 || All.ComovingIntegrationOn || RestartFlag==1 || NumGas!=NumPart)
    terminate_program("3D geometry diagnostic requires one rank, noncomoving fresh gas-only run");
  double box[3]={boxSize_X,boxSize_Y,boxSize_Z};
  if(Old)
    {
      double h=All.Time-OpeningTime;
      if(!Ready || !(h>0) || NumGas!=Nnodes) terminate_program("3D geometry diagnostic invalid drift interval");
      int nn;struct rd_tetra_record *fresh=capture(T,h,1,&nn);
      struct rd_tetra_metric *om=alloc(Nold*sizeof(*om)),*nm=alloc(nn*sizeof(*nm));
      struct rd_cavity_metric *c=alloc((Nold+nn)*sizeof(*c));struct rd_registry_summary s;
      int info=rd_registry_compare(Old,Nold,fresh,nn,h,box,&s,om,nm,c);
      if(info) {mpi_printf("3D registry compare error=%d\n",info);terminate_program("3D geometry registry comparison failed");}
      if(!PairWritten)
        {
          FILE *f=output("geometry_first_pair.bin","wb");uint32_t header[3]={(uint32_t)Nold,(uint32_t)nn,sizeof(*Old)};
          if(fwrite(header,sizeof(header),1,f)!=1 || fwrite(&h,sizeof(h),1,f)!=1 || fwrite(Old,sizeof(*Old),Nold,f)!=Nold || fwrite(fresh,sizeof(*fresh),nn,f)!=nn)
            terminate_program("3D geometry snapshot write failed");
          fclose(f);PairWritten=1;
        }
      fprintf(Steps,"{\"step\":%d,\"time\":%.17g,\"h\":%.17g,\"nodes\":%d",All.NumCurrentTiStep,All.Time,h,Nnodes);
#define SI(x) fprintf(Steps,",\"" #x "\":%d",s.x)
#define SD(x) fprintf(Steps,",\"" #x "\":%.17g",s.x)
      SI(old_count);SI(new_count);SI(removed);SI(inserted);SI(cavities);SI(changed_vertices);SI(max_vertices);SI(winding_cavities);SI(id_alias_old);SI(id_alias_new);SI(reversed_common);
      SI(old_endpoint_negative);SI(old_interval_negative);SI(old_uncertain);SI(new_pullback_negative);SI(new_mid_negative);SI(new_interval_negative);SI(new_uncertain);
      SD(coverage0);SD(coverage1);SD(old_forward_coverage);SD(new_pullback_coverage);SD(min_old_interval);SD(min_new_interval);SD(min_pullback_ratio);
      SD(max_cavity_volume_defect);SD(max_cavity_moment_defect);SD(max_midpoint_gcl_defect);SD(max_gauss_gcl_defect);
      SD(max_mean_normal_correction);
#undef SI
#undef SD
      quantiles("q_old",om,Nold,0);quantiles("q_new_mid",nm,nn,1);quantiles("q_new",nm,nn,2);
      double (*mass)[3]=alloc(Nnodes*sizeof(*mass));
      for(int t=0;t<Nold;t++) for(int v=0;v<4;v++) mass[node(Old[t].id[v])][0]+=om[t].v0/4;
      for(int t=0;t<nn;t++) for(int v=0;v<4;v++) {int j=node(fresh[t].id[v]);mass[j][1]+=nm[t].v0/4;mass[j][2]+=nm[t].v1/4;}
      double dm=0,mdm=0,msigned=0,mtemporal=DBL_MAX,mpull=DBL_MAX,mnew=DBL_MAX;int nonpositive=0;
      for(int j=0;j<Nnodes;j++)
        {
          double delta=mass[j][1]-mass[j][0];dm+=fabs(delta);mdm=fmax(mdm,fabs(delta));msigned+=delta;
          double temporal=(mass[j][1]+mass[j][2])/2;mtemporal=fmin(mtemporal,temporal);nonpositive+=temporal<=0;
          mpull=fmin(mpull,mass[j][1]);mnew=fmin(mnew,mass[j][2]);
        }
      fprintf(Steps,",\"dm_l1\":%.17g,\"dm_max\":%.17g,\"dm_sum\":%.17g,\"min_nodal_pullback\":%.17g,\"min_nodal_new\":%.17g,\"min_nodal_temporal\":%.17g,\"nonpositive_nodal_temporal\":%d,\"reg_rms\":%.17g,\"reg_max\":%.17g,\"mesh_rms\":%.17g}\n",dm,mdm,msigned,mpull,mnew,mtemporal,nonpositive,RegRms,RegMax,MeshRms);
      for(int j=0;j<s.cavities;j++) fprintf(Cavities,"%d,%.17g,%llu,%d,%d,%d,%d,%d,%d,%.17g,%.17g,%.17g,%.17g\n",All.NumCurrentTiStep,All.Time,(unsigned long long)c[j].min_id,c[j].vertices,c[j].removed,c[j].inserted,c[j].winding,c[j].invalid_old,c[j].invalid_new,c[j].volume_defect0,c[j].volume_defect1,c[j].moment_defect0,c[j].moment_defect1);
      for(int side=0;side<2;side++)
        {
          struct rd_tetra_metric *m=side ? nm:om;struct rd_tetra_record *r=side ? fresh:Old;int n=side ? nn:Nold;
          for(int t=0;t<n;t++) if(m[t].negative_interval || m[t].uncertain) invalid_record(&r[t],&m[t],side);
        }
      fflush(Steps);fflush(Cavities);fflush(Invalid);
      mpi_printf("RD-3D-GEOM step=%d time=%.9g tets=%d/%d changed=%d/%d cavities=%d max_vertices=%d inverted_old/new=%d/%d pullback=%d\n",All.NumCurrentTiStep,All.Time,Nold,nn,s.removed,s.inserted,s.cavities,s.max_vertices,s.old_interval_negative,s.new_interval_negative,s.new_pullback_negative);
      free(mass);free(c);free(nm);free(om);free(fresh);free(Old);free(GeomNodes);
    }
  else
    {
      Steps=output("geometry_steps.jsonl","w");Cavities=output("geometry_cavities.csv","w");Invalid=output("geometry_invalid.jsonl","w");
      fprintf(Cavities,"step,time,min_id,vertices,removed,inserted,winding,invalid_old,invalid_new,volume_defect0,volume_defect1,moment_defect0,moment_defect1\n");
    }
  Nnodes=NumGas;GeomNodes=alloc(Nnodes*sizeof(*GeomNodes));
  for(int j=0;j<NumGas;j++) {GeomNodes[j].id=P[j].ID;memcpy(GeomNodes[j].x,P[j].Pos,sizeof(GeomNodes[j].x));}
  qsort(GeomNodes,Nnodes,sizeof(*GeomNodes),nodecmp);
  for(int j=1;j<Nnodes;j++) if(GeomNodes[j].id==GeomNodes[j-1].id) terminate_program("3D geometry diagnostic duplicate primary ID");
  Old=capture(T,0,0,&Nold);OpeningTime=All.Time;Ready=0;
  double coverage=0;
  for(int t=0;t<Nold;t++) coverage+=Old[t].orientation*rd_tetra_signed_volume(Old[t].x);
  double expected=box[0]*box[1]*box[2];
  if(fabs(coverage-expected)>1e-11*expected)
    terminate_program("3D geometry diagnostic physical mesh does not cover periodic box");
}
#endif
