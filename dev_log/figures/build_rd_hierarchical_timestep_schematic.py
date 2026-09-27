#!/usr/bin/env python3
"""A small, verified Delaunay example of nodal hierarchical timesteps.

The panels show interval openings, not both RK stages. This is an illustrative
mesh, not a native run or a numerical accuracy/conservation test.
"""
import argparse
import json
import os
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR', '/private/tmp/rd_hierarchy_schematic_mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.legend_handler import HandlerTuple
from matplotlib.patches import FancyArrowPatch, Polygon
import numpy as np
from scipy.spatial import Delaunay

INK = '#253340'
COLORS = {1: '#D78A00', 2: '#008C83', 4: '#3979BF'}
PALE = {1: '#F9E5B5', 2: '#C6EAE3', 4: '#CCDEF2'}
XY = np.array([[-1.6, .1], [-1.2, 1.25], [0., 0.], [.6, 1.25], [1.5, .1]])
NAMES = ['A', 'B', 'C', 'D', 'E']
PERIODS = np.array([4, 4, 4, 2, 1])
TRIANGLES = np.array([[0, 1, 2], [1, 2, 3], [2, 3, 4]])


def dt_label(period):
    return r'$\Delta t$' if period == 1 else rf'${period}\Delta t$'


def verify():
    expected_sets = {tuple(sorted(t)) for t in TRIANGLES}
    scipy_sets = {tuple(sorted(t)) for t in Delaunay(XY).simplices}
    assert expected_sets == scipy_sets
    triangle_periods = PERIODS[TRIANGLES].min(axis=1)
    assert triangle_periods.tolist() == [4, 2, 1]
    events = []
    for step in range(5):
        synchronized = step % PERIODS == 0
        due = step % triangle_periods == 0
        assert np.array_equal(due, synchronized[TRIANGLES].any(axis=1))
        events.append({'time_in_smallest_steps': step,
                       'synchronized_nodes': [n for n, active in zip(NAMES, synchronized) if active],
                       'triangles_starting': [i + 1 for i, active in enumerate(due) if active],
                       'contribution_targets': {str(i + 1): [NAMES[j] for j in t]
                                                for i, t in enumerate(TRIANGLES) if due[i]}})
    assert [e['triangles_starting'] for e in events] == [[1, 2, 3], [3], [2, 3], [3], [1, 2, 3]]
    star_periods = PERIODS.copy()
    for tri, period in zip(TRIANGLES, triangle_periods):
        star_periods[tri] = np.minimum(star_periods[tri], period)
    return {'illustrative_not_native': True, 'scipy_delaunay_matches': True,
            'node_names': NAMES, 'xy': XY.tolist(), 'nodal_timestep_multipliers': PERIODS.tolist(),
            'triangles': TRIANGLES.tolist(), 'triangle_timestep_multipliers': triangle_periods.tolist(),
            'star_timestep_multipliers': star_periods.tolist(),
            'stage_live_nodes_for_this_patch': [n for n, live in zip(NAMES, star_periods == PERIODS) if live],
            'node_symbols_encode_timebin_synchronization_not_stage_live': True,
            'node_fill_always_encodes_nodal_timestep': True,
            'outer_ring_encodes_timebin_synchronization': True,
            'node_colours': {n: COLORS[int(p)] for n, p in zip(NAMES, PERIODS)},
            'events': events}


def clocks(ax, step):
    ax.set_xlim(-.95, 4.32)
    ax.set_ylim(-.15, 3.72)
    ax.axis('off')
    ax.axvspan(step - .095, step + .095, ymin=.14, ymax=.91, color='#E6E9ED', zorder=0)
    ax.plot([step, step], [.43, 3.38], color=INK, lw=.8, ls=(0, (2, 2)), zorder=1)
    for y, period in zip([3., 2., 1.], [4, 2, 1]):
        ax.annotate('', xy=(4.22, y), xytext=(0, y),
                    arrowprops={'arrowstyle': '->', 'color': COLORS[period], 'lw': 1.1}, zorder=2)
        ax.text(-.26, y, dt_label(period), ha='right', va='center', color=COLORS[period], fontsize=11.5)
        for t in range(0, 5, period):
            active = t == step
            if active:
                ax.scatter(t, y, s=80, facecolors='white', edgecolors=INK, linewidths=.9, zorder=3)
            ax.scatter(t, y, s=40 if active else 18,
                       facecolors=COLORS[period], edgecolors='white', linewidths=.45, zorder=4)
    for t in range(5):
        ax.text(t, .25, '0' if t == 0 else dt_label(t), ha='center', va='center', fontsize=9.5)
    ax.text(-.92, 3.64, r'Node timebins $\Delta t_i$', ha='left', va='center', fontsize=9.5, color='#526473')


