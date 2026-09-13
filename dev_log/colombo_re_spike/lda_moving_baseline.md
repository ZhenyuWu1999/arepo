# Moving LDA baseline：glass Yee / Sod 与 ALE 时间更新的适用范围

2026-09-12。接续 log3 §26 的静态基线，用户要求相同测试在 moving mesh
上比较。运行目录在前一日建立，保留名称
`local_runs/lda_moving_baseline_glass_20260911`。

## 方法和控制变量

三条共同路径使用 laboratory-frame P1 contour residual、equal timestep、
现有 basis repair 与 stage-zero primitive refresh、Arpaia 时间几何。
网格速度沿用 AREPO 的流速/半步压力加速度预测与现有正则化。
IC 与静态基线逐文件相同：glass48 铺接的 Yee48²/96²/192²，boost1、
box10、γ1.4、t1；Sod 完整128² glass，单管初始实际 Nx≈64、t.08。

- **ALE lumped temporal RK2**：仍使用 LDA 空间分配，把 F1 时间项换成
  已有 N 分支的对角时间质量。只放宽受保护诊断开关的适用范围，
  不改主算法默认值。
- **ALE GL/F1 two-pass**：现有 moving equal-step total-residual 更新。
- **ALE F1 four-pass diagnostic**：把已有静态 rate-consistent Heun
  扫描接在现有 ALE prepare/finish 之间。它是兼容性测试，不能先验
  称为守恒、时间二阶的 moving Heun。

另跑既有 **element-comoving-frame GL/F1** 的 Yee48²和Sod，对照
坐标条件数的影响。现有四次扫描明确排除 element frame，因此没有
直接撤掉那个限制；三种时间处理的主比较统一使用 laboratory frame。
不同方法的流体演化会反馈到后续网格速度，最终坐标/拓扑并不相同。

静态时，对角时间质量与 nodal divisor 相同，lumped 更新可化为普通
Heun。移动时必须区分 temporal area 与 modified divisor；直接对
静态 ODE 做 Heun 的推理不能跨过这一差别。

Yee 主序列 dt cap为1/256、1/512、1/1024；48²另有1/512、1/1024、
1/2048，96²另有1/1024。Sod与上一轮相同CFL=.08、cap=1/3000。
主空间误差在**最终移动坐标**上评价解析解，以最终RD median-dual
面积加权。dt阶梯同时改变流体状态、网格轨迹和flip历史；按particle ID
计算的自收敛只能叫耦合状态诊断，不能照搬静态固定网格的时间p。

与上一轮 static Roe 的虚线比较同时改变了 mesh 和 total residual；
不能把全部差异都归因于网格运动。此次零运动/Roe短控制验证的是
实现退化，而不是证明 contour 与 Roe 在激波上等价。

## 三个基础门槛

新增13组短控制：三种方法各自的 static Roe、zero-motion ALE Roe、
uniform moving flow、短程 moving Yee，以及 element-frame GL/F1
的短程 moving Yee。全部正常结束。

zero-motion/Roe 与对应静态路径的最大ρ/p/v差不超过3.11e−15，坐标
完全相同。均匀流的ρ/p/v误差不超过5.56e−16；其节点RD面积确实
变化，最大相对变化8.25e−4，所以不是仅检查刚体平移。
周期坐标位移按最短周期距离计算，不能把跨盒子的wrap记为近10的
实际位移。

这些检查证明了退化关系与该测试中的free-stream preservation；
**不自动证明非均匀流的端点守恒**。

## 四次扫描为什么不能仅靠静态 Heun 的证明

下面先用无flip的Campoli时间几何隔离问题；Arpaia还包含既知的
modified-divisor到endpoint转换项。每个守恒分量都满足相同的全局
求和关系。记nodal面积为s0、s1，dt=h，令

\[
D=\operatorname{diag}(s_1),\quad b=(s_0+s_1)/2,\quad
a=(s_1-s_0)/h,\quad
v(U)=-D^{-1}R(U),\quad G(U)=2v(U)-D^{-1}M(U)v(U).
\]

