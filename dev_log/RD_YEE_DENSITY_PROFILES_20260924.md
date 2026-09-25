# Yee boosted LDA: density profiles at 384²

作者：Codex；请求：Zhenyu。2026-09-24。

使用§107已完成的LDA/Gauss3 lab-frame static/moving结果，boost=(1,0)、t=1。没有新跑模拟或修改thesis。

## 定义与画图方法

每个snapshot有147456个原始节点。半径相对解析中心(6,5)，采用周期minimum-image距离，不重新拟合数值中心。密度解析解为 [1−(γ−1)β²/(8π²γ) exp(1−r²)]^[1/(γ−1)]，γ=1.4、β=5。原始节点直接绘图，不重插值。

误差逐节点相对各自r的解析解计算，再以最终median dual area=m/rho加权，径向bin宽0.05。不是先平均密度再减bin中心的解析值。完整域L1与原summary.json匹配至浮点精度；图显示r≤4.5，下表覆盖整个方盒至r=√50。

## 图像

![Density profile](/Users/zhenyuwu/arepo_rd/local_runs/yee_static_moving_384_20260924_v1/figures/yee_lda_density_profile_384.png)

![Native-node error maps](/Users/zhenyuwu/arepo_rd/local_runs/yee_static_moving_384_20260924_v1/figures/yee_lda_density_error_map_384.png)

二维图两侧使用相同色标，绘制原始节点，以解析中心为原点；没有重插值。

## 误差径向分解

| Radius | Static mean absolute error | Moving mean absolute error | Static fraction of global L1 | Moving fraction of global L1 |
|---|---:|---:|---:|---:|
| 0–1 | 0.000101703 | 0.00036826 | 17.23% | 40.07% |
| 1–2 | 9.02393e-05 | 0.000146301 | 45.91% | 47.72% |
| 2–3 | 3.39347e-05 | 1.73074e-05 | 28.76% | 9.42% |
| 3–4 | 5.63046e-06 | 3.53241e-06 | 6.69% | 2.69% |
| 4–√50 | 5.27869e-07 | 5.55753e-08 | 1.42% | 0.10% |

完整域rho L1：static1.852956e−5、moving2.887549e−5。Moving的r<2误差占87.79%，static为63.14%。Moving在r<1的平均绝对误差约为static的3.62倍，在1<r<2约为1.62倍，但2<r<3约为static的0.51倍；外围不是造成其全域误差更大的主要来源。

Moving在r<1平均有符号误差为+2.2506e−4，在1<r<2为−7.9932e−5，表现为涡核密度略偏高、外圈偏低，另有非轴对称散布。原始密度曲线几乎重合。单靠这一形状不能将误差命名为纯扩散或某个实现缺陷。

## 为什么boost不保证moving更准确

解析解的平移速度为1，最大旋转速度为β/(2π)=0.795775（r=1），这里bulk velocity没有远大于涡旋内部运动。当前moving速度来自流体速度、半步压力加速度和网格规整项，并非只以boost刚性平移（冻结源码src/mesh/set_vertex_velocities.c:255及其后续regularization分支）。旋转流场同时让网格变形并允许拓扑变化。

Moving可减少整体平移相对网格的输运误差，却不消除压力/声波、时间离散、网格几何及topology/endpoint处理等误差。LDA本身已具有较低的数值耗散，因此static的bulk-advection误差未必占主要地位。当前profile与“外围误差下降、核心附加误差抵消收益”一致，但它没有分离这些误差来源。

候选解释包括网格变形/regularization/翻边、时间与几何离散、近Lagrangian矩阵条件数/数值秩以及F1 fallback。它们仍是待验证机制；不能用图断言其中某项为原因，也不能由单个分辨率profile推断持续降阶。保持§109的全四点拟合结论。

## 可复现记录

`plot_yee_density_profiles.py`同时保存在tests/rd和本档案。`density_profiles.json`保留快照路径/hash、解析中心、bin定义、原始summary hash和全部径向统计。`density_profiles.log`保留运行输出。两张PNG已视觉检查，所有误差点均来自保存快照，未追加768²等计算。
