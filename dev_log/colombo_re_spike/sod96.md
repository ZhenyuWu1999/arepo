# Sod 实际 N_x=48（全周期盒子 96²）：N/LDA + RK2，CR 与 basis repair 配对比较

**分辨率更正：**`sod96` 是存档名称，单个激波管区域长度为半盒，实际
纵向分辨率为 48；先前全盒 32² 对应实际 16。后续以实际分辨率为主。

日期：2026-09-11。分支 `test/colombo-re-explicit-hierarchy`，接续主日志
§21。用户要求把 32² Sod 提高到 96²，同时给出 N 和 LDA 的图片对比。

后续针对 high 标签和大幅 vx 散点的核对，见
[同初值回归对照及旧图审计](sod96_regression.md)，主日志 §23。

**六组均完成。N 中 CR low 比 basis repair 更模糊、误差更大；LDA 中
CR low 虽然也拓宽接触间断，却显著抑制速度散点与横向噪声，使本例的
总体误差更小。** 因此，低阶拓扑的内在混合与完整流体测试的净误差
必须区分。这里是本分支的显式 CR-inspired 算子，不是原文隐式 BDF。

## 配置与对照含义

- 9216 个相同初始节点，周期 unit box，seed=20260911，jitter 幅度
  为格距的 ±0.08。ρ_L=1、ρ_R=.125、p_L=1、p_R=.1、v=0、γ=1.4。
- 六组都采用移动网格、Arpaia temporal mass、existing total-residual
  RK2、ALE contour、element comoving frame。N 使用 lumped mass；
  LDA 使用现有 GL/F1，包括已有的 rank-deficient F1 lumped fallback。
  没有加入 shear/entropy floor、B blending 或新的物理流体 limiter。
- 每个 RD scheme 配 basis repair（含 primitive consistency refresh）、
  pure CR graph-minimal low、existing high + CR positivity fallback。
  最后一项的 high 公式仍是原 uniform-shift correction；其 exact-component
  分组与旧 support repair 不同，故 θ=1 也不要求完整流体轨迹完全相同。
- t_final=.08，CourantFac=.08，MaxSizeTimestep=1/3000。Equal timestep
  是每个 run 内全部节点同步，不表示六个 run 的时间序列完全相同；
  流场反馈后实际步数为 490–540，最大实际 dyadic dt=.0003125。
- 每组仅初末两个 HDF5 snapshots。在 .25<x<.75 与中央 exact Riemann
  solution 对照，避开周期另一道跳跃的相互作用。误差与平均曲线都用
  RD median-dual area m/rho 加权，未使用 Voronoi Volume。

## 终点结果

| RD | 拓扑 | L1(ρ) | L1(vx) | L1(二维速度) | L1(p) | RMS(vy) |
|---|---|---:|---:|---:|---:|---:|
| N | basis repair | .028099 | .067275 | .067963 | .032956 | .005670 |
| N | CR low | .030218 | .071938 | .072592 | .035127 | .006205 |
| N | high + CR fallback | .028098 | .067124 | .067811 | .032924 | .005588 |
| LDA | basis repair | .023041 | .090221 | .096919 | .025941 | .054975 |
| LDA | CR low | .022302 | .053303 | .054927 | .023825 | .012245 |
| LDA | high + CR fallback | .023028 | .090665 | .097205 | .025977 | .054653 |

N 的 CR low 相对 basis repair：密度误差 +7.54%，速度误差 +6.81%，
压力误差 +6.59%。LDA 则为 −3.21%、−43.33%、−8.16%，横向 RMS
下降 77.73%。LDA 的纯 low 仍有接触展宽和残余振荡，不能据一个 Sod
案例把它定为默认方法；N、smooth Yee 和 LDA Sod 对耗散的需求不同。

两组 high + CR fallback 的全部 events 都接受 θ=1，正性后备没有触发。
它们分别处理 N 的 4901 和 LDA 的 10519 个 exact changed components。
这解释了它们既保留原 high 精度，也保留 LDA 的明显振荡：仅判断正
密度/正内能的 limiter 不会自动约束仍在正性域内的速度散点。

Native CR 最大 component 为八个节点。Low 的 5156/6636 是组件计数，
不是实际 elementary flip 数；mode 1 的 limited 计数只是 θ 固定为 0。

## 正性、守恒和独立核对