对周期P1 contour、线性节点运动和该中点几何，所需的两条求和恒等式为

\[
\mathbf1^T R(U)=a^T U,\qquad \mathbf1^TM(U)=b^T.
\]

Euler的M是块矩阵，上式按守恒分量理解；其列和为对应的b乘单位块。
于是

\[
\mathbf1^TDG(U)=-a^TU+\frac h2 a^Tv(U).
\]

现有two-pass更新采用

\[
U^*=U^0+h v_0,\qquad
U^+=U^0+h\left(\frac32v_0+\frac12v_* -D^{-1}M_*v_0\right).
\]

把上面的列和代入，得到 `s1ᵀU+−s0ᵀU0=0`，即Campoli的端点总量
抵消。关键是空间predictor、时间质量项与几何面积配套。

若换成对冻结slab算子G的普通Heun：

\[
U^H=U^0+hG_0,\qquad U^+=U^0+\frac h2(G_0+G_H),
\]

相同求和直接给出

\[
\boxed{\ s_1^TU^+-s_0^TU^0
=\frac{h^2}{4}a^T(v_0+v_H-2G_0)\ }.
\]

右侧通常非零。它在静态a=0时消失，在均匀流各rate为0时也消失，
所以完全可能同时通过static degeneration与free-stream两项控制。
这份额外误差不需要edge flip存在。

一个满足两条求和恒等式的三节点线性代数反例给出：two-pass总量变化0，
four-pass变化−9.458920045e−7，与框内表达式差3.79e−17。它验证的是
求和代数，不是Euler精度或稳定性测试；代码与数值存于
`tests/rd/probe_lda_moving_mass_balance.py`及结果目录的
`mass_balance/algebra_check.json`。另外安排实际无flip短Yee的
Arpaia/Campoli对照，检验该额外项在原生hydro中的表现。

另用2304节点、4608个周期三角形、指定的光滑可压缩网格速度，独立
重建P1 contour求和与 `(s1−s0)ᵀU/h`，四个Euler分量的最大差为
4.65e−14，old/new总面积都为100。这验证了推导所用的几何求和关系，
不是把一个任意矩阵反例直接当作流体代码证明。代码与输入冻结在
同一probe脚本及 `mass_balance/contour_identity.json`。

原生短Yee控制（48²、t=.03125、cap=1/256）全部完成，六例的
topology repair steps均为0：

| 几何 / 时间处理 | 相对质量变化 | 相对总能量变化 |
|---|---:|---:|
| Arpaia / lumped | +4.0200e−10 | +5.0505e−10 |
| Arpaia / GL/F1 two-pass | +4.3224e−11 | +4.6557e−11 |
| Arpaia / four-pass | −2.1229e−10 | −2.4272e−10 |
| Campoli / lumped | 0（输出舍入精度） | 0（输出舍入精度） |
| Campoli / GL/F1 two-pass | 0（输出舍入精度） | 0（输出舍入精度） |
| Campoli / four-pass | −2.5080e−10 | −2.8975e−10 |

两阶段方法的Arpaia/Campoli差别符合既有端点转换限制；four-pass在
Campoli中仍有额外缺陷。其rank-deficient temporal-mass计数非零，
但该fallback保持相同的时间质量列和，并不能使上述端点抵消自动成立。
这里无需把全部额外漂移归到某个rank事件，已有求和反例和无flip
原生控制足以否定“静态Heun证明可直接移植”的说法。

## Moving Yee：空间误差与时间步敏感性

以下是最终坐标上的RD面积加权误差。48²、96²、192²来自同一glass
平铺族，不是三套独立随机glass；p按相邻分辨率的误差比计算。

