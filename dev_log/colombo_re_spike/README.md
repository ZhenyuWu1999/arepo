# Colombo-inspired 显式拓扑与 hierarchy：测试分支结果

分支：`test/colombo-re-explicit-hierarchy`。
起点：`315bece11785f4e05c98c07819b0842a8cf4d156`；先以 `c479457`
保存此前未提交的 log 3 §§18–19 和 ledger 正性审计，再开展本轮实验。
日期：2026-09-10 开始。主日志见 log 3 §20。

2026-09-11 后续：[原生 Euler 测试、限幅及几何 RK2 的耗散检查](phase2_hydro.md)
已完成，见 log 3 §21。下面保留第一阶段的原始范围与结果。

同日进一步完成用户要求的 [Sod 96² N/LDA + RK2 配对比较](sod96.md)，
见 log 3 §22；CR low 在 N 中增大误差，在 LDA 中通过减弱振荡降低了
本例净误差，不能把低阶混合与所有流体测试的误差变化等同。

**结论：已建立可手工检查的显式几何转移，并把它与真正的局部节点区间
结算接通；一阶 scalar 参考不需要 future-outflow reserve 或递归全域
wakeup。但低阶拓扑耗散明显，还不是生产 moving Euler/RK2 方案。**

## 1. 工作分工与证据

按用户要求使用了 5 位独立子 agent；运行槽上限为主任务加 3 位，因此
分批复用了本任务中已有 agent，没有另开用户任务。主任务额外完成
模块集成、独立 ODE/精度比较和 moving-scalar 驱动。

| 子任务 | Agent | 主要产物 |
|---|---|---|
| signed swept geometry | cr_swept_geometry | geometry.py、geometry.md；另复核 moving 驱动 |
| 显式算子与 Euler 转移正性 | review_claude_positivity | explicit.py、explicit_operator.md |
| 一阶局部状态区间结算 | review_positive_ledger | local_closure.py、hierarchy.md |
| 随机 bins、相邻/周期 cavity 反例审查 | adversarial_design_review | adversarial.py、adversarial.md |
| AREPO 接入与独立 C 小核 | voronoi_rd_alternative | topology_kernel.c、c_kernel.py、arepo_integration.md |

上表代码短名均指 `tests/rd/` 中带 `colombo_re_` 或 `audit_cr_` 前缀的
文件。最后一位 agent 的历史名称含 voronoi，但本轮只做 P1 工程审计，
没有恢复 native FV 开发。

