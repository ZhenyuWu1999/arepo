# N + Gauss3 contour 与 Roe split：Sod / 长时间 moving KH 对照

作者：Codex；请求：Zhenyu。日期：2026-09-24。

## 结论与适用范围

已在当前源码中仅开放 **equal-step ALE N + Gauss3** 的实验配置，复用已有 N 差额等分修正。没有加入 positivity limiter、改变 CFL/时间步上限或放宽 A2。LDA 的原有路径保持。

历史 LDA/Roe 负质量已用原二进制精确复现；当前源码中 LDA/Roe 也发生负质量，但时间和粒子不同。N 的结果必须独立判断，不能把 LDA 的失败推广到 N。单元分配守恒、完整更新的全局守恒、正性、形态和精度是不同的检查。

当前配对实验中，N/Roe、N/Gauss3、LDA/Gauss3 均完成 KH 到 t=10，LDA/Roe 在 t=1.0327148 因负质量停止。四组 Sod 均完成。N 的两种残差给出相近 Sod 误差，不能据此宣称 Gauss3 普遍更准确或必不可少。

## 当前源码：相同设置的 2×2 对照

| Scheme / residual | KH 终止时间 | KH 状态 | 最后保存密度范围 | 最大已保存质量相对漂移 |
|---|---:|---|---:|---:|
| N / roe_split | 10 | 完成目标 t=10 | 1.10966–2.0884（t=10） | 0.0138187 |
| N / gauss3 | 10 | 完成目标 t=10 | 1.07742–2.03056（t=10） | 0.0136335 |
| LDA / roe_split | 1.03271 | 负质量停止 | 0.571155–2.53262（t=1.00006） | 0.00294601 |
| LDA / gauss3 | 10 | 完成目标 t=10 | 0.892303–2.06077（t=10） | 0.0123776 |

**失败曲线只统计到最后有效快照，不将其当作失败端点或 t=10。**

| Scheme / residual | Sod 状态 | density L1 | velocity L1 | plateau vx std | vx min / max |
|---|---|---:|---:|---:|---:|
| N / roe_split | 完成 t=.08 | 0.0235933 | 0.0550657 | 0.0139150 | -2.164323e-08 / 1.011044 |
| N / gauss3 | 完成 t=.08 | 0.0233814 | 0.0551844 | 0.0146614 | -2.274083e-08 / 1.01116 |
| LDA / roe_split | 完成 t=.08 | 0.0172331 | 0.0447580 | 0.0281524 | -0.7949014 / 1.059788 |
| LDA / gauss3 | 完成 t=.08 | 0.0169389 | 0.0442896 | 0.0258498 | -0.737231 / 1.058177 |

Sod L1 使用当前 median-dual area 归一化加权，选择原始 x∈(.25,.75) 的单管，与相同坐标/时间下解析解比较。平台速度 std 是相对区域加权均值，使用 ξ=2(x−.25)∈[.70,.76]。没有将 N 更强的耗散或较小散布直接称为更高精度。

## LDA 负质量：历史精确重放与当前复现

历史 frozen e33aea3 二进制 SHA256：`2709ff437c30a194a537f261369a08f253bc9a08310644937395435c8a4299d2`。同一 IC/参数在 t=.800476 再次使 ID923 的质量成为 −1.06377e−5，前一步质量 1.016e−5。五个已保存快照的坐标、rho、p、速度、质量与原始档案逐项完全相同。

当前 LDA/Roe 的末尾诊断：

```text
RD-ALE-PREP time=1.0327148 dt=0.00030517578 elements=4608 minA=[7.782e-05,7.782e-05,7.782e-05] coverage=[0.99999999999999867,0.99999999999999922] delta_identity=2.600e-18 uniform=0 stationary=0 static_bit_mismatch=0 static_max_diff=0.000e+00
RD-ALE-FINISH time=1.0327148 uniform=0 max_dU=8.209e-01 endpoint_cons=5.139e-05 temporary_change=[5.140635e-05,2.278056e-05,-2.645732e-05,8.243333e-06] rebase_change=[-1.395413e-08,-1.044300e-08,2.933039e-09,-6.867396e-08] endpoint_change=[5.139239e-05,2.277012e-05,-2.645438e-05,8.174659e-06] totals=[1.5048573273490999,0.22621816927896651,-0.0003066805248867527,6.4215428893049831]
RD-RK2 time=1.0327148 f1_lumped=0 predictor_min_rho=1.009795e-02 predictor_min_press=1.367776e+00 stage_beta=mixed
very bad...i=679 ID=374 mass=-8.234e-06 oldMass=1.36862e-05 utherm=338.627 pos=0.164079|0.694084|0
TERMINATE: ******!!!!!******  Code termination on task=0, function do_validity_checks(), file src/hydro/update_primitive_variables.c, line 169: stop
```

