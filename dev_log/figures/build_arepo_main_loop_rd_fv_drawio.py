#!/usr/bin/env python3
"""Create a generic RD/FV copy of the numbered function-name flowchart.

Preserve the reviewed source, all geometry, connectors and manual gravity
labels. Show the main-loop interfaces without solver-specific stage dispatch.
"""
import argparse
import copy
import hashlib
import html
from pathlib import Path
import re
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
SOURCE = HERE/'Arepo_flowchart_main_loop_RD_functions_reviewed_20260914.drawio'
SOURCE_SHA = 'd4d124cac61c4e9e69660c2dd2a3cd5ad6565b98879f52cd9655de87f892038e'
OUTPUT = HERE/'Arepo_flowchart_main_loop_RD_FV_functions_20260914.drawio'


def label(description, calls):
    code = '<br>'.join(html.escape(s).replace('_', '_<wbr>') for s in calls)
    return ('<div style="font-size:14px;line-height:125%;">'+description+'</div>'
            '<div style="height:9px;"></div>'
            '<div style="font-family:Courier New;font-size:12px;line-height:135%;">'+code+'</div>')


def main(output):
    before = SOURCE.read_bytes()
    assert hashlib.sha256(before).hexdigest() == SOURCE_SHA, 'Review any new manual source edits first'
    doc = ET.ElementTree(ET.fromstring(before))
    diagram = doc.find('diagram')
    diagram.set('id', 'arepo-main-loop-rd-fv')
    diagram.set('name', 'AREPO main loop - RD or FV')
    model = diagram.find('mxGraphModel')
    model.set('background', '#FFFFFF')
    cells = {c.get('id'):c for c in model.findall('root/mxCell')}
    edits = {
        'title': 'AREPO main loop - RD or FV',
        'subtitle': 'Main-loop structure with RD or FV hydrodynamics; function names and numbered blocks',
        'rd-predictor': label('Hydrodynamics (RD or FV)<br><b>Begin step</b>',
                              ['RD: rd_step_begin(&Mesh)', 'FV: compute_interface_fluxes(&Mesh)']),
        'rd-corrector': label('Hydrodynamics (RD or FV)<br><b>End step</b>',
                              ['RD: rd_step_end(&Mesh)', 'FV: compute_interface_fluxes(&Mesh)']),
        'domain-mesh': label('Domain / tree update (when due);<br>mesh construction (when required)', [
            '[when domain update is due]',
            'drift_all_particles()',
            'domain_Decomposition(); ngb_treebuild(NumGas)',
            '[when mesh construction is required]',
            'create_mesh(); mesh_setup_exchange()']),
        'scope': 'RD and FV are alternative hydrodynamic solvers at the two main-loop entry points.',
        'scope-conditional': 'Mesh updates, gravity and source terms depend on the simulation configuration.',
        'function-scope': 'Selected main-loop calls are shown; initialization and restart setup are omitted.',
    }
    for key,value in edits.items():
        cells[key].set('value',value)
    original = {c.get('id'):c for c in ET.fromstring(before).findall('.//mxCell')}
    assert cells.keys() == original.keys()
    for key,c in cells.items():
        expected = copy.deepcopy(original[key])
        if key in edits:
            expected.set('value', edits[key])
        assert ET.tostring(c) == ET.tostring(expected), key
    assert len([c for c in cells.values() if c.get('parent')=='process']) == 14
    assert len([c for c in cells.values() if c.get('edge')=='1']) == 15
    assert len([c for c in cells.values() if c.get('id','').startswith('step-number-')]) == 14
    visible = ' '.join(c.get('value','') for c in cells.values())
    assert not re.search(r'\b(static|moving|ALE)\b|RD_RK_STAGE', visible, re.I)
    run = (HERE.parents[1]/'src/main/run.c').read_text()
    for call in ('rd_step_begin(&Mesh)', 'rd_step_end(&Mesh)', 'compute_interface_fluxes(&Mesh)'):
        assert call in run
    with output.open('xb') as stream:
        doc.write(stream, encoding='utf-8', xml_declaration=True)
    assert SOURCE.read_bytes() == before
    print(output)
    print('Preserved all 14 numbered boxes and 15 edges; changed only eight labels and page metadata.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=OUTPUT)
    main(parser.parse_args().output)
