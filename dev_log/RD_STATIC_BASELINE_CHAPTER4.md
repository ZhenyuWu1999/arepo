# Chapter 4 静网格 AREPO-RD 基准审查

日期：2026-09-13。开发分支：`develop_pureC_RD`。
本次原生构建源代码：`943f7ae`。此前 Gauss/hierarchy/MPI 证据源代码：`255046f`。
研究分支 `test/colombo-re-explicit-hierarchy` 保留在 `53cb65a`。

本文记录实现选择与可支持的论文结论，不修改 thesis 正文。**“冻结基准”是冻结一组可复现的算法与已知限制，不表示所有准确性、稳定性和工程问题都已解决。**

## 1. 基准的组织方式

把静网格写成统一 ALE-RD 的特殊情况：

\[
\sigma_i=0,\qquad x_i^{n+1}=x_i^n,\qquad
T^{n+1}=T^n,\qquad A_T^{n+1}=A_T^n=A_T.
\]

这里的静止对象是网格；流体速度可以非零，advected Yee 仍属于静网格测试。
固定点集上可能重新构造相同的 Delaunay 网格，但本基准不包含点移动、refinement 或拓扑转移。

建议保留两份明确命名的配置：

| 配置 | 用途 | 定位 |
|---|---|---|
| `examples/yee_2d/Config_RD_RK2_LDA_GAUSS3_EQUAL.sh` | 静网格、等时间步、Gauss3 LDA/F1 | 空间残差与 MPI 对照的参考配置 |
| `examples/yee_2d/Config_RD_RK2_LDA_GAUSS3_HIER.sh` | 同一静网格与 Gauss 残差，CFL 选择层级、frozen-star 两调用调度 | 守恒层级实现；不是与等步 F1 精度等价的 multirate RK2 |

`Config.sh` 和历史配置没有被静默替换。N/lumped、旧 Roe/F1、四调用 rate-Heun 是独立对照，不能把不同配置的收敛阶或稳定性结果互相挪用。

## 2. 数学形式与工程选择表

