# P1 moving RD：full-patch 异步转移与剩余流出预算

2026-09-10，续 log 3 §§14–17；独立复核 Claude §17 后的推导与小验证。
主记录为 `RD_DEVELOPMENT_LOG_3_localMac.md` §18。只研究现有 P1 路线；
没有修改生产 C、论文或 log 2，没有开展 Euler PDE/MPI/cosmological 测试。

## 1. 先区分四个问题

1. **时间覆盖**：删除旧 triangle 之前，它的欠缺区间是否已结算？新
   triangle 是否从自己的 birth time 开始？这决定有无漏算/重复积分。
2. **守恒转移的支撑**：由 active 节点独自承担修正，还是整个 cavity
   的实际 extensive ledger 都可参与？这与何时采用新 connectivity 独立。
3. **转移瞬间的正性**：转移前 admissible 的账本，转移后是否 admissible？
4. **剩余时间区间的正性**：转移修改了 inactive Q，但旧 frozen U 仍在
   驱动后续 residual；到自己的粗步末端是否仍有正密度和正内能？

Claude 正确指出前两项不能捆绑。上一轮 event closure 测试采用 active-only
修正，其正性反例不能否定 event closure 本身。保持 inactive U 不变是
当前 frozen-star 时间积分的一致性要求；额外保持 Q-gU 不变只是上一版
转移的选择，不是物理定律。下面放开后一个限制。

但将 full-patch 同步修正直接用于异步 ledger，并不能自动解决第 3、4 项。
本次既给出一个第 3 项的条件性构造，也实际复现了它在第 4 项失败的情形。

## 2. Claude 的 positivity/DMP 评论应怎样理解

### 2.1 两个密度阈值属于不同算子

单位正方形 AC→BD，规则六邻居的完整旧 nodal masses 为

    a = old changed-patch masses = (1/3, 1/6, 1/3, 1/6)
    b = new changed-patch masses = (1/6, 1/3, 1/6, 1/3)
    o = unchanged outside masses = (2/3, 5/6, 2/3, 5/6)
    m- = o+a = (1, 1, 1, 1)
    m+ = o+b = (5/6, 7/6, 5/6, 7/6).

取 A,C active，rho=(1,r,1,r)。若 inactive B,D 的新 extensive mass
仍必须等于 m+ rho，留给 active 的总质量是

    (2+2r) - (7/3)r = 2-r/3.

r>6 已经不可能全部为正；r=8 时为 -2/3。这个反例不依赖很小的 outside
mass。Claude 的 r*=13 是 **full-patch uniform-shift 高阶算子**的密度
阈值，不能用来否定 active-only 算子的不可行性。两者并不矛盾。

### 2.2 密度比小不等于 Euler 状态安全

仍用上述规则 star，gamma=1.4，四点 rho=p=1、vy=0，令

    vx = (4,-4,4,-4),    E = 21/2.

full-patch 高阶均匀 shift 的 D_momentum=-8/3，M=4，给出

    vx_high = (14/3,-10/3,14/3,-10/3)
    p_high  = (-7/45,89/45,-7/45,89/45).

因此密度比为 1 仍可产生负压力。Claude 的低速度随机扫描支持其采样
状态的经验表现，不能仅凭密度对比给 KH/Gresho/Yee 建立 Euler 保正定理。
这也不表示那些实际测试必然出错；实际状态与这里的相反高速状态不同。

### 2.3 守恒变量的凸包不提供压力或 entropy 的上界

同一例子的同步低阶 patch-average 转移守恒、保正，而且在旧守恒向量
凸包中；它得到 rho=1、E=21/2，但

    vx_low = (52/15,-52/21,52/15,-52/21)
    p_low  = (2021/1125,6557/2205,2021/1125,6557/2205)
           ≈ (1.7964,2.9737,1.7964,2.9737).

旧压力全为 1，新压力却更高，specific entropy ln(p/rho^gamma) 也增大。
这是守恒混合把相反速度的动能转成内能；不能仅凭出现此现象就判定为
非物理错误，但它严格反驳“守恒向量凸包保证没有压力/熵新极值”。

因此 relaxed DMP + common alpha 可以用于明确指定的**守恒分量范围**，
不能直接宣称解决 KH 中的 entropy excursion。如果增加压力/熵最大值
限制，必须另外证明低阶端点满足该限制；alpha=0 不再自动提供可行端点。
Euler 最低熵约束与最高熵约束也不能混为一谈。

