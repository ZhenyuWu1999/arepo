# P1 RD：在局部同步点换基，避免截断旧时间区间

> 后续修正：本文“所有受换基影响的顶点同步”是对同时修改所有顶点 U 的
> 原映射给出的充分条件，不是任意守恒换基的必要条件。保持 inactive U
> 不变、更新其 Q/g 账本并只修改 active U，可以放松等待条件。深层级
> 检查及局部三角形区间结算见 `RD_P1_deep_hierarchy_topology_20260909.md`。

日期：2026-09-09。源码基线：`75c3d6ac65b8edce2741a372fc9507dacf22151e`。

用户决定：论文提交前继续修补 P1 RD；原生 FV + corner RD 停留在现有
Python 代数检查，作为 possible future work。本记录不建议切换论文主方法。
本次只增加独立 Python 检查和设计记录，没有修改生产 C 求解器或 thesis。

## 1. 本次新增结论与适用范围

值得先实现的小范围方案是：**RD 可以延迟采用新的对角线；在发生改变的
区域内，所有受换基影响的顶点自然同步后，先结束旧连通关系上的积分，
再执行同一时刻的守恒换基。** 全局其他区域仍然可以处于粗步中间。

这不是“任意时刻发生翻边后补一个质量修正”。它改变 RD 采用拓扑的时刻，
使拓扑切换避开尚未结束的相关时间区间。AREPO 的原生 Delaunay/Voronoi
网格仍可按原来的时刻重建，RD 暂时使用自己的旧三角形连通关系。

目前支持这一方案的是：固定 dyadic bins 下的时间区间论证、现有 Campoli
守恒条件，以及一个规定运动的标量 ALE/N 检查。**尚未实现自动 cavity
管理、真实 Delaunay 事件调度、Euler 稳定性或 MPI 持久化。** 因此应称为
一个有明确验收条件的候选方案，不是已经完成的任意运动网格算法。

## 2. 为什么“只结算翻边的两个三角形”还不够

设每个顶点自己的步长为 h_i，三角形步长为

    h_T = min_{i in T} h_i.

现有 frozen-star 层级算法会让 inactive 顶点继续接收 extensive increment，
但在自身步末以前保持供残差使用的 U_i 不变。换基一般会改变四个顶点的
U_i，因而也会改变这些顶点在**未翻边的邻接三角形**中的取值。

因此需要分别检查：

1. 被删除/新生的三角形有没有遗漏或重复计算时间区间；
2. 换基有没有在某个邻接三角形的时间区间中途改变其冻结的顶点状态。

本次反例把翻边安排在 tick 2，翻边前后的三角形步长都是 1 或 2，所以
被替换三角形的区间完全闭合。然而四个顶点中仍有步长 4 的顶点；换基
中途改变了其 frozen state，32 ticks 后全局同步点的质量误差最高约
`1.69e-7`。每一次换基本身的质量误差仍只有 `2.23e-16`。

把同一换基放到 tick 3，还会出现三角形的未结算区间和出生前积分，
相应最大质量误差约 `1.14e-5`。两个对照都说明，瞬时零和转移并不能
独自修复时间积分。这些对照使用本文明确给出的 naive ledger extension，
不是声称当前生产代码已实现了这种换基。

## 3. 局部同步条件为什么不必递归唤醒全域

令 P 为一次完整 cavity 换基中所有状态将被修改的顶点集合。对单次
2-to-2 flip，就是四个顶点；多次翻边应按完整 cavity 处理。
固定、对齐的二进制步长下，选择

    t_s / h_i 为整数，对所有 i in P 成立。

等价于等到 P 中最大步长的下一个同步点。**必须先按旧连通关系完成 t_s
这一轮 predictor/corrector，并恢复 active primitives，再执行换基。**

这给出以下局部条件：

- 对任何包含 P 中顶点 i 的旧三角形，h_T <= h_i，且 h_T 整除 h_i。
  因而这些三角形全部在 t_s 到达步末，而不仅仅是被删除的两个三角形。
- P 中每个顶点的完整旧 star 都已结算；在当前 Campoli 几何账本约定下，
  可以检查 g_i = m_i^-、Q_i^- = m_i^- U_i^-。
- 新三角形的步长也整除至少一个所属顶点的步长，t_s 是它们共同的合法
  区间起点；下一次积分不会回溯到它们出生之前。
- 区域外粗步顶点可以保持 inactive。对区域外尚未结束的三角形，若它
  包含 P 中顶点，它已经在上述证明中，不可能尚未结束；若它不包含，
  它的顶点状态不被换基改变。

所以这不是“唤醒四个点，然后不断递归唤醒邻居”：我们**等待已有合法
同步点**。局部最大步长等于全局最大步长时，它退化为全局同步方案；
局部最大步长更小时，就可以在全局大步内部接受拓扑变化。

