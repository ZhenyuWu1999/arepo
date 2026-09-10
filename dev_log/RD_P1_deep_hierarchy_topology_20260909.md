# 深时间层级下的 P1 翻边：从等待顶点，转向管理三角形时间区间

> **2026-09-10 正性验收修正：** active-only 转移可以把合法输入变成负密度，
> 而且存在该约束下根本没有保正解的情况。不得因标量守恒通过就将其作为
> 稳健主方案；N 输运的正性不能自动传递给包含此映射的整体方法。见 §9。

> **2026-09-10 独立复核补充（Opus 5，见 log 3 §17）：** §9 的反例取四点外部
> lumped 质量都是 1/12，对应几乎完全属于 cavity 的顶点。规则 6 邻居星下
> 生产映射的临界密度对比度是 13 而非 5。另外，把修正支撑从 active 扩到
> 整个 patch（w_i=m_i^+/M）后，本文的映射**恒等于**
> `residual_distribution_solver.c:2272-2320` 的生产 repair，因此那不是一个
> 待研究的新算子。真正的开放代价是正性检查被推迟到顶点唤醒时刻。

日期：2026-09-09。源码基线 `75c3d6ac65b8edce2741a372fc9507dacf22151e`。
起因：用户指出 cosmological simulation 的时间层级差异可能很大，旧 RD
连接等到所有顶点同步时可能已经严重偏离 Delaunay。这个顾虑成立：上一轮
全节点同步方案只能作为有条件参考，不能保证在深层级下有可接受的等待。

本次仍只研究 P1。新增两个标量时间积分检查及一个独立 Euler 状态转移
检查，没有改 C、没有运行 Euler PDE/MPI/cosmological simulation。
原生 FV + corner RD 仍停留在 future work。

## 1. 必须修正上一轮的强条件

不能在 inactive 顶点自身步中间任意修改其 frozen U。但该顶点的 extensive
Q 本来就会接收邻接细步贡献，几何账本 g 也会变化。**U 不变不等于 Q/g
都不能变。** 上一轮 full-mass transfer 同时改变四个顶点的 U，才需要
四个点全部同步。

记 P 是完整翻边 cavity 的节点集，A 是其中本时刻 active 的节点集，
I=P\A。以下 delta m 是在同一事件时刻、相同物理 cavity 上计算的旧/新
完整 P1 lumped mass 差；只有 changed triangles 对差值有贡献。

    delta m_i = m_i^+ - m_i^-
    D = sum_{i in P} delta m_i U_i

选择 sum_{i in A} w_i=1，且 inactive 节点 w_i=0，执行

    g_i^+ = g_i^- + delta m_i
    Q_i^+ = Q_i^- + delta m_i U_i - w_i D.

active 节点已完成自己的旧 star，故 g_i^-=m_i^-、Q_i^-=m_i^- U_i，
可恢复 U_i^+=Q_i^+/m_i^+。inactive 节点**不恢复 primitive**，保持 U_i。

三个可直接核对的恒等式：

1. sum Delta Q_i = D-D=0，转移本身守恒。
2. inactive 节点 Q_i^+-g_i^+ U_i = Q_i^--g_i^- U_i；已积累的非几何
   增量没有被重新解释成另一个 frozen state。
3. 均匀 U 时，sum delta m=0，所以 D=0；g 和 Q 成比例转移，均匀场保持。

最简单的权重是 w_i=m_i^+/M_A，M_A=sum_A m_i^+。它给所有 active
节点相同的状态修正 -D/M_A。全节点 active 时就退化为之前的 full-mass
weighted transfer。它没有解决时间区间覆盖；下面是相应调度条件。

## 2. 第一层改进：等被改变三角形同步，通常是第二小步长

先维持现有自然三角形时钟 h_T=min_{i in T} h_i。只在所有被删除和加入
的三角形都到达合法区间边界时换基，使用上述 active-only map。

对二维一个凸四边形的 2-to-2 flip，把四个顶点步长排序为

    h_(1) <= h_(2) <= h_(3) <= h_(4).

旧的两个三角形和新的两个三角形合起来是四种三点组合，故

    max_{T in old union new} min_{i in T} h_i = h_(2).

对固定、对齐的 dyadic bins，共同边界只需按 h_(2) 等待。被转移修改 U
的 active 节点，其所有邻接三角形自然也已到达步末；其他 coarse U 不变。
这不是四点全同步，也不是让外围粗步全部变细。