| 层面 | 统一 ALE 描述或候选 | 静网格极限及本次基准 | 仍需注意的区别 |
|---|---|---|---|
| 守恒变量 | \(U=(\rho,\rho v_x,\rho v_y,E)^T\) | 存储 extensive \(Q_i=S_iU_i\)，\(S_i=\sum_{T\ni i}A_T/3\) | \(S_i\) 是 P1 median-dual lumped area，通常不是 AREPO 的 Voronoi `Volume` |
| 空间基函数 | 三角形连续 P1 basis \(\psi_i\) | \(U_h=\sum_i\psi_iU_i\)，不增加边上自由度 | P1 表示状态，不意味着非线性 \(F(U_h)\) 沿边线性 |
| 网格速度 | \(\sigma_h=\sum_i\psi_i\sigma_i\) | \(\sigma_h=0\)；坐标和 generator velocity 在输出中独立核对 | 流体的 boost 不等于网格运动 |
| Arpaia 几何时间质量 | 元素系数 \(A_m\)；节点分母由 \(A_m+(A_1-A_0)/2\) 汇总 | \(A_0=A_m=A_1\)，退化成固定 \(A_T,S_i\) | 这里比较的是当前实现的几何权重，不是宣称所有文献变体完全等同 |
| Campoli 几何时间质量 | 元素系数 \((A_0+A_1)/2\)；节点分母由 \(A_1\) 汇总 | 与上一行完全相同；静网格不需要开启任何 moving mass flag | 因此静网格基准无需在两者间作数值选择，也不能据此替 moving mesh 定案 |
| ALE 残差 | \(\Phi_T=\oint F(U_h)n\,ds-\int_T\sigma_h\cdot\nabla U_h\,dA\) | \(\Phi_T=\oint F(U_h)n\,ds\)，基准选择 contour | 原公式含一个网格体积项；与完整 \(F-U\sigma\) 边界通量的联系还需要 GCL/面积项 |
| 旧 split / Roe 形式 | 物理项使用 Roe \(\widehat U\)，网格项使用物理 \(U\) | 网格项消失，但其物理项相当于沿 \(P_1Z\) 表示积分；保留为历史对照 | \(F(U(P_1Z))\) 与 \(F(P_1U)\) 仍不同，不能因 \(\sigma=0\) 就说 split 与 Gauss-U 一样 |
| 旧 nodal contour | 沿边积分线性插值 \(I_hF(U_i)\)，等价端点梯形 | 不选为新基准，Gauss 替换其物理通量积分 | 即使 \(\sigma=0\)，一般也不等于 \(F(P_1U)\) 的积分 |
| 边上积分 | Gauss–Legendre 3 点或 5 点 | **3 点**：`RD_ALE_CONTOUR_GAUSS=3`；5 点作为积分敏感性对照 | 对多项式分别精确到 5/9 次；一般 Euler \(F(P_1U)\) 非多项式，不能宣称精确或五/九阶流体方法 |
| Roe 线性化与 K 矩阵 | Roe 平均，ALE 特征速度使用 \(v-\bar\sigma\) | 保留原 Roe/特征分解构造；\(\bar\sigma=0\) | Gauss 改变总残差的求积，不替换 K 矩阵，也不把 \(\widehat U\) 当成物理边状态 |
| LDA 分配 | \(\phi_{iT}=-K_i^+z,\ (\sum_jK_j^-)z=\Phi_T\) | 主配置选 LDA；直接解 RHS，不显式求矩阵逆 | 秩亏时必须检查空间 RHS 的可解性/残差守恒，不能默认伪逆自动解决所有问题 |
| 局部 element-comoving frame | Galilean 变换，\(b_T=\bar\sigma_T\)，最后变回 lab ledger | \(b_T=0\)，变换是恒等；主配置使用 laboratory frame | `RD_ELEMENT_COMOVING_FRAME` 当前不允许静网格 hierarchy；无需解除 guard 才能表示这一极限 |
| 宇宙学共动坐标 | scale factor、Hubble 项及宇宙学源项 | **关闭 `ComovingIntegrationOn`** | 与上一行的局部 Galilean 变换不同；本基准不验证 cosmological integration |
| LDA 时间质量 | F1 元素质量作用 \((M_Tw)_i=\beta_{iT}(A_T/3)\sum_jw_j\) | **保留 F1**，不是 lumped LDA Heun | Arpaia/Campoli 几何差异消失，不代表 F1 与 lumped 的区别消失 |
| 时间推进 | `RD_RK2_TOTAL_RESIDUAL` 两阶段结构 | 等步内部两遍；hierarchy 跨两调用并记 extensive 增量 | 固定空间网格下，当前标准 GL/F1 测得时间阶约 1；不要只凭 flag 名称称其二阶时间方法 |
| Hierarchy | 顶点 dyadic bins、三角形最细 bin、完整星形邻域 live/frozen mask | 自然 CFL 选择；非活跃顶点也接收 ledger 增量 | `RD_HIERARCHICAL_TEST_PATTERN` 只是测试用强制细化，主配置不启用；mask 改变 F1 leading operator |
| MPI 与几何 | 独占 physical simplex + 完整 star 汇总 + ghost 元数据/增量交换 | `CREATE_FULL_MESH`，最小 ID ownership；已验证小规模 MPI 一致性 | full mesh 指完整局部 tessellation（含 ghosts），不是每个 rank 重算整个全局域 |
| 奇异求解 | 直接分解/后备秩判定与守恒断言 | 保留已有政策，无新增 epsilon regularization 或放宽 A2 阈值 | F1 **时间质量**在 rank<4 时回退 lumped，不是空间 range completion 或 positivity limiter |
| N、B 与 limiter | N/lumped 与 N–LDA blending 是其它空间/质量选择 | 不在 Gauss LDA 主配置启用 N 混合、B 或额外 limiter | 当前 Gauss guard 限定 LDA；不能自动把结果推广到 N/B+Gauss |
| 拓扑/GCL 修正 | moving edge flip、basis repair、CR、局部区间结算 | 固定连通性下没有这些增量；主配置关闭 | 静网格测试不验证 moving topology conservation |
| Checkpoint | 两调用 hierarchy 有跨调用的未完成 RK 阶段 | 保留 mid-stage restart 拒绝保护 | **任意时刻中断/重启尚未支持**；该保护会终止某些 stop/定时 checkpoint 请求 |

## 3. Gauss 的具体公式

