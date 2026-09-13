# Sod 实际分辨率与 glass 上 LDA 振荡诊断

2026-09-11，接续 log 3 §23。用户要求以单个激波管的实际分辨率标注，
并用 glass IC 查明当前结果为何明显比 Morton 2023 Figure 7 更有振荡。
本轮是诊断，不修改论文，也不将任何诊断开关提升为 production 默认。

## 分辨率与基准归属

对于目前全周期单位正方形盒子，单个 Riemann fan 的比较区间是
`0.25<x<0.75`，长度为 0.5。定义初始代表性间距
`h=sqrt(A_box/N_total)`，以 `N_x=L_tube/h` 标注。因此旧全盒 96² 是
实际 N_x=48，旧 32² 是实际16；本轮全盒128²为实际 N_x≈64。
Glass 没有严格的列，这个定义是基于平均节点面密度，不是将全部
不同 x 坐标数当成纵向分辨率。图横坐标统一为 `x_tube=2(x−.25)`。

[Morton et al. (2023), §5.1.1 与 Figure 7](https://academic.oup.com/mnras/article/518/3/4401/6847219)
明确使用一阶 LDA/N、gamma=5/3、CFL=0.4；uniform 是 Cartesian 隔行错开
半个间距的网格。用户所附图的干净结果不能直接当作我们当前 GL/F1 RK2
在不规则网格上的预期结果。本轮没有原始数据，也没有复现其原代码。
本地旧 `create_morton2023.py` 的目录 n 是全盒边长计数，不应继续把
这种内部命名当成用户图中单管实际分辨率；本轮没有改写历史数据。

## 控制变量

主网格是本地已有的官方 SWIFT relaxed periodic `glassPlane_128.hdf5`，
16384 个节点，不重新随机撒点，也不把 jittered Cartesian 称作 glass。
所有 glass variants 使用同样的归一化坐标和 IDs。左右 rho,p 保持
(1,1)/(.125,.1)，v=0，中央间断 x=.5，周期镜像间断在边界。
主对照 gamma1.4、t=.08；CFL=.08、dt cap=1/3000。半步对照将 CFL
和 cap 都减半。另保留同分辨率 jittered Cartesian、gamma5/3 与
row-offset regular 的诊断。后者不是 Morton 的严格重现：时间和 CFL
并未全部对齐，不能拿误差表宣称复现精度。

- LDA1：现有 `RD_DIAG_PREDICTOR_ONLY`，一次完整空间 LDA update。
  不是简单关闭 RK2 后的 legacy 两次半权重/Taylor 外推路径。
- GL/F1 RK2：当前默认两阶段 total-residual 方法。
- Lumped Heun：新增受 guard 限制的 `RD_DIAG_LDA_LUMPED_TEMPORAL`，只在
  static equal-step LDA 下将 corrector 的时间质量分配改为对角 lumped。
  两个空间 residual sweeps 保持不变。没有修改默认算法。
- Zero-motion ALE：相同 ALE/basis 配置，强制 sigma=0；分别采用 contour
  与 Roe total。用它分开 residual 选择与真实网格运动/翻边的影响。
- Moving：与前轮相同的 Arpaia/contour/comoving/basis+refresh。

12项全部完成，均保留初值及 t=.02/.04/.06/.08 五个 snapshots。
完整数值表由 `summary.json` 生成：

| 对照 | vx_min | vx_max | RMS(vy) | L1(rho) | L1(p) |
|---|---:|---:|---:|---:|---:|
| glass_fe | -1.709784e-08 | 1.138474 | 0.004534466 | 0.02315006 | 0.02279914 |
| glass_rk2 | -0.7765731 | 1.009347 | 0.01023829 | 0.01576321 | 0.01502464 |
| glass_rk2_halfdt | -0.7671865 | 1.010072 | 0.01023752 | 0.01583181 | 0.0150829 |
| glass_zero | -0.6623744 | 2.487301 | 0.02527555 | 0.01614049 | 0.0155954 |
| glass_moving | -0.7175571 | 1.365506 | 0.01771522 | 0.01717603 | 0.01844392 |
| jitter_fe | 5.260391e-08 | 1.245444 | 0.005378048 | 0.0241198 | 0.02359893 |
| jitter_rk2 | -0.6050862 | 1.057078 | 0.01370505 | 0.01596719 | 0.01444922 |
| glass_fe_g53 | -4.277127e-08 | 0.9643726 | 0.003746825 | 0.02475407 | 0.02386606 |
| glass_rk2_g53 | -0.5972951 | 0.8953155 | 0.008304457 | 0.01688322 | 0.01561812 |
| regular_fe_g53 | 1.42704e-07 | 0.8907596 | 1.232576e-16 | 0.02395106 | 0.02235637 |
| glass_lumped | -2.397175e-08 | 1.143904 | 0.004530439 | 0.02346909 | 0.02319013 |
| glass_zero_roe | -0.7765731 | 1.009347 | 0.01023829 | 0.01576321 | 0.01502464 |

所有 extrema 与误差均保留
中央半盒全部节点，误差与横向 RMS 使用 RD median-dual 面积权重。
正密度/正压力与算法完成只作运行检查，不作为无振荡的标准。

## 已隔离出的机制

### GL/F1 的影响不能等同于普通 RK2

同一 glass 上，一阶 LDA 的 vx_min≈−1.7e−8，GL/F1 的 vx_min≈−.7766；
保留 RK2 但改为 lumped mass 后 vx_min≈−2.4e−8。负速度 undershoot
随 F1 修正而出现，无法简单归结为“两阶段更新就会振荡”。然而一阶与
lumped 的 vx_max≈1.14，仍高于精确平台，且密度/压力 L1 更大；它们
不是无条件有界的方案，也没有证明其激波质量整体更高。

这与现有离散公式一致。令 `v(U)=−S⁻¹R(U)`、`C(U)=S⁻¹M_F1(U)`，
其中 S 为 median-dual lumped mass。当前 GL/F1 是

\[
U^*=U^n+\Delta t\,v^n,\qquad
U^{n+1}=U^n+\Delta t\left(\frac32v^n+\frac12v^*-C^*v^n\right).
\]

当 `C=I` 时恰好为普通 Heun。对固定网格、正则状态分支展开，GL/F1
在 dt→0 下的 rate 为 `(2I−C)v`，而 FE/lumped Heun 是 `v`。因此
F1 引入的空间耦合不会仅靠减小 dt 就消失。这不是声称数学上已证明
F1 必然产生本例某个负值，而是解释缩步不能消除它的可能机制。

实测将 timestep 减半，vx_min 只从 −.7766 变为 −.7672，横向 RMS
从 .0102383 变为 .0102375。未见接近消除问题的改善，不支持本例主要
由过大的时间步导致。这里只做一层半步控制，没有宣称严格时间收敛。

### Glass 与 EOS 都不能单独消除问题

同实际分辨率、相同 gamma 下，jittered Cartesian 的 GL/F1 vx_min
约 −.6051，glass 约 −.7766；glass 横向 RMS 较低但负速度极值并不
更小。不能将先前所有振荡解释成 jitter 太大。

换到 gamma5/3，glass GL/F1 仍有 vx_min≈−.5973；一阶 glass 则没有
显著负速度。一阶规则网格 gamma5/3 保持横向对称到 roundoff，vx_max
约 .8908，定性上更接近用户提供的 Figure 7。这里同时提示时间质量
形式与几何的作用，但不是与原论文数据的误差级复现。

### 零运动对照用于隔离 contour residual

Zero-motion contour 在没有翻边时也出现很大的速度散点。日志中的
`stationary=1`、`static_bit_mismatch=0`、`static_max_diff=0`，以及
`removed=inserted=exact=0`，说明这个现象不需要几何变化或 topology
repair 才能发生。将相同配置中的 contour total 改回 Roe total 的
终点对照，另外按 ID 与静网格逐点比较，见
`static_zero_roe_comparison.json`。其坐标逐点完全相同，rho/p/v 最大绝对差
分别为 1.82e−14/2.39e−15/1.20e−14；zero-motion Roe 与 static 的
物理解相同到舍入误差。只将 Roe total 改为 contour，vx_max 从
1.00935 增至 2.48730，RMS(vy) 从 .0102383 增至 .0252756。

源码的 contour total 插值节点物理 flux F(U_i)，而 Roe total 来自
参数向量线性化。它们在非线性状态上的离散 residual 不必相同；在
激波附近差异可以很大。守恒与 Galilean covariance 的检查，并不
等于离散 shock boundedness 或 entropy stability 的证明。

因此上一轮“moving 比 static 增加散点”的描述应收窄：那一对同时
改变了网格运动和 total residual，不能全部归因于运动/翻边。本轮
实测 moving contour 甚至比 zero-motion contour 的 vx 最大散点更小，
进一步否定了简单的单调归因。尚未隔离真实运动中的每项反馈。

## 对后续 moving/hierarchy 研究的意义

先在 glass 上固定物理 residual 与时间质量的激波基线，再评价拓扑
算子的附加耗散。CR low 能压住一部分散点，不能因此证明 topology
repair 是原始散点来源，或将这种抑制当成普遍优越性。

本轮没有足够依据直接把 production F1 换成 lumped，或把 moving
contour 改回 Roe：前者牵涉 smooth-flow 精度，后者牵涉既有 ALE/GCL/
守恒设计。也没有证明 F1 的代码实现有代数错误。已经确定的是需要
分别检查两项实际离散选择的 shock 行为，不能再笼统归于 LDA、RK2、
Cartesian、edge flip 或 MPI。

## 复现与存档

主 driver：`tests/rd/audit_sod_glass_oscillations.py`；分析：
`tests/rd/plot_sod_glass_oscillations.py`。Driver 以 fresh root 运行，
接收 glass、前轮 moving archive 与 static-control archive 的路径。
最终版本一次性组织全部控制；实际执行顺序为原10项、再补2项。
所有 binary/config/header/linkage/build logs、IC、params、五个时刻的
snapshots、run logs、逐点/误差统计、图与 SHA256 provenance 保留在
`/Users/zhenyuwu/arepo_rd/local_runs/sod_glass_nx64_20260911`。
旧 Nx48 两组图已重绘明确实际分辨率；原始标签版和原 provenance
保存在各 archive 的 `labels_before_resolution_correction` 中。

## 结果图

![时间质量与 residual 隔离](/Users/zhenyuwu/arepo_rd/local_runs/sod_glass_nx64_20260911/figures/mass_residual_controls.png)

![Glass 完整流体剖面](/Users/zhenyuwu/arepo_rd/local_runs/sod_glass_nx64_20260911/figures/glass_profiles.png)

[时间质量与 residual 图 PDF](/Users/zhenyuwu/arepo_rd/local_runs/sod_glass_nx64_20260911/figures/mass_residual_controls.pdf)；[EOS/几何对照](/Users/zhenyuwu/arepo_rd/local_runs/sod_glass_nx64_20260911/figures/gamma_geometry_controls.png)。
