# P1、ALE contour 与 Gauss 的完整对应；KH 晚期形态的文献对照

2026-09-12，接续 log3 §29；本轮为代码核对、数学推导与文献检查，
没有新增流体模拟，也没有修改算法。代码基线 ede418b。

## 1. 从 Euler 到运动 P1 单元残差

二维守恒变量及通量为

\[
 U=(\rho,m_x,m_y,E)^T,\qquad
 p=(\gamma-1)\left(E-\frac{m_x^2+m_y^2}{2\rho}\right),
\]
\[
 F_x=(m_x,m_x^2/\rho+p,m_xm_y/\rho,(E+p)m_x/\rho)^T,
\quad
 F_y=(m_y,m_xm_y/\rho,m_y^2/\rho+p,(E+p)m_y/\rho)^T.
\]

考虑一次固定拓扑的运动三角形 T(t)，面积 A，重心坐标 lambda_i。
顶点位置 x_i(t) 和速度 sigma_i 给出仿射网格速度

\[
 U_h(x,t)=\sum_{i=1}^3\lambda_i(x,t)U_i(t),\quad
 \sigma_h=\sum_i\lambda_i\sigma_i,\quad
 \partial_t\lambda_i+\sigma_h\cdot\nabla\lambda_i=0.
\]

因此 Euler 强残差积分可写成

\[
 \mathcal R_T=\int_T(\partial_tU_h+\nabla\cdot F(U_h))\,dA
 =\frac A3\sum_i\dot U_i+\Phi_T,
\]
\[
 \Phi_T=\int_T[\nabla\cdot F(U_h)-\sigma_h\cdot\nabla U_h],dA.
\]

由于 grad U_h 为常量，且平均 sigma_bar=(sigma_1+sigma_2+sigma_3)/3，
在这一瞬时仿射单元上有精确恒等式

\[
 \boxed{\Phi_T=\oint_{\partial T}
 [F(U_h)-U_h\bar\sigma_T^T]n\,ds.}
\tag{1}
\]

这正是当前代码 contour 总残差的目标形式。法向 n 在此向外。
代码用对顶点的内法向 N_i，因此旧的节点表达式是
Phi_old=(1/2) sum_i ell_i [F(U_i)-U_i sigma_bar^T] N_i。
它与逐边外法向梯形积分相同，因为 sum_i ell_i N_i=0。

要区分真正的运动控制体边界通量：

\[
 \frac{d}{dt}\int_{T(t)}U_h\,dA+
 \oint_{\partial T(t)}[F(U_h)-U_h\sigma_h^T]n\,ds
 =\mathcal R_T,
\]
\[
 \Phi_T=\oint[F(U_h)-U_h\sigma_h^T]n\,ds
       +\int_T U_h\nabla\cdot\sigma_h\,dA.
\tag{2}
\]

式(1)包含的平均速度不能直接冒充式(2)的真实面速度，而漏掉
几何体积项。式(1)的 mesh 输运被积函数线性于 U_h，端点规则精确；
式(2)边上的 U_h sigma_h 一般是二次函数。前轮“mesh 输运已经精确”
专指式(1)的冻结空间算子，不是宣称整个运动时空积分、Arpaia更新或
翻边结算完全精确。当前算法仍保留既有时间几何与拓扑误差。

## 2. 原方法与 Gauss 恰好替换哪一项

边 e=(a,b) 长 ell_e，参数 s∈[0,1]，外法向 n_e。

\[
 U_e(s)=(1-s)U_a+sU_b.
\]

原 contour 为

\[
 \Phi_T^{old}=\sum_e\ell_e\left[
 \frac{F(U_a)+F(U_b)}2 n_e
 -(\bar\sigma_T\cdot n_e)\frac{U_a+U_b}2\right].
\tag{3}
\]

Gauss 为