当前失败前的 predictor 仍为正；空间残差分配检查未失败，负质量在完整两阶段更新后检查最终状态时触发。这证明的是正性失效，不能把空间残差守恒误差或 Gauss 求积误差直接当作已确定的根因。

历史实现含 refreshed-basis 拓扑处理。当前分支没有该 RD_ALE_TOPOLOGY_REFRESH 选项，使用一次 rebuild、在新 connectivity 上做两次 sweep 的公共 begin/end hook。不能把两版之间的变化归因于单独一个 residual；本报告的 2×2 表格始终使用同一份当前源码。

## 设置与实现

- 当前源码基于 `adc424ba93f8cb98ff494dd8e98b41fafcd2e98b` 的冻结工作树，包括用户原有未提交改动；826 个 tracked 文件逐一校验，完整源码包和 patch 已保存。
- 8 个独立配置/二进制；每种 scheme 和 residual 各自有 KH（谱 CFL）及 Sod（原 CFL）版本。全部使用 element co-moving frame、Arpaia 面积对、一个 MPI rank，OMP/BLAS 各 1 线程，最多 4 个并发任务。
- KH：smooth tanh、宽度 .025、glass48²、unit box、gamma1.4、rho1/2、p2.5、vx±.5、vy=.1 sin(4πx)，CFL=.3、dt cap=.02、目标 t=10，每 .2 输出一次。每个初始扰动波长约 24 个初始点间距。
- Sod：periodic box128²、单管有效初始 Nx≈64、gamma1.4、CFL=.08、dt cap=1/3000，原始时间 t=.08 对应单管归一化时间 τ=.16。
- N 使用 diagonal lumped temporal mass，LDA 使用 mixed-stage F1；这是两种完整方案的对照。同一 scheme 内的 Roe/Gauss 比较保持该 scheme 的时间质量选项。
- Gauss3 总残差先独立计算。N raw 分配后加入 `(Phi−sum rawN)/3`；A2 验证目标总和。当前修改没有开放 N/Gauss5、B/Gauss、N/static Gauss 或 moving hierarchy。

## 验证与局限

- 8 次 native uniform 全部通过，rho/p/v 最大变化 1.9984e−15。
- `make check_rd` 四个已有代数检查全部通过；8 个 native science runs 保留所有完成/失败结果；另有 1 次历史负质量 replay。
- 当前非均匀 moving tests 存在可测的总质量/能量漂移。三个完成的 KH 在 t=10 的质量相对漂移为 1.19–1.38%，JSON 保留每个快照的值。不能因 A2 通过就宣称完整 moving update 严格守恒，漂移根因仍需单独定位。这也是结果与历史 topology-repair 档案分开报告的原因。
- Gauss3 在此改善 LDA/KH 的生存性，不能证明一般 positivity、收敛阶、KH 长期准确性，也不能证明 N 必须使用 Gauss3。未做新的 MPI/分层时间步/sharp-KH 验证。

## 产物与复现

- [完整 JSON](/Users/zhenyuwu/arepo_rd/local_runs/n_gauss3_split_20260924_v1/summary.json)
- [配置、编译及运行说明](/Users/zhenyuwu/arepo_rd/local_runs/n_gauss3_split_20260924_v1/README.md)
- [源码/实现核对](/Users/zhenyuwu/arepo_rd/local_runs/n_gauss3_split_20260924_v1/code_review.md)
- [历史重放核验](/Users/zhenyuwu/arepo_rd/local_runs/n_gauss3_split_20260924_v1/legacy_replay/verification.json)

![Sod profiles](/Users/zhenyuwu/arepo_rd/local_runs/n_gauss3_split_20260924_v1/figures/sod_profiles.png)

![KH evolution](/Users/zhenyuwu/arepo_rd/local_runs/n_gauss3_split_20260924_v1/figures/kh_evolution.png)

![KH diagnostics](/Users/zhenyuwu/arepo_rd/local_runs/n_gauss3_split_20260924_v1/figures/kh_diagnostics.png)

本轮未修改 thesis，未 commit 或 push。
