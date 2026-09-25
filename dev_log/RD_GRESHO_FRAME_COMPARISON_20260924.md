# 当前 moving Gresho：N/Roe split 与 LDA/Gauss3 的 lab / co-moving 对照

作者：Codex；请求：Zhenyu。日期：2026-09-24。

## 结论

**当前 boost=10 的 Gresho 不以 co-moving frame 为完成运行的必要条件，但该 frame 仍显著改善矩阵条件，值得保留。** N/Roe split 和 LDA/Gauss3 在 lab、co-moving 两种计算坐标及 boost 0、10 下，全部完成短时 t=.02 和长期 t=1。长期各4096步，无A2或负质量终止。此次没有复现旧版 boost10 首步失败。

区分两个问题：同一物理算例在 lab/co-moving 计算坐标中的差异，衡量坐标实现和舍入影响；两次不同 boost 的算例在去平移/去速度后比较，检验整个离散方法的 Galilean 性质。N 保留完整 U−Uhat mesh correction，短时 boost 差异在两种计算坐标中都约1.5e−5，不能靠 co-moving 消除。LDA/contour 的短时 boost 差异已很小，co-moving 进一步降至接近舍入量级。

## 设置和历史对应

- 使用历史 `create_mmrd_ics.py` 的 deterministic jitter48²：2304顶点、seed20260811、jitter=.4格距、unit periodic box、gamma5/3。
- 标准Gresho：rho1、峰值旋转速度1、核心p=5+12.5r²，沿x加boost0或10。两boost使用相同位置、密度和热能。
- CFL=.3、MaxSizeTimestep=.01、MinSizeTimestep=1e−5、RD spectral CFL、原face-angle mesh regularization。没有加稳定化、positivity limiter或放宽求解器断言。
- 当前公共begin/end hooks、一次rebuild、new connectivity上的两次ALE sweep、Arpaia面积。N/lumped+Roe split；LDA/mixed F1+P1-U Gauss3 contour。每一对配置只开关RD_ELEMENT_COMOVING_FRAME。
- 单MPI rank、OMP/BLAS各1线程。主对照最多4并发，额外只读诊断与主任务重叠时总共最多5个rank。
- 这是历史设置在**当前源码**上的重测，不是旧Linux/历史二进制精确重放。log2 §§25–28记录了早期失败及后续修正，尤其§28纠正了早期co-moving遗漏mesh correction的解释。当前源码、拓扑路径、平台/LAPACK与旧版不同，不能把旧失败消失单独归因于换了某个residual。

当前源码基于 `adc424ba93f8cb98ff494dd8e98b41fafcd2e98b` 的冻结工作树（含既有未提交改动），源码包SHA256 `f1064f41b96ac8841a58c5907fc54ae34982a4f28b4cacffff463940b3b0583d`。

## t=1 的解析剖面误差

L1按当前median-dual area=m/rho归一化加权，对去boost后的方位速度与当前位置上的解析v_phi(r)比较。这里的L1不同于后表按ID逐点匹配的boost差异。

| Scheme / residual | Frame | Boost | v_phi L1 | v_phi peak | 相对总质量漂移 |
|---|---|---:|---:|---:|---:|
| N / roe_split | lab | 0 | 0.0197051665 | 0.8523711 | 5.6374e-05 |
| N / roe_split | lab | 10 | 0.0197645029 | 0.8589686 | 4.55598e-05 |
| N / roe_split | comoving | 0 | 0.0197051624 | 0.8523711 | 5.6374e-05 |
| N / roe_split | comoving | 10 | 0.0197644772 | 0.8589687 | 4.55648e-05 |
| LDA / gauss3 | lab | 0 | 0.0079231445 | 0.9391254 | 6.20154e-05 |
| LDA / gauss3 | lab | 10 | 0.00792314439 | 0.9391254 | 6.20155e-05 |
| LDA / gauss3 | comoving | 0 | 0.00792314429 | 0.9391254 | 6.20155e-05 |
| LDA / gauss3 | comoving | 10 | 0.00792314433 | 0.9391254 | 6.20155e-05 |

两种计算frame的解析剖面误差基本相同。本次没有看到co-moving带来可观的宏观精度提升。完整更新的质量漂移仍为约4.56e−5至6.20e−5（0.0046–0.0062%），不能把残差闭合或正常完成当作严格全局守恒证明。

## 去boost后的逐点差异

