#!/usr/bin/env python3
"""Audit native RD triangles, primary owners, periodic geometry and MPI packets."""
import argparse
import csv
from collections import Counter, defaultdict
import json
from pathlib import Path

import h5py
import numpy as np
from scipy.spatial import Delaunay, cKDTree


def read(folder, call, kind):
    rows = []
    for file in sorted(folder.glob(f"call_{call:02d}_rank_*_{kind}.csv")):
        with file.open() as stream:
            rows.extend(csv.DictReader(line for line in stream if not line.startswith("#")))
    return rows


def key(ids, xy, primary, box):
    order = np.argsort(ids)
    ids = np.asarray(ids)[order]
    shifts = np.rint((np.asarray(xy)[order] - np.array([primary[int(i)] for i in ids])) / box).astype(int)
    shifts -= shifts[0]
    return tuple(int(x) for x in np.column_stack((ids, shifts)).ravel())


def capture(folder, call=0):
    ns = read(folder, call, "nodes")
    assert len({int(r["id"]) for r in ns}) == len(ns)
    primary = {int(r["id"]): [float(r["x"]), float(r["y"])] for r in ns}
    owners = {int(r["id"]): int(r["rank"]) for r in ns}
    indexes = {(int(r["rank"]), int(r["index"])): int(r["id"]) for r in ns}
    counts = Counter(owners.values())
    ts = read(folder, call, "triangles")
    keys, metadata = [], {}
    coordinate_error = 0.0
    area_error = 0.0
    for r in ts:
        ids = [int(r[f"id{j}"]) for j in range(3)]
        xy = np.array([[float(r[f"x{j}"]), float(r[f"y{j}"])] for j in range(3)])
        rank = int(r["rank"])
        for j, pid in enumerate(ids):
            task = int(r[f"rank{j}"])
            assert task == owners[pid]
            index = int(r[f"originalindex{j}"]) if task != rank else int(r[f"index{j}"]) % counts[rank]
            assert indexes[task, index] == pid
            error = (xy[j] - primary[pid] + 5) % 10 - 5
            coordinate_error = max(coordinate_error, float(np.max(abs(error))))
        assert rank == owners[min(ids)]
        winner = ids.index(min(ids))
        assert 0 <= int(r[f"index{winner}"]) < counts[rank]
        u, v = xy[1] - xy[0], xy[2] - xy[0]
        area = abs(float(u[0]*v[1] - u[1]*v[0])) / 2
        area_error = max(area_error, abs(area - float(r["area"])))
        k = key(ids, xy, primary, 10)
        assert k not in metadata, "Duplicate physical triangle"
        keys.append(k)
        metadata[k] = dict(ids=ids, xy=xy.tolist(), owner=rank, slot=int(r["slot"]), area=float(r["area"]))
    assert len(keys) == 2 * len(ns)
    assert coordinate_error < 1.e-12 and area_error < 1.e-12
    assert abs(sum(float(r["area"]) for r in ts) - 100) < 1.e-10

    ev = read(folder, call, "evaluations")
    assert len(ev) == 3 * len(ts)
    assert Counter((int(r["rank"]), int(r["slot"])) for r in ev) == Counter({(int(r["rank"]), int(r["slot"])): 3 for r in ts})
    assert all(int(r["active"]) == 1 for r in ts)
    assert {int(r["stage"]) for r in ev} == {call}
    for r in ev:
        assert indexes[int(r["destination"]), int(r["target_index"])] == int(r["id"])

    fields = ["dMass", "dMomentumX", "dMomentumY", "dEnergy"]
    def packet(row, source):
        return (int(row[source]), int(row["destination"]), int(row["target_index"]),
                *(float(row[f]) for f in fields))
    expected = Counter(packet(r, "rank") for r in ev if int(r["rank"]) != int(r["destination"]))
    exported = read(folder, call, "exports")
    imported = read(folder, call, "imports")
    assert expected == Counter(packet(r, "source") for r in exported)
    assert expected == Counter(packet(r, "source") for r in imported)
    for r in imported:
        assert indexes[int(r["destination"]), int(r["target_index"])] == int(r["id"])
    routing = np.zeros((len(counts), len(counts)), dtype=int)
    for r in exported:
        routing[int(r["source"]), int(r["destination"])] += 1
    summary = dict(nodes=len(ns), triangles=len(ts), node_counts=dict(sorted(counts.items())),
                   triangle_counts=dict(sorted(Counter(int(r["rank"]) for r in ts).items())),
                   max_native_primary_coordinate_error=coordinate_error, max_native_area_error=area_error,
                   area_sum=sum(float(r["area"]) for r in ts), residual_evaluations=len(ev)//3,
                   remote_vertex_contributions=len(exported), packet_values_match_exactly=True,
                   routing_matrix=routing.tolist(), stage=call)
    return primary, owners, metadata, ev, summary


def snapshot(path):
    with h5py.File(path) as f:
        p = f['PartType0']; order = np.argsort(p['ParticleIDs'][:])
        fields = {name: p[name][:][order] for name in ('ParticleIDs','Coordinates','Masses','Density','Velocities','InternalEnergy','Pressure')}
    return fields


