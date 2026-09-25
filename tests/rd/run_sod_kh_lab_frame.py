#!/usr/bin/env python3
"""Lab-frame extension of the frozen September24 N/Roe and LDA/Gauss3 campaign.

Reuses its exact source, ICs, parameters and co-moving control binaries/results.
Each new Config differs only by removing RD_ELEMENT_COMOVING_FRAME.
"""
import argparse,json,shutil,subprocess
from pathlib import Path
from run_n_gauss3_split import REPO,sha,write,rewrite,build,run

def prepare(root,control):
    root.mkdir(parents=True,exist_ok=True);(root/'source').mkdir(exist_ok=False)
    prov=json.loads((control/'source_provenance.json').read_text())
    assert sha(control/'source.tar')==prov['source_tar_sha256']
    checked=[]
    for f,h in prov['tracked_hashes'].items():
        if f.startswith('src/') or f in ('Makefile','defines_extra'):
            assert sha(REPO/f)==h,('Source changed since control',f);checked.append(f)
    shutil.copy2(control/'source.tar',root/'source.tar');subprocess.run(['tar','-xf',str(root/'source.tar'),'-C',str(root/'source')],check=True)
    shutil.copy2(control/'source_provenance.json',root/'source_provenance.json')
    for d in ('configs','inputs','runs','artifacts'):(root/d).mkdir()
    for f in ('run_n_gauss3_split.py',Path(__file__).name):shutil.copy2(REPO/'tests/rd'/f,root/f)
    c=json.loads((control/'campaign.json').read_text());cases=[];controls=[];methods=[]
    for scheme,residual in (('N','roe_split'),('LDA','gauss3')):
      for family in ('kh','sod'):
        oldmethod=f'{scheme}_{residual}_{family}';method=oldmethod+'_lab';methods.append(method)
        config=(control/'configs'/f'{oldmethod}.sh').read_text();assert config.count('RD_ELEMENT_COMOVING_FRAME\n')==1
        (root/'configs'/f'{method}.sh').write_text(config.replace('RD_ELEMENT_COMOVING_FRAME\n',''))
        meta=json.loads((control/'artifacts'/oldmethod/'provenance.json').read_text());assert sha(control/'artifacts'/oldmethod/'Arepo')==meta['binary_sha256']
        for problem in ('uniform',family):
          old=next(x for x in c['cases'] if x['method']==oldmethod and x['problem']==problem)
          name=problem+'_'+method;folder=root/'runs'/name;folder.mkdir();inp=Path(old['ic']);assert sha(inp)==old['ic_sha256']
          target=root/'inputs'/inp.name
          if not target.exists():shutil.copy2(inp,target)
          text=rewrite((control/'runs'/old['name']/'param.txt').read_text(),dict(InitCondFile=target.with_suffix(''),OutputDir=str(folder/'output')+'/'))
          (folder/'param.txt').write_text(text)
          cases.append(dict(old,name=name,method=method,frame='lab',ic=str(target),ic_sha256=sha(target),param_sha256=sha(folder/'param.txt'),control_name=old['name'],control_dir=str(control/'runs'/old['name'])))
          controls.append(dict(name=old['name'],directory=str(control/'runs'/old['name']),binary_sha256=meta['binary_sha256'],config_sha256=meta['config_sha256']))
    write(root/'campaign.json',dict(methods=methods,cases=cases,controls=controls,control_archive=str(control),scope=__doc__,checked_current_source_files=len(checked),source_tar_sha256=sha(root/'source.tar'),settings={k:c[k] for k in ('geometry','kh','sod')},limits='Co-moving controls reused after provenance verification, not rerun. No solver or tolerance changes.'))
    print('Prepared 4 lab builds, 8 native runs, paired with verified archived co-moving controls.',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','build','run'));p.add_argument('root',type=Path);p.add_argument('--control',type=Path,default=REPO.parent/'local_runs/n_gauss3_split_20260924_v1');p.add_argument('--select',nargs='+');p.add_argument('--group',choices=('all','uniform','science'),default='uniform');p.add_argument('--workers',type=int,choices=(1,2,3,4),default=4)
    a=p.parse_args();r=a.root.resolve()
    if a.action=='prepare':prepare(r,a.control.resolve())
    elif a.action=='build':build(r,a.select)
    else:run(r,a.group,a.select,a.workers)
