# LDA 基线复核：advected Yee 空间收敛、辅助时间阶梯与 glass Sod

2026-09-11，接续 log3 §25 与 `heun_baseline_history.md`。用户要求把
advected Yee 的空间收敛纳入基线，时间收敛作为辅助指标。本轮新增
21 组 Yee 与 1 组 Sod 原生 AREPO 运行，复用上一轮两组 Sod；不改变
solver、默认配置或论文。源代码为 `0899c7e`，测试分支为
`test/colombo-re-explicit-hierarchy`。

## 比较对象与口径

三种方法都保持 static mesh、Roe total residual、LDA 空间分配、相同
初值、equal timesteps、双精度及现有 DEBUG assertions。只比较时间
质量处理与积分方式：

1. **Lumped LDA Heun**：对 `v=−S⁻¹R_LDA` 做真正 Heun；配置增加
   `RD_DIAG_LDA_LUMPED_TEMPORAL`。不是历史上的 Taylor predictor 混合路径。
2. **Standard GL/F1**：现行 two-pass total-residual correction，固定 h
   的 leading rate 为 `G=(2I−S⁻¹M_F1)v`。
3. **F1 rate-consistent Heun**：对 G 做真正 Heun，配置增加
   `RD_RK2_RATE_CONSISTENT_HEUN`；保留 F1，不是把时间质量换回 lumped。

Yee 使用现有 `yee_boost_common.py` 的解析态和 IC 生成器：box=10，
γ=1.4，β=5，boost=1，中心初始为(5,5)，终点 t=1，generator sampling。
SWIFT glass48 分别作 1×1、2×2、4×4 周期铺接后缩放到同一个 box。
这是**同一 glass 家族的铺接序列**，不是三个独立松弛的 glass。

- 主空间序列：48²、96²、192²，Δt=1/256、1/512、1/1024。
- 辅助时间序列：固定48²，Δt=1/256、1/512、1/1024、1/2048。
- 空间误差的时间敏感性复核：96² 再跑 Δt=1/1024；48² 的半步已包含
  在时间阶梯中。

Yee 的 N 是整个10×10 box 的等效分辨率，平均间距 h=10/N；没有
Sod 的“中央半区需要除以二”问题。Sod 仍标**单管实际 Nx≈64**，完整
周期 box 为128² glass 节点；玻璃没有字面意义上的规则列。
Sod γ=1.4、t=0.08、CourantFac=.08、MaxSizeTimestep=1/3000，复用
`sod_glass_nx64_20260911` 的完全相同 IC。相同 CFL/cap 不保证各方法
逐步 dt 相同，实际 timestep 统计保存在 summary 中。

误差统一使用 RD median-dual 面积 `Masses/Density` 归一化加权，不能
误用 Voronoi Volume。所有方法按 ParticleIDs 对齐，检查同一初始
坐标、守恒态和面积；静态末态坐标及面积也检查不变。
空间序列严格说是 **h 与 Δt∝h 的联合细化**；半步复核用于判断其
时间误差敏感性，而不是把有限个 h 点称为完整的半离散收敛证明。

时间阶数使用同一网格上数值解之间的差：

\[
D(\Delta t)=\|\rho_{\Delta t}-\rho_{\Delta t/2}\|_1,\qquad
p=\log_2[D(\Delta t)/D(\Delta t/2)].
\]

不从对解析 PDE 解的总误差平台直接拟合时间阶。
summary 另存密度 L2，以及守恒向量 `(rho,rho vx,rho vy,E)` 的 L1/L2
自收敛；向量使用未另行量纲归一化的欧氏长度，主结论采用密度指标。

## 空间结果：真正 Heun 仍不能修复 lumped 的非定常精度损失

| 方法 | ρ L1，48² | ρ L1，96² | ρ L1，192² | h-orders |
|---|---:|---:|---:|---:|
| Lumped LDA Heun | 2.913729e−3 | 1.558756e−3 | 7.788923e−4 | 0.902 / 1.001 |
| Standard GL/F1 | 6.430158e−4 | 1.748167e−4 | 5.245707e−5 | 1.879 / 1.737 |
| F1 rate-consistent Heun | 6.551337e−4 | 1.778519e−4 | 5.319881e−5 | 1.881 / 1.741 |

