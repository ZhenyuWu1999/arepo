# Moving equal-timestep RD：两入口实验及验证边界

> **已撤下的历史实验。** Zhenyu 随后明确拒绝额外网格构造。
> 当前实现已删除预构造，改为一次建网格的开始／结束接口，见
> [RD_MOVING_SINGLE_MESH_HOOKS_20260914.md](RD_MOVING_SINGLE_MESH_HOOKS_20260914.md)。
> 下文保留该轮实现和失败验证的原始记录，不代表当前执行路径。

2026-09-14，Codex (GPT-6)，按 Zhenyu 的要求实现和测试。

已实现可选的 moving equal N/LDA predictor/corrector 两入口路径。
它是一个可运行的工程实验，**尚未通过长时逐点等价门槛，也不是性能优化**。
不替换 default/reference Config，不改变 moving hierarchy 的阶段位置。

## 1. 实现与额外代价

沿用 `RD_RK2_SPLIT_STAGES`。第一入口调用 `rd_ale_split_predictor()`，
其中执行真正的 `compute_residuals(..., RD_RK_STAGE_PREDICTOR)`；
第二入口只执行 `compute_residuals(..., RD_RK_STAGE_CORRECTOR)`。

现有 ALE 数学更新使用终点 Delaunay 连接，并由它回推旧时刻及中点几何。
因此第一入口不能直接拿旧连接代替终点连接。本实验先按已确定的节点时间步
及网格速度预构造终点网格，运行 predictor，再恢复主循环的时间、坐标和
非阶段字段。正常主循环随后推进时间、进行 domain decomposition 和网格重建，
第二入口消费已经保存的 predictor。

这里保存的守恒量是 ALE 中间面积归一化下的阶段量；不是提前完成物理终点更新。
每个节点保存原物理守恒量、旧状态、预测阶段状态、时间质量除数和终点面积。
corrector 重建临时三角形集合，以连接指纹、元素数和逐节点面积检查预构造一致性。
连接指纹是三节点 ID 排序后的组合散列，不是无碰撞的拓扑证明；本实验为周期
48² 网格，未推广到同一组 ID 可对应多个绕周期三角形的极小网格。

预构造还会修改 AREPO 的持久 DC 邻接链和随机数流；二者也完整保存、恢复。
邻居树在预构造中按现有机制延迟 drift，回退后重新建立。禁止直接在这个入口
调用 `do_box_wrapping()`，因为它依赖 domain decomposition 临时创建的迁移表。

新增缓存约每节点80字节，另需临时完整 P/SphP/DC 副本；临时副本使用系统
malloc，未计入 AREPO 自身的内存计数。每步额外构造一次网格并重建一次邻居树。
例如最终 DEBUG Yee t=1 单次完整进程耗时为3.70秒（internal）与5.32秒（split）；
这只是小算例单次计时，不是正式性能基准。拆分入口没有带来加速。

当前范围：二维、非宇宙学、周期、纯气体、单 MPI rank、equal timestep、
source-free N 或标准 GL/F1 LDA。保留原有 ALE 限制，并排除 refinement、
double stencil、gravity、stage-altering diagnostics 等不适用组合。
moving hierarchy、moving MPI、B 和 four-pass Heun 没有因本次工作获得新验证。

## 2. 源码和可复现配置

主改动位于：

- `src/main/run.c`：第一入口包装函数、第二入口 corrector、完整步重启时建初始网格。
- `src/hydro/residual_distribution_solver.c`：终点预构造事务和 ALE 阶段缓存消费。
- `src/main/allvars.h`、`src/main/cpp_functions.h`：节点缓存、拓扑元数据及声明。
- `examples/yee_2d/Config_RD_ALE_LDA_GAUSS3_EQUAL_SPLIT.sh`：明确标记限制的实验 Config。
- `tests/rd/check_moving_equal_split_stages.py`：冻结、构建、25算例及严格比较。
- `tests/rd/check_moving_split_sensitivity.py`：独立的原方法坐标 ULP 扰动诊断。

最终源码档案：
`../local_runs/moving_equal_split_stages_20260914_v4`。

