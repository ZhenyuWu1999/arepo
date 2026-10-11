#include <float.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include "rd_simplex_registry.h"

static long double det(const long double a[3], const long double b[3], const long double c[3])
{
  return a[0] * (b[1]*c[2]-b[2]*c[1]) - a[1] * (b[0]*c[2]-b[2]*c[0]) + a[2] * (b[0]*c[1]-b[1]*c[0]);
}

double rd_tetra_signed_volume(const double x[4][3])
{
  long double e[3][3];
  for(int i=0;i<3;i++) for(int a=0;a<3;a++) e[i][a]=(long double)x[i+1][a]-x[0][a];
  return (double)(det(e[0],e[1],e[2])/6);
}

static double quality(const double x[4][3], double volume)
{
  double area=0;
  for(int i=0;i<4;i++)
    {
      int f[3], k=0;
      for(int j=0;j<4;j++) if(j!=i) f[k++]=j;
      long double a[3],b[3],cross[3];
      for(int d=0;d<3;d++) {a[d]=(long double)x[f[1]][d]-x[f[0]][d]; b[d]=(long double)x[f[2]][d]-x[f[0]][d];}
      for(int d=0;d<3;d++) cross[d]=a[(d+1)%3]*b[(d+2)%3]-a[(d+2)%3]*b[(d+1)%3];
      area+=(double)(sqrtl(cross[0]*cross[0]+cross[1]*cross[1]+cross[2]*cross[2])/2);
    }
  return area>0 ? volume/pow(area,1.5) : 0;
}

void rd_tetra_canonicalize(struct rd_tetra_record *r, const double box[3])
{
  for(int i=1;i<4;i++) for(int j=i;j>0;j--)
    {
      int cmp=(r->id[j]>r->id[j-1])-(r->id[j]<r->id[j-1]);
      for(int a=0;cmp==0 && a<3;a++) cmp=(r->image[j][a]>r->image[j-1][a])-(r->image[j][a]<r->image[j-1][a]);
      if(cmp>=0) break;
      uint64_t id=r->id[j];r->id[j]=r->id[j-1];r->id[j-1]=id;
      for(int a=0;a<3;a++)
        {
          int32_t k=r->image[j][a];r->image[j][a]=r->image[j-1][a];r->image[j-1][a]=k;
          double v=r->x[j][a];r->x[j][a]=r->x[j-1][a];r->x[j-1][a]=v;
          v=r->w[j][a];r->w[j][a]=r->w[j-1][a];r->w[j-1][a]=v;
        }
    }
  int32_t anchor[3]; memcpy(anchor,r->image[0],sizeof(anchor));
  for(int i=0;i<4;i++) for(int a=0;a<3;a++)
    {r->image[i][a]-=anchor[a];r->x[i][a]-=anchor[a]*box[a];}
  r->orientation=rd_tetra_signed_volume(r->x)<0 ? -1 : 1;
}

static int keycmp(const void *a,const void *b)
{
  const struct rd_tetra_record *x=a,*y=b;
  for(int i=0;i<4;i++) if(x->id[i]!=y->id[i]) return x->id[i]<y->id[i] ? -1:1;
  for(int i=0;i<4;i++) for(int d=0;d<3;d++) if(x->image[i][d]!=y->image[i][d]) return x->image[i][d]<y->image[i][d] ? -1:1;
  return 0;
}

int rd_registry_prepare(struct rd_tetra_record *r,int n,int *id_aliases)
{
  *id_aliases=0;
  if(n<0 || (n && !r)) return -1;
  qsort(r,n,sizeof(*r),keycmp);
  for(int i=1;i<n;i++)
    {
      if(keycmp(&r[i-1],&r[i])==0) return -2;
      if(memcmp(r[i-1].id,r[i].id,sizeof(r[i].id))==0) (*id_aliases)++;
    }
  return 0;
}

