"""Extract plotted coordinates from the primary Figure 20 SVG, not raw data."""
import csv
import hashlib
import json
from pathlib import Path
import os
import re
import xml.etree.ElementTree as ET

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(os.environ['RD_BLOB_AUDIT_ROOT']).resolve();OUT=ROOT/'plots'
svg=ROOT/'reference_cloudMass.svg'
tree=ET.parse(svg).getroot();ns={'s':'http://www.w3.org/2000/svg'}
source=next(p for p in tree.findall('.//s:path',ns) if p.get('stroke')=='#d62728' and len(p.get('d',''))>150)
d=source.get('d');before,after=d.split('H',1)
numbers=lambda s:np.array([float(x) for x in re.findall(r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?',s)])
xy=numbers(before).reshape(-1,2)
xy=np.vstack((xy,np.column_stack((numbers(after),np.repeat(xy[-1,1],len(numbers(after)))))))
# Tick calibration checked against the displayed primary figure: x=0,.5;
# y=0,1. The common SVG y flip cancels in this affine calibration.
t=(xy[:,0]-55.77597)/(2*(103.87942-55.77597))
mass=(xy[:,1]-53.586877)/(280.38688-53.586877)
with (OUT/'morton_fig20_N32_vector_trace.csv').open('x',newline='') as f:
    writer=csv.writer(f);writer.writerow(['t_over_tKH_as_published','cloud_fraction_from_vector_trace'])
    writer.writerows(zip(t,mass))
rows=list(csv.DictReader((OUT/'N_equal_np8_thresholds.csv').open()))
ct=np.array([float(r['tau'])/1.6 for r in rows]);cm=np.array([float(r['M64_T9']) for r in rows]);cm/=cm[0]
levels=np.linspace(.05,.95,19)
reference_time=np.interp(levels,mass[::-1],t[::-1])
current_time=np.interp(levels,cm[::-1],ct[::-1])
factor=np.dot(current_time,reference_time)/np.dot(current_time,current_time)
rms=float(np.sqrt(np.mean((reference_time-factor*current_time)**2)))
half=float(np.interp(.5,mass[::-1],t[::-1]))
result=dict(source_url='https://arxiv.org/html/2204.01757v2/cloudMass.svg',
    source_sha256=hashlib.sha256(svg.read_bytes()).hexdigest(),
    extraction='red solid N=32^3 vector path; axis ticks calibrated; not original snapshot data',
    reference_half_time_published_tKH=half,current_half_time_tKH=float(np.interp(.5,cm[::-1],ct[::-1])),
    empirical_time_stretch= float(factor),fit_mass_levels=levels.tolist(),
    reference_time_at_levels=reference_time.tolist(),current_time_at_levels=current_time.tolist(),
    fit_RMS_time_residual_tKH=rms,
    caution='A fitted time stretch is a shape comparison, not evidence for a valid alternative time unit or a correction to the paper.')
(OUT/'published_curve_comparison.json').write_text(json.dumps(result,indent=2)+'\n')
fig,axes=plt.subplots(1,2,figsize=(11.5,4.5),layout='constrained')
for ax in axes:
    ax.plot(ct,cm,color='#2468a0',lw=2,label='COSMA N/RK2, actual time / stated $t_{KH}$')
    ax.set(ylim=(-.02,1.04),ylabel=r'$M_{\rm cloud}/M_{\rm cloud,0}$')
axes[0].plot(t,mass,color='#c0392b',lw=2,label='Morton Fig. 20: N1, 32³ (SVG trace)')
axes[0].set(xlabel=r'$t/t_{\rm KH}$, using the published definition',xlim=(0,2.))
axes[0].set_title('Literal published time convention')
axes[1].plot(t/factor,mass,color='#c0392b',lw=2,label=f'Reference time divided by fitted {factor:.3f}')
axes[1].set(xlabel='Displayed time coordinate',xlim=(0,.95))
axes[1].set_title('Curve-shape diagnostic only')
axes[1].text(.97,.65,'Empirical rescaling\nNot a validated time conversion',ha='right',
             transform=axes[1].transAxes,fontsize=9,color='.35')
for ax in axes:ax.legend(frameon=False,fontsize=8,loc='upper right')
for ext in ['png','svg']:fig.savefig(OUT/f'published_curve_comparison.{ext}',dpi=190)
plt.close(fig)
print(json.dumps(result,indent=2))
