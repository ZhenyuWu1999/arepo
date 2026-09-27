# Thesis 4.2 数学复核与 4.2.3 精简建议

2026-09-26；作者：Codex；请求：Zhenyu 再检查 moving mesh RD theory 的数学推导，
判断是否可以开始写 4.3，以及是否删除 4.2.3。本轮只读 thesis，不修改正文。

## 来源与结论

检查当前本地 thesis main，HEAD `0f560a0` 的
`/Users/zhenyuwu/Desktop/MyThesis/Zhenyu-PhDThesis/zhenyu_thesis/chapter4/chapter4.tex`，
主要范围为第 295–918 行；对照 Chapter 3 的 Roe、N/LDA 与时间质量定义，并读
4.3 的奇异求解、时间项 fallback 和 endpoint conservation 说明。
Chapter 4 SHA256：`ebe1af94eb9a221b25a7a15525aa430b94e113a2ac426a6f11e80f96fb86434a`。
当前源码的小节号为 4.2.3 Scope；本地 chapter4.aux 显著过旧，不用其公式号定位。
红色 “to delete” 备选不是本轮所评的 reference formulation。

**主推导没有发现需要重构的代数错误，可以开始 4.3；定稿前应补上 LDA 守恒的相容性
条件，并修正文献范围的错误陈述。** 4.2.3 可以删去独立标题，必要限制并入相邻正文。
这里不把给出两阶段算法等同于证明所有 Euler 算例二阶、正性或完整更新严格守恒。

核对本地 Arpaia–Ricchiuto–Abgrall (2015), J. Sci. Comput. 63:502–547，
DOI 10.1007/s10915-014-9910-5，§4.4.2、§4.5、§6.1 与 Appendix；
PDF 18–20、23、32 页已渲染检查，保留完整公式与上下文。在线作者上传版本也确认 §6
包含 perfect-gas Euler equations，而非只处理 scalar/simplified Euler。

## 通过的主要推导

| 部分 | 检查结论与必要条件 |
| --- | --- |
| 坐标链式法则、intensive/conservative ALE、Reynolds 积分式（306–434） | 正确；空间散度始终对当前 x 求导，J 换元和几何项符号一致。 |
| 移动 P1 基、element-mean mesh velocity（458–494） | 在固定连接的仿射三角形上正确。grad U_h 为常量，所以积分中的 sigma_h 可以精确换为其单元均值；不能将这一步扩展到任意高阶 U_h。 |
| Roe ALE shift 与 mesh correction（503–525） | K_ALE 的 1/2、法向方向和修正负号正确；修正恢复作用在 U_h 上的网格输运，不能省略。 |
| LDA contour 与 G3（532–569） | 等价 contour 使用 element-mean sigma；网格项精确，非线性 Euler flux 通常为求积近似。G3 点、权重正确。 |
| midpoint 面积差与 DGCL（578–624） | 2D、直线节点轨迹、有效固定连接下为精确恒等式。不能据此令几何 midpoint 面积等于端点面积均值。 |
| 加权移动 Galerkin balance（637–657） | 正确；利用随网格输运的测试函数，时间导数产生的几何项符号匹配。 |
| midpoint 时间乘积（658–677） | 当前保留 O(dt^3) 是正确而必要的限定；光滑状态增量 O(dt)，几何面积差 O(dt^2)。 |
| predictor/corrector 几何项与 row-sum lumping（680–826） | 两阶段均得到 1+dt div(sigma)/2；modified area 的 1/3 与 endpoint difference 的 1/2 正确。corrector 必须使用 U^{n+1}-U* 的未知增量，当前写法正确。 |
| N mesh correction 等分（853–862） | 在共同 Roe 矩阵及相容 inflow solve 下，三个节点之和恢复指定 Roe split total；没有发现漏项。 |
| N/lumped、LDA/F1 和 mixed-stage beta（864–895） | 与所声明的算法相符；奇异 F1 的独立限制见下，公式本身不证明时间二阶。 |

独立抽取 200 组有效随机三角形运动，验证面积式、DGCL、mesh-mean identity 及时间乘积
**精确余项**，最大绝对差 `3.49e-16`。这些仅是代数交叉检查，不是 native solver 验证。
令 Mhat_ij=(1+delta_ij)/12，则单元时间乘积的精确余项为

\[
\left[\frac{A_{n+1}+A_n}{2}-A_{1/2}\right]
\sum_j\widehat M_{ij}(U_j^b-U_j^a).
\]

这直接支持正文的 O(dt^3)，也说明常值不变状态下余项严格为零。

## 必须补条件：LDA 分配不能无条件声称守恒

第 849–850 行现在直接说 nodal contributions satisfy sum(phi_i)=Phi。
Chapter 3 对停滞 Roe residual 的相容性说明不能自动覆盖独立构造的 nonlinear
P1-U Gauss contour。由 sum K_ALE=0 得

\[
\sum_i\widetilde\phi_i
=-\sum_i K_i^{ALE,+}(S^-)^\dagger\widetilde\Phi
=S^-(S^-)^\dagger\widetilde\Phi.
\]

