#!/usr/bin/env python3
"""Reflow the user's final embedded draw.io diagram for a landscape thesis page.

The input is the editable XML embedded in the user-approved PDF. Only layout,
line breaks and typography change; the 14 labels and 15 connections are checked.
The output is a new file, leaving every earlier diagram untouched.
"""
import argparse
import copy
import html
from pathlib import Path
import re
import xml.etree.ElementTree as ET


def plain(value):
    value = value.replace(r'\(', '(').replace(r'\)', ')')
    return re.sub(r'\s+', '', html.unescape(re.sub(r'<[^>]*>', '', value)))


def style(cell, **changes):
    parts = cell.get('style', '').split(';')
    parts = [p for p in parts if p and p.split('=')[0] not in changes]
    cell.set('style', ';'.join(parts + [f'{k}={v}' for k, v in changes.items()]) + ';')


def geometry(cell, x, y, width, height):
    geom = cell.find('mxGeometry')
    for key, value in zip(('x', 'y', 'width', 'height'), (x, y, width, height)):
        geom.set(key, str(value))


def build(source, output):
    tree = ET.parse(source)
    model = tree.find('.//mxGraphModel')
    cells = {c.get('id'): c for c in model.findall('root/mxCell')}
    original = copy.deepcopy(cells)
    for cell in cells.values():
        if cell.get('value'):
            cell.set('value', cell.get('value').replace(r'\(', '(').replace(r'\)', ')'))
    model.set('pageWidth', '1404')
    model.set('pageHeight', '744')
    model.set('background', '#FFFFFF')
    tree.find('diagram').set('name', 'AREPO main loop - landscape')

    geometry(cells['title'], 30, 8, 1300, 32)
    style(cells['title'], fontSize=26)
    geometry(cells['subtitle'], 30, 38, 1300, 1)
    for i, x in enumerate((30, 228, 468, 678, 938)):
        geometry(cells[f'legend-dot-{i}'], x, 48, 12, 12)
        geometry(cells[f'legend-text-{i}'], x + 19, 44, 390 if i == 4 else 215, 22)
        style(cells[f'legend-text-{i}'], fontSize=16)
    geometry(cells['frame'], 18, 72, 1376, 659)
    geometry(cells['loop-ribbon'], 18, 72, 22, 659)
    geometry(cells['loop-label'], -121, 390, 300, 24)
    style(cells['loop-label'], fontSize=16)
    cells['loop-label'].set('value', r'run(): while (1)')

    columns = [
        ['outputs', 'node-timebins', 'sources-first', 'gradients-first', 'vertex-velocity'],
        ['exchange-predictor', 'rd-predictor', 'next-sync', 'active-nodes', 'domain-mesh'],
        ['exchange-corrector', 'rd-corrector', 'recover-primitives', 'sources-second'],
    ]
    descriptions = {
        'node-timebins': 'Select hydro timesteps from the CFL<br>condition; assign node timebins<br>(equal or hierarchical)',
        'sources-first': 'Gravity / source terms:<br>first half-step',
        'exchange-predictor': 'Exchange primitives, vertex velocities<br>and gradients',
        'sources-second': 'Gravity / source terms:<br>second half-step',
        'recover-primitives': 'Recover primitives for synchronized nodes;<br>close the hydro step',
    }
    for col, keys in enumerate(columns):
        for row, key in enumerate(keys):
            cell = cells[key]
            geometry(cell, 54 + 444 * col, 100 + 128 * row, 404, 112)
            value = cell.get('value').replace(r'\(', '(').replace(r'\)', ')')
            if key in descriptions:
                value = re.sub(r'(<div[^>]*>).*?(</div>)',
                               lambda m: m[1] + descriptions[key] + m[2], value, count=1)
            value = value.replace('font-size:14px;line-height:125%', 'font-size:18px;line-height:112%')
            value = value.replace('font-size:12px;line-height:135%', 'font-size:14px;line-height:112%')
            value = re.sub(r'<div style="height:9px;">(?:<br>)?</div>', '<div style="height:4px;"></div>', value)
            cell.set('value', value)
            style(cell, spacing=6, fontSize=18,
                  fontColor='#FFFFFF' if key == 'outputs' else '#202D3A')
    for key, cell in cells.items():
        if key.startswith('step-number-'):
            geometry(cell, 6, 6, 22, 22)
            style(cell, fontSize=14)

    routes = {
        'flow-05': [(478, 668), (478, 156)],
        'flow-10': [(922, 668), (922, 156)],
        'flow-14': [(1370, 540), (1370, 84), (256, 84)],
    }
    for key, points in routes.items():
        cell = cells[key]
        geom = cell.find('mxGeometry')
        for child in list(geom):
            geom.remove(child)
        array = ET.SubElement(geom, 'Array', {'as': 'points'})
        for x, y in points:
            ET.SubElement(array, 'mxPoint', {'x': str(x), 'y': str(y)})
    style(cells['flow-14'], entryX=0.5, entryY=0)
    entry = cells['entry-from-setup']
    style(entry, entryX=0.3, entryY=0)
    geom = entry.find('mxGeometry')
    for child in list(geom):
        geom.remove(child)
    ET.SubElement(geom, 'mxPoint', {'x': '175.2', 'y': '72', 'as': 'sourcePoint'})
    for cell in cells.values():
        if cell.get('edge') == '1':
            style(cell, strokeWidth=1.5)

    assert cells.keys() == original.keys()
    for key, cell in cells.items():
        assert plain(cell.get('value', '')) == plain(original[key].get('value', '')), key
        for attr in ('source', 'target', 'parent', 'edge', 'vertex'):
            assert cell.get(attr) == original[key].get(attr), (key, attr)
    assert sum(c.get('parent') == 'process' for c in cells.values()) == 14
    assert sum(c.get('edge') == '1' for c in cells.values()) == 15
    assert sum(k.startswith('step-number-') for k in cells) == 14
    with output.open('xb') as stream:
        tree.write(stream, encoding='utf-8', xml_declaration=True)
    print(f'Created {output}; verified all labels, 14 numbered boxes and 15 connections.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    build(args.source, args.output)