Colombo & Re 提供几何思路与比较基线；下面的显式同伦和局部时间耦合
都是本分支提出的扩展，**不是原文 BDF 算法的复现**。
[原文](https://arxiv.org/html/2204.11668v1)。

## 2. 可以直接核对的四点数学

组合同一 cavity 的 old ghost/new records，构造矩阵 L，满足

    1^T L = 0,    L 1 = -delta_m,    L_ij <= 0 (i != j).

在人工参数 s∈[0,1] 上取 g(s)=g_old+s delta_m，并执行

    A = diag(g(s)) - ds L
    Q_next = A [Q/g(s)]
    g_next = g(s)+ds delta_m.

只要 ds L_ii <= g_i(s)，A 非负；列和为 g(s)，故 Q 总量守恒；行和为
g_next，故 Q_next/g_next 是旧状态的凸组合。由此，同一时刻 admissible
Euler 输入保持正密度和正内能，常量场保持。此证明不使用 Euler 矩阵
N 的正性假设，也不演化通过零面积的真实 triangle。

单位方形 AC→BD 的 `graph_minimal` 例子尤其便于人工检查：

    delta_m = (-1,1,-1,1)/6
    L = (1/24) [[ 8,-1,-2,-1],
                [-3, 4,-3,-2],
                [-2,-1, 8,-1],
                [-3,-2,-3, 4]].

规则六邻居完整旧质量为 (1,1,1,1)，完整新质量为 (5,7,5,7)/6，ds=1
满足条件。一般 cavity 按上述对角条件选择几何子步。

默认 `spectral` 规则每个 record 用 alpha=max|nu|；新 `graph_minimal`
规则用 alpha=max(0,-min nu)，只对 pure-geometry 组合算子建立符号条件，
不声称是全局最优耗散，也不能用于替换 Euler physical LF 波速。

完整推导见 [explicit_operator.md](explicit_operator.md)。每个节点跨
records 的 swept balance 必须为零；仅总面积变化为零并不够。

## 3. 时间耦合中实际简化了什么

翻边时，只结算两个被删除 triangles 不足以刷新四个节点的状态。
新的**一阶参考**按以下规则处理：

1. 结算所有含任一 cavity 节点的旧 triangles 到事件时刻。
2. 恢复四点真正的同时间 Q/g；外围节点只收 extensive 增量，U 不刷新。
3. 执行同时间几何转移，刷新四点状态与 trace epoch。
4. 新 triangles 从事件时刻开始，保留者沿用 last time；原 bins 不变。

只要某节点的 trace 改变，其所有 incident triangles 都已闭合，就没有
跨越状态变化的欠缺区间。closure 边界的节点 trace 不被强制修改，故
不需要递归刷新整个区域。一阶参考不需要 RK predictor 或 frozen-until。

规则网格每次涉及 4 个状态刷新、16 个 triangles、14 个 Q 接收节点。
16/512 是一个 16×16 网格例子的局部范围，**不是任意非结构网格的固定
上界**；实际工作量取决于节点度数、事件密度和相邻 cavity。

守恒比较必须尊重现有 RD hierarchy 的语义：不同时间区间的 raw Q
在中间 fine tick 的和不必恒定。共同时间的虚拟结算总量、以及全部
区间完成后的宏同步总量才是该方案的审计对象。此检查不实际推进全域。
独立源码审计确认现有 static hierarchy 采用同样的宏同步目标。

## 4. 已跑验证

| 检查 | 结果与适用范围 |
|---|---|
| 1000 随机凸 cavity 几何 | GCL、nodal balance、独立 Gauss 积分交叉核对误差≤3.34e-16 |
| 4096 次 admissible Euler 几何转移 | adaptive 规则全部保持正性；相对守恒≤7.12e-16 |
| 30 个 static scalar 基准 | 包含预期失败对照；21 个安全 closure 例守恒误差≤2.45e-15 |
| 18 个 CR + hierarchy 组合 | 安全 closure 通过；继续冻结旧 U 的 CR 对照仍出现负值 |
| 24 个独立随机调度例 | 1769 flips；含 846 次同 tick 追加 flip、514 次周期 cavity；共同时间守恒≤2.00e-15 |
| 16 个 moving scalar ALE 例 | 线性规定节点轨迹，含 1:1024；共同时间守恒≤4.44e-16，均匀态误差≤1.49e-14 |
| C99 独立小核 | 256 Euler cases；C/Python差≤4.35e-16，守恒≤6.44e-16；另有 ODE refinement 与 scalar callback |

moving 驱动检查整个区间的 quadratic signed-area minimum、实际 g 的
闭合、转移前 Q/U 正性，以及节点自上次完整刷新后的累计 scalar 流出
系数不超过当前 g。独立复核发现的“转移可能掩盖之前负值”的诊断缺口
已修正。本组轨迹满足该充分条件，但没有建立任意网格运动的自动 CFL
选择器。只有线性、固定 nodal velocity；尚未测试速度中途变化。

随机相邻 cavity 的驱动是独立扩展模型，使用本次 `geometry_records`
和默认 spectral 的 adaptive `topological_remap`；1769 次事件因此也
检查了 CR 几何转移与静态 scalar hierarchy 的组合。它没有把原先单
cavity 驱动自动扩展为任意网格生产接口，也没有测试 moving Euler。

## 5. 不能被“全部通过”掩盖的负面结果

对单位 cavity 上的 affine scalar 1+0.2x-0.1y，单次转移改变节点值：

| 转移 | 最大节点变化 |
|---|---:|
| CR spectral 低阶 | 0.117857 |
| CR graph_minimal 低阶 | 0.0535714 |
| 此前 full-patch low | 0.0428571 |
| 此前 high uniform-shift | 浮点零 |

相同非均匀场翻边再翻回后，weighted variance 的保留比例分别约为
0.01459、0.22695、0.34620、1。最后一项没有无条件正性保证，所以这个
表不能直接据此选 high 为最终算法。它说明**新低阶几何算子虽然有明确
正性证明，却不比旧修正在精度上自动更好**。几何子步趋细只收敛到该
耗散 ODE；不会消除 ODE 本身的耗散。缩小 cavity 的 affine 误差为 O(h)。

继续冻结旧 U 时，CR spectral/minimal 的 peak 对照分别达到
-0.357643、-0.0804715；同样转移配合完整局部 closure 后保持正。
只刷新四点却少结算外围 incident triangles 的对照仍破坏守恒。

## 6. 当前工程判断

优先保留本次较简单的**完整局部状态区间结算**思路。几何 LF 算子可作
保正低阶参考或将来的限制端点，尚不宜直接作为默认拓扑算法。下一道
关卡是低耗散/高阶转移与实际 Euler 时间更新的配合，而不是继续叠加
future-outflow reserve。

现有 moving RD 的 predictor/corrector 在同一 mesh event 连续执行；
不要误套 static split-call 路径可能已预付半步的解释。但二者都不能
直接拿这个一阶参考当作 RK2：真实区间、预测状态、质量项与额外节点
刷新仍须相容。生产接口详见 [arepo_integration.md](arepo_integration.md)。

尚未完成：生产 AREPO 驱动集成、Euler 物理输运、RK2 时间精度、动态
bins、真实 Delaunay crossing、变化网格速度、MPI、重力/宇宙学。
本分支没有更改 `src/`、原分支指针、论文或 log 2。

## 7. 复现

仓库根目录，Python 环境需 NumPy/SciPy，最后一项另需 C99 编译器：

```sh
PY=/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python
$PY tests/rd/colombo_re_geometry.py --samples 1000
$PY tests/rd/colombo_re_explicit.py --samples 512 --seed 20260910
$PY tests/rd/audit_cr_comparison.py
$PY tests/rd/audit_cr_local_closure.py
$PY tests/rd/audit_cr_coupling.py
$PY tests/rd/audit_cr_adversarial.py --samples 24
$PY tests/rd/audit_cr_moving.py
$PY tests/rd/audit_cr_c_kernel.py --samples 64 --seed 20260910
```

原始 JSON、摘要、源码/结果 SHA256 和环境版本：
`/Users/zhenyuwu/arepo_rd/local_runs/colombo_re_spike_20260910/`。
