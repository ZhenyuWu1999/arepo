#!/usr/bin/env python3
"""Independent periodic topology/graph audit and scientific plots for the M2 pilot."""
import argparse
import ctypes as C
from itertools import product
import json
from pathlib import Path
import sys
import h5py
import numpy as np
from scipy.spatial import Delaunay
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from test_simplex_registry import Record, independent_interval

def read_pair(path):
    with path.open('rb') as f:
        no,nn,size=np.frombuffer(f.read(12),dtype='<u4');h=float(np.frombuffer(f.read(8),dtype='<f8')[0]);assert size==C.sizeof(Record)
        old=(Record*int(no)).from_buffer_copy(f.read(int(no*size)));new=(Record*int(nn)).from_buffer_copy(f.read(int(nn*size)));assert not f.read(1)
    return old,new,h

def key(r):
    return tuple(r.id),tuple(np.ctypeslib.as_array(r.image).ravel())

def graph_audit(old,new):
    a={key(r):r for r in old};b={key(r):r for r in new};common=a.keys()&b.keys()
    changed=(a.keys()^b.keys())|{k for k in common if a[k].orientation!=b[k].orientation}
    graph={};sides=[]
    for side,records in enumerate([a,b]):
        for k,r in records.items():
            if k not in changed: continue
            sides.append((side,r));images=np.ctypeslib.as_array(r.image)
            for v in range(1,4):
                u,t=int(r.id[0]),int(r.id[v]);d=tuple(int(x) for x in images[v])
                graph.setdefault(u,[]).append((t,d));graph.setdefault(t,[]).append((u,tuple(-x for x in d)))
    remaining=set(graph);components=[];labels={}
    while remaining:
        anchor=min(remaining);potential={anchor:(0,0,0)};queue=[anchor];winding=False
        while queue:
            u=queue.pop()
            for v,d in graph[u]:
                p=tuple(x+y for x,y in zip(potential[u],d))
                if v in potential: winding|=potential[v]!=p
                else: potential[v]=p;queue.append(v)
        remaining-=potential.keys();label=len(components)
        for v in potential: labels[v]=label
        components.append(dict(min_id=anchor,vertices=len(potential),winding=int(winding),removed=0,inserted=0))
    for side,r in sides: components[labels[int(r.id[0])]][['removed','inserted'][side]]+=1
    return sorted(components,key=lambda c:c['min_id'])

