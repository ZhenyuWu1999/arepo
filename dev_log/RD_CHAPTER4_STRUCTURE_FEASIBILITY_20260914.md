# Chapter 4：流程图、层级时间步与 MPI 图的可行性

日期：2026-09-14。作者：Codex (GPT-6)。范围：Zhenyu 明确列出的第 2–4 项；本条消息的第 1 项未完整显示。本次检查旧文档、log 1/2、当前源代码和已有输出，未改求解器或 thesis，未启动新模拟。

结论：三项都适合 Chapter 4，而且已有材料可以复用。建议以“如何嵌入 AREPO → 如何安排三角形的时间更新 → 如何跨 MPI rank 完成同一次更新 → 数值证据”为顺序。绘图和写作不需要等待大规模代码清理，也不需要先实现另一种 F1 hierarchy。守恒图已有数据；正式效率结论还需要匹配实际步长并重复计时。

## 1. 已核对材料与证据范围

- 原流程图：[Arepo_flowchart.pdf](/Users/zhenyuwu/Desktop/MyThesis/useful_resources/Arepo_document/Arepo_flowchart.pdf)，单页，署名 Zhenyu Wu，2023-03-07。已完整渲染并检查该页；图中已经有两处 FV/RD 分支。
- 同目录 [Arepo_document.md](/Users/zhenyuwu/Desktop/MyThesis/useful_resources/Arepo_document/Arepo_document.md) 为旧调用流程笔记。
- 旧并行图：[task_responsibility_new.png](/Users/zhenyuwu/Desktop/arepo_test/data_analysis/compare_residual_mesh/task_responsibility_new.png)，已查看；对应 [compare_rd_arepo_mesh.ipynb](/Users/zhenyuwu/Desktop/arepo_test/data_analysis/compare_residual_mesh/compare_rd_arepo_mesh.ipynb) 的相关单元已读。绘图程序使用 majority-task 和 ID 集合去重，不能直接作为当前算法说明。
- log 1 提到的 `/home/zwu/MyThesis/useful_resources/MPI_1.png`、`MPI_2.png` 未在本地找到；上面的 notebook/图片提供了可复用的图形风格。
- log 1 的 2026-08-01 “Current RK2 control flow”及 MPI 说明、log 2 §3.2、§7.4、§7.9 已核对。log 2 §7.9 指出早期部分 FV/几何判断来自流程图推断；这次以实际调用点为准。
- 当前规则见 [static baseline](/Users/zhenyuwu/arepo_rd/arepo/dev_log/RD_STATIC_BASELINE_CHAPTER4.md)、[Gauss hierarchy/MPI report](/Users/zhenyuwu/arepo_rd/arepo/dev_log/colombo_re_spike/static_gauss_hierarchy_mpi.md)、[hierarchy design](/Users/zhenyuwu/arepo_rd/arepo/dev_log/RD_hierarchical_timestep_conservation_design.md)、[phase-B prototype](/Users/zhenyuwu/arepo_rd/arepo/dev_log/RD_hierarchical_timestep_phaseb_prototype.md)。

本次查阅的本地 HEAD 为 `5f3db112c8487ce9f597e4c0f8c5e99c2e04531c`，分支 `develop_pureC_RD`。下面重新统计的原生输出来自已冻结的 `943f7ae` 构建：二维、周期边界、静态网格、gamma=1.4、LDA/F1、Gauss3、CREATE_FULL_MESH。当前小规模 MPI 验证覆盖 1/2/4 ranks；CREATE_FULL_MESH 是完整的本地网格加 ghost，并非每个 rank 都复制全局网格。历史 active-only/migration 结果来自其他配置，不能替代当前 Gauss 路径的验证。

## 2. AREPO 流程图：可直接重画，不以大重构为前置条件

保留旧图的整体结构和颜色含义，正文图压缩到约 8–12 个主框，突出初始化、时间步选择、同步点推进、domain/mesh、状态交换、hydrodynamic update、输出。将 RD 内核做成一个局部展开框；详细函数清单留附录。

旧图的两个红色水动力框已经标出 FV/RD，但当前 equal 与 static hierarchy 的阶段位置不同：