这里的守恒仍使用既有固定连通关系 Campoli hierarchy 的条件：一致的
共享边 P1 contour trace、相容的冻结状态/预测量、正确几何积分、完整
owned triangle 集合。该论证没有把普通 RD 的每个异步小步变成零和
transaction；总量应在全局同步点按完整区间检查。

## 4. 同步后如何沿用 P1 守恒换基

以下 m 是 P1 lumped area，U 是守恒变量向量。P 的外部三角形不改变，
但其质量系数应包含在受影响顶点的完整 m_i 中。

    delta m_i = m_i^+ - m_i^-
    D = sum_{i in P} delta m_i U_i^-
    M = sum_{i in P} m_i^+ = sum_{i in P} m_i^-
    U_i^+ = U_i^- - D/M
    Q_i^+ = m_i^+ U_i^+

因为完整 cavity 的总面积未变，sum delta m_i = 0，故

    sum_{i in P} Q_i^+ = sum_{i in P} Q_i^-.

这复用了已经检查过的 full-mass weighted transfer。均匀场不变；正确
同一时刻几何下，仿射场由 P1 积分一致性保持。它是表示转移，不是新增
一个 Euler 空间离散方法。换基后同步设置 DualArea、RD_GeoLedger 和 Q，
并使下一轮使用新连通关系计算 star bins。

Euler 正性仍需要之前的 patch-common alpha 限制器，而非每个点单独限制。
保守的低阶端点为

    Q_i^L = m_i,out U_i^- + m_i,P^+ Ubar_P,
    Ubar_P = sum m_i,P^- U_i^- / sum m_i,P^-.

以同一个 alpha 对所有节点和所有守恒分量混合 Q^L 与 Q^H，可以同时
保持总量与 admissibility，前提是换基前已有合法的同步状态。原生产
repair 在高阶结果不合法时会终止，并未接入这个正性回退。
正性限制会损失无限制映射的精确可逆性，不能同时声称两者无条件成立。

## 5. 新 Python 检查的结果

复现：

```sh
/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python tests/rd/audit_p1_patch_sync.py
```

依赖 NumPy/SciPy；直接复用既有 scalar Campoli ALE/N kernel。
网格是周期 4x4 顶点网格；翻边区域内步长为 h、2h、4h、4h，外部为 8h。
移动测试采用固定顶点速度，位置沿直线变化；另有静止几何对照。
检查两种基础步长、均匀/非均匀标量、四种细步顶点位置、两种请求时刻，
以及 fixed / patch_sync / immediate 三种策略，共 192 cases。
请求翻边由测试指定，不是计算 Delaunay 条件产生。

| 检查 | 最大误差或现象 |
|---|---:|
| fixed control，全局同步点质量 | 4.45e-16 |
| patch_sync，全局同步点质量 | 4.45e-16 |
| patch_sync，单次换基质量 | 4.45e-16 |
| patch_sync，均匀场节点误差 | 4.45e-16 |
| patch_sync，几何账本 closure | 8.33e-17 |
| patch_sync，三角形遗漏/出生前积分 | 0 / 0 |
| immediate，tick 2 换基 | 质量误差最高 1.70e-7，无三角形寿命错误 |
| immediate，tick 3 换基 | 质量误差最高 1.14e-5，有寿命错误 |

安全方案的四次换基都在 ticks 4、12、20、28，均不是全局同步点。
最小测试三角形面积约 `0.02939`，不存在趋近塌缩的几何。
均匀场在 unsafe 对照中也保持到了 roundoff，进一步说明只测均匀流
不足以发现这类非均匀状态的守恒故障。

原始 JSON：`/Users/zhenyuwu/arepo_rd/local_runs/p1_patch_sync_20260909/scalar_results.json`。
这些结果没有验证 Euler、shock、时间收敛阶、改变 bins、自动翻边区域
合并或 MPI，也没有验证延迟到来的三角形能一直保持有效。

## 6. AREPO 中可复用的部分，以及真正要增加的部分

源码检查支持一个比重写求解器更小的接口方向：现有 RD 残差主要从
`T->DP` 与 `T->DT[].p[]` 读取节点和连通关系；`triangle_get_normals_area`
只依赖三个顶点坐标，不要求读取 Voronoi face 或 circumcenter。
这意味着可以先研究一个 RD 专用的临时 tessellation view，将旧 RD
三角形装入私有 DT，再调用已有的 N/几何/star-bin/累加代码。
这只是源代码层面的可行性判断，不是已编译验证的接口。