新标量检查复用前一轮的 192 cases，active-only 版本最大全局同步质量
误差 `4.44e-16`，inactive Q-gU 转移误差 `1.39e-17`。把全节点 U 都改掉
的对照仍出现最高 `1.69e-7` 误差。

深层级例子（非均匀标量、规定运动）：

| 四点步长 / h | 全节点同步的采用时刻 / h | active-only 采用时刻 / h |
|---|---:|---:|
| 1,2,256,1024 | 1024 | 2 |
| 1,1024,1024,1024 | 1024 | 1024 |

第一行 active-only 质量误差 `6.66e-16`。第二行暴露了明确的剩余问题：
只有一个细步节点时，第二小步长也可能非常大，单靠这个策略还不够。
一般多三角形 cavity 的条件应按其实际 old/new triangle clocks 计算，
不能直接套用四点的 h_(2) 公式。

## 3. 第二层改进：局部结束三角形区间，不唤醒 inactive 节点

更有希望的补充机制是让受拓扑事件影响的三角形在事件时刻 t_f 完成
尚未计算的区间。当前 concentrated moving hierarchy 在步末计算完整
区间，正好有机会使用这种规则；不能照搬到有预先提交半步贡献的其他
积分器。

候选流程：

1. 每个 RD 三角形保存 last_integrated_time。每次积分的真实长度为
   t_event-last_integrated_time，而非无条件使用 2^bin。
2. 事件前，普通 due triangles 正常积分；即将删除而尚未 due 的旧
   triangles 也积分到事件时刻。未自然到期的这种三角形，其三个节点
   都是 inactive，所以使用冻结状态，不中途提交这些节点的 primitive。
3. 完成旧网格本轮贡献、恢复正常 active 节点后，执行 §1 的转移。
   要求 A 非空，并通过正性/幅度检查。
4. 新三角形的 last_integrated_time 初始化为 t_f。以后第一次自然
   到期时只积分 [t_f,t_next]；不能再从 t_next-h_T 开始。
5. 将受影响的 inactive 节点标记为 frozen，直到它们**当前自身时间
   区间的末端（包括该末端 RK sweep）**。下一个自身区间才可解除。

第 5 步是必要的新状态。翻边后，一个以前邻接 fine triangle 的 coarse
节点可能在新网格上只剩 coarse triangles。如果仅根据当前 star 判断，
它会在本次粗步结尾突然成为 live predictor；这个 predictor 却没有贯穿
已经切开的旧时间区间。测试中去掉冻结标记，总量误差重新出现。

冻结标记可在积分末端之前设置，因为当前 moving path 的 predictor 与
corrector 集中在同一次调用事件；更早的小步中这个 inactive 节点本来就
没有非零 predictor。这个性质是候选方案复用现有算法的重要限制条件。

### 为什么这比强行 wakeup 小一些

提前结算的是少量三角形的欠缺增量，不是把四个 coarse 节点的完整 star
都强行推进并恢复新的 primitive。因此不需要由四点向外递归唤醒节点。
每个被修改 U 的节点仍然是自然 active；inactive U 保持相容。

Campoli 的局部 G+L 总和等于相应 ALE contour 的时间积分。对这里的
线性轨迹/冻结节点，区间切分保持共享边 trace 的相容性；对 live 节点，
必须保证其完整预测区间未被中途切分，冻结标记正是保护这个条件。
这给出保守性的候选构造。实际 Euler 的 contour reconciliation、全部
stage 细节仍须在 C 实现中逐项对照；标量验证不是完整 Euler 证明。

如果事件发生时 cavity 内没有 active 节点，本版 active-only map 不可
执行；不能隐式除以零，也不能假装已唤醒节点。可以等到最早的局部节点
同步，若几何不允许，则需事先安排合法的更小节点步或采取另一种转移。

## 4. 区间结算验证及其边界

`tests/rd/audit_p1_event_flush.py` 进行了 128 个普通组合和 8 个深层级
组合，包含有/无冻结标记对照。两个深层级设置为
`(1,2,256,1024)` 和 `(1,1024,1024,1024)`，基础 h=.02/1024，运行两轮
全局周期；在 ticks 1 和 1025 翻边，第二次还实际触发旧 coarse triangle
的提前部分区间结算。

| 结果 | 最大误差 |
|---|---:|
| 完整 interval + frozen-until 规则，全局同步质量 | 2.00e-15 |
| 均匀标量场 | 7.78e-16 |
| 几何账本闭合 | 8.66e-15 |
| inactive Q-gU 在转移中的变化 | 1.39e-17 |
| 去掉 frozen-until 的质量误差 | 2.32e-6 |

