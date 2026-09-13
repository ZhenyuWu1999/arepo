# Legacy Roe-Uhat/U split：与当前 Gauss 基线的匹配复测

2026-09-12，log3 §31。用户要求在 chapter4 数学草稿说明 Gauss，
并重新测试旧混合残差的长期 LDA KH 与 moving Sod。8次原生启动完成，
没有修改C求解器。构建源 e33aea3；实验分支保持不变。

## 数学与实验问题

关闭 `RD_ALE_CONTOUR_RESIDUAL` / `RD_ALE_CONTOUR_GAUSS`，明确开启
`RD_ALE_SPLIT_MESH_VELOCITY`。分别启用/关闭 `RD_ELEMENT_COMOVING_FRAME`。
旧残差为

\[
 \widetilde\Phi_{split}^T=\sum_iK_i^{ALE}\widehat U_i
 -\int_T\sigma_h\cdot\nabla(U_h-\widehat U_h)dA
 =\sum_iK_i^{phys}\widehat U_i-\int_T\sigma_h\cdot\nabla U_h,dA.
\]

旧形式不需要额外逐边Gauss循环，仍是一个有意义的替代插值选择，
不能因为共动系表达不如contour简洁就排除。GL/F1、Arpaia面积配对、
两阶段RK2、refreshed basis repair与运动设置均保持匹配。

其简洁性来自理想气体Roe参数 Z=(sqrt(rho),sqrt(rho)u,sqrt(rho)v,
sqrt(rho)H)。记其分量z0..z3，有

\[
 U(Z)=\left(z_0^2,z_0z_1,z_0z_2,
 [z_0z_3+(\gamma-1)(z_1^2+z_2^2)/2]/\gamma\right)^T,
\]
\[
 p(Z)=\frac{\gamma-1}{\gamma}[z_0z_3-(z_1^2+z_2^2)/2],
 \quad F_x(Z)=(z_0z_1,z_1^2+p,z_1z_2,z_1z_3)^T.
\]

U和F都是Z的二次函数。若Z_h线性，div F(U(Z_h))线性，所以单元
均值处的Roe线性化可以直接给出物理残差积分。
代码的 Uhat_i=(dU/dZ)(Zbar) Z_i 是该积分的辅助线性化状态，
不是一个新的可直接作为流体状态解释的节点值。
因此要区分三条路径：线性Z产生的通量积分、节点通量的线性插值，
以及线性U产生的非线性通量Gauss积分。三者不是同一个函数的不同
代数写法。Gauss比较的意义不能简化为“旧Roe不够精确”。

历史log2 §§41–42/61已记过两种moving LDA均失败；那一组生产glass、
IC与拓扑处理不与当前完全相同。本轮重新使用已冻结的新基线，
以免把历史结果当成当前匹配结果。

## 设置与输入核验

KH复用 `kh_gauss_20260912` 的smooth/sharp glass48² IC与参数：
gamma1.4、p2.5、rho1/2、vx±.5、vy=.1sin(4pi x)，smooth tanh宽度
.025；CFL.3，cap.02，目标t10，每.2保存。谱CFL与regularization不变。
每个被激发波长含约24个初始点间距。

Sod复用 `sod_contour_gauss3_20260912` 的glass128²和参数：单管
**有效初始Nx≈64**，gamma1.4，t.08，CFL.08，cap1/3000。
不额外给Sod启用KH所用的谱CFL。分别构建KH/Sod lab/frame，共4二进制。
两次uniform门槛先完成，rho/p/v最大变化5.55e-16，质量/能量漂移0。
随后至多4个singleton原生任务，OMP/BLAS各1线程；没有后台继续运行。
分析逐ID验证新旧对照的初始位置、状态、RD面积完全相同。

## Smooth KH：旧split仍无法长期运行

| 方法 | 本轮/复用结果 | 最后保存rho_min |
|---|---|---:|
| 旧nodal contour（复用） | t=.444717负质量停止 | .2530，t=.400085 |
| Legacy split，lab | t=.800476负质量停止 | .0268261，t=.800171 |
| Legacy split，frame | t=.800476负质量停止 | .0268260，t=.800171 |
| Gauss3/5（复用） | 均正常到t10 | .84695/.83938，t10 |

