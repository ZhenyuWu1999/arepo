# Yee A2 tolerance audit and co-moving run choice, 2026-09-25

User decision: enable co-moving for ongoing moving-mesh numerical comparisons; do not promote it to thesis default. Gresho boost10 previously passed, so mechanism remains unresolved. Codex inspected unchanged production source and the archived48Yee failure. No assertion or solver changes.

## What is checked

`src/hydro/residual_distribution_solver.c:1223` checks the raw element residual identity, before a timestep/global sum:

D = max_k |Phi_k - sum_i phi_ik| <= 4096 DBL_EPSILON S.

For LDA (`:5102`), S is the maximum component of |Phi_k| + sum_i,p |K^+_ikp| |x_p|, plus phi_scale from residual assembly. This pre-cancellation scale avoids demanding tiny relative error against a nearly vanishing Phi. It is not a literal zero-error test or a fixed1e-12 absolute threshold. It also is not a demonstrated bound on every operation upstream: eigenmatrix construction/cancellation, solve and numerical-rank projection are distinct sources. The code comment calling it a forward-roundoff bound should not be interpreted as a proven bound for the full pipeline.

Observed48Yee lab failure: stage0, t=.23730469, triangle4544, D=4.8811713134963575e-12, S=2.3695518079228197, tolerance=2.1550948148822679e-12. Thus D/S=2.0599555e-12 versus allowed9.0949470e-13, excess factor2.264945. Multiplying the tolerance by more than2.265 would accept this one event, but establishes neither later stability nor global conservation. D/S is relative to the arithmetic scale, not to Phi, total mass or total energy.

The failing triangle's full matrix, singular values and component residuals were not dumped. Earlier larger absolute RK2 defects passed because their S was larger; RD-WORST only prints a new absolute maximum. Thus existing worst-case logs cannot reconstruct this exact failure. The previous step's aggregate SVD/rank counts do not identify this triangle's rank.

## Useful decomposition for a future targeted diagnostic

Let Sminus=sum_i K_i^-, B=sum_i K_i^+, and x be the computed solve output. Ignoring final dot-product/summation rounding for this algebra,

Phi - sum_i phi_i = Phi + B x = (Phi - Sminus x) + (Sminus+B)x.

The first term tests linear-system compatibility/solve residual (including effects of numerical-rank truncation); the second tests the assembled split identity. Final floating-point products/sums add their own errors. Measuring these separately on the failed element, with singular values, would distinguish a scale-bound underestimate from a discarded residual component or an inaccurate matrix identity. A large condition number alone does not prove this cause.

`rd_solve_upwind_system` uses LU with a small pivot-ratio trigger for DGELSD, whose RD_SVD_RCOND=-1 default uses machine precision. Contour residual compatibility with a numerically truncated range is not automatic. This is a candidate explanation, not a claim about the observed triangle. Co-moving changes the conservative-variable representation and arithmetic conditioning; passing with it is evidence of sensitivity, not unique attribution. Gresho and Yee differ in local states/geometry, so equal boost does not imply equal singular spectra or assertion margins.

## Action taken

Tolerance4096 and all solver code retained. Verified exact-source archived co-moving binary, sole Config difference RD_ELEMENT_COMOVING_FRAME. New campaign `../local_runs/yee_boost10_comoving_20260925_v1/` has moving co-moving at BOTH boosts1/10 and ALL48/96/192 resolutions; static controls stay lab. No mixed-frame curve. Reuses already completed48boost10 co-moving case/uniform gate. Adds boost1 uniform, boost10 short192 pilot and five science cases. Existing lab/static recovery continues separately.

Two additional singleton workers, at most6 total, both OMP_NUM_THREADS and OPENBLAS_NUM_THREADS=1; MaxMem512MiB. One-shot launchd label com.zhenyuwu.codex.yee-comoving-20260925-v1. All artifacts/inputs/parameters archived; final three-point fits and native density profiles generated after static controls and co-moving runs complete. Final visual QA pending. Existing48lab failure remains unchanged. No thesis/default Config edits or commit/push.

The user subsequently stopped all local tests for COSMA migration. See [the current handoff](RD_COSMA_YEE_HANDOFF_20260925.md). The scientific tolerance assessment above is unchanged.