特别地，单 fine 节点的 `1:1024:1024:1024` 组合也可以在 ticks 1/1025
处理事件，质量误差 `1.34e-15`，不再等到 1024/2048。

所有翻边都是人工指定的二维对角线切换，轨迹固定且三角形远离塌缩。
这没有测试 Delaunay 事件检测、改变 timebins、强剪切、多 cavity 交叠、
Euler PDE、重力、宇宙学膨胀、三维拓扑或 MPI。现有 moving RD 源码本身
也通过 guards 排除了 comoving/source/refinement 等路径；不能把这里的
层级比例测试称为 cosmological simulation 验证。

## 5. 真正不能省略的困难：active-only 转移未必允许正性

少数 active 节点承担全部 D，状态变化幅度为 |D|/M_A。M_A 很小时可能
很大。限制 alpha 只能在存在一个合法低阶目标时奏效，不能凭空创造
质量或能量。

active 总量的目标是

    Q_A,target = sum_A m_i^+ U_i - D.

Euler admissible extensive states 构成凸锥。如果这个目标不是正密度、
正内能的状态，就不存在保持 inactive U 不变的正性 active-only map。
如果目标 admissible，则令所有 active U 都等于 Q_A,target/M_A，得到
一个守恒且正性的低阶端点；可用共同 alpha 与高阶端点混合。

独立随机 Euler 状态转移检查取 1000 组：302 组高阶端点合法，153 组可
通过共同 alpha 限制，545 组目标本身不合法。可行样本的最大守恒误差
`3.56e-15`。**这些是刻意宽分布随机样本，不是实际流体中的失败率。**

一个直接反例：单位方形 AC->BD，active=A,C，inactive=B,D；四点外部
质量都为 1/12，密度 (1,100,1,100)。保持 B,D 的密度不变后，需要的
active 总质量是 -32.5，所以任何 limiter 都救不了这一受限映射。

因此最初只能把此法作为通过可行性检查的路径。不可行时可研究扩大到
更多**已 active** 的修正支撑点、等其他点同步、或允许修正进入 inactive
的延迟状态账本；后者需要另一套时间/正性论证，本次未实现。不能宣称
守恒、正性、不改 inactive U、立即接受任意翻边四项已经同时解决。

## 6. 对“偏离 Delaunay 太远”的实际控制

全域有多少 bins 不是直接几何指标。建议同时记录：

- 相邻三角形对角之和超过 pi 的程度，衡量局部 Delaunay 违反；
- q_T=4 sqrt(3) A_T/(l_1^2+l_2^2+l_3^2)，衡量三角形形状；
- 本次轨迹段上 signed area 的最小值及到形状阈值的预计时间；
- pending 时间、cavity 大小、转移修正幅度与可行性失败次数。

在固定直线轨迹段，面积是二次式，可以在整个区间而不仅端点检查。
阈值需用测试选择；面积为正并不等价于 CFL、安全 upwind 条件全部满足。

优先在自然三角形同步点转移；几何期限更紧时，且 A 非空、转移可行，
尝试局部区间结算。这样不会仅因一个粗节点的 1024h 就强制保留旧边。
仍需保证旧三角形在**上一个事件到当前事件**之间有效；本办法不修复
已经发生的反转，也不精确定位步内真实 Delaunay crossing。

邻居 timebin 比例限制可以作为辅助，但不能是主证明：事后减少 inactive
节点的 bin 不会自动结算它原来的完整积分状态；“发现危险再全部 wakeup”
仍回到了之前的困难。若采用前瞻限制，应在节点合法步边界约束其下一步，
并在速度更新时重新核对几何预测。全域硬性相同 bin 与局部有梯度的 bin
限制是不同的成本，不能预先假定传播一定轻微或一定会抹平全域层级。

## 7. AREPO 接入：数学对象保持 P1，新增的是事件账本

候选最小数据与改动：

1. 持久 RD triangle：oriented IDs、periodic winding、birth/last-integrated
   time；旧节点的访问与 MPI owner/halo。原先延迟翻边方案已经需要这些
   三角形记录，现在进一步记录区间长度。
2. 本轮 RD element set：normal-due 或 topology-forced；为两个 RK stages
   固定同一份 [start,end]。**不能 predictor 后就提交 last_time，使
   corrector 读到零长度区间。** corrector 完成后才提交时间。
3. `rd_ale_hierarchical_prepare` 当前硬编码 2^bin 的 dt，需从 element
   interval 读取。正常无事件的路径保持原来的 dyadic dt。
