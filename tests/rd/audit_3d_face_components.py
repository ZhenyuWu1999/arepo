#!/usr/bin/env python3
"""Read-only audit of archived periodic 3D mesh changes.

Uses face-incidence BFS, exact integer boundary cancellation and integer image
potentials, independently of the native vertex union and Claude's face union.
This audits signed-chain geometry and mass bookkeeping, not a transfer solver.
"""
import argparse
from collections import Counter, defaultdict, deque
import csv
import hashlib
import json
from pathlib import Path
import platform
import subprocess

import numpy as np
from analyse_3d_geometry_pilot import read_pair


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key(r):
    return tuple(map(int, r.id)), tuple(map(int, np.ctypeslib.as_array(r.image).ravel()))


def face_key(ids, images, skip):
    indices = [i for i in range(4) if i != skip]
    base = images[indices[0]]
    return tuple((ids[i], tuple(images[i]-base)) for i in indices)


def components(labels, neighbours):
    unseen = set(labels)
    result = []
    while unseen:
        seed = min(unseen)
        unseen.remove(seed)
        queue, found = deque([seed]), []
        while queue:
            u = queue.popleft()
            found.append(u)
            for v in neighbours(u):
                if v in unseen:
                    unseen.remove(v)
                    queue.append(v)
        result.append(found)
    return result


