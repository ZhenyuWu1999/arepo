# 显式 CR 拓扑算子的耗散、限幅与原生 Euler 测试

日期：2026-09-11；分支 `test/colombo-re-explicit-hierarchy`。
接续 [phase 1](README.md) 和主日志 §20；本轮主记录为 log 3 §21。
用户已授权在测试分支接入 AREPO 并进行 standard hydro tests。

**当前 CR-inspired 低阶拓扑转移确实比原有 high 换基修正更耗散。
原生流体测试已经使用现有 N + RK2；不能把差别归因于没有使用 RK2。
保留原 high、以 CR low 为正性后备的版本基本恢复原精度，但没有显示出
优于原修正的精度收益。** 这里研究的是本分支从 signed swept geometry
构造的显式扩展，不是 Colombo–Re 原文隐式 BDF 方法的完整复现。

## 1. 区分物理 RK2 与几何积分

所有 native runs 都启用 `RD_RK2_TOTAL_RESIDUAL`、moving N、equal step、
ALE contour 和 comoving frame。当前 CR low 在人工几何参数上做 adaptive
forward Euler；这是与物理流体 RK2 不同的积分。

固定几何生成元满足

\[
Q'=-LU,\quad Q=gU,\quad g'=\delta m,\quad
\mathbf1^TL=0,\quad L\mathbf1=-\delta m,\quad L_{ij}\le0\ (i\ne j).
\]

记不变的加权均值为 c，lumped nodal variance 为
\(V=\sum_i g_i(U_i-c)^2\)，可直接得到

\[
V'=-\sum_{i\ne j}(-L_{ij})(U_i-U_j)^2\le0.
\]

因此混合已经存在于精确 ODE；提高人工时间积分阶数不会删除它。
这是 scalar nodal variance 的恒等式，不是 Euler entropy 定理。

独立审计比较 FE、midpoint RK2、Heun RK2 与 DOP853：7 个几何、两种
生成元、420 次固定步积分。FE 最后一次细化的阶数为 1.005–1.010，
两种 RK2 为 2.006–2.042；守恒/常量误差不超过 8.89e-16。
单位方形、完整旧节点质量均为 1，scalar `[1,4,2,.3]`，翻边再翻回：

| graph-minimal 转移 | 保留的节点方差比例 |
|---|---:|
| FE，1 个几何子步（§20 的样例） | 0.226954 |
| FE，每个事件 4 子步 | 0.272489 |
| Heun RK2，每个事件 4 子步 | 0.286250 |
| 同一 ODE 的高精度积分 | 0.285884 |
| 原 unlimited high 修正，配对回翻 | 1 |

这些比例只属于这个诊断，不能读成每个真实 Delaunay flip 都损失 71%
的流体结构。High 的配对可逆性也不表示单次转移保持任意连续场范数，
更不保证正密度/正内能。完整推导、affine 误差及 spectral 对照见
[geometry_rk2.md](geometry_rk2.md)。

## 2. 接入 AREPO 的具体方式

在同一个旧物理时刻 t_n 做表示转移：旧 connectivity → 拉回 t_n 的新
connectivity，然后执行现有 ALE equal-step N/RK2。旧/新 changed triangles
按共享边组成精确 component；每个 component 用同一 collapse point
计算 signed semi-edge sweeps。流体不经过零面积的真实网格。

这构造了一条直接 old-to-new 几何路径，没有重建漂移期间实际翻边的
顺序。一个 changed component 可能包含多个事件，计数不能称为 flip 数。
原生测试最大 component 为 6 个节点；实现上界为 512，超限或无效几何
明确终止。ID、方向、周期 embedding、边界链、nodal swept balance、
完整质量路径与全域实际 pullback mass 总量均有检查。

代码在 `src/hydro/rd_cr_topology.h`，由 solver 中新编译选项控制。
移植了组装后再 subcycle 的 graph-minimal low；同一 component、全部
Euler 分量共用一个 θ，取 `U=(1-θ)Ulow+θUhigh`。High 是我们原来的
uniform-shift correction，并非本轮发明的 CR 高阶算子。

| Config 短名 | 拓扑与时间质量 |
|---|---|
| original | 原 support repair，Arpaia |
| refresh | 原 repair + stage-0 primitive 同步，Arpaia |
| cr_low | CR graph-minimal low，Arpaia |
| cr_positive | 原 high + CR low 正性限幅，Arpaia |
| cr_dmp | 上项再限制同时间 component 的密度上下界，Arpaia |
| cr_campoli | 与 cr_positive 配对，只改 Campoli endpoint mass |