void rd_tetra_interval(const struct rd_tetra_record *r,double h,int closing,struct rd_tetra_metric *m)
{
  memset(m,0,sizeof(*m));
  long double edge[3][3],delta[3][3],c[4]={0,0,0,0};
  double x0[4][3],xm[4][3],x1[4][3];
  long double span=0;
  for(int i=0;i<4;i++) for(int a=0;a<3;a++)
    {
      x0[i][a]=r->x[i][a]-(closing ? h*r->w[i][a] : 0);
      xm[i][a]=x0[i][a]+h*r->w[i][a]/2;
      x1[i][a]=closing ? r->x[i][a] : x0[i][a]+h*r->w[i][a];
    }
  for(int i=0;i<3;i++) for(int a=0;a<3;a++)
    {
      /* Account for reconstruction error even on arm64, where long double
       * may have no extra mantissa. Differences exclude common translation. */
      edge[i][a]=(long double)x0[i+1][a]-x0[0][a];
      delta[i][a]=h*((long double)r->w[i+1][a]-r->w[0][a]);
      span=fmaxl(span,fabsl(edge[i][a])+fabsl(delta[i][a]));
    }
  for(int mask=0;mask<8;mask++)
    {
      int power=((mask>>0)&1)+((mask>>1)&1)+((mask>>2)&1);
      c[power]+=r->orientation*det(mask&1 ? delta[0]:edge[0],mask&2 ? delta[1]:edge[1],mask&4 ? delta[2]:edge[2])/6;
    }
  long double error=256*DBL_EPSILON*span*span*span;
  m->error=(double)error;
  m->v0=(double)c[0];m->vmid=(double)(c[0]+c[1]/2+c[2]/4+c[3]/8);
  m->v1=(double)(c[0]+c[1]+c[2]+c[3]);
  long double min=c[0],smin=0;
  if(m->v1<min) {min=m->v1;smin=1;}
  long double a=3*c[3],b=2*c[2],d=c[1],roots[2];int nr=0;
  if(a==0) {if(b!=0) roots[nr++]=-d/b;}
  else
    {
      long double disc=b*b-4*a*d;
      /* A nearly repeated stationary point is not dropped silently. */
      long double discerr=64*LDBL_EPSILON*(b*b+fabsl(4*a*d));
      if(disc<0 && disc>=-discerr) disc=0;
      if(disc>=0)
        {
          long double q=-.5L*(b+copysignl(sqrtl(disc),b));
          if(q==0) roots[nr++]=-b/(2*a);
          else {roots[nr++]=q/a;roots[nr++]=d/q;}
        }
    }
  for(int i=0;i<nr;i++) if(roots[i]>0 && roots[i]<1)
    {
      long double s=roots[i],v=((c[3]*s+c[2])*s+c[1])*s+c[0];
      if(v<min) {min=v;smin=s;}
    }
  m->vmin=(double)min;m->smin=(double)smin;
  m->negative0=c[0]<-error;m->negative1=m->v1<-error;m->negative_interval=min<-error;
  m->uncertain=fabsl(min)<=error;
  m->q0=quality(x0,m->v0);m->qmid=quality(xm,m->vmid);m->q1=quality(x1,m->v1);
  m->ratio=m->v1>0 ? m->v0/m->v1 : NAN;
  double scale=fmax(fmax(fabs(m->v0),fabs(m->v1)),(double)(span*span*span));
  if(scale==0) scale=DBL_MIN;
  m->midpoint_defect=(double)(c[3]/4)/scale;
  for(int i=0;i<4;i++)
    {
      int f[3],j=0;for(int k=0;k<4;k++) if(k!=i) f[j++]=k;
      long double a[3],b[3],norm2=0,maxarea=0;
      for(int k=0;k<3;k++) {a[k]=h*((long double)r->w[f[1]][k]-r->w[f[0]][k]);b[k]=h*((long double)r->w[f[2]][k]-r->w[f[0]][k]);}
      for(int k=0;k<3;k++) {long double q=a[(k+1)%3]*b[(k+2)%3]-a[(k+2)%3]*b[(k+1)%3];norm2+=q*q;}
      const double (*levels[3])[3]={x0,xm,x1};
      for(int t=0;t<3;t++)
        {
          long double u[3],v[3],area2=0;
          for(int k=0;k<3;k++) {u[k]=(long double)levels[t][f[1]][k]-levels[t][f[0]][k];v[k]=(long double)levels[t][f[2]][k]-levels[t][f[0]][k];}
          for(int k=0;k<3;k++) {long double q=u[(k+1)%3]*v[(k+2)%3]-u[(k+2)%3]*v[(k+1)%3];area2+=q*q;}
          maxarea=fmaxl(maxarea,sqrtl(area2)/2);
        }
      if(maxarea>0) m->mean_normal_correction=fmax(m->mean_normal_correction,(double)(sqrtl(norm2)/(24*maxarea)));
    }
  /* Independent face integral for GCL, not the same polynomial derivative. */
  long double swept=0;
  for(int t=0;t<2;t++)
    {
      long double s=.5L+(t ? 1:-1)/(2*sqrtl(3));
      long double x[4][3];
      for(int i=0;i<4;i++) for(int k=0;k<3;k++) x[i][k]=(long double)x0[i][k]+s*h*r->w[i][k];
      for(int i=0;i<4;i++)
        {
          int f[3],j=0;for(int k=0;k<4;k++) if(k!=i) f[j++]=k;
          long double u[3],v[3],w[3];
          for(int k=0;k<3;k++)
            {u[k]=x[f[1]][k]-x[f[0]][k];v[k]=x[f[2]][k]-x[f[0]][k];w[k]=(r->w[f[0]][k]+r->w[f[1]][k]+r->w[f[2]][k])/3;}
          for(int k=0;k<3;k++) swept-=h*.5L*r->orientation*(i%2 ? 1:-1)*(u[(k+1)%3]*v[(k+2)%3]-u[(k+2)%3]*v[(k+1)%3])/2*w[k];
        }
    }
  m->gcl_defect=(double)(swept-(c[1]+c[2]+c[3]))/scale;
}