以上三个例子已由 `audit_p1_ledger_remap.py` 用有理数精确核对。

## 3. 异步历史余项不能省略

原 active-only 增量式把权重扩到 full patch 后是

    Q_i+ = Q_i- + delta_m_i U_i - w_i D
         = m_i+ U_i + (Q_i- - m_i- U_i) - w_i D.

用实际几何账本表示则是

    Q_i+ = g_i+ U_i + (Q_i- - g_i- U_i) - w_i D.

只有历史余项为零，才退化为同步 uniform-shift map。inactive 节点已经
收到细步邻居的贡献时，Q/g 一般不同于冻结的 U。因此“同一同步算子的
异步增量扩展”是合理候选，“一般异步状态下 bit-identical”不是恒等式。

同步低阶增量也不能直接继承同步凸性证明。例如 g=m-=(1,1,1,1)，冻结
U=(1,1,1,1)，正的实际 Q=(0.1,1.9,1,1)。同步高/低两端的增量均为
delta_m，却使 Q_A+=0.1-1/6=-1/15。这是一个代数输入反例，**没有声称
该任意输入已由当前时间积分动力学到达**；下一节改用实际 Q/g 避开它。

## 4. 用实际 Q,g 构造转移瞬间保正的 full-patch map

### 4.1 几何账本有可用的解释

在这里的 fixed-bin、endpoint-ledger、实际区间结算模型中，令 s_T 为
当前每个 triangle 最后结算到的时间。由初始化、几何增量和转移的归纳：

    g_i = sum_{T contains i} A_T(s_T)/3.

每个 T 的几何增量是 [A_T(t)-A_T(s_T)]/3；翻边前将所有 removed T
结算到事件时刻 t。因此 changed old patch 的 a_i 可以从 g_i 中扣除，

    o_i = g_i-a_i >= 0,    g_i+ = o_i+b_i,

o_i 是 unchanged triangles 在各自 s_T 的正面积贡献，**不是一般意义的
同一时刻 outside nodal mass**。自然 active 时所有 incident T 都已结束
到当前 t，于是 g_i=m_i(t)。这要求三角形在相关区间内有效、几何更新与
时间戳一致；不能用强行重置 g 掩盖遗漏区间。本次不主张旧 Arpaia
physical-Q storage rebase 也由这个恒等式自动修复，见 log 3 §10。

### 4.2 实际账本的低阶与高阶候选

定义 W_i=Q_i/g_i；这是用于转移的账本状态，不是 inactive residual 的
冻结状态 U_i。设 cavity 的旧、新面积相同，即 sum a=sum b。取

    Wbar = (sum_i a_i W_i)/(sum_i a_i)
    Q_i^L = o_i W_i + b_i Wbar
    g_i+ = o_i+b_i.

则 sum Q^L=sum Q，而且 Q_i^L/g_i+ 是输入 W 的凸组合。只要输入 W
admissible，g_i、g_i+ 为正，a,b,o 非负，就有转移瞬间的 Euler 正性。
常量 W 同样保持。该转移不要求 cavity 内存在 active 节点。

对应的 uniform-shift 高阶候选为

    D_g = sum_i (b_i-a_i) W_i,    G = sum_i g_i+ = sum_i g_i
    Q_i^H = g_i+ (W_i-D_g/G).

共同 alpha 混合 Q^L 与 Q^H，任意 alpha 均守恒；可在 W 上施加 Euler
admissibility 和守恒分量 relaxed DMP。同步时 W=U、g=m，退化为已有
两端点。异步时 W 是混合时间历史，不是共同物理时刻的 P1 场；这里的
“高阶”仅指沿用同步端点，**未证明异步空间/时间精度**。

转移更新整个 cavity 的 Q,g；只给自然 active 顶点恢复 U=Q/m。
inactive U 保持冻结，直到自身区间末端；之前的 frozen-until latch 仍需
保留，避免 topology change 中途改变其 predictor 类型。

2000 个宽分布随机 admissible Euler ledger 样本通过 transfer 检查：
相对守恒误差最大 3.28e-16，均匀状态误差最大 5.21e-16。1445 个高阶
端点不 admissible，加入 2% 守恒分量 relaxed DMP 后 1992 个样本限制了
alpha，最小 alpha=0.1391。**这些计数不是流体测试失败率**，也没有
测试后续 Euler 演化。输入 W admissible 是必须检查的前提。

