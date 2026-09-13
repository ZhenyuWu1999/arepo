# LDA 基线中的四种 Heun：历史回顾与精度含义

2026-09-11，接续 log 3 §24。用户决定先核实旧基线，暂不继续 CR/basis
repair 扩展，并询问当初 Heun 是否因不满足二阶时间精度被排除。
本轮重新读取 volume1、volume2 和时间质量推导；不新跑流体测试，不
改 solver、默认 Config 或论文。下述旧测量是日志记载，不是本轮重测。

## 结论

不能把当时的决策缩写为“LDA + Heun 不是时间二阶，所以换 F1”。
历史上有四个不同对象：

| 路径 | 更新对象/方式 | 时间精度与历史定位 |
|---|---|---|
| 旧 AREPO-RD 路径 | 两次半权重 residual，梯度/PDE Taylor predictor | 固定网格实测一阶；不是严格 Heun on RD rate |
| 这次的 LDA lumped Heun | `v=−S⁻¹R_LDA`，两阶段均用同一 rate | 标准 ODE Heun，正则光滑分支时间二阶；本次仅测 Sod，未重跑时间阶梯 |
| 当前标准 GL/F1 | predictor 用 v，再做一次 F1 total-residual correction | 旧固定网格阶梯约一阶；联合 h,dt 收敛在当时 glass 上约1.88/1.74 |
| F1 rate-consistent Heun | 每个物理 RK 阶段构造 `G=(2I−S⁻¹M_F1)v`，再对 G 做 Heun | 旧固定网格实测二阶；四次扫描，后来因成本/实用误差未选为默认 |

“lumped mass 与 N 使用的质量矩阵相同”是准确的；“因此 LDA 变成 N”
或“因此违反时间二阶条件”都不成立。LDA 的空间 residual 仍是 LDA。
Lumped 本身是合法且守恒的质量选择，代价在于能否保持目标非定常
P1 RD 的时空精度，而不是矩阵只能归 N 使用。

## 旧记录的先后关系

1. Volume1 约line461--497：早期把两次半权重调用称为 formally second
   order Heun，因为 predictor 是一阶 Taylor。这是早期判断，不是最终
   时间精度证据。
2. 2026-07-29，约line2351--2445：指出旧 LDA 使用 lumped 时间权重而
   非 F1；引入 temporal residual 是为修复非定常 RD 的质量/空间分配
   不匹配，不只是替换 RK 外壳。
3. 2026-07-30，约line3570--3608：boosted Yee 的 lumped h-orders
   .93/.95，而 stationary Yee 是1.86/1.98，说明静止平衡测试不足以
   判断非定常精度。
4. 2026-08-01，约line4760--4808：固定网格 Richardson 测得 N+RK2
   约2.009、LDA+F1 约1.011、旧 N baseline 约1.001。旧日志说前两行
   “only mass differs”不够严谨，因为空间 N/LDA 也不同；它们自身不
   构成纯质量矩阵隔离。后续 F1 方法分析/阶梯，以及本轮固定空间 LDA
   的质量切换控制，应分开评估。
5. 同一条记录把旧 lumped h-ladder 外推至 dt→0：空间阶由.970变为
   .971；n64 density error 从2.037404e−3变为2.039429e−3。旧路径确有
   一阶时间误差，但它不是该空间收敛退化的主要来源。
6. `LDA_F1_Heun_vs_standard_LDA_RK2.md` §12.2：标准 GL/F1 在 triangular/
   glass/jittered 上固定网格 p≈.98--1.00；F1 rate-Heun 在 triangular
   和 glass 上 p≈2.000。不能把它与 lumped Heun 混为一谈。
7. 2026-08-04，volume1 line8134--8218：F1 rate-Heun 不成为 production
   默认，原因是当时比 GL/F1 慢1.57--1.77倍，而 boosted Yee/Sod 的
   density L1 约大1.4--2.3%。这是特定工作区间的成本/误差决策，
   不是证明它数学上不合格。此前 Sod 的 A2 assertion 属 roundoff
   tolerance 问题，随后 `eb72efd` 修复（volume1 line8404--8423）。