| 位置 | 对候选实现的含义 |
|---|---|
| `src/main/run.c:329` mesh rebuild | 原生网格可以照常重建 |
| `src/main/run.c:356` 连续两个 RD stages | 输入应为本轮仍有效的旧 RD 连通关系；MPI 版须保留两阶段间 exchange |
| `src/main/run.c:368` primitive recovery | 完成后才可执行本轮获准的同步换基 |
| `src/hydro/residual_distribution_solver.c:338` star bins | 必须来自实际 RD 三角形集合，不能从提前更新的原生 DT 计算 |
| 同文件 `:1389` element set | 可研究注入私有 DT view，减少改动 N kernel |
| 同文件 `:1540` old triangle record | 当前只有排序 ID 和 area/3，是诊断快照，远不足以作为持久三角形 |
| 同文件 `:2767` moving hierarchy | 尽量沿用 Campoli 几何/残差账本，禁止新三角形回溯出生前区间 |
| `src/mesh/voronoi/voronoi.c:1139` normals | 正定向三角形即可供该几何函数使用；不能据此声称任意畸形网格都稳定 |
| `src/mesh/set_vertex_velocities.c:279` active loop | 现有速度更新主要在节点自身 active 时进行，有利于按区间管理轨迹 |

必要的持久数据至少包括有定向的 vertex IDs、周期 winding、RD 拓扑
版本及区间时间。不能保存跨 `free_mesh()` 的 DT/DP 索引或指针。
当前 DP 中找到所有所需点/周期像时可复用；缺失时必须补充私有点记录，
MPI 下还要显式补旧三角形需要的 halo，不能假定新 Delaunay halo 足够。

本地原型可以先保存完整 RD triangle list，以简化正确性检查；将来再
压缩为“当前原生三角形集合 + 少数 pending cavity”，不是一开始就优化。
这不是重建一个通用网格生成器，但也不是取消一个编译 guard 就能完成。

多个 candidate cavity 必须各自有相同的旧/新边界，并覆盖同一物理区域。
共享受修改节点的 cavity，应合并或明确串行处理，不能独立使用过时状态。
随等待发生的新翻边可能让 cavity 增大；必须记录等待时间和最大区域大小，
不能预先假定代价始终局部。

## 7. 最大的未解决条件：旧 RD 三角形能否等到同步点

刚刚失去 Delaunay 性质不等于面积为零。一个非退化 flip 附近可以继续
短暂使用旧三角形，但不能保证任意长的粗步等待都安全。
规定直线运动时，可写

    A_T(s) = a_T + b_T s + c_T s^2,

在整个等待区间检查端点和区间内的驻点，要求最小 signed area 大于安全
阈值；还需质量/CFL 条件，面积为正只是必要条件之一。
时间步或节点速度改变后要重新建立有效区间，不能用已经失效的预测。

若会在同步前塌缩，不能到那一刻再强制 wakeup 并宣称数学问题解决。
需要提前在合法时间边界缩短相关 bins/限制运动，或者有完整 rollback 与
重新积分。后两项尚未实现。第一版可以使用受控运动、固定 bins、明确
有效性检查并在违反条件时终止；这足以研究局部同步机制，却不是面向
任意强剪切运动的最终解决方案。

另一个差别：当前 equal-step repair 在旧时刻将状态转移到拉回的新连接，
再前进；本文先用旧连接前进再在新时刻转移。二者不保证有限步长结果
完全一致。须独立比较 equal-bin 极限的精度，不能直接继承已有收敛图。

## 8. 面向论文前验证的顺序

1. 人工核对三件事：P 中所有节点同步能否保证相关区间闭合；上述换基
   恒等式；原函数调用顺序能否实现“旧网格结束，再转移”。
2. 单 rank、Campoli + N、规定网格运动、固定 bins，先在隔离 C 副本实现
   一个受控 cavity。验收逐区间 coverage、Q/g/m、非均匀 Euler 总量。
3. 再加入自动完整 cavity 比较与短期延迟，测等待时间/几何质量；通过
   平滑问题后再测间断。精度、正性与守恒分别记录。
4. 接入已有 MPI increment/predictor 交换原型；新增 pending 拓扑唯一
   owner、旧节点 halo 和 migration，比较 1/2/4 ranks。数学定义不变，
   但此前 MPI 一致性结果不能自动覆盖这些新增状态。

初期选 Campoli，是为了隔离已发现的 Arpaia live-storage rebase 缺陷。
不是否定 Arpaia 论文公式，而是不同时调试两个独立的实现问题。
现有 frozen-star mixed-bin 方法已有一阶时间收敛证据；修复守恒不等于
恢复二阶时间精度，本方案不新增二阶声明。

上述是可以逐项人工检查的推进顺序，不是“一周内完成完整算法”的承诺。
若旧三角形有效性或 cavity 管理超出预算，应保留已有可信的 equal-step
结果，并清楚界定 hierarchical 结果的适用范围，而不是以守恒单项通过
替代完整验证。
