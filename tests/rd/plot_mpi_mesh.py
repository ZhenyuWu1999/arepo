#!/usr/bin/env python3
"""Plot verified native RD geometry; SciPy is used only by the separate audit."""
import argparse
from collections import defaultdict
import json
import os
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR','/private/tmp/arepo_rd_mpi_matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection, LineCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle, Polygon
import numpy as np

COLORS=['#0072B2','#E69F00','#009E73','#CC79A7']
INK='#202C38'


def periodic_shapes(triangles):
    polys=[];ranks=[]
    for t in triangles:
        xy=np.array(t['xy'])/10
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                coords=xy+[dx,dy]
                if np.all(coords.max(axis=0)>0) and np.all(coords.min(axis=0)<1):
                    polys.append(coords);ranks.append(t['owner'])
    return polys,np.array(ranks)


def decorate(ax, title, limits=(0,1,0,1)):
    ax.set_aspect('equal');ax.set_xlim(limits[:2]);ax.set_ylim(limits[2:])
    ax.set_xlabel(r'$x/L$');ax.set_ylabel(r'$y/L$')
    ax.set_title(title,loc='left',fontweight='bold',pad=12)
    ax.tick_params(direction='out',length=3,color=INK)
    for spine in ax.spines.values():spine.set_color('#687581')


def save(fig,out,name):
    for ext in ('pdf','svg','png'):
        fig.savefig(out/(name+'.'+ext),dpi=240,facecolor='white',bbox_inches='tight',pad_inches=.09)
    plt.close(fig)