等于目标 residual 的充分必要条件为目标在 range(S^-) 内；满秩时自动成立。
这不是 beta 的任意分量相加问题，而是线性系统是否有精确解的问题。
同样，秩亏时写 m_ij=A beta_i/3，并不能保证其全空间 column sum 是 A I/3。
4.3 第 1590–1596 行已经分别说明空间相容性检查和 F1 temporal lumping fallback。

最小正文改法：把无条件结论改成“当上述线性系统相容时，节点残差之和等于单元残差”，
并引用 4.3 的 singular solve/temporal fallback；不用在 4.2 重讲伪逆，也不用把正文改成
“所有矩阵必须可逆”。不在本轮提出或实现新的空间 residual completion。

### 明确的正状态反例（独立单元代数）

三角形 (0,0),(1,0),(0,1)，sigma=0，gamma=7/5；三个节点 rho=p=1，速度分别
(1,0),(0,1),(-1,-1)。守恒状态为

\[
U_1=(1,1,0,3),\quad U_2=(1,0,1,3),\quad U_3=(1,-1,-1,7/2).
\]

共同 Roe 平均速度为零，Hbar=25/6。S^- 的秩为 3，左零向量可取
ell=(-25/6,0,0,1)。直接 conservative-state contour 得

\[
\widetilde\Phi=(-1,0,1/10,-257/60)^T,
\qquad \ell\widetilde\Phi=-7/60\ne0.
\]

本例 rho 恒为 1，边上的 Euler flux 至多三次，因此 G3 本身精确；不是求积误差。
P1 conserved state 的压力亦保持正。G3/G8 结果相同至舍入精度。
伪逆分配总和的质量分量与目标相差约 -0.0264750，能量分量相差 +0.00635401。
这证明相容条件不可删除。它不代表本例是某次已发生的生产模拟失败，也不定位此前
Yee A2 失败的具体原因。原 native assertion 不能作为“对任何状态都相容”的证明。

## 必须修正：Arpaia 文献范围

第 300 行称 Arpaia 主要做 scalar/simplified Euler，“instead of the complete Euler
equations”。这不准确。2015 论文 §6（打印页 524 的 Equations 87–88）明确列出二维
理想气体完整质量、两分量动量和总能量 Euler 系统；§6.1（打印页 533）给出系统特征
矩阵、特征分解及分配说明。

可保留“主要推导先以标量展示”，但不应把本工作的区别表述为首次补上完整 Euler。
更准确的区别是面向 AREPO 的节点运动、Delaunay 重连、选定空间 residual，以及
存储和时间推进的具体实现。固定连接假设与生产拓扑变化的区别需要继续保留。

## 另外两处小的表述修正

- 第 454 行 geometric source “absorbed into the median dual cell”应指 **modified
  dual-area coefficient**；实际 median-dual 几何面积并未因此改变。后面的 736–737 行
  已经正确区分两者，前文应一致。
- 第 440 行把 Hubbard 的完整 space-time ALE RD 定义直接等同于瞬时边界项过于简化。
  更稳妥是说其采用 conservative ALE / space-time formulation，其空间边界通量对应
  该项；不要把带时间贡献的完整 residual 与瞬时项混为一谈。本轮未重新核对 Hubbard
  全文公式，因此此项是范围措辞建议，不给出新的 Hubbard 公式号。

第 298 行 Galilean invariance 是方法动机，不能仅由“网格随流体移动”推出本实现的
严格离散 Galilean covariance；Roe/contour 两种重构和实际 mesh velocity 规则仍有区别。
第 532 行 KH 的 robustness 结论应限于已做的对照，不能读作 general positivity theorem。
这两项不改变本轮确认的主推导。

## 4.2.3 可以取消独立小节

当前 4.2.3（902–918）不含新数学推导，第一段重复 lab/Gauss3/midpoint/Arpaia/LDA-F1
选项，第二段多为实现范围。全 thesis 的 .tex 中没有对其 label 的引用。

建议：

1. 删除独立的 Scope 标题及重复的选项清单。
2. 4.2.2 末尾保留极短衔接：推导假设单个 global step 内固定连接；其 uniform-state
   性质不等同于一般非均匀状态下的 endpoint conservation；重连与实际存储见 4.3。
   原 4.2.2 开头已有 fixed-connectivity/global-step 假设，无需再写长段。
3. 单 rank、equal timestep、lab frame 等具体 reference 选择并入 4.3 开头，那里目前
   已有大部分内容。static limit 的不同空间 residual 由 4.2.2 第 897–898 行的
   “with the residual evaluations specified here”以及前面 N/LDA 定义承接。

4.3 的 endpoint balance 是必要内容：单元空间 residual 分配闭合与完整 endpoint
总量守恒不同。当前 4.3 已写有 fixed-connectivity geometry defect 和 topology rebase
defect，不能因删除 Scope 而把这些问题从实现/结果中省略。

## 记录与验证边界

档案 `../local_runs/chapter4_2_math_review_20260926_v1/` 保存独立算式检查及 JSON 结果、
Arpaia 文本提取和上述页面渲染。未编辑/编译 thesis、未运行 hydrodynamics、未改 solver、
未提交或同步。报告及 log3 是本轮新增的项目记录。