## 5. 更重要的新反例：保正转移后，粗步末端仍可变负

`audit_p1_ledger_future_outflow.py` 使用已有标量 N residual 做一个真正
的时间积分诊断：静止 periodic 4×4 顶点网格，32 个 P1 triangles，
速度 (0.31,-0.17)，一个细步节点，其余步长为 8h。初值除一个 inactive
节点为 1 外都为 0.01。在 tick 1 人工翻转一条对角线；这不是自然
Delaunay crossing。所有 removed triangles 的欠缺区间先结算，新增
triangles 从 birth time 开始；inactive 状态一直冻结到自身末端。

旧/新网格最小 nodal bound m_i/sum_T k_iT^+ 都为 0.5208333333。
采用粗步 H=0.95×该上限=0.4947916667。相同初值和步长的结果：

| 方法 | 翻边时输入/输出正性 | 粗步末端 min U |
|---|---|---:|
| 保留原 connectivity | 无转移 | 0.01 |
| §4 的 full-patch 凸低阶转移 | 都为正，最小值 0.01 | **-0.03443564406** |
| §6 的剩余流出预留低阶转移 | 都为正 | 0.01 |

负值一例的所有已计算 predictor states 也保持为正，最小值 0.01。
全局总量仍守恒，没有 orphan/prebirth intervals。问题不来自明显的
漏算时间区间，也不能通过“转移时已经检查了正性”排除。

具体地，inactive 高值节点在普通低阶转移后仅剩

    Q_after_remap = 0.05627031762,

但它仍用旧 U=1 支付余下区间的流出，其待付流出为

    R_future = 0.059375.

后续流入不足以补回差额，粗步末尾 Q=-0.00251093238。换基瞬间的
Euler/scalar 凸性证明看不到这份“尚未支付的流出”。**只缩短被删除
triangle 的本次积分区间，没有同时缩短 inactive 节点的剩余冻结区间。**

## 6. 标量情况下：先预留全部剩余流出，再转移剩余部分

静态标量 N residual 可以写成

    Phi_iT = k_iT^+ (U_i-U_in,T),    k_iT^+ >= 0,

其中 U_in,T 是非负权重的流入组合。inactive i 在自身末端 t_i,end 前
保持 U_i 不变；若所有 stage 的流入状态非负，它需要预留的流出量为

    lambda_i = sum_{T contains i} k_iT^+ (t_i,end-s_T)
    R_i = lambda_i U_i.

s_T 使用 **转移之后每个 triangle 的 last-integrated time**：新 T 从
event 开始，unchanged T 可能还欠一个从 event 之前开始的区间。不能只
计算 event→t_i,end；本测试 tick 1 时最长欠缺仍是 8h，而不是 7h。
自然 active 节点所有 incident history 都已结算，本次 frozen reserve=0。

令 g^-、g^+ 是转移前后的实际几何账本。若

    d_i^- = g_i^- - lambda_i > 0,
    d_i^+ = g_i^+ - lambda_i > 0,
    S = sum_{i in P} (Q_i-R_i) >= 0,

则存在一个简单、故意较耗散的低阶端点：

    Q_i^L = R_i + d_i^+ S/(sum_{j in P} d_j^-).

因为 sum g^+=sum g^-，同一 lambda 下 sum d^+=sum d^-，故该映射
守恒，且 Q_i^L>=R_i。在固定未来系数、没有新事件改变该预算、后续
流入非负的条件下，inactive 节点不会因支付 frozen outflow 而变负。
严格正性取 S>0 和 d_i^+>0。常量 U_0、Q_i=g_i^- U_0 时，S=U_0
sum d^-，所以 Q_i^L=g_i^+ U_0，均匀场保持。

这不是 §4 outside-preserving map；它混合整个 cavity 的**剩余预算**，
不保持线性场，也不保证 W 的原有最大值范围。作为最低阶端点可以再
与更准确的守恒高阶候选混合，但 alpha 必须检查 Q_i>=R_i，而不只是
Q_i>0。测试没有实现该后续高阶 limiter。

本例 S=0.00890979549>0，min d^-=0.003125，min d^+=0.00430501302。
预留转移后高值节点 Q=0.06072189073，足以覆盖 R=0.059375。
theta=(0.5,0.8,0.9,0.95)、均匀/非均匀、三种模式共 24 个组合通过
预期断言；负值对照是**预期失败**，不是算法通过。最大质量误差
1.39e-17，均匀误差 1.11e-16。