def periodic_keys(x):
    tiles=np.array(list(product([-1,0,1],repeat=3)));n=len(x)
    coords=(x[None,:,:]+tiles[:,None,:]).reshape(-1,3)
    triangulation=Delaunay(coords)
    simplices=triangulation.simplices
    ids=simplices%n+1;images=tiles[simplices//n]
    order=np.argsort(ids,axis=1);ids=np.take_along_axis(ids,order,axis=1);images=np.take_along_axis(images,order[:,:,None],axis=1)
    keep=np.all(images[:,0,:]==0,axis=1);ids,images=ids[keep],images[keep]
    # Every selected central-anchor star is interior to the padded cube.
    return {(tuple(i),tuple(m.ravel())) for i,m in zip(ids,images)}

def main(root):
    dest=root/'analysis_extra';dest.mkdir(exist_ok=False);audits=[]
    for name in ['rest_random_cfl0.1_diag','rest_random_cfl0.3_diag','advection_cfl0.1_diag','shear_cfl0.3_diag']:
        folder=root/'runs'/name;old,new,h=read_pair(folder/'output/geometry_first_pair.bin')
        components=graph_audit(old,new)
        import csv
        with (folder/'output/geometry_cavities.csv').open() as f: rows=list(csv.DictReader(f))
        first_step=json.loads((folder/'output/geometry_steps.jsonl').read_text().splitlines()[0])['step']
        expected=[{k:int(c[k]) for k in ['min_id','vertices','winding','removed','inserted']} for c in rows if int(c['step'])==first_step]
        assert sorted(expected,key=lambda c:c['min_id'])==components
        audit=dict(case=name,graph_components=len(components),winding=sum(c['winding'] for c in components))
        if name in ['rest_random_cfl0.1_diag','advection_cfl0.1_diag']:
            n=4096;x=np.empty((n,3));w=np.empty((n,3));seen=set()
            for r in old:
                for i in range(4):
                    j=int(r.id[i])-1;x[j]=np.array(r.x[i])-np.array(r.image[i]);w[j]=r.w[i];seen.add(j)
            assert len(seen)==n
            for label,records,positions in [('old',old,x),('new',new,(x+h*w)%1)]:
                actual={key(r) for r in records}
                # Closing native keys use opening primary images. Convert the
                # independently reconstructed closing keys to that convention.
                independent=periodic_keys(positions)
                if label=='new':
                    wraps=np.floor(x+h*w).astype(int);converted=set()
                    for ids,flat in independent:
                        images=np.array(flat).reshape(4,3)-wraps[np.array(ids)-1];images-=images[0]
                        converted.add((ids,tuple(images.ravel())))
                    independent=converted
                assert actual==independent,(name,label,len(actual-independent),len(independent-actual))
                audit[label+'_periodic_keys']=len(actual)
        audits.append(audit);print(audit,flush=True)
    results=json.loads((root/'results.json').read_text());diag=[z for z in results if '_diag' in z['case'] and not z['case'].startswith('probe')]
    problems=['rest_random','advection','gresho','shear','sedov'];labels=['Rest/random','Advection','Gresho','Shear','Sedov'];colors=['#2166ac','#d6604d']
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for j,cfl in enumerate([.1,.3]):
        rows=[next(z for z in diag if z['case']==f'{p}_cfl{cfl}_diag') for p in problems];xx=np.arange(5)+(j-.5)*.35
        axes[0].bar(xx,[z['max_vertices'] for z in rows],width=.33,label=f'CFL {cfl}',color=colors[j]);axes[1].bar(xx,[z['new_pullback_negative'] for z in rows],width=.33,color=colors[j])
    axes[0].set_yscale('symlog',linthresh=5);axes[0].axhline(40.96,color='gray',ls='--',label='1% of nodes')
    axes[0].set_ylabel('Largest connected cavity (vertices)');axes[1].set_ylabel('New-tetra pullback inversions (occurrences)')
    for ax in axes: ax.set_xticks(np.arange(5),labels,rotation=15);ax.grid(axis='y',alpha=.2)
    axes[0].legend();fig.suptitle('Native 16³ FV trajectories: short diagnostic runs')
    fig.savefig(dest/'geometry_overview.png',dpi=180);fig.savefig(dest/'geometry_overview.pdf');plt.close(fig)
    events=[]
    for z in diag:
        for line in (root/'runs'/z['case']/'output/geometry_invalid.jsonl').read_text().splitlines():
            e=json.loads(line)
            if not e['closing']: continue
            r=Record();r.orientation=e['orientation'];np.ctypeslib.as_array(r.x)[:]=e['x'];np.ctypeslib.as_array(r.w)[:]=e['w']
            coeff,minimum,where=independent_interval(r,e['h'],1);events.append((coeff[0]/coeff.sum(),z['case'],e,coeff))
    ratio,name,e,coeff=min(events,key=lambda row:row[0]);s=np.linspace(0,1,501);curve=np.polynomial.polynomial.polyval(s,coeff)/coeff.sum()
    fig,ax=plt.subplots(figsize=(7,4),layout='constrained');ax.plot(s,curve,color=colors[1],lw=2);ax.axhline(0,color='black',lw=.8);ax.scatter([0,.5,1],np.polynomial.polynomial.polyval([0,.5,1],coeff)/coeff.sum(),color=colors[0],zorder=3)
    ax.set(xlabel='Normalized step time s',ylabel='Signed V(s) / V(new)',title=f"{name}, step {e['step']}: new tetra pulled back");ax.text(.04,.92,f'V(old)/V(new) = {ratio:.3f}',transform=ax.transAxes);ax.grid(alpha=.2)
    fig.savefig(dest/'pullback_example.png',dpi=180);fig.savefig(dest/'pullback_example.pdf');plt.close(fig)
    (dest/'audit.json').write_text(json.dumps(dict(audits=audits,worst_event=dict(case=name,ratio=ratio,event=e)),indent=2)+'\n')
if __name__=='__main__': main(Path(sys.argv[1]).resolve())
