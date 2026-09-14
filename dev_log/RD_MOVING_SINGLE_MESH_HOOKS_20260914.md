# RD 共用开始／结束入口：每步一次 moving mesh 构造

2026-09-14，Codex (GPT-6)，按 Zhenyu 的进一步要求完成。

**已移除上一轮的双网格预构造方案。** 用户明确指出，目标只是让主循环形式
符合流程图，不接受额外计算。现在统一外部的 `rd_step_begin()` / `rd_step_end()`
接口，保留各方法原有的实际阶段执行位置；不为方框的名字更改 ALE 数值算法。

## 实现

`src/main/run.c` 两个 RD 入口现在分别调用上述函数，网格的正常 drift、
domain decomposition、`create_mesh()` 位置均保留。

| RD 路径 | `rd_step_begin()` | 正常网格转换后 `rd_step_end()` |
|---|---|---|
| static equal，启用 split | predictor | corrector |
| static hierarchy | predictor | corrector |
| moving equal，启用 step hooks | 仅登记待完成时间区间 | 原有 predictor 和 corrector 连续执行 |
| moving hierarchy | 不执行残差扫描 | 原有两次阶段调用，位置及顺序不变 |
| 未拆分的 equal total-residual 路径 | 不执行残差扫描 | 原有内部阶段循环 |

因此，本次统一的是**步开始／结束接口**，不是声称 moving predictor 已经在
第一个方框内完成。现有 moving ALE 需要新连接关系，两阶段仍共享正常重建后的
同一张网格、同一份元素集合和同一份 ALE 几何。

删除了 `rd_ale_split_predictor()`、预构造时钟推进、P/SphP/DC/RNG 快照回退、
额外邻居树重建、拓扑指纹比较和80字节/节点的预构造缓存。ALE 几何准备恢复成
上一轮预构造之前的实现，代码段与 static-split v2 冻结源码完全相同。

保留原来的 `RD_RK2_SPLIT_STAGES` 开关以兼容现有实验 Config 的名称：
它在 static 时分开两个数值阶段，在 moving equal 时启用开始／结束时间检查。
moving 的第一个入口只做常数级检查和记录一个端点，没有节点循环、MPI collective、
几何计算或残差扫描。DEBUG 模式额外打印两行入口日志。

沿用 binary restart 端点标记，pending checkpoint 在恢复后完成该步；
完整步末 checkpoint 延长 TimeMax 时重建一张起始网格，再开始新步。
这张 restart setup 网格不属于额外的逐步网格构造。

## 原生验证结果

冻结档案：`../local_runs/moving_single_mesh_hooks_20260914_v1`。
10个独立配置、25个 moving 算例、28次启动，**全部完成，14组比较全部通过**。
同方法的 hooks/internal 比较以及三组 restart/extension 比较中，
最终节点状态、坐标、面积和 timebins **完全一致，最大差为0**。
未启用 hooks 的对照也与上一轮 v4 中未拆分的原参考输出完全一致。

覆盖 moving LDA/F1 Gauss3、N、zero mesh velocity、Campoli 及
topology repair + exact-patch diagnostic，短时 t=.125、续算 t=.25 和长时 t=1。
原先失败的三个 t=1 逐点比较本次全部精确一致，没有调整1e-10比较门槛。
三个长时 hooks 算例的全部512行阶段 checksum 也分别与原参考逐行一致。
repair 的 t=1 算例有125/256步发生连接变化，两个版本一致。

沿用2304节点 glass48、周期盒 `[0,10)²`、gamma=1.4、Yee beta=5、
初始中心(5,5)、背景 x 速度1。CFL=.2，实际步长1/256；regularization
参数.5和face-angle1.5，domain fraction=.01，MaxMemSize=512。
moving 为1 MPI rank，两种线程限制均为1。时间直接使用代码物理时间。

状态比较按相同节点 ID，定义 `U=(rho,rho*v_x,rho*v_y,rho*E)`，
E 是单位质量总能量；面积从 Mass/rho 恢复。uniform 最大 U 变化6.22e-15，
保存状态的 rho/p 全部为正。本轮不声称新的收敛阶，也不修复原 ALE 守恒限制；
物理端点守恒统计与原参考完全相同。

## 计算次数核对

分析器不仅比较结果，还检查每个 begin/end 日志区间：

- 恰好1次 `VORONOI: create delaunay mesh`。
- 恰好1次 `RD-ALE-PREP`，即一次 ALE 几何准备。
- 恰好1次 stage-0 和1次 stage-1 checksum，即两次残差扫描。
- 不允许出现旧预构造路径的 `RD-ALE-SPLIT` 日志。

所有启用 hooks 的1216步均通过；整个25例 campaign 共2272个物理步。
普通 t=1 运行共有258次 mesh construction：初始化的2次，加上256步各1次，
与原版相同。pending stop/resume 的32步为34次；完整步续算64步为67次
（初始化2次、恢复起始网格1次、每步1次）；pending extension 为66次。

主要数值工作量已恢复原版；只增加常数级函数分派、端点检查和 DEBUG 日志。
单次 DEBUG t=1 进程计时约4.285/4.317秒（LDA internal/hooks）、
3.761/3.777秒（Campoli）、3.993/3.992秒（repair）。这些不是正式速度基准，
不能分辨微小调用开销和运行噪声；“无重复计算”的证据来自逐步计数和代码路径。

## 回归、源码与复现

另做 static 回归：equal internal/split、1/4 ranks、equal-bin 和 mixed-bin
hierarchy、uniform，共7例；结果见同档案下 `static_regression/summary.json`。
7例均通过，同 rank 及原参考比较完全一致；跨路径最大差1.29e-14。
`make check_rd` 的3组既有代数检查全部通过。

- 基础 commit：`5f3db112c8487ce9f597e4c0f8c5e99c2e04531c`。
- source patch SHA256：`53c74844ed3107a97b7fac665f6ffdde2a5dacdfe0bc1b2f0d5f934666722ea7`。
- source tar SHA256：`cb6dcaefac2d019c3f9c660809c74aba178bc325b0036e6507089a2e5410b212`。
- Config：`examples/yee_2d/Config_RD_ALE_LDA_GAUSS3_EQUAL_SPLIT.sh`。
- runner/analyzer：`tests/rd/check_moving_equal_split_stages.py`。

Config 的 SPLIT 名称是历史名称，其注释已明确说明 moving 的实际语义。
档案保留每种构建的 Config、header、binary hash、linkage、参数、输入、
输出、restart、源码和日志。分析器最终版本以 `.final.py` 另存。
初次分析遇到文件系统以 resumed log 在前返回的问题，按文件名排序恢复
正确时间顺序后通过；原失败分析日志保留，没有重跑计算或放宽检查。

## 流程图

可以保留14个主循环方框和连接，仅将两个 RD 红框改为：

- **Begin RD step**：`rd_step_begin(&Mesh)`。
- **Complete RD step**：`rd_step_end(&Mesh)`。

图注说明 static split 的 predictor/corrector 分别对应这两处，moving ALE
的数值两阶段在新网格上连续完成。网格重建仍在原方框内，只做一次。
用户手动修改的 draw.io、原始图及 thesis chapter 本轮均未改动。
旧双构造实验及失败结果作为历史档案保留，已不在当前执行路径。没有 Git commit。
