#!/usr/bin/env python3
"""Supplement the old/new split experiment with spatial and patch checks.

The spatial ladder refines h and dt together and is only a smooth scalar
accuracy diagnostic. The deliberately negative instantaneous-transfer case
is an expected counterexample to positivity, not a passed positivity gate.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np
import explore_true_ale_split as base
import explore_true_ale_split_balance as candidate
import explore_true_ale_split_euler as euler


def instantaneous_checks():
    xy = np.array([[0., 0.], [1., 0.], [1., 1.], [0., 1.]])
    a = np.array([[0, 1, 2], [0, 2, 3]])
    b = np.array([[0, 1, 3], [1, 2, 3]])
    old, new = base.Mesh(a, xy[a], 4), base.Mesh(b, xy[b], 4)
    affine = 1 + .2 * xy[:, 0] - .1 * xy[:, 1]
    mapped, event = candidate.balance(old, old, new, new, affine, affine)
    assert np.max(abs(mapped - affine)) < 1e-14
    positive = np.array([.01, 10., .01, 10.])
    negative, failed = candidate.balance(old, old, new, new, positive, positive)
    assert negative.min() < 0  # Expected failure of an unlimited high transfer.
    assert abs(new.mass @ negative - old.mass @ positive) < 1e-14
    return dict(affine_error=float(np.max(abs(mapped-affine))),
                positive_input=positive.tolist(), output=negative.tolist(),
                conserved_total=float(new.mass @ negative),
                negative_output_is_expected=True, balance=failed)


def main(output):
    output.mkdir(parents=True, exist_ok=False)
    sources = [Path(p).resolve() for p in (__file__, base.__file__, candidate.__file__, euler.__file__)]
    for source in sources:
        shutil.copy2(source, output / source.name)
    (output / 'provenance.json').write_text(json.dumps({p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sources}, indent=2) + '\n')
    result = dict(instantaneous=instantaneous_checks(), spatial=[])
    for method in ('n', 'lda_f1'):
        rows = []
        for n in (8, 16, 32):
            row, state = candidate.run(n, 8*n, .5, method, 'smooth')
            row['observed_h_slope'] = float(np.log2(rows[-1]['L1']/row['L1'])) if rows else None
            rows.append(row)
            np.savez_compressed(output / f'{method}_{n}.npz', **state)
            print(json.dumps(row), flush=True)
        result['spatial'].append(dict(method=method, cases=rows))
    (output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    main(parser.parse_args().output.resolve())