CR 模式均同步 primitive fields。为隔离这个差别，主要精度比较采用
`refresh`；它只修正原 repair 后 Density/Pressure/velocity/Csnd 与
`ale_uold` 不一致的 stage-0 读取。原 `original` 仍单独保留。
密度 DMP 不等于压力、速度或 entropy 的 DMP；其原生容差为
`128*eps*max(rho)`。本轮四分量 Euler 限定 v_z=0。

## 3. 原生 standard hydro tests

完成 20 个一进程原生 AREPO runs，每个只保留初末两个 snapshots：
Yee n24 六方法、n48 四方法；Sod n32 六方法及半时间步四方法。
所有 run 正常结束、输出有限正密度/正压力，并发生实际 connectivity
变化。这是 equal-step Euler 测试，不是 production Euler hierarchy/MPI。

Yee 使用现有 polar IC generator、seed=20260911、boost=(0.5,0)，
n24 为 578 节点、n48 为 2304 节点，t=0.2；最大步长 .005/.0025。
Sod 为周期方盒中的两道跳跃、32×32 jittered 节点、γ=1.4、t=.08，
在 x∈[.25,.75]、波尚未相遇的中央 Riemann 问题上计算误差。
最大步长 .001，半步对照 .0005；AREPO dyadic 实际步长约为
.000625/.0003125。所有空间误差使用 RD median-dual 权重 `m/rho`，
不使用 snapshot 中 Voronoi Volume。

| 测试 | 方法 | 密度 L1 | 压力 L1 |
|---|---|---:|---:|
| Yee n24 | refresh | .00261535 | .00344900 |
| Yee n24 | cr_low | .00284189 | .00369416 |
| Yee n24 | cr_positive | .00261582 | .00345001 |
| Yee n24 | cr_dmp | .00261840 | .00345107 |
| Yee n48 | refresh | .00143104 | .00188575 |
| Yee n48 | cr_low | .00160020 | .00208194 |
| Yee n48 | cr_positive | .00143104 | .00188575 |
| Yee n48 | cr_dmp | .00143183 | .00188657 |
| Sod n32 | refresh | .05081558 | .05745035 |
| Sod n32 | cr_low | .05137482 | .06424246 |
| Sod n32 | cr_positive | .05088581 | .05751846 |
| Sod n32 | cr_dmp | .05104105 | .05762262 |

Yee n48 的 low 密度误差高约 12%；Sod 的 low 压力误差高约 12%。
Yee n24/n48 的 low 速度 L1 分别约为 refresh 的 2.24/2.26 倍。
完整 Euler 误差混合了物理离散、不同后续网格轨迹与拓扑转移，不能
直接把 L1 差额解释成纯拓扑耗散系数；独立几何实验才隔离了该因素。

`cr_positive` 和 `cr_campoli` 在所有本轮标准测试中都接受 θ=1。
因此这些 runs 验证了保留 high 的精度，而未激活正性后备分支。
Yee n24 positive 处理 42 个 components；Sod positive 419；Yee n48
positive 135。Hard density DMP 在相应 runs 的 41/42、418/429、
135/135 components 上限幅。不同方法的网格反馈使计数不同。
两个 Yee 分辨率不能独自证明空间阶数，特别是 dt 同时发生变化。

## 4. 守恒与耗散分别核对

原 support repair 改了 `ale_uold` 和 extensive storage，但 stage-0
物理 flux 仍会读旧 primitive。这次增加受编译开关保护的同步，并用
`refresh` 对照测量：Sod 原方法质量/能量误差约 9.67e-7/1.96e-6，
同步后降至 6.65e-9/7.23e-9；流场 L1 基本不变。

剩余 Arpaia 漂移**复现了主日志 §10 已确定的 endpoint rebase 缺陷**，
不是本轮首次发现，也不应归为 CR 拓扑自身不守恒。§10 的公式为
`Qnew=B+(m+/D)L`，附加总量为 `sum((m+/D-1)*L)`，没有普遍零和保证。

