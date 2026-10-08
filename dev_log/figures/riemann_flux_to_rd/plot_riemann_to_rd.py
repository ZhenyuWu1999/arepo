"""Original vector schematic of a median-dual Riemann-flux RD construction.
Static spatial operator, unreconstructed nodal states. No solver runs or thesis edits.
"""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, FancyArrowPatch

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'output' / 'pdf'
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Serif', 'font.size':15,
    'mathtext.fontset':'stix', 'pdf.fonttype':42, 'ps.fonttype':42,
    'svg.fonttype':'none', 'savefig.facecolor':'white'})
INK='#272c34'; MUTED='#68717b'; BLUE='#236ea0'; ORANGE='#b85822'; GREEN='#398567'; PURPLE='#79549b'
P=np.array([[-1.5,0.0],[1.6,0.28],[0.10,2.82]])
G=P.mean(axis=0)
M={(i,j):(P[i]+P[j])/2 for i,j in [(0,1),(1,2),(0,2)]}
# Inward, edge-length-weighted opposite-edge normals for the CCW triangle.
n=np.empty((3,2))
for i in range(3):
    e=P[(i+2)%3]-P[(i+1)%3]
    n[i]=[-e[1],e[0]]
nu={(i,j):(n[j]-n[i])/6 for i,j in M}
assert np.allclose(n.sum(axis=0),0)
for (i,j),v in nu.items():
    assert abs(np.dot(v,G-M[i,j]))<1.e-14
    assert np.dot(v,P[j]-P[i])>0
    assert abs(np.linalg.norm(v)-np.linalg.norm(G-M[i,j]))<1.e-14
for i in range(3):
    assert np.allclose(sum((n[j]-n[i])/6 for j in range(3) if j!=i),-n[i]/2)
# Arbitrary vector-valued nodal fluxes and conservative pair fluxes check the identity.
rng=np.random.default_rng(9812)
F=rng.normal(size=(3,4,2)); phi=np.zeros((3,4)); pair={}
for (i,j),v in nu.items():
    H=rng.normal(size=4)
    di=H-F[i]@v; dj=F[j]@v-H
    phi[i]+=di; phi[j]+=dj
    assert np.allclose(di+dj,(F[j]-F[i])@v)
err=float(np.max(np.abs(phi.sum(axis=0)-0.5*np.einsum('imd,id->m',F,n))))
assert err<1.e-13
(ROOT/'geometry_check.json').write_text(json.dumps({'vertices':P.tolist(),'inward_scaled_normals':n.tolist(),'pair_normals':{str(k):v.tolist() for k,v in nu.items()},'residual_sum_max_abs_error':err},indent=2)+'\n')

fig=plt.figure(figsize=(13.2,8.5))
fig.text(.5,.966,'From a Riemann flux to residual distribution',ha='center',va='top',fontsize=21,color=INK)
axs=[fig.add_axes([.038,.395,.438,.485]),fig.add_axes([.525,.395,.438,.485])]

def arrow(ax,start,end,color=INK,lw=1.65,rad=0.,scale=15,alpha=1):
    a=FancyArrowPatch(start,end,arrowstyle='-|>',mutation_scale=scale,
        linewidth=lw,color=color,connectionstyle=f'arc3,rad={rad}',alpha=alpha)
    ax.add_patch(a)
    return a

def base(ax,labels=True):
    ax.set_xlim(-2.03,2.12); ax.set_ylim(-.6,3.16); ax.set_aspect('equal');ax.axis('off')
    for i,c in enumerate([BLUE,ORANGE,GREEN]):
        j=(i+1)%3;k=(i+2)%3
        poly=np.array([P[i],(P[i]+P[j])/2,G,(P[i]+P[k])/2])
        ax.add_patch(Polygon(poly,facecolor=c,alpha=.09,edgecolor='none'))
    ax.add_patch(Polygon(P,fill=False,edgecolor=INK,linewidth=1.6,joinstyle='round'))
    for key,mid in M.items():
        ax.plot([mid[0],G[0]],[mid[1],G[1]],color=MUTED,lw=1.25,ls=(0,(3,3)))
    for i,c in enumerate([BLUE,ORANGE,GREEN]):
        ax.plot(*P[i],'o',ms=6.8,mec=c,mfc='white',mew=1.5,zorder=5)
    if labels:
        for i,(dx,dy) in enumerate([(-.10,-.24),(.06,-.25),(0,.20)]):
            ax.text(*(P[i]+[dx,dy]),[r'$i:\,\mathbf{U}_i$',r'$j:\,\mathbf{U}_j$',r'$k:\,\mathbf{U}_k$'][i],ha='center',va='center',fontsize=17,color=[BLUE,ORANGE,GREEN][i])

ax=axs[0];base(ax)
ax.text(.5,1.025,'(a) Evaluate the numerical flux',transform=ax.transAxes,ha='center',fontsize=16,color=INK)
mid=M[0,1]; ax.plot([mid[0],G[0]],[mid[1],G[1]],color=PURPLE,lw=3.4,zorder=3)
for point,lab,off in [(G,'$G$',[-.20,.12]),(mid,'$m_{ij}$',[-.06,-.25])]:
    ax.plot(*point,'o',color=INK,ms=3.8,zorder=4)
    ax.text(*(point+off),lab,ha='center',fontsize=15,color=INK)
