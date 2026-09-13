# 两种 high repair 与 LDA 速度振荡核对（实际 N_x=48）

**分辨率更正：**文中 96² 表示全周期盒子；图中半盒激波管的实际 N_x=48。
后续以实际分辨率为主，旧目录名仅保留作 provenance。

2026-09-11，接续 Sod96 报告及 log 3 §22。用户询问 basis repair 与
high+CR fallback 的区别，并指出旧 Sod 图似乎没有这么大的 vx 振荡。
本轮核对源码、旧图及作图程序，并用相同 96² 初值追加三个隔离对照。
没有改 solver C，也没有重跑旧历史 commit。

## High 公式相同，patch 和失败处理不同

High 是拓扑表示转移的候选端点，不是另一种物理 LDA/RK2 求解器。
对于一个 patch P，旧/新完整节点面积为 m-/m+：

\[
D_P=\sum_{j\in P}(m_j^+-m_j^-)U_j^-,\qquad
U_i^H=U_i^- - D_P/\sum_{j\in P}m_j^+.
\]

Basis repair 选择 Δm 超出 roundoff envelope 的节点，通过新 triangles
形成 support components，直接采用 high；若产生 inadmissible 状态则
终止。最后一个 correction weight 取剩余量以闭合浮点守恒。

High+CR fallback 按精确 old/new changed triangles 的共享边形成
components，保留相关的零净 Δm 节点；另计算正性的 CR graph-minimal
low，取 `U+=(1−θ)Ulow+θUhigh`。整个 component 的全部守恒分量共用
θ，尽量取 1。同 patch、同输入、θ=1 时，两者数学上相同；实际分组、
节点集合和处理顺序可以不同，故完整流体轨迹不要求相同。

本轮两个 high+fallback Sod96 runs 全部 θ=1，没有把 low 混入结果。
Admissibility 只要求正密度、正内能，并不限定 vx 上下界。因此它不是
速度 maximum principle 或震荡探测器，不能消除仍满足 rho,p>0 的散点。

## 相同初值的额外对照

三个新增 runs 为 moving no_repair、moving original repair（未刷新
primitive）、static LDA/GL/F1 RK2；与上轮相同 IC、gamma1.4、t=.08。
静网格去掉不适用的 mesh regularization 参数。三个 run 均正常完成，
每个保留初末两张 HDF5。以下直接统计 .25<x<.75 的全部节点：

| 对照 | vx 最小 | vx 最大 | RMS(vy) | 相对质量漂移 |
|---|---:|---:|---:|---:|
| Static LDA RK2 | −1.0323 | 1.0949 | .01540 | 1.97e-16 |
| Moving，关闭 repair | −.5041 | 1.7644 | .04545 | 3.15e-4 |
| Moving，旧 repair | −.8830 | 1.7849 | .05486 | 8.33e-7 |
| Moving，basis repair + refresh | −.8694 | 1.8019 | .05498 | 1.86e-9 |
| Moving，high + CR fallback | −.8838 | 1.8425 | .05465 | 6.14e-10 |
| Moving，CR low | −.4015 | 1.0373 | .01224 | 6.20e-9 |

大速度振荡不需要新 CR fallback 或 primitive refresh 才能发生。
但 repair 仍会通过状态/几何反馈改变幅度，不能据此证明它毫无放大
作用。No-repair 跨翻边不守恒，只能作成因诊断，不能推荐为数值方案。
Static LDA 也有很强的局部激波 undershoot，但没有 moving 情况中同样
广泛的高速度散点。应区分局部 dispersive undershoot 与二维速度散点。
“完成且 rho,p>0”不等于该 LDA 激波解已满足质量要求；CR low 降低
这组有振荡基线的误差，也不证明一种普遍更优的拓扑算法。

![Matched velocity controls](/Users/zhenyuwu/arepo_rd/local_runs/cr_sod96_regression_20260911/figures/lda_velocity_controls.png)

用户进一步指出 Morton 是 static mesh，并要求静网格对照。上述 static
run 正是同一 IC 的该项验证，并非复现 Morton 的原参数。其 density L1
为 .0202691、pressure L1 为 .0192008，质量/总能量漂移为 1.97e-16/0。
下图采用相同坐标范围，保留全部节点散点；实线为面积加权 bin means。

![Static versus moving LDA](/Users/zhenyuwu/arepo_rd/local_runs/cr_sod96_regression_20260911/figures/static_moving_lda_profiles.png)

[静网格对照 PDF](/Users/zhenyuwu/arepo_rd/local_runs/cr_sod96_regression_20260911/figures/static_moving_lda_profiles.pdf)

## 旧图的实际内容

- `useful_resources/moving_mesh_sod/morton2023-sod-profiles-n128.png`
  是本地组合图，其中 moving-LDA 曲线是后来附加的 ALE 扩展，不能称为
  Morton 原论文结果；**Morton 原基准是 static mesh**。本地附加曲线
  已有 vx 振荡。但 `plot_morton2023.py:70,145` 画的是
  512-bin 加权均值，没有全部粒子散点。其 row-offset 网格加 1e-6 h
  jitter、gamma5/3、box2、t=.2；当前为 Cartesian .08 h jitter、
  gamma1.4、box1、t=.08，不能直接比较视觉包络。
- `shear_eigenvalue_floor/sod-lda-shear-floor-profiles.png` 三行是
  rho、p、vy，**没有 vx**；这张有粒子 scatter，使用 relaxed glass48，
  比较 static、moving baseline、shear floor=.45。
- `shear_eigenvalue_floor/sod-entropy-floor-full-profiles.png` 同样没有
  vx；其程序只画 bin means 和 ±1σ，不画全部粒子极值。

旧 glass 日志的 moving transverse RMS≈.0201、max|vy|≈.128，也确实
比当前值小，但其采样域和测试条件不同。尚未逐项隔离 jitter、EOS、
分辨率、CFL 与旧版本的影响。因此不能把全部幅度差归于作图或 jitter，
也不能宣称已排除所有回归。应据具体旧图核对用户记忆，而不是用
“LDA 本来就振荡”带过。

## 复现与存档

运行 `tests/rd/audit_cr_sod_regression.py NEW_ROOT REFERENCE_ROOT`，
分析 `tests/rd/plot_cr_sod_regression.py NEW_ROOT REFERENCE_ROOT`。
REFERENCE_ROOT 是上轮 `local_runs/cr_sod96_20260911_omp1` 的绝对路径。
本次 NEW_ROOT 为 `local_runs/cr_sod96_regression_20260911`。
OMP_NUM_THREADS=1、OPENBLAS_NUM_THREADS=1，两个 singleton 最大并发。
新增耗时约43.3/46.3/17.5秒（no repair/original/static）。冻结的
binaries/configs/headers/build logs、相同 IC、params、初末 snapshots、
logs、summary、PNG/PDF 和 provenance 均保留。主日志为 §23。