| 时间处理 | ρ L1，48² | ρ L1，96² | ρ L1，192² | ρ空间p | 速度向量空间p |
|---|---:|---:|---:|---|---|
| ALE lumped | 2.87907e−3 | 1.66246e−3 | 8.99402e−4 | .792 / .886 | .835 / .918 |
| GL/F1 two-pass | 1.07436e−3 | 3.05025e−4 | 8.98789e−5 | 1.816 / 1.763 | 1.708 / 1.403 |
| F1 four-pass diagnostic | 1.06477e−3 | 2.98969e−4 | 8.72134e−5 | 1.832 / 1.777 | 1.720 / 1.418 |

lumped没有恢复到二阶空间收敛；192²时密度误差约为GL/F1的10倍，
速度误差约13倍。GL/F1的密度表现接近p≈1.8，但最细一档速度只有
p≈1.4，不能由此宣称一般非结构glass上的渐近二阶。four-pass的
解析误差接近GL/F1，但其守恒问题使它不能作为已验证的moving替代。

22个主Yee运行（包括frame控制）的实际步数均等于指定denominator，
实际dt确为对应cap。主dt减半后，48²/96²的密度L1变化分别为：
lumped +.0093%/−.0933%，GL/F1 +.5893%/+.6904%，four-pass
+.0176%/−.4995%。因此这些主误差差别不主要来自当前dt大小。

48²的dt=1/256、1/512、1/1024、1/2048中，matched-ID密度相邻差的
表观p分别为lumped −.79/2.18、GL/F1 .36/1.60、four-pass .29/1.81。
轨迹和拓扑也变化，这组非单调序列不能确定固定空间离散的时间阶。
它只说明本次耦合移动测试中未进入清晰的时间自收敛区间。

| 时间处理 | 相对质量漂移，48² | 96² | 192² |
|---|---:|---:|---:|
| ALE lumped | 3.5009e−9 | 5.4416e−10 | 9.5238e−11 |
| GL/F1 two-pass | 1.7016e−9 | 2.0018e−10 | 4.7364e−11 |
| F1 four-pass diagnostic | 1.2495e−7 | 4.4116e−8 | 2.2799e−8 |

48²的dt减半序列中，两阶段方法的质量漂移约按dt²下降；four-pass
从1.2495e−7降到7.5156e−8、3.1480e−8、1.5205e−8，下降更慢。
前述无flip Campoli控制已将其额外缺陷与basis repair隔离。

## Moving Sod：较小的L1并不等于较小的震荡

这里完整周期盒有128²个初始glass节点，**单管初始实际Nx≈64**。
表中的vx极值与误差在单管分析区间计算；图保留所有节点散点。
四例实际步长均落在7.8125e−5和1.5625e−4，步数分别为
918、969、965、969。它们匹配CFL和cap，不是相同逐步轨迹。

| 时间处理 | ρ L1 | vx L1 | p L1 | vx范围 | vy RMS |
|---|---:|---:|---:|---|---:|
| ALE lumped | .023558 | .054942 | .026675 | ≈0 至 1.0173 | .005721 |
| GL/F1 two-pass | .017169 | .049079 | .018441 | −.6722 至 1.3524 | .017750 |
| F1 four-pass diagnostic | .017372 | .049265 | .018556 | −.6764 至 1.4462 | .016688 |
| GL/F1 element frame | .017176 | .049136 | .018444 | −.7176 至 1.3655 | .017715 |

lumped显著抑制速度负谷和横向散布，但密度/压力更耗散、L1更大。
GL/F1虽然激波更锐利，仍有很大的局部速度震荡。四次扫描并未消除
这一问题。所有输出ρ/p仍为正；负vx不能直接叫做Euler positivity
失效，也不能用这些有限测试建立positivity定理。

| 时间处理 | 相对质量漂移 | 相对总能量漂移 |
|---|---:|---:|
| ALE lumped | 3.2381e−10 | 1.2046e−10 |
| GL/F1 two-pass | 1.1898e−9 | 3.5977e−9 |
| F1 four-pass diagnostic | 8.5861e−5 | 9.8684e−5 |
| GL/F1 element frame | 1.2390e−9 | 3.6875e−9 |