def plot(root, output_dir=None, thesis=False):
    audit=json.loads((root/'analysis/audit.json').read_text())
    mesh=json.loads((root/'analysis/native_mesh.json').read_text())
    assert audit['scipy_native_keys_identical'] and audit['first_stage']['packet_values_match_exactly']
    nodes=mesh['nodes'];triangles=mesh['triangles']
    xy=np.array([n['xy'] for n in nodes])/10
    node_ranks=np.array([n['rank'] for n in nodes]);ids=np.array([n['id'] for n in nodes])
    polys,ranks=periodic_shapes(triangles)
    out=output_dir or (root/'figures'/'thesis' if thesis else root/'figures')
    out.mkdir(parents=True,exist_ok=True)
    suffix='_thesis_20260915' if thesis else '_20260915'
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.labelsize':11,'axes.titlesize':11,
                         'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','text.color':INK,
                         'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,'savefig.transparent':False})

    fig,axs=plt.subplots(1,2,figsize=(11.5,6.0) if thesis else (11.5,7.0))
    fig.subplots_adjust(left=.065,right=.985,bottom=.21 if thesis else .23,
                        top=.96 if thesis else .865,wspace=.19)
    axs[0].add_collection(PolyCollection(polys,facecolors='none',edgecolors='#B9C0C6',linewidths=.22))
    axs[0].scatter(xy[:,0],xy[:,1],c=[COLORS[r] for r in node_ranks],s=6,zorder=3,linewidths=0)
    axs[1].add_collection(PolyCollection(polys,facecolors=[COLORS[r] for r in ranks],edgecolors='#FFFFFF',linewidths=.14,alpha=.83))
    for ax,title in zip(axs,('(a) Primary node ownership','(b) Triangle computation ownership')):
        decorate(ax,title)
        ax.add_patch(Rectangle((.45,.45),.10,.10,facecolor='none',edgecolor=INK,lw=1.15,ls='--',zorder=5))
        ax.text(.56,.56,'Detail',fontsize=8,color=INK,bbox=dict(facecolor='white',edgecolor='none',pad=1.3),zorder=7)
    handles=[Patch(facecolor=COLORS[r],label=f'Rank {r}: 576 nodes / {audit["first_stage"]["triangle_counts"][str(r)]:,} triangles') for r in range(4)]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.53,.01 if thesis else .048),ncol=2,frameon=False,fontsize=10,columnspacing=3,handlelength=1.4)
    if not thesis:
        fig.text(.065,.987,'Native AREPO-RD triangulation on a glass IC',ha='left',va='top',weight='bold',fontsize=14)
        fig.text(.53,.019,'2,304 nodes  |  4,608 physical triangles  |  4 MPI ranks  |  periodic box',ha='center',fontsize=10)
    save(fig,out,'rd_mpi_glass_rank4_overview'+suffix)

    # A and B are adjacent, physically captured elements at a three-rank junction.
    examples=audit['examples']; important={i for e in examples for i in e['ids']}
    fig=plt.figure(figsize=(6.0,6.55) if thesis else (9.7,7.2))
    ax=fig.add_axes([.13,.19,.83,.78] if thesis else [.075,.30,.52,.60])
    ax.add_collection(PolyCollection(polys,facecolors=[COLORS[r] for r in ranks],edgecolors='#73808B',linewidths=.42,alpha=.22))
    region=(xy[:,0]>.45)&(xy[:,0]<.55)&(xy[:,1]>.45)&(xy[:,1]<.55)
    ax.scatter(xy[region,0],xy[region,1],c=[COLORS[r] for r in node_ranks[region]],s=17,edgecolors='white',linewidths=.5,zorder=4)
    for e in examples:
        coords=np.array(e['xy'])/10
        ax.add_patch(Polygon(coords,facecolor=COLORS[e['owner']],edgecolor=INK,linewidth=1.6,alpha=.90,zorder=5))
        center=coords.mean(axis=0)
        ax.text(*center,e['label'],ha='center',va='center',weight='bold',fontsize=13,zorder=8)
    offsets={1142:(-27,-31),1146:(7,16),1147:(20,-13),1150:(-58,13)}
    for pid in sorted(important):
        index=int(np.flatnonzero(ids==pid)[0]);point=xy[index];rank=node_ranks[index]
        ax.scatter(*point,s=110,color=COLORS[rank],edgecolors=INK,linewidths=1.0,zorder=9)
        ax.annotate(f'ID {pid}\nRank {rank}',point,xytext=offsets[pid],textcoords='offset points',
                    fontsize=9,ha='center',va='center',zorder=10,
                    bbox=dict(boxstyle='round,pad=.25',fc='white',ec='#9AA5AE',lw=.65),
                    arrowprops=dict(arrowstyle='-',color=INK,lw=.8,shrinkA=2,shrinkB=7))
    decorate(ax,'' if thesis else '(a) Native triangles at a rank boundary',(.45,.55,.45,.55))
    ax.set_xticks([.46,.48,.50,.52,.54]);ax.set_yticks([.46,.48,.50,.52,.54])

    if thesis:
        fig.legend(handles=[Line2D([],[],marker='o',color='none',markerfacecolor=COLORS[r],markeredgecolor=INK,label=f'Rank {r}',markersize=7) for r in range(4)],
                   loc='lower center',bbox_to_anchor=(.55,.025),ncol=4,frameon=False,columnspacing=1.5)
        save(fig,out,'rd_mpi_glass_rank4_boundary'+suffix)
        print(out)
        return

    textax=fig.add_axes([.64,.30,.34,.60]);textax.axis('off')
    textax.text(0,1,'(b) Responsibility and routing',weight='bold',fontsize=11,va='top')
    textax.text(0,.90,'Triangle fill: computing rank\nNode colour: primary owning rank',fontsize=10,linespacing=1.6,va='top')
    textax.text(0,.72,'A  |  Vertex ranks: 1, 2, 2',weight='bold',fontsize=11,va='top')
    textax.text(0,.64,'Smallest ID: 1142, owned by rank 1.\nRank 1 computes this triangle.\nThe two rank-2 contributions\nare sent from rank 1 to rank 2.',fontsize=10,va='top',linespacing=1.55)
    textax.text(0,.40,'B  |  Vertex ranks: 1, 2, 3',weight='bold',fontsize=11,va='top')
    textax.text(0,.32,'Smallest ID: 1142, owned by rank 1.\nRank 1 computes this triangle.\nContributions for IDs 1146 and 1150\nare sent to ranks 2 and 3.',fontsize=10,va='top',linespacing=1.55)
    textax.text(0,.085,'Only the instance containing the\nwinning primary node claims the triangle.',fontsize=9,style='italic',va='top',linespacing=1.4)
    fig.text(.075,.975,'Cross-rank triangles: two examples from the native mesh',va='top',weight='bold',fontsize=14)
    fig.legend(handles=[Line2D([],[],marker='o',color='none',markerfacecolor=COLORS[r],markeredgecolor=INK,label=f'Rank {r}',markersize=7) for r in range(4)],
               loc='lower center',bbox_to_anchor=(.5,.175),ncol=4,frameon=False,columnspacing=3)
    fig.text(.075,.117,'Ownership rule: select the smallest ParticleID among the three vertices;',fontsize=10)
    fig.text(.075,.087,'its primary owning rank evaluates the residual and distributes one contribution to each vertex.',fontsize=10)
    fig.text(.075,.037,'Static full-mesh example, equal timesteps. Geometry and MPI packets are captured from the solver.',fontsize=9,color='#50606D')
    save(fig,out,'rd_mpi_glass_rank4_boundary_20260915')
    print(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path)
    p.add_argument('--thesis',action='store_true',help='Compact copies without figure titles or the detail explanation panel.')
    p.add_argument('--output-dir',type=Path,help='Directory for generated PDF, SVG and PNG files.')
    args=p.parse_args()
    plot(args.root.resolve(),args.output_dir.resolve() if args.output_dir else None,args.thesis)