对有向边 \(e=(a,b)\)，使用向外法向 \(n_{Te}\)：

\[
U_e(s)=(1-s)U_a+sU_b,\qquad
\Phi_T^{G3}=\sum_{e\subset\partial T}|e|
\sum_{q=1}^3 w_qF(U_e(s_q))\cdot n_{Te},
\]

\[
s_q=\left(\frac12-\frac{\sqrt{15}}{10},\frac12,
\frac12+\frac{\sqrt{15}}{10}\right),\qquad
w_q=\left(\frac5{18},\frac49,\frac5{18}\right).
\]

代码使用 opposite-vertex inward normals，符号在组装时转换。当前实现先计算 nodal contour，再添加同一条边上的
Gauss-minus-trapezoid correction；它与直接 Gauss 求和代数等价。质量通量线性于 \(U\)，因此从 nodal contour 到 Gauss 的质量分量修正恒为零。

共享边反向后相同 Gauss 点/权重成对抵消。因此守恒不要求求积对 Euler 非线性通量绝对精确；要求两边使用相同状态与一致的时间历史。Gauss 点没有独立 timebin、存储状态或 MPI 消息。

旧 split 不能直接加这个同名 correction：它的参考量是 \(F(U(P_1Z))\)，与 nodal contour 不同。若要将旧 split 改为 Gauss-U，需要完整四分量的 Roe-to-U 修正；结果是同一个 Gauss-U 方法。见
[legacy_split_gauss_identity.md](colombo_re_spike/legacy_split_gauss_identity.md)。

每个三角形每遍扫描有 9/15 个内部求积点。当前 correction 实现还重复求端点通量，约为 15/21 次物理 flux evaluation，对照原来的 3 次。
这不等于整个求解器变慢 5/7 倍。此前移动网格串行计时的额外 CPU 约 0.8–4%，只适用于那些配置；**本次不把该百分比当作静网格 MPI 的已测成本**。

## 4. 时间方法不能混写

令 \(S=\mathrm{diag}(S_i)\)，\(R(U)\) 为已分配的空间残差，\(v=-S^{-1}R\)。固定网格上：

| 方法 | 实际的 leading rate / 性质 | 在基准中的角色 |
|---|---|---|
| Genuine lumped LDA Heun | Heun 作用于 \(v\)；平滑 ODE 分支上时间二阶 | 时间/mass 对照；历史 advected Yee 空间阶约 1，不能因为 Sod 欠冲小就替换 F1 |
| Standard two-pass GL/F1 | \(G_{eq}=v+(I-S^{-1}M)v\)；固定-h 测得时间一阶 | 当前等步参考，明确标注其时间性质 |
| Four-pass F1 rate-Heun | 真正对同一 \(G_{eq}\) 做 Heun；历史时间二阶 | 精度诊断；不能把旧 Roe 版本结果直接等同于本次 Gauss 版本已验证 |
| Frozen-star F1 hierarchy | \(G_{hier}=v+(I-S^{-1}M)Pv\)，\(P\) 为 live mask | 当前保守层级配置；不是等步 F1 的单纯调度优化 |

对固定 mask：

\[
G_{hier}-G_{eq}=(S^{-1}M-I)(I-P)v.
\]

这个差异在固定空间网格、\(\Delta t\to0\) 时不必消失。Gauss 的改变不产生该 mask 问题，也不消除它。
已有 Yee48、\(t=.125\) 的 Gauss 对照，步长上限从 1/256 降到 1/2048，hierarchy-minus-equal 的 conserved-state L1 从
\(5.028\times10^{-4}\) 趋近 \(5.078\times10^{-4}\)，两者各自的时间 self-order 均约 1。

因此论文应分别展示：守恒与 MPI、时间 self-convergence、随空间分辨率的实际误差，以及 hierarchy 相对等步的误差差异。
不能仅用等 bin degeneration 或 MPI 一致性证明 multirate accuracy。

## 5. 审查中已确定的问题与适用边界