速度向量 L1 的 h-orders 分别为 .935/.956、1.811/1.861、1.814/1.866；
密度 L2 和压力也支持同样的区分。192² 上 lumped 的密度误差是标准
GL/F1 的14.85倍，速度误差约14.70倍。两种 F1 的空间结果几乎重合，
标准 GL/F1 的三点密度误差也复现了旧日志的数字。

这确认“lumped 在 Sod 上更平顺”不足以恢复它作为非定常二阶基线的
地位。但 **1.88/1.74 不应写成已经证明 glass 上渐近二阶**。
旧 `mass_matrix_order_analysis.md` 还记录同一 glass 家族到384时的
下一段斜率1.481，并分析了 GL 的质量逆截断与网格不规则性；本轮
没有重跑384。这里只确认当前分辨率范围内 F1 明显优于 lumped，
不把旧文档的经验模型升级成对任意网格的普遍定理。

## 辅助时间结果：阶数不同，实际误差影响较小

| 方法 | 密度时间 p，前/后两组三层阶梯 | 守恒向量 L1 时间 p，最细一组 |
|---|---:|---:|
| Lumped LDA Heun | 2.0038 / 2.0014 | 2.0007 |
| Standard GL/F1 | 0.9916 / 0.9958 | 0.9961 |
| F1 rate-consistent Heun | 2.0003 / 1.9988 | 2.0003 |

全部21组 Yee 的实际同步步数与设置的256/512/1024/2048完全吻合；
日志 Systemstep 与相应1/d一致到打印精度，没有某档被 CFL 偷换步长。
所有 Yee 的 `f1_lumped` 计数为0，时间阶梯不受 rank-deficient mass
fallback 干扰。

从主空间测试的 dt 再减半，对解析密度 L1 的相对变化：

| 方法 | 48² | 96² |
|---|---:|---:|
| Lumped LDA Heun | −0.000408% | −0.000196% |
| Standard GL/F1 | +0.9276% | +0.8535% |
| F1 rate-consistent Heun | −0.00981% | −0.00830% |

“总误差变化小”本身可能含误差抵消，因此同时测了**数值态之差**。
其密度 L1 相对于原解析误差的比例，三种方法在48²分别为
.00362%、1.4345%、.02533%；在96²分别为.00207%、1.3126%、.02222%。
这些数值共同支持：当前 h-ladder 的主要区分来自空间/质量处理，
不是时间步选得不够小。此判断限于这里的终点、CFL、网格与方法。

在48²最细两档上，用已测得的 p=1/2 作 Richardson 状态外推：

- GL/F1 与 F1 rate-Heun 的外推密度态 L1 差为1.1783e−8；各自对
  解析解的误差为6.550453e−4、6.550479e−4。
- Lumped 的外推解析误差仍为2.913713e−3；它与 rate-Heun 的外推
  密度态差为2.679605e−3。

这是有限阶梯的近似外推，不是精确的 dt→0 解。但它独立支持两种
F1 共享 G 的半离散极限，lumped 积分的是另一个 v。
标准 GL/F1 在有限步长下略低的误差含有少量时间/空间误差抵消；
不应把这约1–2%的优势写成普遍优越性，也没有理由仅凭时间 p≈1
丢弃已复现的空间结果。

## Sod：修复时间阶没有消除 F1 关联的速度振荡

| 方法 | ρ L1 | vx L1 | p L1 | vx范围 | vy RMS |
|---|---:|---:|---:|---:|---:|
| Lumped LDA Heun | .0234691 | .0558457 | .0231901 | [−2.40e−8,1.14390] | .00453044 |
| Standard GL/F1 | .0157632 | .0389946 | .0150246 | [−.77657,1.00935] | .01023829 |
| F1 rate-consistent Heun | .0158931 | .0392544 | .0151398 | [−.76181,1.01037] | .01020684 |

Rate-Heun 的密度 L1 比标准 GL/F1 大约0.824%，大幅负 vx undershoot
基本保留；图上两者的激波前速度低谷、密度与压力低谷都非常接近。
因此固定 h 的一阶时间误差不足以解释或解决这组振荡。
Lumped 的主要负速度低谷消失，但接触附近仍有 overshoot，且波形
更宽、ρ/vx/p 的 L1 都更大，不能称为无振荡或更准确的统一基线。

