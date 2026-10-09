"""Shared checks for flip/hierarchy campaign drivers (Codex review R1, 2026-10-09).

The solver default of RD_FLIP_HIGH_MODE changed from 0 to 1 at 8e325e9, so a
Config that relies on the default silently changes meaning.  Every Config
that transfers (RD_ALE_FLIP_TRANSFER or RD_ALE_INTERVAL_HIERARCHY) must state
the mode, and no two methods of one campaign may have identical Configs.
"""
import re


def flip_mode(text):
    """Explicit RD_FLIP_HIGH_MODE of a Config text, or None if it does not transfer."""
    lines = [l.strip() for l in text.splitlines() if l.strip() and not l.lstrip().startswith('#')]
    transfers = 'RD_ALE_FLIP_TRANSFER' in lines or 'RD_ALE_INTERVAL_HIERARCHY' in lines
    modes = [l for l in lines if re.fullmatch(r'RD_FLIP_HIGH_MODE(=\d+)?', l)]
    if not transfers:
        return None
    assert len(modes) == 1 and '=' in modes[0], f'transfer Config must set RD_FLIP_HIGH_MODE=0/1 explicitly: {modes}'
    return int(modes[0].split('=')[1])


def check_configs(configs):
    """configs: {method: Config text}.  Returns {method: mode or None}."""
    modes = {m: flip_mode(t) for m, t in configs.items()}
    canon = {}
    for m, t in configs.items():
        key = tuple(sorted(l.strip() for l in t.splitlines() if l.strip() and not l.lstrip().startswith('#')))
        assert key not in canon, f'methods {canon.get(key)} and {m} have identical Configs'
        canon[key] = m
    return modes