Sod把four-pass的额外漂移放大到约0.01%，远高于既有两阶段方法。
较好的解析L1不能抵消这个结构性缺陷。修复它需要重新推导移动
几何与stage更新的耦合，而不是继续称其为已完成的ALE Heun。

## 坐标系和旧结果回归

短Yee的lab/frame GL/F1场差约6e−15。长程Yee48²的密度L1为
.00107435985和.00107436079，速度L1差约.025%；但matched-ID
最大速度差3.00e−4、周期位置差.001678，不应称为逐点等价。
Sod两者的整体误差与震荡量级接近，最终逐点差明显，网格轨迹亦不同。
因此本轮frame变换没有解决激波散布。

本轮element-frame Sod与先前
`local_runs/sod_glass_nx64_20260911/runs/glass_moving`的ρ、p、v、
周期位置逐项比较均完全一致。大震荡不是此次诊断开关扩展引入的
默认路径回归。既有zero-motion contour激波问题仍未解决；本轮
zero-motion Roe通过不能替代对它的调查。

## 可复现性、图像和当前结论

全部45次原生运行正常结束：13短控制、26主运行、6无flip守恒控制。
同时完成独立求和代数与周期P1 contour验证。39例主campaign中
basis-repair后的最大绝对质量残差1.136868e−13；patch计数不是单条
edge flip数，修补残差小也不意味着整个ALE端点更新严格守恒。

源代码冻结在`11d8abcbde665bc384875924a546d07eb043bdd9`；复用的
静态可执行文件由上一轮archive的SHA256辨认。此次C改动只扩展受
保护lumped诊断开关，未改变默认算法。单次运行一个MPI rank、
OMP/BLAS各一线程；先2个并发，后经内存检查增加到最多4个。
原主队列的5个远端待运行项以显式reservation交给第二队列，最终
状态从各case真实退出码重建，没有把reservation作为完成。
实际使用的中间版调度脚本也单独保留；后续文件锁只改调度安全性。

脚本：`tests/rd/run_lda_moving_baseline.py`（构建/运行/状态），
`tests/rd/analyze_lda_moving_baseline.py`（误差/作图），
`tests/rd/probe_lda_moving_mass_balance.py`（独立代数与contour）。
各脚本的`--help`给出入口。分析使用21cmfast Python，设置
`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLCONFIGDIR=/private/tmp/cr_matplotlib`。
完整IC、配置、二进制、snapshots、日志、JSON、PNG/PDF与源码快照
保留在`/Users/zhenyuwu/arepo_rd/local_runs/lda_moving_baseline_glass_20260911`。
`result_commit.json`区分构建源与结果提交，`provenance.json`记录
SHA256及依赖的旧archive文件，`verification.json`记录完成检查。

- [Yee空间收敛](/Users/zhenyuwu/arepo_rd/local_runs/lda_moving_baseline_glass_20260911/figures/yee_moving_spatial.png)
- [Sod所有节点速度](/Users/zhenyuwu/arepo_rd/local_runs/lda_moving_baseline_glass_20260911/figures/sod_moving_velocity.png)
- [Sod全部物理量及frame控制](/Users/zhenyuwu/arepo_rd/local_runs/lda_moving_baseline_glass_20260911/figures/sod_moving_baselines.png)
- [Yee时间步敏感性](/Users/zhenyuwu/arepo_rd/local_runs/lda_moving_baseline_glass_20260911/figures/yee_moving_timestep.png)
- [Yee端点守恒历史](/Users/zhenyuwu/arepo_rd/local_runs/lda_moving_baseline_glass_20260911/figures/yee_moving_conservation.png)

当前保留lumped作为较耗散的对照、GL/F1作为精度较好的既有moving
路径。four-pass仅作为发现移植缺陷的诊断，不升级为正式基线。
下一科学问题仍是F1/contour的激波震荡与移动时间几何；本轮没有
解决hierarchy/MPI，也没有修改CR、thesis或log1/log2。