| RD / 拓扑 | 最小 predictor ρ | 最小 predictor p | 终点最小 ρ | 终点最小 p |
|---|---:|---:|---:|---:|
| N / basis | .125 | .1 | .125004 | .100005 |
| N / CR low | .125 | .1 | .125006 | .100007 |
| N / high + fallback | .125 | .1 | .125004 | .100005 |
| LDA / basis | .062570 | .029547 | .066302 | .035505 |
| LDA / CR low | .082623 | .051848 | .087956 | .059063 |
| LDA / high + fallback | .062228 | .030347 | .066386 | .033739 |

六组均返回 0，达到 .08，snapshot fields 有限且为正，未触发 predictor
或 topology inadmissibility 检查。这是本组轨迹的结果，不是 LDA 或
Euler/RK2 的一般正性证明。LDA 的累计 F1 lumped counts 分别为
102159/104839/102185（basis/low/high）；这些是跨时间的三角形回退计数，
不是不同网格单元个数。LDA 运行仍保留原实现的奇异矩阵处理。

六组相对质量误差在 1.06e-10–6.20e-9，相对能量误差在
1.02e-10–9.65e-9。此处保留 Arpaia 作统一对照，不能把其已知的
endpoint-rebase 漂移误报为 exact CR transfer 的守恒失败，也不能
宣布本轮已完成严格守恒方案；Campoli 对照见 §21。

四组 CR 各自前八个 dumped events，共 32 个，独立 Gauss geometry
和 Python transfer 回放全部通过：完整状态尺度相对差异 ≤2.23e-16，
转移相对守恒误差 ≤2.56e-16。抽样都是四节点；不能把这个回放结论
扩展为已经独立覆盖原生八节点组件。完整原生计算仍有边界链、swept
balance、质量闭合与实际 pullback 全局总量的在线检查。

## 图片

主图上排 N、下排 LDA，三列为密度、纵向速度和压力。蓝线 basis，
红线 CR low，绿虚线 high + CR fallback，黑虚线 exact。每个节点都
画入散点，曲线为 64 个共同 x bins 的面积加权均值，x 也取 bin 内
加权节点位置；空 bin 不插值。主图共同纵轴保留 LDA 的全部 outliers。

![N/LDA profiles](/Users/zhenyuwu/arepo_rd/local_runs/cr_sod96_20260911_omp1/figures/sod96_N_LDA_profiles.png)

局部图展示接触/激波密度细节及横向速度。密度轴是明确的 zoom；
横向速度没有 percentile clipping，N 与 LDA 使用共同纵轴。

![Contact and transverse motion](/Users/zhenyuwu/arepo_rd/local_runs/cr_sod96_20260911_omp1/figures/sod96_contact_transverse.png)

[主图 PDF](/Users/zhenyuwu/arepo_rd/local_runs/cr_sod96_20260911_omp1/figures/sod96_N_LDA_profiles.pdf)；
[局部图 PDF](/Users/zhenyuwu/arepo_rd/local_runs/cr_sod96_20260911_omp1/figures/sod96_contact_transverse.pdf)；
[误差柱状图](/Users/zhenyuwu/arepo_rd/local_runs/cr_sod96_20260911_omp1/figures/sod96_errors.png)。

## 复现与本地线程问题

最终 campaign 为 `/Users/zhenyuwu/arepo_rd/local_runs/cr_sod96_20260911_omp1`。
README 给出 prepare/build/run/plot/replay 命令；六个冻结 binary、Config、
generated header、version、build log、linkage、初值、param、run log、
初末 HDF5、summary 和 SHA256 provenance 均保留。Solver C 未修改。
N/LDA 配置只改变 RD scheme 与说明注释；本轮不涉及 hierarchy/MPI 移植。

初次运行保存在相邻 `cr_sod96_20260911`，因线程效率问题主动中止，
不计入任何终点比较。Homebrew OpenBLAS 报告 OpenMP backend=2，
仅 OPENBLAS_NUM_THREADS=1 仍为 10 个线程；同时设 OMP_NUM_THREADS=1
才为一个。1 秒采样显示原运行主要耗在 4×4 dgetrs 的 OpenMP barriers。
修正后的每组耗时约 76–83 秒，两个 singleton 并发。
早期共同时间点（N 117 个、LDA 106 个）的日志全局总量完全一致；
不声称做过所有节点的 bitwise 对照。此环境注意项已补入
`context_localMac.md`，避免后续高分辨率测试重复付出同步开销。