实际 Sod 步数：lumped512、标准GL/F1 845、rate-Heun843；lumped始终
dt=.00015625，F1两种为.000078125–.00015625。因此这是一致 CFL/cap
的实用比较，不是各方法逐步固定 dt 的纯时间积分隔离。上一轮
GL/F1 半步控制也保留了强负速度，见 log3 §24。

Sod 的 `f1_lumped` 最大计数分别为31207、31207、63975。源码表明
这是 `solve_rank<4` 的保守时间质量 fallback 计数，**不是 positivity
limiter 的触发次数**。Rate-Heun 在两个 mass-action 阶段累计，不能
把接近两倍的计数解读为两倍的坏元素；lumped diagnostic 在覆盖
T_time 前仍经过该计数位置，也不能据此推断它实际使用了多少 F1。
本轮没有关掉已有 rank-deficient fallback。

所有输出快照的ρ与p保持正值；负 vx 指速度分量的 undershoot，
不等于 Euler admissibility（ρ>0、p>0）被破坏。这些运行也不构成
positivity 或 maximum-principle 的证明。

## 当前判断与未解决范围

主指标保留 **advected Yee 空间精度 + Sod 全节点激波质量**，时间
阶梯作为必须如实记录的辅助诊断。当前证据排除了两个简单归因：
真正 lumped Heun 的空间问题不是其时间积分不够二阶；F1 的 Sod
大幅 undershoot 也没有因采用真正 Heun 而消失。

保留三种实现作为区分空间质量处理、时间积分、激波行为的参考。
本轮不切换 production 默认，不认为已找到兼顾所有目标的最终
基线。继续沿当前 P1 RD 路线时，下一项物理问题仍是 F1 质量修正
附近的激波行为，以及 log3 §24 中 zero-motion ALE contour 的额外
scatter；不能让 edge flip、CR 或 hierarchy 的变化代替这两项审计。
没有新做 moving mesh、hierarchy、MPI 的成功性声明。

## 验证、图片与复现

22组新运行全部正常退出。分析检查了节点数、RD面积、初值逐ID
一致、静态几何不变、末态时刻、ρ/p正值、有限守恒态、Pressure
输出一致性以及 Yee 的实际步长。新运行总质量相对漂移最大
1.45e−15、总能量7.69e−16；这里的总量用 median-dual masses 与
internal+kinetic energy 计算。没有因为振荡而丢弃节点或仅展示 bin
平均；Sod 同时显示全部中央半区节点、RD面积加权均值和解析曲线。

结果根目录：
`/Users/zhenyuwu/arepo_rd/local_runs/lda_baseline_glass_20260911`。
保存 `campaign.json`、`summary.json`、完整运行日志/快照、独立冻结的
三份 binary/config/header/linkage、IC/source helpers/source snapshot、
SHA256 provenance。旧Sod数据保留原路径并在provenance中引用其hash。
所有图同时提供PNG和PDF：

- [Yee 空间收敛](/Users/zhenyuwu/arepo_rd/local_runs/lda_baseline_glass_20260911/figures/yee_spatial_convergence.png)
- [辅助时间阶梯与半步效应](/Users/zhenyuwu/arepo_rd/local_runs/lda_baseline_glass_20260911/figures/yee_temporal_diagnostic.png)
- [Sod 三种基线的速度图](/Users/zhenyuwu/arepo_rd/local_runs/lda_baseline_glass_20260911/figures/sod_velocity_baselines.png)
- [Sod 完整ρ、vx、p图](/Users/zhenyuwu/arepo_rd/local_runs/lda_baseline_glass_20260911/figures/sod_three_baselines.png)

运行入口 `tests/rd/run_lda_baseline_convergence.py` 接收 fresh root、
glass48文件、已有Yee helper、旧Sod根目录。分析入口为
`tests/rd/analyze_lda_baseline_convergence.py ROOT`。
原生运行最多并发两例，`OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=1`。
本机Python为 `/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python`，
绘图设置 `MPLCONFIGDIR=/private/tmp/cr_matplotlib`。复现构建需完整
AREPO checkout；`source_snapshot` 是本次关键文件的归档而非完整源码树。