static int idcmp(const void *a,const void *b)
{uint64_t x=*(const uint64_t*)a,y=*(const uint64_t*)b;return (x>y)-(x<y);}
static int lookup(const uint64_t *ids,int n,uint64_t id)
{int lo=0,hi=n;while(lo<hi) {int mid=lo+(hi-lo)/2;if(ids[mid]<id) lo=mid+1;else hi=mid;}return lo;}

struct uf_node {int parent,size,used,winding,pot[3];};
static int find(struct uf_node *u,int i,int p[3])
{
  if(u[i].parent==i) {p[0]=p[1]=p[2]=0;return i;}
  int q[3],root=find(u,u[i].parent,q);
  for(int a=0;a<3;a++) {u[i].pot[a]+=q[a];p[a]=u[i].pot[a];}
  u[i].parent=root;return root;
}
static void join(struct uf_node *u,int i,int j,const int offset[3])
{
  int pi[3],pj[3],ri=find(u,i,pi),rj=find(u,j,pj);
  if(ri==rj)
    {for(int a=0;a<3;a++) if(pj[a]-pi[a]!=offset[a]) u[ri].winding=1;return;}
  int rel[3];for(int a=0;a<3;a++) rel[a]=offset[a]+pi[a]-pj[a];
  if(u[ri].size<u[rj].size)
    {u[ri].parent=rj;for(int a=0;a<3;a++) u[ri].pot[a]=-rel[a];u[rj].size+=u[ri].size;u[rj].winding|=u[ri].winding;}
  else
    {u[rj].parent=ri;for(int a=0;a<3;a++) u[rj].pot[a]=rel[a];u[ri].size+=u[rj].size;u[ri].winding|=u[rj].winding;}
}