8. Volume2 §1.1 明确 production 用标准 GL/F1，rate-Heun 保留作分析；
   §37.3 更纠正过误删 rate-Heun 的计划，说明它曾真正修复固定网格
   时间阶问题。旧推导文档前半部分的“current method”具有时间语境，
   必须以当前 Config 和最终决策为准。

## 为什么“有 Heun 外形”还不够

在固定网格、光滑正则状态下，设真正 RD 半离散 rate 为 f_h，旧 Taylor
predictor 经变量变换后的 leading rate 为 P_h。简化模型是

\[
U^*=U+\Delta t P_h(U),\qquad
U^{n+1}=U+\frac{\Delta t}{2}\{f_h(U)+f_h(U^*)\}.
\]

展开得到 `Unew=U+dt f_h+(dt²/2) f'_h P_h+O(dt³)`，而同一 ODE
`U'=f_h(U)` 的正确二次项是 `(dt²/2) f'_h f_h`。只说 P_h 是连续
PDE 的一阶 predictor，不保证这两个系数在固定 h 下相同。一般会
留下 O(dt²) 局部缺陷，从而产生 O(dt) 全局时间误差。

真正 lumped Heun 两阶段都用 v，因此正则光滑分支满足二阶 ODE
条件；这不等于它所积分的空间离散已对原 Euler 方程二阶。

对局部线性化的仿射非定常解，lumped temporal 与 LDA spatial 的
元素权重差具有 `Σ_T |T|(I/3−β_i^T)∂tU` 的形式。一般并不自动抵消，
但不能像早期日志那样把“仅 beta=I/3 或 steady 才可能抵消”理解为
全局必要条件：装配、对称性或特殊解也可能抵消。精度判断必须依靠
具体离散分析与非定常 h-ladder，不能只凭“N 的 mass”这个名字。

旧 dt→0 结果表明，在当时已测的 advected Yee 家族上，lumped rate
的 h 误差约一阶。换成严格 Heun 只改善对这个 rate 的时间积分，
不能自动改变其半离散极限。因此这次 Sod 更干净，不足以重新确立
lumped Heun 为满足全部精度目标的 production baseline。

## AREPO 的关系

[Pakmor et al., Improving the convergence properties of the moving-mesh code AREPO, §3](https://arxiv.org/pdf/1503.00562)
先写出 Heun 的起点/终点 flux 平均，再用 primitive-variable 时间
外推避免昂贵的中间状态处理，明确将实现称为 RK 与 MUSCL-Hancock
的 hybrid。故用户说 AREPO“接近 Heun”是准确的；不应将原生 FV 的
验证直接移植为 nodal RD + 任意 predictor 的二阶证明。

FV 的 cell averages、重构和 face flux 与 nodal P1 RD 的 residual
分配不是同一个半离散算子。这里说明为什么复用主循环还需要额外的
RD 阶段/质量修正；并不是重新开启原生 FV+RD 重写路线。

## 当前基线工作范围

先暂停新的 CR/basis 扩展，保留当前分支和全部档案。基线比较固定为
同一份 glass、Roe total、相同初值和终点，明确列出 lumped Heun、
标准 GL/F1、F1 rate-Heun 三种方法。下一项验证需分别考查：

- 固定网格的 dt 自收敛，检验时间积分；
- advected Yee 的 h 收敛且时间误差受控，检验非定常空间精度；
- Sod 全节点 extrema、横向散点及密度/压力误差，检验激波行为。

先前 zero-motion contour 的 scatter 应单独审计，不能靠 topology
修补或 blanket“LDA 不单调”绕过。F1 rate-Heun 与标准 GL/F1 共享 G
的 dt→0 极限，所以即使前者时间二阶，也不能预先宣称会消除 F1
关联的 Sod undershoot。当前没有新增它在该 glass Sod 上的测量。

这份回顾确立比较口径与既有证据；不表示完整基线已经重新验证完毕。
