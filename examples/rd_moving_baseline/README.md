# Moving RD baseline: lazy disabled

User decision, 2026-10-10 (log3 §228): use Campoli plus conservative mode-1
transfer as the baseline, with lazy disabled. Lazy is an optional comparison.

These **2D** Config files were generated from
`tests/rd/run_interval_hierarchy_gates.config(scheme, variant, mode=1)` at
`7c2d949`. The eight configurations passed `flip_campaign_checks.check_configs`;
none contains `RD_ALE_LAZY_FLIP` or the old diagnostic repair. This is a
configuration check, not a new full hydrodynamic validation campaign.

| Files | Time stepping | Transfer |
|---|---|---|
| `Config_{N,LDA,B,HLLC}_equal.sh` | Global equal steps | `RD_ALE_FLIP_TRANSFER` |
| `Config_{N,LDA,B,HLLC}_natural.sh` | Actual-interval hierarchy, natural bins | Built into `RD_ALE_INTERVAL_HIERARCHY` |

All explicitly select high mode 1, floor fraction 0.5, density hull off and
entropy bound off. Natural-bin configurations explicitly set the frozen CFL
ledger limit to 1. N/LDA/B use gamma 1.4; HLLC uses gamma 5/3, as in the source
gate templates. Pair each Config with matching IC and parameter definitions.
Natural bins may collapse to equal bins on a particular problem; measure the
actual populated bins.

Use the equal-step configurations for the initial conservation/accuracy
reference. Use the natural-bin configurations for the separate hierarchy
comparison. Do not change historical campaign drivers or archived Configs to
relabel old results: several historical drivers deliberately default to mode 0.
New campaign preparation should use these explicit files or the same explicit
mode-1/no-lazy definition, and freeze source, configuration, binary and inputs
under the repository's normal provenance rules.

There is no AREPO 3D RD Config here: the native RD implementation still rejects
3D. See `dev_log/RD_3D_FEASIBILITY_20261010.md` for the assessed port and the
independent feasibility probes.