def mesh_panel(ax, step):
    ax.set_aspect('equal')
    ax.set_xlim(-1.93, 1.83)
    ax.set_ylim(-.32, 1.57)
    ax.axis('off')
    for index, tri in enumerate(TRIANGLES):
        coords = XY[tri]
        period = int(PERIODS[tri].min())
        due = step % period == 0
        center = coords.mean(axis=0)
        ax.add_patch(Polygon(coords, facecolor=PALE[period] if due else '#F7F8FA',
                             edgecolor='#687989', lw=1.0, zorder=1))
        if due:
            for point in coords:
                a = center + .37 * (point - center)
                b = center + .82 * (point - center)
                ax.add_patch(FancyArrowPatch(a, b, arrowstyle='-|>', mutation_scale=9,
                                            color=INK, lw=.9, shrinkA=0, shrinkB=0, zorder=3))
        ax.text(*center, rf'$T_{index + 1}$' + '\n' + dt_label(period),
                ha='center', va='center', fontsize=10.3, linespacing=1.18,
                color=COLORS[period] if due else '#9AA5AF', zorder=4)
    offsets = [(-.18, -.025), (-.03, .18), (0, -.21), (0, .18), (.19, -.025)]
    for name, point, period, offset in zip(NAMES, XY, PERIODS, offsets):
        active = step % period == 0
        if active:
            ax.scatter(*point, s=184, facecolors='white', edgecolors=INK, linewidths=1.0, zorder=6)
        ax.scatter(*point, s=93, facecolors=COLORS[period],
                   edgecolors='white', linewidths=.6, zorder=7)
        ax.text(*(point + offset), rf'${name}$', fontsize=13, ha='center', va='center', color=INK)


def build(output):
    audit = verify()
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                         'text.color': INK, 'mathtext.fontset': 'dejavusans',
                         'pdf.fonttype': 42, 'ps.fonttype': 42, 'svg.fonttype': 'none',
                         'savefig.transparent': False})
    fig = plt.figure(figsize=(8.4, 7.8), facecolor='white')
    outer = fig.add_gridspec(2, 2, left=.05, right=.985, top=.94, bottom=.155,
                            hspace=.27, wspace=.14)
    for step in range(4):
        inner = outer[step // 2, step % 2].subgridspec(2, 1, height_ratios=[1., 1.55], hspace=.04)
        clock_ax = fig.add_subplot(inner[0])
        clocks(clock_ax, step)
        clock_ax.set_title(f'({chr(97 + step)})  ' + r'$t = ' + ('0' if step == 0 else ('' if step == 1 else str(step)) + r'\Delta t') + '$',
                           loc='left', fontsize=13, fontweight='bold', pad=13)
        mesh_panel(fig.add_subplot(inner[1]), step)
    handles = [Line2D([], [], marker='o', ls='none', color=COLORS[p],
                      markerfacecolor=COLORS[p], markersize=7) for p in [4, 2, 1]]
    handles.append((Line2D([], [], marker='o', ls='none', color=INK, markerfacecolor='white', markersize=10),
                    Line2D([], [], marker='o', ls='none', color='white', markerfacecolor='#687989', markersize=6.5)))
    labels = ['Node: ' + dt_label(p) for p in [4, 2, 1]] + ['Ring: synchronized']
    fig.legend(handles=handles, labels=labels, handler_map={tuple: HandlerTuple(ndivide=1)},
               loc='lower center', bbox_to_anchor=(.52, .09), ncol=4,
               frameon=False, fontsize=10, columnspacing=1.8, handletextpad=.5)
    stem = 'rd_hierarchical_timestep_schematic'
    for ext in ['pdf', 'svg', 'png']:
        fig.savefig(output / f'{stem}.{ext}', dpi=220, bbox_inches='tight', pad_inches=.08, facecolor='white')
    plt.close(fig)
    (output / 'schematic_schedule.json').write_text(json.dumps(audit, indent=2) + '\n')
    print(json.dumps({'output_dir': str(output), 'verified': True,
                      'triangle_starts': [e['triangles_starting'] for e in audit['events']]}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    build(parser.parse_args().output_dir.resolve())