### 条件不可省略

- 若 S<0，在该 cavity 内守恒重分配也不可能让每个节点都满足 Q_i>=R_i。
  若 d^+ 不正，这个构造也不可用。需要扩大支撑、在合法时间边界缩步，
  或真正结束有关节点的旧冻结区间；不能靠裁剪负值或换一个 alpha 解决。
- 对 moving scalar，几何收缩、相对速度变化以及未来 k^+(t) 的上界必须
  一并纳入。静态 lambda 公式不能直接移植；重复 flips 也要重新评估
  预算和可行性。此次只验证一个 flip 的一个粗周期。
- 对 Euler，矩阵 N splitting 不是一个标量非负 outgoing coefficient；
  不能逐分量套用 R=lambda U，也不能只给 density 预留预算就宣称
  pressure 保正。需要对现有 Euler N/RK/ALE 更新找到可验证的
  admissible-set 条件或足够的剩余区间界。这是当前最重要的数学缺口。
- g>0、W admissible、预算可行、所有未来 stage admissible 是不同条件。
  保守的预算是充分条件；超出预算不等于实际解必然变负，流入可能补偿。

## 7. 对现有 AREPO 项目的选择

目前最值得继续的组合是 **P1 + event-time triangle interval closure +
full-patch actual-ledger transfer + 对剩余冻结区间的约束**。相比换成
native FV/corner RD，它保留现有 P1 几何、Euler residual 和 extensive
increment 通道。但它不是把现有 equal-step repair 多调用一次。

需要进入设计的数据仍主要是：persistent triangle 的有向 IDs/periodic
winding、birth/last time、两个 RK stages 共用的真实区间、inactive
frozen-until、actual Q/g、patch 的 old/new masses。预算若最终可行，还
需要对剩余区间的可验证界；先不要把试验性的 scalar lambda 固化进 C。

原生 AREPO 可照常生成 Delaunay 新网格；RD 暂存被删除元素，只为完成
它们尚欠的积分，然后提交转移并销毁旧记录。不必让 AREPO 的 Voronoi
mesh 长期维持非 Delaunay connectivity。但旧 triangle 在上次事件到
当前事件之间仍须有效；event closure 不会修复已经发生的反转。

若无法为现有 Euler N 构造可信的预算，替代路线是**真正结束局部节点
的旧时间区间，再刷新其 U**，而不是只切开 removed triangles。它需要
结算相关 incident histories、处理 predictor 和边界共享 trace，可能
扩大局部同步区域；目前没有证明这是廉价、无递归传播的操作。可在节点
正常步边界采用几何/预算前瞻限制，减少事件时被迫处理这种情形的频率。

对 MPI，不增加新的流体数学要求，但 event 必须有唯一 owner；完整
patch 的 Q/g、旧元素、时间戳和 frozen state 必须可访问，增量只能提交
一次，粒子迁移要携带这些状态。此前 no-topology MPI 对照不能替代这个
验证。最合理的顺序仍是单 rank 数学/区间实现确定后，再做 MPI 集成。

现有 mixed-bin frozen-star 时间精度问题也没有被转移修复；此处不声称
二阶 multirate。Campoli endpoint-ledger 适合作为最少额外存储歧义的
初始对照；Arpaia 还需单独解决 log 3 §10 的 storage rebase 问题，不能
把此次 scalar 静网格结果称为两种 moving-mesh form 已全部解决。

## 8. 复现与证据边界

从仓库根目录运行：

```sh
/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python tests/rd/audit_p1_ledger_remap.py
/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python tests/rd/audit_p1_ledger_future_outflow.py
```

第一个只需 NumPy；第二个导入旧 scalar audit，运行环境需 NumPy/SciPy。
原始 JSON、摘要和 SHA256 provenance：
`/Users/zhenyuwu/arepo_rd/local_runs/full_patch_ledger_20260910/`。
起始 HEAD：`315bece11785f4e05c98c07819b0842a8cf4d156`。

已建立的是：修正支撑与事件调度的区分；实际账本低阶 map 的条件性
瞬间保正；一个随后变负的标量 N 时间积分反例；静态标量剩余预算的
条件性低阶构造。**完整 moving Euler/N 的正性、精度、changing bins、
重复/交叠 cavity、MPI 和生产实现都尚未完成。**
