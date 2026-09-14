# Claude 最新 Chapter 4 写作评论的复核

日期：2026-09-13。作者：Codex（GPT-6）。审查对象：log3 §37（Claude Code / Opus 5），以及该节引用的四份 scratch Python 脚本。
当前 checkout：`develop_pureC_RD`，HEAD `5f3db112c8487ce9f597e4c0f8c5e99c2e04531c`；静网格原生基准构建仍为 `943f7ae`。

**结论：章节组织建议可采纳，F1 mask 的核心诊断成立，但空间误差的历史回顾、模型几何、误差归因实验和 Morton 对照口径需要修正。stale-rate 仍是值得研究的模型思路，不能写成已验证的 AREPO 修复。**

本次读取代码、章节草稿、历史报告及原论文，并运行独立标量模型复算；没有修改 thesis、production C 或 Config，没有新增原生 AREPO 运行。保留 Claude 已暂存的 235 行修改，只在 log3 末尾追加本次记录。

## 1. [P1] §37.4 漏读了已经完成的历史排除与时间细化

Claude 将 median-dual/Voronoi 不一致重新列为当前误差的具体候选，并说历史记录没有区分时间和几何来源。这两点都不符合后续记录。

- [log1 的明确反驳](RD_DEVELOPMENT_LOG.md#objection-the-median-dual-vs-voronoi-volume-suspect-does-not-exist-here)（约 line 3676）已检查 extensive 更新、primitive recovery 与误差范数：三者都使用 RD `DualArea`，不是一处 median dual、一处 Voronoi volume。
- 当前代码仍明确区分两条路径：`src/hydro/update_primitive_variables.c:195` 的 RD 分支使用 `Mass / DualArea`；`Volume` 只在相邻的非 RD 分支出现。`residual_distribution_solver.c:3060` 将各三角形面积的 1/3 累加为 `DualArea`。当前基准的误差权重也采用 `Masses/Density`。
- log1 2026-08-01 的完整 dt ladders（约 line 4362）已经给出旧 jittered 家族的半离散外推：production h-orders `1.551/1.312`，外推后 `1.560/1.315`；总解析误差中的时间贡献量级低于 2%，并存在抵消。这不是仅凭 stationary/boosted 对照作出的猜测。
- 更近的 [2026-09-11 原生复核](colombo_re_spike/lda_baseline_convergence.md)使用与当前相同的 glass 家族、终点及步长上限，但物理残差是旧 Roe。标准 GL/F1 在 48²/96² 减半 dt 后，解析密度 L1 分别**增加** `0.9276%/0.8535%`；两数值态的 L1 差为原误差的 `1.4345%/1.3126%`。这直接支持用户关于旧 Yee 时间误差不大的记忆。

**建议改写：**历史 Roe/F1 已有时间误差影响较小的证据；最新 Gauss-U、192²、t=1 尚缺同配置的精细 dt 对照。后者值得补测，但不能把旧的排除结论撤回，或将通用 context 中仍开放的几何解释问题当作当前已发现的 volume 混用。网格不规则性、F1 质量逆近似等仍可讨论，须与 Voronoi/median 混用区分。

Chapter 4 当前红色工作笔记（`chapter4.tex:42–45`）也保留了早期“需检查实现”的提问。它适合在以后获授权整理草稿时更新为代码审计结论，不能反向当作实现仍未知的证据。

## 2. [P1] §37.5 的周期模型几何错误；修正后核心现象仍成立

四份脚本已在 `/private/tmp` 找到并归档。`f1_consistency.py` 的连接索引使用模 n，但 `assemble()` 直接用基本坐标相减，跨边界三角形没有周期展开。这样会把宽度约 1/n 的单元画成横跨整个盒子的长三角形；用绝对面积又掩盖了翻转。

独立稀疏组装精确复现了原文三组范数和两个 dt 序列，因此不是检查了另一份模型。单位周期盒的结果如下：

| n | 原模型总面积，应为 1 | 原模型负向三角形数 | 原 `||I−S⁻¹M||₂` | 正确周期展开后的范数 |
|---:|---:|---:|---:|---:|
| 12 | 3.360967 | 44 | 1.301185 | 1.020864 |
| 24 | 3.673606 | 92 | 1.374722 | 1.021939 |
| 48 | 3.835069 | 188 | 1.416294 | 1.022443 |

周期展开后，三组总面积均为 1、负向三角形均为 0，最长边随 h 缩小；组装满足常数态残差为零、质量列和及全局守恒检查。原模型即使几何错误也通过后面这些代数检查，说明它们不能替代几何覆盖检查。

在正确周期网格上保留 n=24、50% 固定交替 mask、标量速度 `(1,.4)`、T=.05，初值仍为 `1+.3 sin(2πx) cos(2πy)`：

| 步数 | masked 与 equal 的平均 nodal L1 差 | stale-rate 与 equal 的平均 nodal L1 差 |
|---:|---:|---:|
| 50 | 1.33024105e−2 | 1.13441625e−4 |
| 100 | 1.33024184e−2 | 5.65382209e−5 |
| 200 | 1.33024204e−2 | 2.82236088e−5 |
| 400 | 1.33024209e−2 | 1.41004472e−5 |
| 800 | 1.33024211e−2 | 7.04738654e−6 |
| 1600 | 1.33024211e−2 | 3.52298429e−6 |

面积加权结果另存 JSON，具有相同趋势；正确几何模型全序列最大的面积加权质量漂移为 `1.35e−16`。

所以应撤换原模型的定量表述，但**无需撤回“mask 可改变固定 h 的极限算子”的结论**。

源码 `residual_distribution_solver.c:5425–5478` 明确用 frozen `dU=0` 构造 F1 correction；line 5558 起仅为 live 顶点累加 predictor。令 `E=I−S⁻¹M`，则固定 mask 模型中

\[
G_{eq}=v+Ev,\qquad G_{mask}=v+EPv,\qquad
G_{mask}-G_{eq}=-E(I-P)v.
\]

这与 §33/36 的推导、既有原生 Gauss Yee 差异平台相符。恒等式的数值检查也通过。`v+Ev` 可解释为一次以 lumped S 预条件的 Richardson 更新；因为 S 一般不是 M 的对角部分，严格说不宜无条件称为通常的 Jacobi 迭代。

另需收窄两项推论：

1. `||E||₂=O(1)` 是最坏方向的放大量，不自动给出某个 Euler 解、某个 mask 上误差的下界，更不能据此宣称所有 frozen 顶点都有 O(1) 相对误差。应直接考察 `E(I−P)v`。本次修正后的特定模型初始相对 rate 差约为 .378；这不是原生 Yee 的数值预测。
2. `f1_fix.py` 和本次模型都对**所有顶点每个细步推进 ODE**，并每两个细步缓存完整组装 rate；它们没有实现 due-triangle 调度、完整 star 关闭、跨调用 predictor、变化的 live mask 或 MPI。原脚本甚至每个细步重新计算缓存状态的全局 rate。因此模型不能证明实际修复只需“每个粗顶点每粗步多算一次 residual”，也没有测量任何原生节省。

在固定网格、稳定光滑分支及缓存误差受控的假设下，若缓存 rate 误差为 O(Δt_coarse)，`E` 有界，则该替换留下 O(Δt_coarse) 的 rate 偏差。这解释了模型的一阶恢复；它还不是二阶 multirate 方法。移植时须同时补全 lumped 与 F1 两部分以保持元素零和，证明完整 star rate 的来源与时间戳，并测试实际调度及 MPI。**当前可以把它列为待验证修复方向，不能称已修复。**

## 3. [P1] §37.4 的“三分之一判据”和 stationary 论证过强

`A h²+B h` 的拟合只是一个假设的标量误差模型，不能测定误差来源，甚至不能确认真实误差展开一定存在一个独立的线性项。三点数据的拟合斜率为 `1.864/1.761`，原数据为 `1.873/1.710`，并非完全复现。所谓 finest 层的 31% 是拟合中 `B h` 的占比，不是测得的时间误差预算。

应区分

\[
\|U_{h,\Delta t}-U_{ex}\|_1
=\|e_{space}+e_{time}\|_1
\quad\hbox{与}\quad
\|e_{space}\|_1+\|e_{time}\|_1.
\]

二者一般不相等。时间/空间误差可能抵消；减小 dt 后总 L1 可以增加。上节所引原生结果已经出现这种情况。因此“下降约三分之一则为时间、几乎不动则为几何”的二分判据不成立。

同样，解析 stationary Yee 满足连续 `∂t U=0`，不等于插值后的离散初值满足 `R_h(I_h U)=0`。除非证明当前离散精确保持该稳态，否则不能说其时间离散误差“恒等为零”。Uniform preservation 与精确保持非均匀稳态是不同性质。

**合适的补测设计：**先对最新等步 Gauss3/F1、192²、t=1 保持 IC/二进制/面积权重不变，做 `1/1024,1/2048,1/4096` 三档；核实实际步数和 CFL 是否命中，比较数值态的自差及对解析态的误差，再在确认的时间阶下作状态 Richardson 外推。若要确认空间收敛，还应对其它 h 也控制时间误差，不能由单个 finest h 的试验确认整个空间阶或具体几何机制。本次没有启动该原生补测。

## 4. [P2] §37.3 将 Sod 的文献核对信息带进了 KH 图

两张图的目的划分值得保留：KH 守恒历史证明守恒性质；work–precision 比较检验达到给定精度的代价。

但该节最后引用的 `§5.1.1 / Fig.7`、first-order LDA/N、未写终止时间，来自 log3 §34 的 **Sod** 对照审计，不能当作 KH 的复现说明。

已查阅 [Morton et al. (2023) 原文](https://academic.oup.com/mnras/article/518/3/4401/6847219)：DRIFT 质量/能量变化是 **Fig.6**，对应 KH 测试 **§5.2.1**。Fig.6 比较 32²/64²/128² 与 1/2/4/8 bins；KH 小节另说明其密度图通常为 t=2。后一句不能代替对 Fig.6 横轴及终止时刻的单独核对，也不能套用 Sod 的 EOS/网格/时间说明完成 KH 复现。

当前静网格 smooth KH 的 glass48、γ=1.4、vx=±.5、平滑宽度 .025 等，与原文 KH 的均匀网格、vx=±1 等并不匹配。可以做明确标注的历史方法对照，但不能把非匹配曲线之间的全部差异归因于同一个算法改动。约 `2.06e−14` 是 §36 所有 26 次运行的最大归一化四分量漂移，画 KH 能量图时应使用对应 KH 的 `|E(t)−E(0)|/|E(0)|` 历史，不能用该汇总上界代替整条曲线。

## 5. [P2] 效率数据的缺口需要限定到当前 static hierarchy

“所有日志和报告中没有任何 wall-time/效率测量”过于笼统。已有：

- [Gauss 成本报告](colombo_re_spike/kh_gauss_and_cost.md)的 18 次串行原生重复计时，记录 CPU 和 wall time；
- log1 2026-08-04 GL/F1 与 rate-Heun 的原生时间比较（n96 为 7/11 s，n192 为 47/83 s）；
- [moving Euler 原型](colombo_re_spike/euler_flip_closure.md)的 37.3%、58.2%、58.7% 元素工作量统计，明确不是原生 wall-clock speedup。

这些都**不能替代当前 static Gauss3/F1 hierarchy 对 equal-step 的受控 work–precision 曲线**。这个具体缺口仍然存在。2.22/1.75 是 forced 2:1、192² Yee 的密度/速度误差比，不是普遍的 hierarchy 代价，也不是 CPU 比。

“只需给现有 Sod/KH 计时”能提供匹配配置的 runtime 数据，但还不是完整 work–precision。Yee 有解析解，适合先做成本与误差配对；Sod 可用解析参考但有间断，KH 需要确定的参考解或可信的可比较诊断。成本应同时计实际 residual/triangle sweeps、F1/matrix 工作、全网格遍历与 MPI，辅以同硬件串行安排的重复计时；due-element 数仅是其中一部分。

写作优先级取决于所作结论：如果要宣称 hierarchy 更高效，成本证据必须先补齐；如果只报告静网格的守恒实现及精度限制，可以先写，明确效率尚未量化。无需把性能优化或 stale-rate 工程实现变成整章动笔的前置条件。

## 6. 可以直接采纳的写作路线

1. 统一定义 ALE/P1 变量、残差、时间质量与 ledger；将静网格作为 `σ=0`、固定连通性的可控特例。明确 F1/lumped、P1-U/P1-Z 在此极限下仍不同。
2. 先写 AREPO 中静网格实现及验证：误差、守恒、小规模 MPI、hierarchy 的实际精度差异。基本静网格 RD 理论是已有工作，但**在 AREPO 中实现并审计守恒 ledger、时间层级和 MPI 可以作为本项目的实现成果**；不应笼统说静网格部分完全没有贡献。其独创性范围需与已有工作逐项比较。
3. 等步 moving mesh 作为进一步的主要结果，按其各自构建和验证证据描述；静网格通过不自动验证 DGCL、拓扑转移、moving MPI 或 cosmological integration。
4. moving hierarchy 保持为简短、明确未完成的讨论。静网格 frozen-F1 也应注明改变固定 h 的 limiting operator；不因 `RK2` 配置名而称其严格二阶时间方法。
5. 保留“可冻结的、有明确限制的实验基准”这一定位。§37.1 接受的 active-only、counter-streaming、异步余项和熵诊断更正成立；positivity limiter 的旧熵理由应继续撤回，不能把跑完正态样例当作普适 positivity 证明。

## 7. 复现与证据边界

独立脚本：`tests/rd/review_ch37_models.py`。需要 NumPy/SciPy；均为标量、固定几何、固定 mask 的模型代数与 ODE 检查，不是 Euler PDE 或原生 multirate 验证。

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python \
tests/rd/review_ch37_models.py /path/to/new_model_audit.json
```

输出文件必须尚不存在。脚本检查正确周期覆盖、朝向、局部边长、F1 列和、空间残差常数核/全局列和、rate 恒等式、Richardson 恒等式与每档守恒；同时保留错误几何的复现结果作对照。

归档：`/Users/zhenyuwu/arepo_rd/local_runs/chapter4_claude_review_20260913/`。

- `model_audit.json`：原模型/修正几何的全部数据、面积加权结果与拟合；
- `reviewed_sources/`：Claude 四脚本、审查时 log3、独立复算脚本；
- `provenance.json`：上述文件哈希、当前 HEAD、原暂存日志哈希及 thesis 读取前哈希；
- `exact_counterexamples.txt`：重跑原 exact-arithmetic 脚本，复现 §37.1 的 active-only、负压与混合压强算例。异步余项恒等式按日志定义代数核对；原脚本本身没有实现该项检查。

不需要为这次文档与独立模型审查重新编译 hydrodynamics；当前数值原生能力仍以 §33/36 已冻结证据为准。