| 问题 | 证据/影响 | 对 Chapter 4 的处理 |
|---|---|---|
| 标准 F1 的固定-h 时间阶不是 2 | 已有原生步长序列和 leading-rate 推导 | 可作有明确定义的实验基准；不能声称严格二阶时间 RK2 |
| F1 hierarchy 改变 limiting operator | 上式及 Gauss Yee 固定-h差异平台 | 主文必须报告精度代价；“同一空间残差”不等于“同一完整离散算子” |
| LDA/F1 shock undershoot | 既有 Gauss 静网格 Sod 等步最低 vx≈−.729；层级≈−.113/−.195 | 负速度不是负压，但确属过冲/欠冲；不能声明单调性或一般 positivity |
| 空间收敛不能跨配置借用 | 旧 Roe/F1 t=1 的 h 阶约1.7–1.9；此前 Gauss 只有较短 t=.125 序列 | 本次补 Gauss t=1；如未达二阶如实记录，不用历史表格替代 |
| 奇异空间系统的 range 条件 | 已知 moving sharp KH 的 A2 失败不能由时间 lumped fallback 修复 | 静网格另测 sharp KH；保留断言，区分实测失败与尚未证明的普适性 |
| Restart 未完成 | `src/main/run.c` 两处 mid-stage restart guard；旧 log1 有拒绝写文件测试 | 限定为可完整运行的标准流体实验；不是可任意 checkpoint 的长生产模拟 |
| MPI 范围有限 | 既有27次原生 Gauss运行含1/2/4 ranks；当前构建要求完整局部 mesh | 不宣称大规模扩展效率、active-only Gauss、强制迁移或 cosmological capability |
| EOS/维度/边界范围 | 当前配置 2-D periodic Euler、gamma1.4、无重力/源项 | gamma 只是测试参数；其它 gamma/物理模块需各自验证，不把二维结论外推三维 |

详细历史参考：[static_gauss_hierarchy_mpi.md](colombo_re_spike/static_gauss_hierarchy_mpi.md)、
[heun_baseline_history.md](colombo_re_spike/heun_baseline_history.md)、
[lda_baseline_convergence.md](colombo_re_spike/lda_baseline_convergence.md)。

## 6. 分支、复现和证据归属

本次仅将 Gauss helper、调用位置与静网格编译许可从研究分支带回开发分支，并登记公开配置选项。
没有迁入 CR 拓扑代码、moving-hierarchy Euler 原型、拓扑 primitive-refresh 或 lumped-mass 诊断修改。
主日志及历史报告一同保留，以免切换分支丢失研究记录；其中旧研究脚本的实际源代码仍应按报告中指定的测试分支/提交读取。

本次 `tests/rd/review_static_baseline.py` 独立于 CR 脚本，负责 `prepare/build/spatial/run/analyze`。
原生二进制全部从干净的 `943f7ae` 编译；构建后更改的分析/新增案例脚本不影响已冻结的求解器。
完整源码 tar、Config、生成头文件、链接库、IC 哈希、参数、日志、输出保存在：

`/Users/zhenyuwu/arepo_rd/local_runs/static_baseline_review_20260913/native`。

首轮移植构建在 `484512a` 因漏登记 `RD_ALE_CONTOUR_GAUSS` 被配置检查器拒绝，尚未进入流体演化。
补齐 Template-Config 后重新干净构建；没有使用 `make build` 绕过检查。初次失败日志保留在父目录。