\[
 \boxed{\Phi_T^{G_q}=\sum_e\ell_e\left[
 \sum_{r=1}^{q}w_rF(U_e(s_r))n_e
 -(\bar\sigma_T\cdot n_e)\frac{U_a+U_b}2\right].}
\tag{4}
\]

实现采用修正差

\[
 \Delta\Phi_T=\sum_e\ell_e\sum_rw_r
 \{F(U_e(s_r))-(1-s_r)F(U_a)-s_rF(U_b)\}n_e.
\tag{5}
\]

因为 sum w=1、sum ws=1/2，式(5)加上式(3)即式(4)。源码
`src/hydro/rd_contour_quadrature.h` 用内法向，故修正前有负号。
质量通量 (m_x,m_y) 线性于 U，修正为零；代码只修正两动量和能量。
密度仍能通过后续矩阵分配和耦合时间演化改变。

G3 点为 (1/2−sqrt(15)/10,1/2,1/2+sqrt(15)/10)，
权重 (5/18,4/9,5/18)。G5 的点/权重见 §29 报告或实际 helper。
它们分别精确积分次数≤5/9 的一维多项式。Euler F(U_h) 一般是
有理函数，因此不是精确积分，也不提高完整算法的名义阶数。
这不是“Green–Gauss 梯度重构”，而是边界通量的 Gauss–Legendre 求积。

相邻单元同一边的物理通量修正相反；这不要求它们的 sigma_bar 相同，
因为式(5)已没有 sigma。共动系 U'=G(b)U，b=sigma_bar 时平均输运
消失；先在共动系计算式(4)和分配，再用 G^{-1} 返回，与当前路径一致。

## 3. P1 不要求通量也属于 P1

P1 限制的是 U_h 的表示空间，不是 F(U_h) 的函数空间。
原方法额外采用 I_hF=sum_i lambda_i F(U_i) 的通量插值；这是一个
不同的离散选择。新方法直接求积 F(sum_i lambda_i U_i)，没有新DOF。
把更多 Gauss 点用于同一个线性 I_hF 确实不会改变积分；这里改变的
正是被积函数。不能说旧规则没有精确积分它自己选择的插值。

最简单的例子是 Burgers 通量 f(u)=u²/2，u_h(s)=a+(b−a)s：

\[
 \int_0^1 f(u_h)ds=\frac{a^2+ab+b^2}{6},\quad
 \frac{f(a)+f(b)}2=\frac{a^2+b^2}{4},\quad
 I_{exact}-I_{old}=-\frac{(b-a)^2}{12}.
\]

P1 状态已经产生 P2 通量。Euler 的 m_x²/rho 与 (E+p)m_x/rho
进一步说明非线性。小状态差时缺陷通常从二次状态差开始；强梯度下
可以显著影响残差。由现有 Sod/KH 结果可推断它是重要误差来源，
但没有证明 Gauss 添加了正耗散或满足熵稳定性。

若两端理想气体状态满足 rho>0、E−|m|²/(2rho)>0，守恒变量的凸插值
也可容许，所以内部 Gauss 状态不产生插值过冲。这只保证求值点状态，
不保证 LDA 分配、GL/F1、完整时间更新或翻边后的正性。

## 4. 进入 LDA/F1 的位置；尖锐 KH 的值域问题在哪里

令 A_x=dF_x/dU、A_y=dF_y/dU 在单元 Roe 平均状态取值，

\[
 K_i=A[(A_x-\bar\sigma_x I)\partial_x\lambda_i+
       (A_y-\bar\sigma_y I)\partial_y\lambda_i],\quad
 K_i=K_i^++K_i^-,\quad S^-=\sum_iK_i^-.
\]

单元上 sum K_i=0。可逆时

\[
 \beta_i=-K_i^+(S^-)^{-1},\quad
 \phi_i=\beta_i\Phi_T^{G_q},\quad\sum_i\beta_i=I.
\tag{6}
\]

