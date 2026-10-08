#!/usr/bin/env python3
"""Schematic of the edge-HLLC low-order RD kernel on the thesis Figure 4.2 mesh.

(a) Inside one triangle: residual split along the three median-dual segments.
(b) Edge CD: RD median-dual half faces (one per triangle) versus the MMFV Voronoi face.
Geometry is illustrative (node layout copied from Figure 4.2), not simulation data.
"""
import argparse
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, FancyArrowPatch

P = {'A': (0.0, 0.15), 'B': (0.35, 1.05), 'C': (1.2, 0.0), 'D': (1.75, 1.05), 'E': (2.6, 0.62)}
P = {k: np.array(v) for k, v in P.items()}
TRI = {'T1': 'ACB', 'T2': 'BCD', 'T3': 'CED'}          # counter-clockwise
NODE_COLOR = {'C': '#3a6fb0', 'D': '#2a9d8f', 'E': '#d08a2e'}
INK, MUTED = '#222222', '#8a8a8a'


def centroid(t): return sum(P[v] for v in TRI[t]) / 3


def circumcenter(t):
    a, b, c = (P[v] for v in TRI[t])
    d = 2*(a[0]*(b[1]-c[1]) + b[0]*(c[1]-a[1]) + c[0]*(a[1]-b[1]))
    ux = ((a@a)*(b[1]-c[1]) + (b@b)*(c[1]-a[1]) + (c@c)*(a[1]-b[1])) / d
    uy = ((a@a)*(c[0]-b[0]) + (b@b)*(a[0]-c[0]) + (c@c)*(b[0]-a[0])) / d
    return np.array([ux, uy])


def inward_normals(t):
    x = [P[v] for v in TRI[t]]
    return {TRI[t][i]: np.array([x[(i+1) % 3][1]-x[(i+2) % 3][1], x[(i+2) % 3][0]-x[(i+1) % 3][0]]) for i in range(3)}


def mesh(ax, highlight=()):
    for name, verts in TRI.items():
        ax.add_patch(Polygon([P[v] for v in verts], closed=True, fc='#f2f2f2' if name not in highlight else 'white',
                             ec='#555555', lw=1.0, zorder=1))
        if name not in highlight:
            ax.text(*centroid(name), name, ha='center', va='center', color=MUTED, fontsize=10)
    for k, p in P.items():
        ax.plot(*p, 'o', ms=7, color=NODE_COLOR.get(k, '#9a9a9a'), zorder=5)
        off = {'A': (-.1, 0), 'B': (-.05, .08), 'C': (0, -.1), 'D': (0, .09), 'E': (.1, 0)}[k]
        ax.text(*(p+off), k, ha='center', va='center', fontsize=12, style='italic', color=INK)


def panel_a(ax):
    mesh(ax, highlight=('T3',))
    g = centroid('T3'); n = inward_normals('T3')
    # Sub-quadrilaterals of T3 owned by each node (median-dual pieces).
    for v in 'CED':
        others = [u for u in 'CED' if u != v]
        m1, m2 = (P[v]+P[others[0]])/2, (P[v]+P[others[1]])/2
        ax.add_patch(Polygon([P[v], m1, g, m2], closed=True, fc=NODE_COLOR[v], alpha=.16, ec='none', zorder=2))
    for i, j in (('C', 'D'), ('D', 'E'), ('E', 'C')):
        m = (P[i]+P[j])/2
        ax.plot(*np.c_[m, g], color=INK, lw=1.6, zorder=3)
        mid = (m+g)/2; nu = (n[j]-n[i])/6
        ax.add_patch(FancyArrowPatch(mid, mid+nu*.75, arrowstyle='-|>', mutation_scale=11, color='#c0392b', lw=1.3, zorder=4))
        lab = mid + nu*.75 + np.array([.02, .02])
        ax.text(*lab, f'$\\nu_{{{i}{j}}}$', color='#c0392b', fontsize=10)
    ax.plot(*g, 'k+', ms=8, zorder=4); ax.text(*(g+np.array([.04, -.07])), '$G$', fontsize=10)
    ax.text(1.8, -.33, '$\\Phi_{T_3}=\\frac{1}{2}\\sum_j \\mathbf{G}(\\mathbf{U}_j)\\cdot\\mathbf{n}_j'
            '=\\phi_C+\\phi_D+\\phi_E$', ha='center', fontsize=10)
    ax.set_title('(a) Inside $T_3$: one HLLC problem per median-dual segment', fontsize=10, loc='left')


def panel_b(ax):
    mesh(ax, highlight=('T2', 'T3'))
    m = (P['C']+P['D'])/2
    for t, dy in (('T2', .0), ('T3', .0)):
        g = centroid(t)
        ax.plot(*np.c_[m, g], color=INK, lw=1.8, zorder=3)
        ax.plot(*g, 'k+', ms=8, zorder=4)
        ax.text(*(g+np.array([.02, .07])), f'$G_{{{t[1]}}}$', fontsize=10)
    ax.plot(*m, 'o', ms=4, color=INK, zorder=4); ax.text(*(m+np.array([-.2, .0])), '$m_{CD}$', fontsize=10)
    o2, o3 = circumcenter('T2'), circumcenter('T3')
    ax.plot(*np.c_[o2, o3], color='#7a4fb5', lw=1.8, ls='--', zorder=3)
    for o, t in ((o2, 2), (o3, 3)):
        ax.plot(*o, 's', ms=5, color='#7a4fb5', zorder=4)
        ax.text(*(o+(np.array([-.16, .02]) if t == 2 else np.array([.04, -.1]))), f'$O_{t}$', color='#7a4fb5', fontsize=10)
    ax.plot([], [], color=INK, lw=1.8, label='RD median-dual face $G_2$–$m_{CD}$–$G_3$ (two HLLC problems)')
    ax.plot([], [], color='#7a4fb5', lw=1.8, ls='--', label='MMFV Voronoi face $O_2O_3$ (one Riemann problem)')
    ax.legend(loc='lower center', bbox_to_anchor=(.5, -.2), fontsize=8.5, frameon=False)
    ax.set_title('(b) Edge $CD$: RD half faces versus MMFV Voronoi face', fontsize=10, loc='left')


def main(out):
    plt.rcParams.update({'font.size': 10})
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4), layout='constrained')
    panel_a(axes[0]); panel_b(axes[1])
    for ax in axes:
        ax.set_aspect('equal'); ax.set_xlim(-.25, 2.85); ax.set_ylim(-.45, 1.3); ax.axis('off')
    fig.savefig(out.with_suffix('.png'), dpi=250); fig.savefig(out.with_suffix('.pdf'))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('out', type=Path)
    main(p.parse_args().out)