示例（新的 ROOT 必须已建立且尚无 configs/runs）：

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
PY=/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python
$PY tests/rd/review_static_baseline.py prepare ROOT
# 要求干净源码提交；先核对配置和 IC，再编译。
$PY tests/rd/review_static_baseline.py build ROOT
$PY tests/rd/review_static_baseline.py spatial ROOT
$PY tests/rd/review_static_baseline.py run ROOT
$PY tests/rd/review_static_baseline.py analyze ROOT
```

运行使用最多4个 MPI ranks、每 rank一个 BLAS/OpenMP线程。已有 native 日志不覆盖。测试依赖此前已归档的本地 glass IC；这不是无需数据的独立安装包。

## 7. 本次原生结果

**26 次原生运行全部正常结束；未发现此次静网格移植引入的数值回归。**
五种配置使用标准 `make`（包括配置合法性检查）编译。12 个移植对照案例包括 uniform、Yee 的等步/等 bin/混合 bin、Gauss3/5，以及自然 CFL Sod；
按 particle ID 排序的最终四分量 conservative density 与测试分支归档结果的最大差异为 **0**。

| 本次检查 | 结果 |
|---|---|
| 全部26次运行的已保存时刻，最大归一化四分量守恒漂移 | \(2.06\times10^{-14}\) |
| 对应 1/4 rank 最终状态的最大分量差异，含 KH t=2 | \(3.96\times10^{-14}\) |
| 等 bin hierarchy 退化至内部等步循环，最大差异 | \(1.29\times10^{-14}\) |
| 坐标、generator velocity | 坐标严格不变、网格速度严格为0 |
| 固定 nodal area 的最大输出变化 | \(2.09\times10^{-17}\)，来自通过 Masses/Density 重建时的浮点误差 |
| 所有已保存状态 | 有限且 density/pressure 为正；ID 一致 |
| `make check_rd` | 全部通过；包括秩亏 F1、N/frame covariance 与 shear-floor 算子检查 |

新补8次静网格 KH：相同 glass48、gamma1.4、p=2.5、\(v_y=.1\sin(4\pi x)\)，分别使用 tanh 宽度 .025 和 sharp indicator。
等步与自然 hierarchy 各跑1/4 ranks，CFL .3、步长上限 .02：

| KH 初始界面 | 终止时间 | 等步最小 rho / p | hierarchy 最小 rho / p | hierarchy 最大 frozen 顶点数 |
|---|---:|---:|---:|---:|
| Smooth | 2 | .75707 / 2.07039 | .81522 / 2.08697 | 322 |
| Sharp | .05 | .91912 / 2.29443 | .90513 / 2.31707 | 101 |

这些最小值取自保存的 snapshots，不是逐浮点操作的全局极小值。hierarchy 两组均实际出现两个时间层级，最大 star ratio=2，不能归因于等 bin 退化。
**静网格 sharp KH 未复现 moving sharp KH 的首步 A2 失败**；同一 IC 改变网格速度也改变特征系统，因此不能把那个 moving 失败直接写成静网格已知失败。
这里 sharp 只测试早期 .05，smooth 只到2，不能外推为完整长期 KH 精度验证。

新补6次 Gauss advected Yee，t=1，box10、gamma1.4、beta5、boost1，同一 glass48 平铺家族：

| 方法 | rho L1，48² / 96² / 192² | rho 相邻 h 斜率 | velocity-vector 相邻 h 斜率 |
|---|---|---|---|
| Equal Gauss3/F1 | 6.15304e−4 / 1.67929e−4 / 5.13448e−5 | 1.873 / 1.710 | 1.809 / 1.856 |
| Forced2:1 Gauss3/F1 hierarchy | 1.07819e−3 / 3.59428e−4 / 1.13916e−4 | 1.585 / 1.658 | 1.712 / 1.736 |

这里的48/96/192是整个 Yee 周期盒每轴分辨率；与 Sod 的半盒 effective Nx 定义不同。
误差采用固定 P1 nodal area 加权，解析涡心在 t=1 从(5,5)平移至(6,5)，周期位移取最短距离。
时间上限为1/256、1/512、1/1024；这是空间/时间一起细化的有限分辨率序列，不是 \(\Delta t\to0\) 外推后的纯空间阶证明。
在192²，hierarchy 的密度/速度误差约为等步的 **2.22/1.75 倍**。Gauss 版本的等步趋势与旧 Roe/F1 类似，但 hierarchy 的精度代价现在有了同一终止时间下的直接证据。

[Yee t=1 空间细化图](../../local_runs/static_baseline_review_20260913/native/figures/yee_t1_spatial.png)，同目录另有 PDF。
12次旧案例复现、8次KH、6次Yee细化构成本次26次运行；已有27次测试分支结果是另外的历史证据，没有计入新运行数。

**最终建议：可以冻结以上两份配置作为 Chapter4 的可复现实验基准，并明确列出限制；不能签成“静网格方法已无问题”。**
等步配置用于建立空间残差参考；hierarchy 配置用于展示守恒、并行实现和实际精度代价。
若论文要声明“时间二阶且与等步算子一致的 hierarchical LDA”，当前基准仍不满足这一更强目标，需要另行修改时间离散。
本次没有通过调低 CFL、放宽断言、加入 limiter 或切换 mass matrix 来掩盖上述边界。