| 位置 | 当前 static equal GL/F1 | 当前 static hierarchy | 源码锚点 |
|---|---|---|---|
| 前半段水动力入口 | 此入口为空；不在这里单独执行 predictor | 打开区间、执行 predictor | [run.c:233](/Users/zhenyuwu/arepo_rd/arepo/src/main/run.c:233) |
| 推进同步点及交换状态 | 使用 AREPO 外层同步流程 | 使用 AREPO 外层同步流程 | [run.c:270](/Users/zhenyuwu/arepo_rd/arepo/src/main/run.c:270) |
| 后半段水动力入口 | 一次调用中执行完整 predictor/corrector 两轮 | 执行到期区间的 corrector | [run.c:348](/Users/zhenyuwu/arepo_rd/arepo/src/main/run.c:348) |

因此不要把旧图的两个红框机械标成所有配置统一的“RD stage 1/2”。实验中的 moving-mesh/N hierarchy 又有不同安排，应放在后续工作说明，避免混入本节 static LDA 主线。

RD 展开框可以按实际功能显示：选取负责的三角形与几何 → 读取节点状态 → 计算并分配残差 → F1 时间项 → 将各节点的守恒增量汇总到所属 rank → 恢复 primitive variables。equal 的两轮之间还需要 predictor 状态交换。

“RD 添加的位置”也包括红框以外的两处：

- RD CFL 限制进入原有 timestep 选择：[timestep.c:125](/Users/zhenyuwu/arepo_rd/arepo/src/time_integration/timestep.c:125)。
- RD 用 median-dual 面积恢复密度，见 [update_primitive_variables.c:195](/Users/zhenyuwu/arepo_rd/arepo/src/hydro/update_primitive_variables.c:195)。不能在图中继续把 RD 的节点控制体积一概写成 Voronoi volume。