def analyse(pair, native_csv, first_step):
    old, new, h = read_pair(pair)
    maps = [{key(r): r for r in mesh} for mesh in (old, new)]
    assert len(maps[0]) == len(old) and len(maps[1]) == len(new)
    primary, velocity = {}, {}
    for r in old:
        for i, vid in enumerate(r.id):
            vid = int(vid)
            x = np.array(r.x[i])-np.array(r.image[i])
            w = np.array(r.w[i])
            if vid in primary:
                assert np.max(np.abs(primary[vid]-x)) < 1e-12
                assert np.max(np.abs(velocity[vid]-w)) < 1e-12
            primary[vid], velocity[vid] = x, w
    records, faces, incidence = [], defaultdict(list), []
    for side, current in enumerate(maps):
        other = maps[1-side]
        for k, r in current.items():
            if k in other and r.orientation == other[k].orientation:
                continue
            idx = len(records)
            records.append((side, r))
            ids, images = k[0], np.array(k[1]).reshape(4, 3)
            fs = [face_key(ids, images, skip) for skip in range(4)]
            incidence.append(fs)
            for f in fs:
                faces[f].append(idx)
    groups = components(range(len(records)),
                        lambda u: (v for f in incidence[u] for v in faces[f]))
    membership, region_dm = defaultdict(list), []
    largest_boundary = winding = 0
    volume_defect = moment_defect = coordinate_defect = 0.0
    region_vertices = []
    for label, group in enumerate(groups):
        boundary, edges = Counter(), defaultdict(list)
        for idx in group:
            side, r = records[idx]
            coeff = (2*side-1)*r.orientation
            for skip, f in enumerate(incidence[idx]):
                boundary[f] += coeff*(-1)**skip
            images = np.ctypeslib.as_array(r.image)
            ids = list(map(int, r.id))
            for i in range(1, 4):
                offset = tuple(map(int, images[i]-images[0]))
                edges[ids[0]].append((ids[i], offset))
                edges[ids[i]].append((ids[0], tuple(-x for x in offset)))
        largest_boundary = max(largest_boundary, max(map(abs, boundary.values()), default=0))
        assert not any(boundary.values()), 'nonclosed integer signed boundary'
        seed = min(edges)
        potentials, queue, wraps = {seed: (0, 0, 0)}, deque([seed]), 0
        while queue:
            u = queue.popleft()
            for v, offset in edges[u]:
                candidate = tuple(a+b for a, b in zip(potentials[u], offset))
                if v in potentials:
                    wraps += potentials[v] != candidate
                else:
                    potentials[v] = candidate
                    queue.append(v)
        assert len(potentials) == len(edges)
        winding += bool(wraps)
        verts = set(potentials)
        region_vertices.append(verts)
        for v in verts:
            membership[v].append(label)
        dm = defaultdict(float)
        if wraps:
            region_dm.append(dm)
            continue
        volumes, moments, absolute = np.zeros(2), np.zeros((2, 3)), np.zeros(2)
        for idx in group:
            side, r = records[idx]
            ids = list(map(int, r.id))
            x0 = np.array([primary[v]+potentials[v] for v in ids])
            w = np.array([velocity[v] for v in ids])
            native_x = np.ctypeslib.as_array(r.x)
            discrepancy = x0+side*h*w-native_x
            discrepancy -= discrepancy[0]
            coordinate_defect = max(coordinate_defect, float(np.max(np.abs(discrepancy))))
            for t in (0, 1):
                x = x0+t*h*w
                vol = r.orientation*np.linalg.det(x[1:]-x[0])/6.0
                signed = (2*side-1)*vol
                volumes[t] += signed
                moments[t] += signed*x.mean(axis=0)
                absolute[t] += abs(vol)
                if t == 0:
                    for v in ids:
                        dm[v] += signed/4.0
        volume_defect = max(volume_defect, float(np.max(np.abs(volumes)/absolute)))
        moment_defect = max(moment_defect, float(np.max(np.abs(moments)/absolute[:, None])))
        region_dm.append(dm)
    assert winding == 0, 'this audit requires a nonwinding first-pair region'
    assert coordinate_defect < 1e-12 and volume_defect < 1e-12 and moment_defect < 1e-12
    coupled = components(range(len(groups)),
                         lambda u: (v for node in region_vertices[u] for v in membership[node]))
    coupled_sizes = sorted(len(set().union(*(region_vertices[i] for i in c))) for c in coupled)
    with native_csv.open() as f:
        native_sizes = sorted(int(r['vertices']) for r in csv.DictReader(f)
                              if int(r['step']) == first_step)
    assert coupled_sizes == native_sizes, 'face regions coupled through nodes must recover native vertex groups'
    masses = [defaultdict(float), defaultdict(float)]
    for side, mesh in enumerate((old, new)):
        for r in mesh:
            x = np.ctypeslib.as_array(r.x).copy()-side*h*np.ctypeslib.as_array(r.w)
            vol = r.orientation*np.linalg.det(x[1:]-x[0])/6.0
            for v in r.id:
                masses[side][int(v)] += vol/4.0
    summed, withdrawals = defaultdict(float), defaultdict(float)
    cross_sign = 0
    for v, labels in membership.items():
        values = [region_dm[i][v] for i in labels]
        summed[v] = sum(values)
        withdrawals[v] = sum(max(-a, 0.0) for a in values)
        tolerance = 1e-12*masses[0][v]
        cross_sign += any(a > tolerance for a in values) and any(a < -tolerance for a in values)
    mass_error = max((abs((masses[1][v]-masses[0][v])-summed[v]) for v in primary), default=0.0)
    mass_error /= max(masses[0].values())
    assert mass_error < 1e-12
    fsizes = sorted(map(len, region_vertices))
    return dict(h=h, first_step=first_step, changed_records=len(records),
                face_regions=len(groups), max_face_vertices=max(fsizes, default=0),
                p99_face_vertices=float(np.percentile(fsizes, 99)) if fsizes else 0,
                max_integer_boundary=largest_boundary, winding_face_regions=winding,
                max_volume_defect=volume_defect, max_moment_defect=moment_defect,
                max_coordinate_defect=coordinate_defect,
                coupled_regions=len(coupled), max_coupled_vertices=max(coupled_sizes, default=0),
                changed_vertices=len(membership), shared_vertices=sum(len(v)>1 for v in membership.values()),
                max_membership=max(map(len, membership.values()), default=0),
                vertices_donor_in_one_receiver_in_another=int(cross_sign),
                max_summed_withdrawal_fraction=max((withdrawals[v]/masses[0][v] for v in membership), default=0),
                max_mass_assembly_defect=mass_error)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pilot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), 'refusing to overwrite audit results'
    results, inputs = {}, {}
    for run in sorted((args.pilot/'runs').glob('*_diag')):
        pair = run/'output/geometry_first_pair.bin'
        if not pair.exists():
            continue
        step_file, native_csv = run/'output/geometry_steps.jsonl', run/'output/geometry_cavities.csv'
        first_step = json.loads(step_file.read_text().splitlines()[0])['step']
        result = analyse(pair, native_csv, first_step)
        results[run.name] = result
        for p in (pair, step_file, native_csv):
            inputs[str(p.resolve())] = sha(p)
        print(run.name, json.dumps(result), flush=True)
    repo = Path(__file__).resolve().parents[2]
    args.output.write_text(json.dumps(dict(
        scope='Archived first native pairs only; signed chains, not positive tilings or a transfer positivity proof.',
        normalization='Volume: sum|V|; moment: sum|V| times unit box; mass assembly: maximum old full-star mass.',
        runs=results, provenance=dict(
            head=subprocess.check_output(['git','rev-parse','HEAD'], cwd=repo, text=True).strip(),
            python=platform.python_version(), numpy=np.__version__,
            script_sha256=sha(Path(__file__)), reader_sha256=sha(Path(__file__).with_name('analyse_3d_geometry_pilot.py')),
            input_sha256=inputs)), indent=2)+'\n')


if __name__ == '__main__':
    main()