两条split在同一个ID923出现负质量约−1.064e-5，前一步质量1.016e-5。
它们的失稳时间、位置和最后保存状态高度接近，排除了“只因共动系
写法引入长期失败”的解释。最后保存的质量/能量相对漂移约
1.304e-8/1.456e-8，熵代理范围偏离约210.49；全局守恒好并不能
防止局部状态失效。不能将最后有效快照冒充失败端点。

两条sharp split也在首步t=.000610352触发A2，lab/frame缺陷分别
2.653e-8/2.618e-8，容差6.614e-13/1.939e-13。没有放宽断言、
增加null-space补全或修改SVD。它们没有给出sharp KH长期演化。
本轮没有重复做该旧算子的高精度矩阵捕获，故这里只报告实际A2失败。

## Moving Sod：旧split确实抑制平台大散布

| 方法 | vx标准差 [.70,.76] | 全管maxvx | 全管minvx | rho L1 |
|---|---:|---:|---:|---:|
| Static Roe（复用） | .022394 | 1.00935 | −.77657 | .0157632 |
| Moving nodal contour（复用） | .082562 | 1.36551 | −.71756 | .0171760 |
| Legacy split，lab | .023080 | 1.07405 | −.79469 | .0175158 |
| Legacy split，frame | .022979 | 1.07389 | −.79902 | .0175099 |
| Gauss3（复用） | .022730 | 1.05103 | −.74318 | .0171985 |
| Gauss5（复用） | .022445 | 1.05165 | −.74922 | .0171945 |

平台std按最终RD面积加权，相对区域均值计算，区间避开exact shock。
用户较宽[.70,.80]区域的exact-vx L1：nodal .136595，split lab/frame
.098055/.097971，G3 .095329。split frame的平台std比nodal下降72.2%，
只比G3大约1.1%；rho L1比G3增加约1.8%，负vx低谷稍深。
两条split都完成969步；G3旧档970步。同参数下步数略变是流场反馈。
split lab/frame质量漂移1.693e-9/1.682e-9、能量3.924e-9/3.911e-9。
两坐标系长程结果不逐点相等，但上述统计与定性结论接近。

**结论：只针对这组Sod大散布，旧split就能达到接近Gauss的改善，
Gauss不是唯一办法；但旧split不能替代Gauss对当前smooth KH的
长期运行改善。** 保留它作为重要控制，继续以Gauss3作为跨这两种
测试更有支持的候选，仍不作普遍稳定性/正性或长期KH精度声明。

## Chapter4与归档

已按明确授权修改本地
`/Users/zhenyuwu/Desktop/MyThesis/Zhenyu-PhDThesis/zhenyu_thesis/chapter4/chapter4.tex`，
新增数学草稿subsection `section:ALE_RD_Gauss_physical_flux`，解释旧nodal/
Gauss/split三者、P1兼容性、积分点、符号与验证边界，并补充共动系
公式中的Gauss替换位置。保留原有正文，未改chapter1–3或bibliography。
新增section当前单章预览编号4.2.4；没有将其改成定稿或写入性能结论。
本地修改未push/pull，也未自动同步Overleaf。thesis文件保持待用户正常同步。

独立Chapter4 wrapper经pdflatex编译并重复解析本章交叉引用。
新增公式所在第5–7页检查，主公式页5/6有PNG；外部章节/文献引用在
独立wrapper中未解析属预期，不能称为全thesis最终编译。仅有旧段落
的5.22pt overfull；新增段落无overfull，未改无关旧排版。

Archive: `/Users/zhenyuwu/arepo_rd/local_runs/legacy_split_20260912`。
包含8次尝试（4完成、4诊断失败）、7个复用参考、初始状态核验、
原始数据/配置/二进制、4组PNG/PDF、thesis before/after及编译预览、
verification/result_commit/provenance JSON与源快照。完整quad说明继续
参见§30；本轮未重新运行Gauss结果或修改solver/default/hierarchy。

- [Sod平台与全管vx](/Users/zhenyuwu/arepo_rd/local_runs/legacy_split_20260912/figures/sod_split_comparison.png)
- [KH演化](/Users/zhenyuwu/arepo_rd/local_runs/legacy_split_20260912/figures/kh_split_comparison.png)
- [Chapter4独立编译预览](/Users/zhenyuwu/arepo_rd/local_runs/legacy_split_20260912/thesis_edit/check_chapter4.pdf)