按ParticleID匹配，速度扣除x方向boost，坐标扣除boost×time后取周期最短差。表中速度L1是对所有粒子及两个速度分量的绝对差取平均。

| Scheme | Frame | t=.02 velocity L1 | t=1 velocity L1 |
|---|---|---:|---:|
| N | lab | 1.49812e-05 | 0.00264338 |
| N | comoving | 1.49812e-05 | 0.00264367 |
| LDA | lab | 8.00941e-13 | 6.45182e-10 |
| LDA | comoving | 9.66319e-15 | 5.60922e-10 |

N两种frame有几乎相同的boost差异。这与Roe flux和P1-U mesh transport混合插值的已知离散差异一致，并非再次证明线性求解器出了问题。长期演化包含改变的几何/拓扑，不能把所有t=1逐点差异归因于某一步舍入。LDA的长期boost误差仍很小，但co-moving的改善倍数不能从短时直接外推。

## 首步矩阵诊断

在独立诊断副本中，仅增加打印，记录LDA首次spatial stage的4608个元素。每个元素同时构建lab Sminus和直接用平移速度构建的Sminus，计算奇异值。新增诊断以及原有condition diagnostic的四次短时重跑，其所有保存快照与无诊断的对应计算逐项相同。

为了不让真实/近似秩亏主导统计，以下条件数只取shifted条件数小于1e8的2509个元素；另外2099个元素明确排除，未修改任何求解器rank判据。矩阵entry统计使用全部4608元素。

| Boost | median cond2(lab) | median cond2(shifted) | median paired ratio | median max-abs entry lab / shifted |
|---:|---:|---:|---:|---:|
| 0 | 26123.2 | 21129.8 | 1.13949 | 0.0541675 / 0.0538491 |
| 10 | 5.71865e+08 | 21129.8 | 23981.3 | 9.38484 / 0.0538491 |

boost10下，中位配对条件数降低约2.4万倍，最大绝对矩阵entry的中位值从9.38降至.0538。这直接支持“减小bulk velocity引起的矩阵尺度失衡”。然而co-moving不能消除真正的秩亏，也不能修复N/Roe的混合插值boost差异。

原生RD-DIAG中的cons_defect_abs在不同frame中使用不同坐标分量，不能直接把二者比值当作相同物理范数的改善倍数。完整条件数原始记录保留在matrix_probe/summary.json和run.log。

## 常状态门禁及验证范围

四次boost10常状态运行都正常完成。N/lab最大压力变化1.1822e−12，**未通过原有绝对1e−12门槛**；N/co-moving为1.3856e−13，LDA/lab为1.6076e−13，LDA/co-moving为1.3145e−13。首次science launcher因此停止，日志保留为short_gate_blocked.log。后续Gresho明确作为用户要求的诊断对照继续，未改阈值或把该门禁标为通过。

主对照4构建20原生运行；已有condition diagnostic另1构建2运行；隔离副本的矩阵打印另1构建2运行。24次原生运行均完成，但常状态门禁仅3/4通过。不声称更大boost、其它mesh/CFL、MPI或层级时间步已验证。未改生产solver、thesis、默认配置，未commit/push。

## 对论文表述的建议（尚未写入）

> We evaluate the element matrices in co-moving conservative coordinates to improve their numerical conditioning in the presence of bulk motion. In the present boosted Gresho test, both laboratory and co-moving implementations complete, while the co-moving formulation substantially reduces the conditioning penalty associated with the bulk velocity.

建议保留co-moving作为数值条件改善手段，而不写成当前boost10能正常计算的必要条件。N的Galilean差异另行解释，不将两者混为一谈。

## 文件

- [完整数值结果](/Users/zhenyuwu/arepo_rd/local_runs/gresho_frame_20260924_v1/summary.json)
- [首步矩阵统计](/Users/zhenyuwu/arepo_rd/local_runs/gresho_frame_20260924_v1/matrix_probe/summary.json)
- [运行配置与复现说明](/Users/zhenyuwu/arepo_rd/local_runs/gresho_frame_20260924_v1/README.md)

![Gresho解析剖面对照](/Users/zhenyuwu/arepo_rd/local_runs/gresho_frame_20260924_v1/figures/gresho_profiles.png)

![误差与总质量漂移](/Users/zhenyuwu/arepo_rd/local_runs/gresho_frame_20260924_v1/figures/gresho_histories.png)