| 控制 | 相对质量误差 | 相对总能量误差 |
|---|---:|---:|
| Yee n24 cr_positive / Arpaia | 2.526e-9 | 3.318e-9 |
| Yee n24 cr_positive / Campoli | 1.447e-16 | 2.197e-16 |
| Sod n32 cr_positive / Arpaia | 6.539e-9 | 7.025e-9 |
| Sod n32 cr_positive / Campoli | 1.972e-16 | 3.227e-16 |
| Sod n32 cr_positive / Arpaia / dt÷2 | 1.648e-9 | 1.765e-9 |

半步后的误差约为四分之一，支持本例固定终止时刻的 O(dt²) 累积
漂移解释。Campoli 配对几乎不改变流场精度，恢复到 roundoff 守恒。
这并不自动给出改造 Arpaia 的唯一方法，也不是全系统正性的证明。
物理 CFL 诊断继续保留；本轮正性是已测轨迹的结论，不能由拓扑
凸性推导任意流体步长下的正性。

## 5. 独立回放、限幅与 hierarchy 范围

- 4608 个随机 Euler 同时间转移，以及 48 种配置各 128 次重复事件；
  最大相对守恒误差 8.49e-16，随机 affine high 误差 4.45e-16。
  这些样例实际触发了正性限幅，与标准流体案例的 θ=1 情况互补。
- 原生每个 CR run 的前八个 event dumps 共 104 个，独立 Gauss swept
  geometry/Python map 回放后，完整状态尺度相对差异 ≤1.80e-13，
  C 转移相对守恒 ≤4.22e-16。抽样都为四点 component；另有一般
  4/5/7/12 点几何自检，不能声称独立回放了 native 六点事件。
- 密度 DMP 的边界在微小变化下条件数很差：最大 θ 差异 5.94e-7，
  微小分量的相对差异 1.63e-7，完整状态绝对差异仍 ≤4.44e-13。
  回放发现 Python limiter 的旧 roundoff fallback 会直接减半 θ；
  已改为保留二分时最后一个实际通过判据的候选，避免引入额外耗散。
  实际 Yee event 已作为 `test_cr_limiter_roundoff.py` 回归例保存；
  修改后重跑上述随机、hierarchy 和 native replay 审计。
- 将 limited map 接入既有一阶 scalar local-closure 参考，固定网格和
  prescribed motion、depth 8/1024、uniform/smooth/peak，共 36 个案例
  通过。共同端点守恒 ≤3.78e-15，最小 scalar ≥6.95e-14。
  这没有把原生 Euler RK2 与 hierarchy 接通，也没有证明二阶 multirate
  正性；拓扑前后的局部区间结算仍是下一步独立工作。

## 6. 图片、复现与下一步

原始 campaign：`/Users/zhenyuwu/arepo_rd/local_runs/colombo_re_hydro_20260911`。
该目录的 README、JSON summaries、provenance、冻结的 binary/config/生成
header、param、run.log、初末 HDF5 均保留。前期缺少 HDF5 header flags 的
Sod 初始化失败在 `smoke_prechecks` 中单独保留，不计入 20 个完整 runs。
图均提供 PNG 与同名 PDF：

- [Sod ρ/v/p 剖面](/Users/zhenyuwu/arepo_rd/local_runs/colombo_re_hydro_20260911/figures/sod_profiles.png)
- [Yee 密度与解析解误差图](/Users/zhenyuwu/arepo_rd/local_runs/colombo_re_hydro_20260911/figures/yee_density_maps.png)
- [Yee 径向剖面及 entropy 误差](/Users/zhenyuwu/arepo_rd/local_runs/colombo_re_hydro_20260911/figures/yee_radial_profiles.png)
- [几何 RK2 与不可消除的 low 混合](/Users/zhenyuwu/arepo_rd/local_runs/colombo_re_hydro_20260911/figures/geometry_rk2_dissipation.png)
- [Arpaia/Campoli 质量守恒](/Users/zhenyuwu/arepo_rd/local_runs/colombo_re_hydro_20260911/figures/mass_conservation.png)

建议继续保留原 high，并把正性后备与局部 interval closure 分开研究。
纯 CR low 适合做可证明的同时间正性基线，目前没有理由替代原 high
作为默认精度方案。严格密度 DMP 会限制 smooth extrema，不应把它
自动当作最佳 limiter。下一轮 hierarchy 集成先用 Campoli 守恒参考，
再单独处理 RK2 trace/temporal mass 与提前结算的一致性。
现有数据不支持宣布 moving Euler hierarchical + MPI 已完成，也不支持
据此否定 Colombo–Re 原文或所有由其启发的低耗散扩展。
