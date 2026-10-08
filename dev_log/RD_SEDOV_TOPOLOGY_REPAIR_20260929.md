# Sedov：重新启用 connectivity repair 的原生对照

作者：Codex。日期：2026-09-29。对应 log3 §159。
用户问是否可以像以前一样做 connectivity repair。本轮实际复用当前分支中的
`rd_ale_apply_topology_repair()`，并运行两种原 Sedov 初值。

**结论：旧 repair 对守恒漂移确实有效，但直接复用会破坏正性。两组强 Sedov
均在 repair 内产生负压，未达到 t=0.05。需要保守且保正的 remap，而不是直接打开
原来的 unlimited repair。** 不能将此次失败归于后续 Rusanov/RK stage。

## 原公式及其适用边界

记旧连接上的面积为 S_i，新连接拉回同一物理时刻的面积为 Ŝ_i，
δS_i=Ŝ_i−S_i。旧代码按面积变化节点在新网格上的相邻关系组成 support patch P，
不是逐条重建真实的翻边时序。对每个 patch，

    D_P = Σ_{i∈P} δS_i U_i,
    w_i = Ŝ_i / Σ_{j∈P} Ŝ_j,
    Q_i^H = S_i U_i + δS_i U_i − w_i D_P,
    U_i^H = Q_i^H / Ŝ_i = U_i − D_P / Σ_{j∈P} Ŝ_j.

最后一个节点用剩余权重闭合舍入误差。于是 ΣQ^H=ΣQ^old；uniform 状态下
ΣδS=0，修正消失。但共同的密度/动量/能量密度平移不是 admissible states 的
凸组合，因此不保证 ρ>0、E−|m|²/(2ρ)>0。Sedov 冷背景尤其容易受此影响。

独立的单位正方形翻对角线反例已执行：旧面积为 (2,1,2,1)/6，新面积为
(1,2,1,2)/6。ρ=1、m=0，节点1的 E=100，其余 E=1e−6；D_E≈16.6666665。
旧 high repair 令三个冷节点的 E≈−16.6666655，尽管修正前后总能量严格匹配。
这说明失败不依赖 RK2、Roe 奇异矩阵或某个特殊 timestep。

## 实现与历史一致性

log3 §21.4 已发现：旧 repair 更新 ale_uold/临时 Q，却没有同步 predictor 读取的
Density/Pressure/Vel。此次仅在 `RD_RUSANOV_LOW_ORDER` 与
`RD_ALE_TOPOLOGY_REPAIR_DIAGNOSTIC` 同时开启时，从修正后的 U 恢复这些原始变量，
以及 Utherm/Csnd。保留既定区间 mesh velocity；不调用带 floor/时戳等副作用的
通用 primitive recovery。原修正公式和其失败断言均保留。

此新组合原来被编译 guard 禁止，本轮解除这一项；其他 Rusanov 限制保持。
普通 N/LDA 及无 repair Rusanov 的运行分支未改变。没有实现新的 limiter，
没有切换默认 Config。尤其没有把历史测试分支的 CR limited-high 直接合入生产。

## 匹配设置与原生结果

IC 字节与上一轮相同：SWIFT glass128²、周期单位盒、γ=5/3、ρ₀=1、v₀=0、
p₀=1e−6、注入能量1，21点或 r=0.05/130点注入。实验 Rusanov 空间分布，
N/lumped RK2 时间项，Arpaia modified dual-area coefficient，lab frame，
标准 mesh regularization，adaptive equal steps，CFL=0.1、cap=0.01，单 MPI rank。
OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=1。未平滑 IC 或提高背景压力。

| 种子 | 最后接受时刻 | repair 失败时刻 | 最低失败压力 | 成功非零 repair 的步数 |
| --- | ---: | ---: | ---: | ---: |
| 21点 | 0.00545654296875 | 0.00546875 | −0.0190041899 | 213 |
| 130点 | 0.0015869140625 | 0.00159912109375 | −0.000343357786 | 0 |