ax.text(-.82,.72,r'$S_i\cap T$',color=BLUE,ha='center',fontsize=16)
ax.text(.96,.93,r'$S_j\cap T$',color=ORANGE,ha='center',fontsize=16)
ax.text(.10,2.08,r'$S_k\cap T$',color=GREEN,ha='center',fontsize=16)
c=mid+.50*(G-mid); d=nu[0,1]/np.linalg.norm(nu[0,1])
arrow(ax,c-.40*d,c+.55*d,color=PURPLE,lw=2.0,scale=17)
ax.text(c[0]+.39,c[1]-.26,r'$\boldsymbol{\nu}_{ij}$',fontsize=20,color=PURPLE)
ax.text(c[0]+.40,c[1]+.19,r'$H_{ij}$',fontsize=18,color=PURPLE)
ax.text(-.22,.81,r'$\Gamma_{ij}$',color=PURPLE,fontsize=16,ha='right')

ax=axs[1];base(ax,False)
ax.text(.5,1.025,'(b) Assign fluctuations to the vertices',transform=ax.transAxes,ha='center',fontsize=16,color=INK)
# Arrows denote algebraic assignment; their orientation does not encode a flux sign.
for (i,j),mid in M.items():
    origin=.53*mid+.47*G
    for q in (i,j):
        target=.87*P[q]+.13*G
        active=(i,j)==(0,1)
        color=([BLUE,ORANGE,GREEN][q] if active else '#8e979f')
        arrow(ax,origin,target,color=color,lw=(1.9 if active else 1.05),rad=(.20 if q==i else -.20),scale=(16 if active else 11),alpha=(1 if active else .50))
    if (i,j)==(0,1):
        ax.plot([mid[0],G[0]],[mid[1],G[1]],color=PURPLE,lw=3.4,zorder=3)
        ax.plot(*origin,'o',ms=4.4,color=PURPLE,zorder=4)
ax.text(-.70,.20,r'$D_{ij}^{(i)}$',color=BLUE,fontsize=20,ha='center')
ax.text(.80,.36,r'$D_{ij}^{(j)}$',color=ORANGE,fontsize=20,ha='center')
for q,(dx,dy) in enumerate([(-.05,-.30),(.06,-.30),(.01,.21)]):
    ax.text(*(P[q]+[dx,dy]),[r'$\phi_i^T$',r'$\phi_j^T$',r'$\phi_k^T$'][q],ha='center',va='center',fontsize=23,color=[BLUE,ORANGE,GREEN][q])
ax.text(.0,1.94,'All three pairs\ncontribute',ha='center',va='center',fontsize=12.5,color=MUTED,linespacing=1.5)

fig.text(.253,.405,r'$H_{ij}=|\Gamma_{ij}|\,\widehat f_{\mathbf{\hat n}_{ij}}(\mathbf{U}_i,\mathbf{U}_j)$',ha='center',va='top',fontsize=19,color=PURPLE)
fig.text(.253,.348,r'$\boldsymbol{\nu}_{ij}=|\Gamma_{ij}|\,\mathbf{\hat n}_{ij}=(\mathbf{n}_j-\mathbf{n}_i)/6$',ha='center',va='top',fontsize=17,color=INK)
fig.text(.253,.301,'One normal Riemann problem: HLLC, HLL, Roe, ...',ha='center',va='top',fontsize=12,color=MUTED)
fig.text(.746,.405,r'$D_{ij}^{(i)}=H_{ij}-\mathbf{F}_i\!\cdot\!\boldsymbol{\nu}_{ij}$',ha='center',va='top',fontsize=19,color=BLUE)
fig.text(.746,.348,r'$D_{ij}^{(j)}=\mathbf{F}_j\!\cdot\!\boldsymbol{\nu}_{ij}-H_{ij}$',ha='center',va='top',fontsize=19,color=ORANGE)
fig.text(.746,.281,r'$\phi_i^T=\sum_{j\ne i}D_{ij}^{(i)}$',ha='center',va='center',fontsize=18,color=INK)

fig.add_artist(plt.Line2D([.045,.955],[.245,.245],transform=fig.transFigure,color='#c8ccd1',lw=.8))
fig.text(.5,.213,r'$D_{ij}^{(i)}+D_{ij}^{(j)}=(\mathbf{F}_j-\mathbf{F}_i)\cdot\boldsymbol{\nu}_{ij}$',ha='center',va='center',fontsize=20,color=INK)
fig.text(.5,.151,r'$\Longrightarrow\qquad \phi_i^T+\phi_j^T+\phi_k^T=\frac{1}{2}\sum_{a\in T}\mathbf{F}_a\cdot\mathbf{n}_a=\Phi^T$',ha='center',va='center',fontsize=22,color=INK)
fig.text(.5,.090,'Pairwise numerical fluxes cancel; the element residual is conserved.',ha='center',va='center',fontsize=13,color=MUTED)
fig.text(.5,.049,r'$\mathbf{F}_a=\mathbf{F}(\mathbf{U}_a)$;  $\mathbf{n}_a$: inward normal to the opposite edge, scaled by edge length.',ha='center',va='center',fontsize=11.5,color=MUTED)
fig.text(.5,.021,'Static spatial construction with interpolated nodal fluxes. Arrows in (b) denote assignment, not fluctuation signs.',ha='center',va='center',fontsize=11,color=MUTED)
for ext in ('pdf','png','svg'):
    fig.savefig(OUT/f'riemann_flux_to_rd.{ext}',dpi=200,bbox_inches=None)
plt.close(fig)
print(json.dumps({'outputs':[str(OUT/f'riemann_flux_to_rd.{ext}') for ext in ('pdf','png','svg')],'algebra_error':err}))