Gauss 改的是式(6)右端总残差，未修改特征矩阵定义。F1 满秩时间
质量块仍为 M_ij^F1=(A/3) beta_i，与 j 无关；校正阶段作用为
T_i=beta_i[(A/3)sum_j Delta U_j/Delta t]。秩亏时已有时间块改用
保守 lumped fallback。实际 GL/RK2 使用预测及校正，并保留 Arpaia
面积配对/结算；这里不把它重新描述成另一套直接 Heun 积分器。
普通 Galerkin 的 P1 质量矩阵 A/12 [[2,1,1],[1,2,1],[1,1,2]]
与这个 RD F1 块不是同一对象；选择 P1 并不唯一确定时间稳定化。

尖锐 KH 的失败出现在式(6)的分配，而非 Gauss 函数求值：

\[
 z=(S^-)^\dagger\Phi_T,\quad \phi_i=-K_i^+z,
 \quad\sum_i\phi_i=S^-(S^-)^\dagger\Phi_T.
\]

若 Phi 不在 Range(Sminus)，缺失 r=(I−Sminus Sminus^dagger)Phi。
§29 的实际首步 rank3 捕获、80位复算与强制SVD均确认 r 非零，
约129倍守恒容差。这不是“P1 与 Gauss 冲突”；旧 contour 也会触发。
共享边积分抵消与单元节点分配守恒是两个不同环节，需要分别满足。

## 5. SWIFT/AREPO 与晚期 KH 的文献对照

查阅于2026-09-12。以下是原作者结果，不是本轮新跑的 SWIFT/AREPO。

- [Borrow et al. 2022, SPHENIX §5.6 / Fig.13](https://academic.oup.com/mnras/article/511/2/2367/6423434)：
  SWIFT 的该 SPH 方案将密度比2、剪切速度差1、波长.5 的尖锐界面KH
  展示到10 tau_KH，并讨论晚期高度混合状态。人工热传导会抹去部分
  小尺度次级结构。它不是我们tanh/glass的严格匹配参考。
  按论文时间尺度 tau=(1+chi)lambda/(Delta v sqrt(chi))，代入我们的
  宏观参数得到1.06066，因此我们的t10约为9.43 tau。这仅作量纲归一，
  不是有限厚度可压缩KH的精确线性e-folding时间（惯例也有2pi差别）。
- [Springel 2010, AREPO, Fig.32](https://wwwmpa.mpa-garching.mpg.de/~volker/arepo/arepo_paper.pdf)：
  50×50 moving-mesh对照到t2展示非线性卷涡；不能据此直接为我们t10
  的形态作定量背书。
- [Mocz et al. 2015, §3.1 / Figs.1–3](https://doi.org/10.1093/mnras/stv1598)：
  AREPO中改进Lloyd网格正则化可消除原方案网格尺度的次级结构；
  即使已经改进RK/梯度，旧正则化仍有这些噪声。主模早期增长正确
  也不排除晚期被网格噪声污染。作者将这些次级结构判为数值伪影。
- [Lecoanet et al. 2016, validated nonlinear KH](https://academic.oup.com/mnras/article/455/4/4274/1267403)：
  用Athena与Dedalus及明确扩散建立非线性参考；指出数值噪声可播种
  小尺度结构，无显式扩散时次级不稳定和混合非常强。这支持需要
  可比较物理/数值扩散与收敛检查，而不是按“细节多少”排名。

当前图的晚期紊乱与长期非线性混合相容，但不能逐结构判为物理解。
尤其盒子48²意味着每个被激发波长只有约24个初始间距；tanh尺度
参数delta=.025约1.2h（不等于整个过渡区只有1.2h）。这是粗分辨率
长期稳定性测试。Gauss使旧LDA从t.445停止改善到t10，值得保留；
不能由此认定晚期已收敛，或把scalar B较平滑的图自动判为更准确。
优先验证早期主模增长、48/96/192及独立glass种子、非主模功率是否
集中在网格尺度，再比较晚期能量/混合统计。无需为了判图好坏先
引入另一个新求解器。