- 基础 commit：`5f3db112c8487ce9f597e4c0f8c5e99c2e04531c`。
- tracked source patch SHA256：`a11c167175a4fd53ba29a2f3c5aac02fcd33705fe41a36ec57265e3f04d5f7fc`。
- source tar SHA256：`433784d67e4a98ce21c386cdd4bbb4566e79d190fa115f20903849752f01275c`。

档案保留独立 Config、generated header、二进制和链接库记录、hash、参数、
初值、日志、restart/checkpoint 和结果。最终 C 源码与该冻结档案相符。
`check_moving_equal_split_stages.final.py` 是完成诊断后的分析器副本；
最初副本也保留。分析器仍对未通过的比较返回非零，不把“程序完成”记作等价通过。

所有 native runs 使用本机 arm64 二进制，
`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`；moving 为1 rank。
主实验25算例、28次进程启动均正常完成，**14组比较中11组通过、3组失败**。
另有2个原方法 ULP 扰动运行和6个 static 回归运行。

## 3. 设置与指标

Yee 与 uniform 使用旧档案同一组 glass48 初值：实际2304节点、周期盒
`[0,10)²`，gamma=1.4。Yee beta=5、背景 x 速度1、初始中心(5,5)，
物理时间直接使用代码时间，没有额外归一化。uniform 初始 rho=p=1。
CFL=.2，最大步1/256，mesh regularization 参数为.5和face-angle1.5，
`ActivePartFracForNewDomainDecomp=.01`，MaxMemSize=512。
短程 t=.125，续算 t=.25，拓扑变化对照 t=1；实际 equal 步长1/256。

定义节点状态 `U=(rho, rho*v_x, rho*v_y, rho*E)`，E 为单位质量总能量。
下表的“最大 U 差”是相同节点 ID 的四分量最大绝对差。
坐标差按相同 ID 比较；位移诊断使用周期最短位移。
守恒统计使用物理端点量 `Q=A*U`，A 从 snapshot 的 Mass/rho 恢复；
质量和两动量变化除以初始总质量，能量变化除以初始总能量，再取最大值。
均匀流误差及守恒分别验证，不与非均匀流准确度合并。

预先设定的等价门槛仍为：
`max_abs_U_difference / max(1,max_abs_reference_U) < 1e-10`，
坐标最大绝对差 `<1e-10`，timebins 完全一致。
没有为了长程结果放宽门槛。

## 4. 通过的结果

| 对照 | 最大 U 差 | 最大坐标差 |
|---|---:|---:|
| moving LDA/F1 Gauss3，t=.125 | 9.77e-15 | 1.80e-15 |
| moving N，t=.125 | 6.22e-15 | 1.78e-15 |
| zero mesh velocity，t=.125 | 0 | 0 |
| Campoli LDA，t=.125 | 5.33e-15 | 1.78e-15 |
| topology repair + exact patch diagnostic，t=.125 | 9.77e-15 | 1.80e-15 |
| moving LDA，t=.25，已有3步连接发生变化 | 2.22e-14 | 6.13e-14 |
| predictor 后 binary stop/resume vs 连续运行 | 0 | 0 |
| 完整步 checkpoint 后延长 TimeMax vs 连续运行 | 0 | 0 |
| pending checkpoint 后延长 TimeMax vs 连续运行 | 0 | 0 |

N/LDA uniform 都保持常状态，最大 U 变化不超过6.22e-15，最大归一化
守恒变化9.95e-16。所有保存状态的 rho 和 p 均为正。各 split run 的
predictor/corrector 数量相等，所有预构造/实际几何检查通过。

static 回归单独冻结在 v3/static_regression：static split/internal、
1/4 ranks、equal-bin hierarchy 和 uniform，共6例全部通过。
同 rank internal/split 及原静态参考结果完全一致；最大跨路径差1.29e-14。
v4 相对 v3 的 C 改动仅为 moving split 宏内的 RNG 保存恢复，静态预处理路径不变。
`make check_rd` 三组既有代数检查通过。