21点失败 patch 有两个负压节点，ID7932 和7977；130点为 ID8418。
130点在首次非零 repair 就失败。表中计数是发生非零修正的步数，不是 edge flip 数。
两组分别接受788/130步；此前1576/260个 Rusanov stage 的密度、内能均为正。
实际 CFL 最大0.104797/0.083289，b 最小0.497598/0.498795；均通过原有界限。
uniform gate 完成16步，逐点误差1.11e−15。

**只在共同到达的时刻比较守恒：** 21点在 t=0.00545654296875，

| 相对总量变化 | 无 repair | 原 repair + 一致的 predictor |
| --- | ---: | ---: |
| 质量 | −1.75028022e−4 | −1.97228878e−9 |
| 能量 | −1.24978715e−2 | −1.04590062e−6 |

即能量损失从1.2498%降为0.0001046%，但下一次 repair 导致负压终止。
已成功 repair 的全局守恒审计最大缺口4.44e−16。
130点在首次非零 repair 前，两组总量一致至舍入，能量变化约−4.92e−8。
不能据早期结果宣称 repair 已解决 t=0.05 的守恒或 Sedov 稳定性。

剩余的小漂移与既有 Arpaia endpoint conversion 问题一致（见 log3 §10/21/52）；
此次没有逐步输出并独立闭合该项，因此不把全部剩余误差确定归因于它。

## 如何保留 repair 的收益

沿用历史 §21 的思路：旧 Q^H 作为精度候选，再构造本身守恒、保正的低阶 Q^L，
用同一 patch 参数 θ 混合：

    Q_i = (1−θ) Q_i^L + θ Q_i^H,   0≤θ≤1,
    ΣQ^L = ΣQ^H = ΣQ^old.

选尽可能大的 θ，同时使所有节点满足 ρ>0 和正内能。高候选合法时 θ=1。
**不能仅把原来的 −w_iD_P 改成 −θw_iD_P**：那会留下 (1−θ)D_P 的守恒缺口。
也不能对各节点独立选 θ 而不重新保证配对守恒。

一个简单的保正参考是 Q_i^L=Ŝ_i Ū_P，其中
Ū_P=ΣS_iU_i/ΣŜ_i。在正面积、patch 面积闭合条件下，它是旧状态的凸组合，
守恒且保正，但会混合整个 support patch，可能非常耗散。此次正方形反例核对了
此低端点的守恒/正性，仅用于解释，不是已实现的 native limiter。
更值得复用的是历史独立分支的 CR 几何低端点加 limited-high；此前 Yee/Sod
都接受θ=1，尚无当前强 Sedov 的 native fallback 证据，不能照搬其成功结论。
修复 remap 后还要独立检查 physical endpoint Q 的总量闭合。

## 验证与复现

冻结档案：`../local_runs/sedov_topology_repair_20260929_v1/`。包含源码tar/hash、
working-tree patch、独立 build/binary/Config/generated header/linkage、参数、输入、
所有成功/失败日志及快照。binary SHA256：
`bbba3d6878bd65d9a04991c74caaf6e79948b901239f16b8470dfee362afd852`。
分析入口 `examples/Sedov_2d/analyze_topology_repair.py`；完整审计和图在
`analysis/verification.json`、`analysis/conservation_comparison.png`，图已视觉检查。
无修正参考复用 `../local_runs/sedov_positivity_20260929_v2/` 的不可变原始结果。
所有 binary/config/IC/参数/source.tar 均核验哈希，所有已保存快照有限且物理。

五个 make check_rd 均通过。最初检查误用系统 Python（缺 numpy），改用项目
21cmfast Python 后完成；这是环境调用失败，不是数值失败。原生 build 一次成功。
结束时无活动 solver。没有 thesis、COSMA、commit 或 push 操作。