旧流程图引用 Pakmor et al. (2016) 的式 (21)，其 FV 时间更新与 [Springel (2010)](https://academic.oup.com/mnras/article/401/2/791/1147356) 的原始表述应区分。可在背景中说明 AREPO 的 FV 路径，在 RD 展开框中使用 Chapter 3 的符号；不要直接搬用旧图中含义不同的 Q、W。[Pakmor et al. (2016), §3](https://academic.oup.com/mnras/article/455/1/1134/986779)

代码整理建议：先做调用关系和模块责任说明即可。若以后拆分 `residual_distribution_solver.c`，将几何/ownership、时间调度、单元残差、MPI 汇总作为候选模块；纯整理应保持求值顺序、阶段状态寿命与编译分支，并另做回归。不能仅因静态测试图中没画梯度或网格速度就删除相关调用。

## 3. Hierarchical timestep：几何图、时间图与一份算法

可以借鉴 AREPO 论文 Fig. 17 的时间推进表达方式，但这里不能只把 Voronoi cell 换成 triangle：未知量和原生 timebin 仍属于节点，三角形是残差计算和区间调度的基本单元。[Springel (2010), §7 and Fig. 17](https://academic.oup.com/mnras/article/401/2/791/1147356)

符号先接 Chapter 3：`T` 为 Delaunay 三角形，`|T|` 为面积，`S_i` 为节点 i 的 median-dual 区域，`|S_i|` 为其面积，`U_i` 为保守变量密度向量。若使用 `Q_i`，先定义 `Q_i=|S_i|U_i`，即节点携带的广延守恒量。空间分配残差用小写 `phi_i^T`，包括时间质量项的残差用大写 `Phi_i^T`。

对一个 bin 分配保持不变的区间，定义节点 bin 为 `b_i`，基础时长为 `Delta t_base`，节点步长为 `Delta t_i=2^{b_i} Delta t_base`。三角形使用其三个节点中最细的 bin：

    b_T = min_{i in T} b_i.

再定义节点完整 star 的最细 bin：

    b_i^star = min_{T containing i} b_T.

当前实现中 `b_i^star=b_i` 的节点为 stage-live，其余为 frozen，见 [rd_point_stage_live](/Users/zhenyuwu/arepo_rd/arepo/src/hydro/residual_distribution_solver.c:319)。完整 star 的信息由负责三角形的 ranks 汇总到节点 owner 后交换，不能只看某个 rank 随手持有的 ghost 三角形。

推荐图形：

1. 小网格：约 15–25 个节点，标节点步长，三角形按派生步长着色，用实心/空心或边框区分 live/frozen。
2. 时间轴：画一个完整粗步内的细步，标出三角形区间打开和关闭、predictor/corrector，以及粗节点收到细三角形贡献的时刻。用相对步长 1、2、4 便于阅读；三层只是说明图，不表示当前自然 KH 已验证三层。

配套算法要讲清四件事：三角形什么时候到期；使用什么节点 stage 状态；贡献怎样进入三个节点的守恒量；节点何时刷新 primitive 状态。特别标出 frozen 的是阶段状态策略，粗节点的 `Q_i` 仍会接收细步贡献。

F1 用一个简短说明框交代即可：先定义 predictor 增量 `delta U_i=U_i^*-U_i^n`；当前 frozen 节点向 F1 时间项提供零 predictor 增量，而守恒累积照常进行。这保持相应单元修正的零和，但影响时间质量耦合。异步推进中的不同阶段状态很常见；当前具体的零增量处理则是实现选择。其实际代价用测试量化，不需要把修复 F1 作为本章开写条件。

要区分两种比较：有限步长下不等于 equal-at-finest 是正常可能性；固定网格、固定 2:1 比例并同时缩小步长后仍有差异，则涉及本实现的固定网格极限。已有报告支持后者，正文应诚实说明，而不能只归因于不同调度顺序。是否在目标问题中可接受，应结合误差、稳健性和成本判断。

## 4. 数值图：守恒数据已具备，速度收益需要补公平对照

本次从已有快照重新统计，并保存 [结果清单与快照 SHA256](/Users/zhenyuwu/arepo_rd/local_runs/chapter4_structure_review_20260913/existing_result_inventory_20260914.json)。没有重新运行流体模拟。

### 4.1 KH 守恒历史

已有 smooth KH 四个案例：equal/hierarchy × 1/4 ranks；每个都保存 11 个时刻，从 t=0 到 2。配置为 glass48、gamma=1.4、p=2.5、tanh 宽度 .025、`v_y=.1 sin(4 pi x)`；初态其余定义见基准报告和归档 IC。不同 run 的中间输出时间略有差异，绘图必须使用各快照 Header/Time，不能强制标成完全相同的 0.2 间隔。

由每个快照按 ParticleID 排序后的质量、速度、比内能计算：

    E(t) = sum_i m_i [u_i + (v_x,i^2 + v_y,i^2 + v_z,i^2)/2],
    fractional energy drift = [E(t)-E(0)]/E(0).

这里 `m_i` 是节点携带的质量，`u_i` 是比内能，`v_i` 是速度；不要与 Chapter 3 的质量矩阵 `m_ij^T` 混淆。

| 案例 | 已保存时刻的最大绝对相对能量漂移 | 原始单次 wall time |
|---|---:|---:|
| equal，1 rank | 2.77e-16 | 22.410 s |
| hierarchy，自然 bins，1 rank | 0（本次浮点求和结果） | 22.205 s |
| equal，4 ranks | 1.38e-16 | 9.091 s |
| hierarchy，自然 bins，4 ranks | 1.38e-16 | 7.480 s |

这足以制作当前方法的守恒历史图，结论限于保存时刻的 roundoff 量级。零值不证明所有内部步骤都数学精确为零。可使用带符号线性坐标并标注 1e-16 的尺度，避免为了对数轴给零值添加人为正数。若曲线重叠，可用不同 marker 或上下小面板。

可借鉴 [Morton et al. (2023), Fig. 6 and §5.2.1](https://academic.oup.com/mnras/article/518/3/4401/6847219) 的 KH 能量误差展示思路，但当前初态/网格并非其原始实验；不能把两者无条件叠加后宣称同条件性能改善。若要直接量化相对旧非守恒 hierarchy 的改进，需要匹配设置的旧算法对照；当前已有结果已经足以独立展示本方法守恒。

建议守恒图附一条真实 bins 分布或活跃工作量历史，证明测试期间确实存在多层步长。当前自然 KH 只出现两层、最大步长比 2，应按这个范围描述。

### 4.2 运行时间与误差

上表时间来自原有单次串行启动脚本；不是重复、受控的性能实验。1 rank 的原始耗时几乎一致，不能预设 hierarchy 一定明显加速。4 ranks 的差异也需要重复验证；MPI 强缩放与层级步长的收益是两个不同问题。

尤其要修正现有 Yee 对照的命名印象：同一 MaxSizeTimestep 下，强制两层模式会把一部分节点的候选步长再减半。因此现有 equal 不是“全部采用 hierarchy 最小 bin”的对照。

| Yee t=1，4 ranks | equal 实际步长 | hierarchy 最细步长 | equal/hierarchy 同步事件数 |
|---|---:|---:|---:|
| 48² | 1/256 | 1/512 | 256 / 512 |
| 96² | 1/512 | 1/1024 | 512 / 1024 |
| 192² | 1/1024 | 1/2048 | 1024 / 2048 |

以上步长通过已有 run.log 的同步点和总事件数核对；日志的小数打印有舍入。强制模式的实现见 [timestep.c:209](/Users/zhenyuwu/arepo_rd/arepo/src/time_integration/timestep.c:209)。这些算例仍可用于所给参数下的误差比较，不能直接用于 equal-at-finest 的加速比。

最小补充计划：

- 固定 2:1 分布，与相同网格、相同最细步长的 equal 配对；同时报告实际 bin 占比和细/粗工作量。另用自然 CFL bins 检验实际使用情况。
- 优先用有解析解的 Yee 做“误差–运行时间”图，KH 做守恒和流动表现。KH 可以测成本，但不应单凭守恒把它作为精度等价证明。
- 固定硬件和 rank 数，统一 I/O 与诊断开关；成对交错重复至少 3–5 次，报告中位数及散布。短于一秒的 sharp KH 档案不适合主性能图。
- 同时给完整 wall time、hydro time 和三角形残差计算次数。工作计数应核对是否包含两阶段、完整 star 扫描及通信，不能把打印的 `elements=` 未经检查就当作累计总成本。
- 保留一个固定网格 2:1 的步长细化图，展示 hierarchy 与 equal-at-finest 的差异。它解释 F1 选择；Yee 的空间误差和成本图评估实用影响，二者不能互相替代。

本次审查不支持“Yee 空间误差主要被时间误差污染”的新增断言。以前 Roe/F1 的减半步长实验与用户记忆一致，影响较小；最新 Gauss 的匹配检查应单独给出。

## 5. MPI 责任图：复用配色风格，更新 ownership 规则

建议用三个面板，保持图例含义固定：节点颜色表示存储该节点主副本的 rank；三角形底色表示计算该三角形残差的 rank；实心/空心表示 primary/ghost。时间 bin 不再复用同一套 rank 颜色。

1. 全局小网格：给边界节点标 ID，按当前规则给三角形着色。
2. 单个 rank 视图：显示 primary、ghost 和必要的周期像，突出只能由选定 primary 所在实例认领三角形。
3. 通信箭头：节点 owner 发送状态和时间信息，三角形 owner 计算后把守恒增量送回对应节点 owner；另用小箭头说明 full-star 最细 bin 的汇总。

当前完整/持久静态网格的规则是：取三角形所有顶点中最小的 `(particle ID, task)`，该顶点主副本所在 rank 负责计算，而且只认领包含该 primary 的三角形实例。它与哪个节点当前活跃分开判断，见 [rd_simplex_claimed](/Users/zhenyuwu/arepo_rd/arepo/src/hydro/residual_distribution_solver.c:1316)。这与旧图的 majority-task 规则不同，也不是最小 rank 规则。

一个很有解释力的边界例子：最小 ID 顶点在红色 rank 且用粗步，另外两个顶点在绿色 rank 且用细步。三角形仍由红色 rank 负责，在其细步区间到期时执行，再把绿色节点的贡献返回绿色 rank。用这个例子同时解释“谁负责”与“何时计算”。

active-only 静网格重建存在另一条分支：只在三角形最细 bin 顶点中选择最小 key，以保证到期时对应 primary 的 star 被构建。当前 Gauss 主配置有 CREATE_FULL_MESH，不走这一条；可以在附录说明条件，不能把它写成所有配置的统一规则。周期去重也不能退回单纯排序 ID 三元组，因为周期像需要按物理实例处理。

证据建议附小表即可：当前 1/2/4 ranks 的对应验证，以及 1/4 ranks 按 ID 对齐后的状态差异（当前扩展基准最大约 3.96e-14，含 KH t=2）。这是正确性证据；大规模 scaling、当前 Gauss active-only 和迁移仍需各自测试。旧 log 1 有非 Gauss 配置的 active-only/重复 migration 验证，应保留其历史配置标签。

## 6. 建议的成稿顺序

先完成三张方法图：整体流程图、层级时间步的几何/时间图、MPI 责任/通信图。随后使用已有 KH 快照绘制守恒历史，再补匹配步长的 Yee 误差–成本对照及受控重复计时。F1 的固定网格差异用一张紧凑的测试图或局限性小节说明即可。

这种顺序能先写出结构稳定的方法部分，并让后续实验分别回答守恒、精度与效率问题。当前未进行 thesis 编辑、C 代码清理、新构建或新的 native run。