int rd_registry_compare(const struct rd_tetra_record *old,int no,const struct rd_tetra_record *fresh,int nn,
                        double h,const double box[3],struct rd_registry_summary *s,
                        struct rd_tetra_metric *om,struct rd_tetra_metric *nm,struct rd_cavity_metric *cav)
{
  if(no<=0 || nn<=0 || !(h>0) || !isfinite(h)) return -1;
  memset(s,0,sizeof(*s));s->old_count=no;s->new_count=nn;
  s->min_old_interval=s->min_new_interval=s->min_pullback_ratio=s->min_q0=s->min_qmid=s->min_q1=DBL_MAX;
  for(int side=0;side<2;side++)
    {
      const struct rd_tetra_record *r=side ? fresh:old;int n=side ? nn:no;
      struct rd_tetra_metric *m=side ? nm:om;
      for(int i=0;i<n;i++)
        {
          if(i && keycmp(&r[i-1],&r[i])>=0) return -2;
          if(i && !memcmp(r[i-1].id,r[i].id,sizeof(r[i].id))) {if(side) s->id_alias_new++;else s->id_alias_old++;}
          rd_tetra_interval(&r[i],h,side,&m[i]);
          s->max_midpoint_gcl_defect=fmax(s->max_midpoint_gcl_defect,fabs(m[i].midpoint_defect));
          s->max_gauss_gcl_defect=fmax(s->max_gauss_gcl_defect,fabs(m[i].gcl_defect));
          s->max_mean_normal_correction=fmax(s->max_mean_normal_correction,m[i].mean_normal_correction);
          if(side)
            {
              s->coverage1+=m[i].v1;s->new_pullback_coverage+=m[i].v0;
              s->new_pullback_negative+=m[i].negative0;s->new_mid_negative+=m[i].vmid < -m[i].error;
              s->new_interval_negative+=m[i].negative_interval;s->new_uncertain+=m[i].uncertain;
              s->min_new_interval=fmin(s->min_new_interval,m[i].vmin);s->min_pullback_ratio=fmin(s->min_pullback_ratio,m[i].ratio);
              s->min_q1=fmin(s->min_q1,m[i].q1);s->min_qmid=fmin(s->min_qmid,m[i].qmid);
            }
          else
            {
              s->coverage0+=m[i].v0;s->old_forward_coverage+=m[i].v1;
              s->old_endpoint_negative+=m[i].negative1;s->old_interval_negative+=m[i].negative_interval;s->old_uncertain+=m[i].uncertain;
              s->min_old_interval=fmin(s->min_old_interval,m[i].vmin);s->min_q0=fmin(s->min_q0,m[i].q0);
            }
        }
    }
  int i=0,j=0;
  while(i<no || j<nn)
    {
      int cmp=i==no ? 1:j==nn ? -1:keycmp(&old[i],&fresh[j]);
      if(cmp<0) {om[i++].changed=1;s->removed++;}
      else if(cmp>0) {nm[j++].changed=1;s->inserted++;}
      else
        {
          /* Unchanged key must denote the same linear trajectory, including
           * periodic image, not merely the same IDs. */
          for(int v=0;v<4;v++) for(int a=0;a<3;a++)
            if(fabs(old[i].x[v][a]+h*old[i].w[v][a]-fresh[j].x[v][a])>4096*DBL_EPSILON*box[a] ||
               old[i].w[v][a]!=fresh[j].w[v][a]) return -3;
          /* A key alone is an unoriented simplex. If its orientation reverses,
           * it cannot cancel between the two signed triangulation chains. */
          if(old[i].orientation!=fresh[j].orientation)
            {om[i].changed=nm[j].changed=1;s->removed++;s->inserted++;s->reversed_common++;}
          i++;j++;
        }
    }
  int capacity=4*(s->removed+s->inserted);
  if(!capacity) return 0;
  uint64_t *ids=malloc((size_t)capacity*sizeof(*ids));
  if(!ids) return -4;
  int n=0;
  for(int side=0;side<2;side++)
    {
      const struct rd_tetra_record *r=side ? fresh:old;const struct rd_tetra_metric *m=side ? nm:om;int nt=side ? nn:no;
      for(int t=0;t<nt;t++) if(m[t].changed) for(int v=0;v<4;v++) ids[n++]=r[t].id[v];
    }
  qsort(ids,n,sizeof(*ids),idcmp);int unique=0;for(int k=0;k<n;k++) if(k==0 || ids[k]!=ids[k-1]) ids[unique++]=ids[k];n=unique;
  struct uf_node *u=calloc(n,sizeof(*u));int *label=malloc((size_t)n*sizeof(*label));
  /* Accumulate signed volumes/moments on both common time levels. */
  double (*acc)[10]=calloc(n,sizeof(*acc));
  if(!u || !label || !acc) {free(acc);free(label);free(u);free(ids);return -4;}
  for(int k=0;k<n;k++) {u[k].parent=k;u[k].size=1;label[k]=-1;}
  for(int side=0;side<2;side++)
    {
      const struct rd_tetra_record *r=side ? fresh:old;const struct rd_tetra_metric *m=side ? nm:om;int nt=side ? nn:no;
      for(int t=0;t<nt;t++) if(m[t].changed)
        {
          int a=lookup(ids,n,r[t].id[0]);
          for(int v=1;v<4;v++) {int offset[3];for(int d=0;d<3;d++) offset[d]=r[t].image[v][d];join(u,a,lookup(ids,n,r[t].id[v]),offset);}
        }
    }
  for(int k=0;k<n;k++)
    {
      int p[3],root=find(u,k,p);
      if(label[root]<0) {label[root]=s->cavities;memset(&cav[s->cavities],0,sizeof(*cav));cav[s->cavities++].min_id=ids[k];}
      struct rd_cavity_metric *c=&cav[label[root]];c->vertices++;c->winding=u[root].winding;
    }
  s->changed_vertices=n;
  for(int side=0;side<2;side++)
    {
      const struct rd_tetra_record *r=side ? fresh:old;const struct rd_tetra_metric *m=side ? nm:om;int nt=side ? nn:no;
      for(int t=0;t<nt;t++) if(m[t].changed)
        {
          int p[3],root=find(u,lookup(ids,n,r[t].id[0]),p),k=label[root];
          struct rd_cavity_metric *c=&cav[k];if(side) {c->inserted++;c->invalid_new+=m[t].negative_interval || m[t].uncertain;}else {c->removed++;c->invalid_old+=m[t].negative_interval || m[t].uncertain;}
          double sign=side ? 1:-1;
          acc[k][0]+=sign*m[t].v0;acc[k][1]+=sign*m[t].v1;
          acc[k][8]+=fabs(m[t].v0);acc[k][9]+=fabs(m[t].v1);
          for(int a=0;a<3;a++)
            {
              double center=0,wbar=0;for(int v=0;v<4;v++) {center+=r[t].x[v][a]/4;wbar+=r[t].w[v][a]/4;}
              center+=box[a]*p[a];
              double center0=center-(side ? h*wbar:0),center1=center+(side ? 0:h*wbar);
              acc[k][2+a]+=sign*m[t].v0*center0;acc[k][5+a]+=sign*m[t].v1*center1;
            }
        }
    }
  double boxscale=fmax(box[0],fmax(box[1],box[2]));
  for(int k=0;k<s->cavities;k++)
    {
      struct rd_cavity_metric *c=&cav[k];s->max_vertices=c->vertices>s->max_vertices ? c->vertices:s->max_vertices;s->winding_cavities+=c->winding;
      c->volume_defect0=fabs(acc[k][0])/fmax(acc[k][8],DBL_MIN);c->volume_defect1=fabs(acc[k][1])/fmax(acc[k][9],DBL_MIN);
      c->moment_defect0=c->moment_defect1=NAN;
      if(!c->winding)
        {
          c->moment_defect0=c->moment_defect1=0;
          for(int a=0;a<3;a++) {c->moment_defect0=fmax(c->moment_defect0,fabs(acc[k][2+a])/fmax(acc[k][8]*boxscale,DBL_MIN));c->moment_defect1=fmax(c->moment_defect1,fabs(acc[k][5+a])/fmax(acc[k][9]*boxscale,DBL_MIN));}
          s->max_cavity_moment_defect=fmax(s->max_cavity_moment_defect,fmax(c->moment_defect0,c->moment_defect1));
        }
      s->max_cavity_volume_defect=fmax(s->max_cavity_volume_defect,fmax(c->volume_defect0,c->volume_defect1));
    }
  free(acc);free(label);free(u);free(ids);return 0;
}
