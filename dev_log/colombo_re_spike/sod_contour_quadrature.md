# Sod 的激波后速度散布：P1 状态上的物理通量积分

2026-09-12，接续 log3 §27。用户接受类似 static GL/F1 的局部负 vx
谷，但不能接受 moving 结果在 x_tube=.7–.8 的大散布。本轮以这个
区域为目标，保持 GL/F1 时间质量矩阵和既有 basis repair。

## 来源与待检验的机制

Log3 §24 已用不移动、不翻边的控制隔离：从 Roe 总残差切换到节点
contour 后，最大 vx 从1.009升到2.487。因而不能把所有散布都归因
于实际网格移动。Log2 §36.4 已明确提出，当前积分是 I_h F(U_i)，
并不等于 F(U_h) 的边界积分，建议用三点 Gauss 做针对性检验。
本轮落实这一既有建议，不是新发现一条此前日志未讨论的路线。

旧 contour 的物理部分可等价写成每条边的梯形积分：

\[
 \Phi_F^{\rm old}=\sum_{e=(a,b)}\ell_e\,\boldsymbol n_e\cdot
             \frac{F(U_a)+F(U_b)}2.
\]

新诊断开关 `RD_ALE_CONTOUR_GAUSS=3` 改为

\[
 \Phi_F^{G3}=\sum_e\ell_e\sum_{q=1}^3w_q\,
 \boldsymbol n_e\cdot F((1-s_q)U_a+s_qU_b),
\]

其中 s=(.1127016654,.5,.8872983346)，w=(5/18,4/9,5/18)。
Euler 通量对守恒变量通常是有理函数，因此三点 Gauss 仍是近似，
不是宣称精确积分。没有改成 P1 Roe 参数变量，也没有换 FV。
网格输运、节点存储、F1 mass、两个RK扫描和拓扑修补均保持原样。
实现以新旧边积分之差加到现有 Phi；源码中的法向朝内，所以修正
使用相反号。质量通量对U线性，其积分修正显式设为零。

三个结构性质可独立检查：

1. 相邻三角形的同一条边使用同一节点状态与权重、相反法向，修正
   在全局抵消。它不添加新的全局物理通量源。
2. 保守变量 Galilean 变换 G 是线性的；物理通量变换额外含有线性
   于 U 的项，其 Gauss 与梯形积分相同。因此修正满足 DeltaPhi'=G
   DeltaPhi。它保留 contour 原来优于 Roe+split 的这一性质。
3. 常状态修正为零；若两端 Euler 状态可容许，P1 凸插值也是可容许
   的。这只保证积分点状态，不是 LDA 完整更新的 positivity 定理。

## 实现与独立检查

实际 C helper 位于 `src/hydro/rd_contour_quadrature.h`，由受保护的
lab/frame 两个 contour 路径调用。只开放 equal-step LDA 诊断，未
改变默认配置，也不声称实现 hierarchy 支持。

`tests/rd/test_contour_gauss3.py` 编译实际 helper，针对200组非均匀
Euler 状态检验共享边反向抵消、boost变换、独立三点规则和64点
Gauss参考积分。共享边/boost/三点独立计算差分别为2.23e−15、
1.20e−14、2.84e−15；常状态修正为0。三点积分误差相对梯形误差
的中位比约.00104，最大.0274（仅针对该测试的状态分布）。

初次构建源提交：`559f8a4`（当时开关名为`RD_ALE_CONTOUR_GAUSS3`）。
随后`a4d5a76`将其统一为`RD_ALE_CONTOUR_GAUSS=3/5`并增加五点
精度控制；三点公式未变，旧二进制保持冻结。三种初始构建分别为lab、element frame、
zero-motion element frame。原生测试复用上一轮逐字节相同的glass
IC、gamma1.4、CFL.08、Sod cap1/3000，单管初始实际 Nx≈64，t=.08。
Yee复用48²/96² IC与相应dt；4个短控制先检查均匀流及lab/frame。

## 评价口径

所有图保留分析区间中的全部节点，使用RD面积加权均值。单独统计
x_tube∈[.70,.76] 的速度标准差，避开 t=.08 时约.780的精确激波；
该标准差含区域内的平均趋势，并非纯横向傅里叶模幅值。用户指定的
[.70,.80]包含激波，另报告该区域相对解析解的vx L1。整体ρ/vx/p
误差、负vx谷、守恒及Yee误差同时记录，不能只把散点抹平就算通过。

## 完成的三点积分结果

所有Sod对照使用相同初始状态、glass坐标和ID。moving主比较双方
都使用element frame，zero-motion对照均没有位置变化或拓扑修补。

| 配置 | 平台vx标准差 [.70,.76] | 全管max vx | 全管min vx | ρ L1 |
|---|---:|---:|---:|---:|
| Static Roe GL/F1 | .022394 | 1.00935 | −.77657 | .0157632 |
| Zero-motion，旧节点contour | .120801 | 2.48730 | −.66237 | .0161405 |
| Zero-motion，Gauss-3 | .027307 | 1.04215 | −.72929 | .0157222 |
| Moving，旧节点contour | .082562 | 1.36551 | −.71756 | .0171760 |
| Moving，Gauss-3 element frame | .022730 | 1.05103 | −.74318 | .0171985 |
| Moving，Gauss-3 laboratory frame | .022740 | 1.04961 | −.74315 | .0171983 |

Moving平台标准差降低约72.5%，达到static参照的约1.015倍；
zero-motion降低约77.4%。[.70,.80]整体vx L1从.136595降到.095329，
不是只在避开激波的小窗口中改善。移动密度L1仅增加约.13%。
全节点放大图仍显示有限散布，并不是逐点等于static，但原来显著
张开的散点区域已收紧到static量级。负vx谷仍在，符合本轮要将其
与平台散布区分的目标。