def analyse(root):
    out = root / 'analysis'; out.mkdir(exist_ok=True)
    p, owners, triangles, ev, first = capture(root/'runs/rank4_capture/output/mpi_mesh')
    p1, o1, t1, ev1, single = capture(root/'runs/rank1_capture/output/mpi_mesh')
    pnext, onext, tnext, enext, second = capture(root/'runs/rank4_capture/output/mpi_mesh',1)
    assert triangles.keys() == t1.keys() == tnext.keys()
    assert p == pnext and owners == onext
    ids = np.array(sorted(p)); xy = np.array([p[int(i)] for i in ids])
    with h5py.File(root/'inputs/yee_glass48.hdf5') as f:
        order = np.argsort(f['PartType0/ParticleIDs'][:]); icxy = f['PartType0/Coordinates'][:,:2][order]
        assert np.array_equal(ids,f['PartType0/ParticleIDs'][:][order])
    assert np.max(abs((icxy-xy+5)%10-5))<1.e-12
    with h5py.File(root/'inputs/glassPlane_48.hdf5') as f:
        glass = f['PartType0/Coordinates'][:,:2] % 1
    distance, source_index = cKDTree(glass,boxsize=1).query(icxy/10 % 1)
    assert len(set(source_index))==len(ids) and distance.max()<1.e-14
    # The historical Yee generator assigns new sequential IDs in source-row
    # order; source glass IDs are not used as a cross-file identity key.
    with (out/'glass_id_mapping.csv').open('w') as f:
        w=csv.writer(f);w.writerow(['arepo_id','source_glass_row'])
        w.writerows(zip(ids,source_index))

    offsets = np.array([(x,y) for x in (-1,0,1) for y in (-1,0,1)])
    tiled = np.concatenate([xy+10*shift for shift in offsets])
    tiled_ids = np.tile(ids,9)
    delaunay = Delaunay(tiled)
    faces = delaunay.simplices
    centroids = tiled[faces].mean(axis=1)
    faces = faces[np.all((centroids>=0)&(centroids<10),axis=1)]
    scipy_keys = [key(tiled_ids[tri],tiled[tri],p,10) for tri in faces]
    assert len(scipy_keys)==len(set(scipy_keys))==2*len(ids)
    assert set(scipy_keys)==triangles.keys(), 'SciPy/native topology mismatch'

    edges=defaultdict(list)
    for triangle in triangles.values():
        v=triangle['ids'];coord=np.array(triangle['xy'])
        for a,b in [(0,1),(1,2),(2,0)]:
            edges[key([v[a],v[b]],coord[[a,b]],p,10)].append(triangle['owner'])
    assert len(edges)==3*len(ids) and all(len(v)==2 for v in edges.values())
    boundary_edges=sum(v[0]!=v[1] for v in edges.values())
    cross_rank=[t for t in triangles.values() if len({owners[i] for i in t['ids']})>1]
    minority=[t for t in cross_rank if Counter(owners[i] for i in t['ids'])[t['owner']]==1 and len({owners[i] for i in t['ids']})==2]
    three=[t for t in cross_rank if len({owners[i] for i in t['ids']})==3]
    def interior(t):return np.all((np.array(t['xy'])>.8)&(np.array(t['xy'])<9.2))
    def central(t):return float(np.sum((np.array(t['xy']).mean(axis=0)-5)**2))
    a=min([t for t in minority if interior(t)],key=central)
    b=min([t for t in three if interior(t)],key=central)
    examples=[]
    for label,t in zip(('A','B'),(a,b)):
        rows=[r for r in ev if int(r['rank'])==t['owner'] and int(r['slot'])==t['slot']]
        examples.append(dict(label=label,**t,vertex_owners=[owners[i] for i in t['ids']],
                             increments=[{k:(float(v) if k in ('dMass','dMomentumX','dMomentumY','dEnergy','triangle_dt') else int(v)) for k,v in r.items()} for r in rows]))

    outputs={name:snapshot(root/'runs'/name/'output/snap_001.hdf5') for name in ('rank4_capture','rank4_control','rank1_capture')}
    control={k:float(np.max(abs(outputs['rank4_capture'][k].astype(float)-outputs['rank4_control'][k].astype(float)))) for k in outputs['rank4_capture']}
    assert all(v==0 for v in control.values()),control
    rankdiff={k:float(np.max(abs(outputs['rank4_capture'][k].astype(float)-outputs['rank1_capture'][k].astype(float)))) for k in outputs['rank4_capture']}
    assert max(rankdiff.values())<1.e-11,rankdiff
    summary=dict(first_stage=first,second_stage=second,rank1=single,
                 scipy_periodic_triangles=len(scipy_keys),scipy_native_keys_identical=True,
                 rank1_rank4_native_keys_identical=True,periodic_edges=len(edges),boundary_edges=boundary_edges,
                 cross_rank_triangles=len(cross_rank),minority_owner_triangles=len(minority),three_rank_triangles=len(three),
                 source_glass_position_error=float(distance.max()),dump_on_off_max_difference=control,
                 rank1_rank4_max_difference=rankdiff,examples=examples)
    (out/'audit.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'native_mesh.json').write_text(json.dumps(dict(nodes=[dict(id=int(i),xy=p[int(i)],rank=owners[int(i)]) for i in ids],triangles=list(triangles.values())),indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('examples','rank1')},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path)
    analyse(parser.parse_args().root.resolve())
