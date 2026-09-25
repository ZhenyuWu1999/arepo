# Moving Yee frame convergence and Gresho boost10

作者：Codex；请求：Zhenyu。2026-09-24。

本轮只补充数值证据和图，不修改 thesis、solver 或默认 Config。用户倾向于把 lab frame 用于 thesis reference，把 co-moving 保留为代码优化选项，待本轮结果审核后确认。

## 当前源码的 Yee 配对测试

所有16个新 Yee runs 均完成 t=1，保存状态的密度、压力均为正，没有负质量或 A2 终止。复用经过 hash 验证的4个当前源码二进制及既有4个 uniform gates，后二者不是此次新构建/新运行。两 frame 的 Config 唯一差别是 RD_ELEMENT_COMOVING_FRAME。

设置：periodic box10，glass48²/96²/192²，gamma1.4，beta5，boost=(1,0)，CFL.2，dt caps1/256、1/512、1/1024；96²另做 dt 减半。实际步数逐例核验。N/Roe 保留完整 mesh correction，N temporal lumping；LDA 用 P1-U Gauss3 与 mixed-stage F1。当前 Arpaia geometry、new-connectivity 上两次 sweep，没有 topology repair。

解析解在最终移动节点坐标上评估。L1 用最终 median-dual area=m/rho 归一化加权，速度误差用二维向量 Euclidean norm。表中的阶为 h 与 dt 同时减半的观测阶，不是固定 h 的时间阶，也不是严格二阶定理。

| Scheme / frame | rho L1: 48 / 96 / 192 | rho orders: 48→96 / 96→192 | velocity orders |
|---|---|---|---|
| N_lab | 0.0030303958 / 0.0017013889 / 0.0009103007 | 0.8328 / 0.9023 | 0.8377 / 0.9176 |
| N_comoving | 0.0030303954 / 0.0017013014 / 0.00090988934 | 0.8329 / 0.9029 | 0.8377 / 0.9178 |
| LDA_lab | 0.0010615635 / 0.00029661438 / 8.7756938e-05 | 1.8395 / 1.7570 | 1.7526 / 1.3845 |
| LDA_comoving | 0.0010615627 / 0.00029657034 / 8.7586732e-05 | 1.8397 / 1.7596 | 1.7517 / 1.3934 |

| Method | Relative total-mass drift at 48 / 96 / 192 |
|---|---|
| N_lab | -1.61965e-05 / -3.70181e-06 / -2.48036e-06 |
| N_comoving | -1.6197e-05 / -3.59879e-06 / -2.34142e-06 |
| LDA_lab | -1.49573e-05 / -3.85379e-06 / -1.48254e-06 |
| LDA_comoving | -1.49571e-05 / -3.85628e-06 / -1.42775e-06 |

| 96² dt halving | rho L1 relative change | velocity L1 relative change |
|---|---:|---:|
| N_lab | -0.1725% | -0.0982% |
| N_comoving | -0.1607% | -0.1040% |
| LDA_lab | 0.1450% | 0.6078% |
| LDA_comoving | 0.1934% | 0.5106% |

Frame differences in analytic errors (co-moving / lab − 1):

| Resolution / method | rho error change | velocity error change |
|---|---:|---:|
| yee_N_lab_n48_dt256 | -1.34629e-05% | -1.91091e-05% |
| yee_N_lab_n96_dt512 | -0.00513889% | 0.00301969% |
| yee_N_lab_n96_dt1024 | 0.00668732% | -0.00279349% |
| yee_N_lab_n192_dt1024 | -0.0451895% | -0.00503237% |
| yee_LDA_lab_n48_dt256 | -7.54868e-05% | -0.000491657% |
| yee_LDA_lab_n96_dt512 | -0.0148478% | 0.0643985% |
| yee_LDA_lab_n96_dt1024 | 0.0334438% | -0.0323138% |
| yee_LDA_lab_n192_dt1024 | -0.193952% | -0.550363% |

![Yee convergence](/Users/zhenyuwu/arepo_rd/local_runs/yee_frame_convergence_20260924_v1/figures/yee_frame_convergence.png)