新方法没有换lumped、添加人工粘性系数或事后平滑；不过它确实
改变空间通量离散，不能由“未添加粘性项”推论数值耗散完全不变。
当前结果支持节点物理通量积分选择是本例散布的重要来源，不证明
旧contour不一致或其他流动中的全部不稳定性都出于同一原因。

Gauss-3 zero-motion的相对质量/能量漂移为1.97e−16/4.85e−16。
Moving lab为1.56e−9/3.67e−9，与既有Arpaia限制相当，未出现
上一轮直接移植four-pass导致的额外大漂移。初始场逐项相同，所有
保存的状态均通过有限值和ρ/p正值检查。保持正值不构成LDA定理。

短Yee lab/frame的ρ/p/v差不超过5.11e−15。长Sod的整体误差与
平台统计很接近，但逐点速度差可达.099、位置差.00595；长期网格
轨迹分岔使其不应被称作bitwise或逐点等价。

## 光滑流检查

Moving advected Yee使用相同48²/96² glass家族，t=1，实际dt分别
为1/256、1/512（256/512步），误差用最终RD面积和移动坐标。

| 量 | 原节点contour L1，48²/96² | Gauss-3 L1，48²/96² | 原空间阶 | Gauss-3空间阶 |
|---|---|---|---:|---:|
| ρ | .00107436 / .00030503 | .00114575 / .00031268 | 1.816 | 1.874 |
| p | .00133505 / .00036413 | .00148075 / .00038663 | 1.874 | 1.937 |
| 速度向量 | .00147507 / .00045160 | .00136029 / .00040080 | 1.708 | 1.763 |

ρ/p误差略增，速度误差减小，没有lumped那种接近一阶的退化。
只有两档空间检查，尚不是独立glass族或渐近二阶证明；也没有在
本轮重新测固定空间离散的时间阶。旧Yee主参考是lab，新是element
frame，上一轮已测得48²两frame整体密度误差几乎相同、速度差约
.025%；因此不要把这个表同时当成长时间逐点frame等价测试。

## 五点积分控制和结论边界

五点规则进一步降低独立积分误差，其200组状态检查中相对梯形
误差的中位比为2.44e−6，最大.00340。原生Gauss-5均匀流和moving
Sod也均正常结束。Sod平台标准差=.022445、max vx=1.05165、
min vx=−.74922、ρ L1=.0171945，质量漂移1.5263e−9。
它与Gauss-3的平台统计相近（标准差差约1.26%），支持改善不是
三点规则的偶然效果。长期网格轨迹不同，G3/G5逐点速度差仍可达
.130；这里验证的是目标统计和整体误差的稳定性，不是逐点求积
收敛或完整时间阶定理。

针对本次已复现的glass Sod，可以将**Gauss contour + GL/F1**作为
下一步基线候选。它已把用户关心的大散布降至static的量级，保留
锐利激波，并通过有限的光滑流与守恒检查。负vx谷没有消失，这
不是本轮验收目标。当前证据不包括KH/Gresho长程、不同glass种子、
更高Sod分辨率或hierarchical timestep；不能把旧日志中的全部
moving-LDA困难一并宣布解决。

## 归档与复现

新增11次原生运行：4次初始短控制、3次Gauss-3 Sod、2次长Yee、
1次Gauss-5均匀流、1次Gauss-5 Sod，全部正常退出。另复用3次已
冻结的static/zero/moving参照，未重跑或修改旧archive。最多4个
独立单rank运行同时执行，OMP/BLAS各一线程；大部分时间为2个。

入口：`tests/rd/run_sod_contour_quadrature.py` 的 prepare/build/run/
extend5；`tests/rd/analyze_sod_contour_quadrature.py` 计算和作图；
`tests/rd/test_contour_gauss3.py --points 3/5`检验实际C helper。
当前配置使用`RD_ALE_CONTOUR_GAUSS=3`或`=5`，要求已有equal-step
LDA contour；初次三点构建的历史开关名仍保留在冻结配置中。
没有修改默认配置、CR/hierarchy、thesis、log1或log2。

数据、输入、配置、二进制、构建与运行日志、JSON及PNG/PDF保存在
`/Users/zhenyuwu/arepo_rd/local_runs/sod_contour_gauss3_20260912`。
`campaign.json`逐case区分构建源559f8a4/a4d5a76，
`result_commit.json`记录最终结果提交；`source_snapshot`与
`provenance.json`保留源码及文件SHA256。`verification.json`检查
全部退出状态以及二进制/IC哈希。所有科学图均已检查。

- [Moving速度与局部放大](/Users/zhenyuwu/arepo_rd/local_runs/sod_contour_gauss3_20260912/figures/moving_sod_gauss3.png)
- [Zero-motion速度对照](/Users/zhenyuwu/arepo_rd/local_runs/sod_contour_gauss3_20260912/figures/zero_sod_gauss3.png)
- [Moving密度、速度、压力](/Users/zhenyuwu/arepo_rd/local_runs/sod_contour_gauss3_20260912/figures/moving_sod_gauss3_full.png)
- [Gauss-3与Gauss-5平台比较](/Users/zhenyuwu/arepo_rd/local_runs/sod_contour_gauss3_20260912/figures/gauss3_gauss5_plateau.png)
- [Yee光滑流检查](/Users/zhenyuwu/arepo_rd/local_runs/sod_contour_gauss3_20260912/figures/yee_gauss3_check.png)