4. SphP 增加 frozen-until 或等价的当前自身区间标记；与现有 star-bin
   判定共同决定 predictor 是否 live，随粒子迁移和 exchange 更新。
5. 换基更新所有 P 的 Q/g，只对 active 恢复 primitive 和当前 DualArea。
   inactive 的缓存 primitive 不应被普通“统一刷新”代码悄悄覆盖。

现有 extensive increments、MPI exports、inactive 接收增量可继续复用。
原生 AREPO 也以共享界面步长向 active/inactive 两端更新守恒量，但它的
原生 FV 守恒证明不是本 P1 转移的证明。
[Springel 2009, §7.2](https://arxiv.org/pdf/0901.4107)。本地调用顺序见
`src/main/run.c:203,224,356,368`；bin 改动目前只遍历 active particles，见
`src/time_integration/timestep.c:199`，增长时的对齐检查在 `:789`。

MPI 不引入新数学形式，但持久拓扑跨域和所有 rank 采用同一事件必须
另外验证。当前已有的 MPI prototype 不能证明这部分已经正确。

## 8. 当前取舍与复现

不建议把“等全部四点同步”作为深层级下唯一主机制。保留它作易解释的
回退/参考；先验证 active-only transfer，再验证局部 interval closure
与 frozen-until，分别用删掉某一条件的对照暴露错误。比换成 native FV
更贴近现有 P1 算法，但仍有正性、精度和工程验证工作。

本次复现：

```sh
/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python tests/rd/audit_p1_active_transfer.py
/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python tests/rd/audit_p1_event_flush.py
```

原始 JSON、汇总及 SHA256 provenance 存在：
`/Users/zhenyuwu/arepo_rd/local_runs/p1_active_transfer_20260909`。
本次没有证明整体时间二阶或高分辨率收敛；冻结粗节点的精度限制仍在。

## 9. 2026-09-10：正性是主验收条件，active-only 映射已有严格反例

用户问这种工程处理是否会让 N scheme 失去 positivity。准确结论是：
本次没有修改或反驳 N residual 自身的正性性质；但新增的 transfer 可以
破坏正性，因此即使假定输运阶段保正，组合算法也不能继承这个保证。
这不是仅仅“还没有证明”，而是存在具体的负密度反例。

以下用精确有理数检查，不依赖 RK、CFL、时间步大小或浮点误差。
单位方形 AC->BD，四点外部 lumped contribution 都取 1/12，则

    m^- = (5/12, 1/4, 5/12, 1/4)
    m^+ = (1/4, 5/12, 1/4, 5/12).

令 A,C active，B,D inactive；旧密度为 (1,4,1,4)。取零速度、常正压力，
所有旧 Euler 状态都 admissible。这是转移算子的合法输入反例，不是
声称已经运行了一个新的完整 Euler PDE 问题。

    old total mass = 17/6
    new inactive mass if rho_B=rho_D=4 is fixed = 10/3
    required new active mass = 17/6 - 10/3 = -1/2.

所以任何仅由 active 状态承担修正、同时保持上述 inactive 几何质量
转移和 frozen state 的守恒映射，都不能保证密度正性。该结论不依赖
active 权重怎样分配。仅缩小输运 CFL、而保留相同 active 集合及这次
强制拓扑接受，不能改变这个代数障碍。

允许所有节点修改时，既有 patch-average 低阶转移在同一例子给出

    rho^L = (5/3, 12/5, 5/3, 12/5),

总质量仍为 17/6，所有密度为正；常压力/零速度也保持。这表明问题不是
“P1 守恒转移与正性必然不相容”，而是当前 active-only 约束太强。
但在 hierarchical 情形中立即修改 inactive primitive 又会损害冻结
时间历史，因此不能直接照搬这个同一时刻的全节点 fallback。

源代码再次核对：当前 equal-step 高阶 repair 本身也没有无条件正性保证，
在 `residual_distribution_solver.c:2342` 附近发现不合法状态就终止；
它尚未接入此前独立验证的全 patch 低阶 convex fallback。equal-step
情形有可构造的保正低阶端点；active-only 情形还可能连端点都不存在。

当前决策：保留三角形 lifetime closure / frozen-until 的守恒研究价值，
但把 active-only 转移降为受限实验，不以失去正性换取提前翻边。
下一项数学任务应是建立可保正的转移及其异步时间解释，例如研究允许
inactive conserved ledger 分担修正、而 primitive 继续冻结的办法。
这会改变此前 Q-gU 不变的选择，其一致性与正性尚未证明，不能当作
已经解决的新补丁。完整方法仍须分别验证输运、时间积分与转移的正性。