## Gresho + boost10

复用已验证的当前源码 September24 Gresho 对照，未重跑。jitter48²，unit box，gamma5/3，boost=(10,0)，t=1。绘图前去掉平移及 bulk velocity，点颜色是节点方位速度，无额外场插值。

| Scheme | lab v_phi L1 | co-moving v_phi L1 |
|---|---:|---:|
| N / Roe split | .0197645029 | .0197644772 |
| LDA / Gauss3 | .00792314439 | .00792314433 |

两种 frame 的宏观精度基本一致，N/LDA 的方案差异更明显。co-moving 改善矩阵条件的效果仍成立：boost10 的非退化元素子集中，median paired condition-number ratio约2.4万，但这不等于当前测试的解误差改善倍数。

保留旧 gate 的限制：Gresho boost10 的 N/lab uniform 最大压力变化1.1822e−12，略超过原有绝对1e−12阈值；该 gate 仍标记为 failed。不能因 science runs 完成或图重合而宣称所有门禁通过。本轮 Yee 使用 boost1，不能替代 Yee boost10 或更大 boost 的测试。

![Gresho boost10](/Users/zhenyuwu/arepo_rd/local_runs/yee_frame_convergence_20260924_v1/figures/gresho_boost10_frames.png)

## KH 质量漂移与 moving hierarchy 的历史边界

用户关于 edge flip 的记忆有实证依据。Log2 §71 的旧 KH 对照中，相对质量漂移从2.523e−3降到6.923e−6，说明拓扑修正去掉了该例的主要误差。但后续 §73.5 明确指出剩余误差仍与 flips 相关，不能按当时的日志字段自动判定其全部物理来源。该历史量级也不能直接套到当前未修正实现的1.2–1.4%。

当前端点总量分解（log3 §78 与 September18 SCIENCE_REVIEW）：

`sum(Q_new-Q_old) = sum((H-m_old) U_old) + sum((m_new-D) (U_new-U_old))`

其中 H 是在新 connectivity 上回溯得到的旧面积权重，m_old 是实际旧权重，D 是 Arpaia modified divisor。第一项为 topology basis 变化，第二项为 divisor 到实际 endpoint storage 的差异，无 flip 时仍可能非零。本轮没有对当前 KH 的两项重新作逐步定量分解。

Moving hierarchy 还多一个 coupling 问题：翻边会使旧三角形提前消失、新三角形在局部时间步中途出现。仅在 endpoint connectivity 上按当前 timebin 回溯，可能漏算或重复计算存续时间。守恒空间 transfer 不自动修复这些时间区间。见 log3 §11 及 RD_topology_hierarchy_conservation_20260909.md。

源码已有受限的 N-only RD_ALE_HIERARCHICAL 原型，不应写成从未实现。log3 §35 的独立 Euler/actual-interval 原型给出可行性证据，但一般 native moving hierarchy、LDA/F1、拓扑历史、MPI/restart 与长期精度仍未完成验证。因此当前 thesis moving reference 使用 global equal timesteps。

## 结论与复现

配对frame对rho L1的影响不超过0.20%，对velocity L1不超过0.56%，远小于此例N/Roe与LDA/Gauss3组合的差异。LDA高分辨率速度阶的下降在两frame中同时存在。

这些数据支持将 lab frame 作为当前 thesis reference 的计算坐标，并把 co-moving 留作改善矩阵条件的可选优化。此判断不解决 topology/endpoint 的守恒问题，也不将 KH 的长期 frame 差异认定为零。就 KH t10 transverse kinetic energy 而言，scheme 间差异确实大于各 scheme 的 frame 差异；这是该诊断量的结论，不能推广到所有指标。

所有精确参数、源包、binary/config hashes、ICs、native logs、三个快照/例及分析脚本保存在：

`/Users/zhenyuwu/arepo_rd/local_runs/yee_frame_convergence_20260924_v1`

当前 source tar SHA256: `b2a915f657bfc46ae6cce1cc315ea3776fafb74e8cd3e8d08b6d7a43302dd9c6`。

未修改 thesis、生产代码或默认配置，未 commit/push。
