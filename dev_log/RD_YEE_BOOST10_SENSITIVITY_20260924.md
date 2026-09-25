# Yee LDA boost sensitivity, 2026-09-24 — preliminary

Requested by Zhenyu; prepared/analyzed by Codex. Source and solver unchanged. Boost1→10, static/moving LDA/Gauss3 lab frame at48²,96²,192² to t1; matched ICs except boost, matched steps1024/2048/4096. Four uniform gates and two192 short pilots passed. Four192 science runs remain in background. No384/768 or thesis edits.

|96², t1 | boost1 density L1 | boost10 density L1 | boost10/1 |
|---|---:|---:|---:|
|static|1.7031580e-4|1.8668099e-3|10.9609|
|moving|2.9420123e-4|2.9433091e-4|1.000441|

Final median-dual area-weighted L1 at native generator positions, exact periodically advected center, no fitted recentering. Moving/static density ratio at boost10=.157665; vector-velocity error ratio=.0487785. Boost1 controls use4×smaller dt than earlier campaign, and density errors at48/96 change only roughly1%. Completed96 plot visually checked:

![96 profiles](/Users/zhenyuwu/arepo_rd/local_runs/yee_boost10_static_moving_20260924_v2/figures/yee_lda_boost96_profile.png)

48² lab moving boost10 failed A2 raw residual conservation at step243,t≈.237305, defect4.88117e-12 > tolerance2.15509e-12. Preceding predictors positive, failed case retained, no t1 error assigned and no tolerance change. Matched48co-moving diagnostic (only frame Config flag differs; same source/IC/dt) passes uniform and reaches t1, density L1 .0010557291 and vector-velocity L1 .0013091227. This is frame-sensitive numerical behavior, not proof of the precise matrix operation at fault. Do not substitute this diagnostic into the lab convergence curve or silently change thesis baseline.

The96 result supports the expected benefit under stronger bulk advection. Boost-insensitive error at a fixed resolution is different from an h-independent floor; the latter is not established. Previous density errors continued decreasing through384. Topology/geometry, temporal terms, reconstruction/quadrature and matrix/F1 effects are candidates, not measured causal decompositions. Global fits require all three completed points; failed series stays incomplete.

Archive and live handoff: `/Users/zhenyuwu/arepo_rd/local_runs/yee_boost10_static_moving_20260924_v2/README.md`. Main session5902; independent final analyzer94005. The main parent is expected to assert after all remaining runs complete owing to retained48failure; the independent watcher still analyzes results. Final tables/figures and visual QA pending. No commit/push.

## 2026-09-25 recovery correction

At13:59CST none of the original four192 solver processes, parent or watcher was alive. Logs stopped together at23:36 previous night; cause unknown. Thus the prior background-running statement was incorrect. No192 restart checkpoint existed. All partial outputs retained. Only four192 cases restarted from unchanged ICs in `local_runs/yee_boost10_static_moving_20260925_recovery_v1`, using a one-shot launchd job independent of the conversation. ParentPPID1 and advancing logs verified. Existing completed/failed cases reused without changes. Final summary/plots and visual QA remain pending in the recovery archive, not the original archive.

## Superseded running status, 2026-09-25

All local recovery/co-moving tests were stopped by the user for COSMA migration. No192 t1 result is available from these partial runs. See [the current handoff](RD_COSMA_YEE_HANDOFF_20260925.md) and termination records; the earlier running statuses above are historical.