## 5. 长程逐点比较没有通过

| t=1 两入口 vs internal | 最大 U 差 | 最大坐标差 | 有连接变化的步数 |
|---|---:|---:|---:|
| Arpaia LDA/F1 Gauss3 | 9.25e-5 | 3.00e-4 | 131/256 |
| Campoli LDA/F1 Gauss3 | 8.04e-4 | 4.28e-4 | 132/256 |
| Arpaia + topology repair | 1.41e-5 | 3.36e-5 | 125/256 |

最后一列统计存在连接变化的时间步，不是单条边翻转数。
三个 case 的时间步仍完全一致，连接和节点面积的两阶段衔接检查均未失败。
但这些结果不能称作长时逐点等价，因此实验选项尚不作为正式默认实现。

补充诊断使用**未拆分的原版本**，只把 IC 的 x/y 坐标向正方向移动
1或8个 ULP（分别最大1.78e-15、1.42e-14），流体初值保持原值。
它们在 t=1 的最大 U 差也达到3.29e-5和5.86e-5。
这支持“原 moving mesh/state 演化会放大极小差异”的解释，
但不足以严格证明拆分差异全部来自舍入，不能代替上述失败门槛。
此前 moving lab/frame 对照也报告过小解析误差差异但较大的逐 ID 轨迹差异，
见 `colombo_re_spike/lda_moving_baseline.md` 的坐标系回归讨论。

在各自最终移动节点上计算 Yee 解析解，使用最终 RD 面积加权的 L1：

| Arpaia Gauss3，t=1 | density L1 | pressure L1 | velocity-vector L1 |
|---|---:|---:|---:|
| internal | .00106156270547 | .00134954120099 | .00128675311903 |
| split | .00106156270293 | .00134954133589 | .00128676040730 |

整体解析误差非常接近。这不是新空间/时间收敛阶验证，也不证明所有算例可互换。
这里的 L1 为 `sum(A_i*abs(error_i))/sum(A_i)`，速度使用二维误差向量模长。

## 6. 守恒边界

两入口拆分并未修复原 ALE 的端点面积/拓扑守恒问题。
无 topology repair 的 Arpaia t=1 最大采样归一化漂移，internal/split 分别为
3.78991e-5和3.78986e-5；Campoli 也约3.79e-5。
带现有 repair 的 Arpaia 为9.93961e-9和9.93985e-9，仍包含原有 ALE 端点限制。
这些数值是端点物理 Q 的守恒诊断，不是元素内部残差守恒误差。
尤其不能把 static hierarchical conservation 的结论直接移给这个 moving 实验。

## 7. 保留的失败与工程建议

- v1：还原 SphP 后 DC 链仍是预构造的新链，正常 domain decomposition
  报 `q == DC[q].next`。未当成数值格式失败；通过完整 DC 快照修复。
- v2：预构造直接调用依赖失效迁移表的 `do_box_wrapping()`，Bus error。
  改为现有邻居树的延迟 drift，并让正常 domain 路径处理周期包装。
- v3：25例均完成，长程3组逐点门槛失败。v4 补存 RNG 后该差异保持不变，
  因此不能把随机数流说成已确认的原因。v1–v4 档案均保留。
- static runner 初次使用了错误的命令行参数顺序，没有启动计算；已更正。
  `make check_rd` 初次系统 Python 缺 NumPy，失败日志保留，随后指定已配置的
  21cmfast Python 后通过。

目前可以继续用这个显式实验选项研究统一入口，但不建议仅为图形统一而
承担额外网格构造并把它升级为正式路径。后续工程重点应是减少终点几何预构造
和状态回退成本，明确几何准备与两个状态阶段的边界，再决定是否替换原实现。

若图表示本实验，14个外层方框可以保留，但第7框的函数名必须包括
`rd_ale_split_predictor()`，说明它先预构造终点网格；第12框才是单独的 corrector。
不能只删除旧图里的“static”便声称默认 moving/hierarchy 均已统一。
本轮没有改用户手调的 draw.io、原始 PDF 或任何 thesis chapter，也没有提交 Git。
