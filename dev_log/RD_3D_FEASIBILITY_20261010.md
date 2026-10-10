# 3D RD 纳入当前研发的可行性研究

- 作者：Codex，2026-10-10，为 Zhenyu Wu。
- 用户决定：关闭 lazy，作为当前 baseline；现在研究把初步 3D 测试纳入开发，避免在 2D 完善后才发现三维架构问题。
- AREPO：`feature/ale-flip-conservation-hierarchy`，代码 HEAD `7c2d949`；已有未提交审核记录保留。
- Standalone：`/Users/zhenyuwu/rdsolver`，`dev`，`adfbe55586fc926f1911dbecfbdb915c8f667c11`，原目录保持干净。
- 本轮完成源码对照、明确的无 lazy 配置、隔离编译/小型 standalone 运行及独立 3D 代数探针。未实现 AREPO 3D RD，未改 thesis。

## 1. 结论与 baseline

**可行，而且应当现在开始纳入小规模三维验证。** AREPO 已具备三维 Delaunay 网格；standalone 已有四面体上的 Euler N/LDA/B 运算。无需从零编写四面体剖分器，但整个 moving RD 也不能通过复制旧 C++ 类或去掉 `TWODIMS` guard 获得。

首个 AREPO 3D 目标建议是：单 rank、周期、固定粒子数、全局等步长、无 gravity/refinement、无 lazy。先打通固定网格 N 的状态/几何接口，同时提前验证移动四面体的几何积分与重连 transfer；随后做真正的 moving 3D 均匀流和斜向平流。不要等完整 2D 精度/性能扫描结束才做这些工作，也不要把 3D hierarchy/MPI 全部完成当作首次测试的前提。

当前二维 baseline 已具体化为 `examples/rd_moving_baseline/` 的八份 Config：

- N/LDA/B/HLLC，各有 equal-step 与 natural interval hierarchy 两种。
- Campoli；显式 `RD_FLIP_HIGH_MODE=1`；floor fraction .5；hull/entropy bound off。
- 全部关闭 lazy；natural 配置的 frozen CFL ledger limit=1。
- equal-step 是基本参照；natural hierarchy 是另外一条需要验证的组合，不把时间分层默认等同于基本参照。
- 八份配置互异且通过现有配置检查。尚未用它们重跑完整 native gates。
- 历史 frozen runs 与历史 mode-0 campaign 定义保留，不能将过去的 lazy 结果改称无 lazy。

## 2. 已经存在的代码与可复用边界

| 部分 | 查到的实现 | 移植判断 |
|---|---|---|
| AREPO 3D 网格 | `src/mesh/voronoi/voronoi.h:144` 的 `tetra.p[DIMS+1]`；`voronoi_3d.c` 的 2→3、3→2、4→4 等操作 | 直接使用 AREPO 的 DP/DT、周期像和网格生命周期，不引入另一套 CGAL 主循环。 |
| 单纯形唯一 ownership | `residual_distribution_solver.c:1610`，已遍历 `DIMS+1` | 有可复用基础；三维周期重复/幽灵副本与 deleted tetra 仍须独立验证，不能把二维 MPI 结果当作三维验证。 |
| Standalone 空间 RD | `rd/triangle3D.h`：4 顶点、5 守恒量、5×5 特征矩阵，N/LDA/B 与 F1 相关运算 | 可作公式/局部 kernel 参照；不是可直接采用的完整时间推进器。 |
| Standalone 几何 | `triangle3D.h:934` 起：四面体面法向和 `VOLUME/4` | 复用数学定义，重写为独立 C geometry helper；需 signed volume、稳健法向、周期展开。旧实现用 `abs(volume)`，不足以检测运动过程中的倒置。 |
| 当前 AREPO 状态 | `allvars.h:1368`、`mesh.h:127`、`voronoi_exchange.c:296,415`，RD predictor 数组固定 `[4]` | 扩为维度相关的状态/通信布局；三维 z 动量必须参与整个更新、能量、正性与诊断。 |
| 当前 AREPO 残差 | `residual_distribution_solver.c:187` 明确拒绝非 TWODIMS；几何构建在 1726 行仍只调用二维 helper | 实质改造，不能只移除 guard。 |
| 保守 transfer | `src/hydro/rd_flip_transfer.h` 的 donor/receiver 权重与 convex blend | 代数原则可推广；当前 C 实现及 `rd_rusanov_internal` 都固定四分量，需要独立推广和测试。 |
| interval hierarchy | 当前 registry、birth/start clocks、完整 star closure | 生命周期思路可沿用，但三维几何时间积分、quadruple key、周期像和通信需重做验证。第一版 native 3D 不启用。 |
| HLLC-RD | `rd_hllc.h` 当前是三角形 median-dual 和单个切向速度 | 需要三维 median-dual 面向量及两个切向自由度/向量形式；不是现成 AREPO FV HLLC 的直接开关。适合作为后续强激波路径。 |

容易忽略的接口陷阱：AREPO 的 `voronoi_3d.c:3773` 函数 `calculate_tetra_volume` 实际返回有符号 determinant，即 **6V**，没有除以 6；用于 RD lumped volume 时必须明确单位。`triangle_normals` 目前是 `normal[3][2]`、`mag[3]`，也不能装四面体几何。

## 3. 本轮实际做过的检查

证据根目录：`../local_runs/rd_3d_feasibility_20261010_v1/`。

### 3.1 Standalone 隔离编译与小型静态运行

从 clean commit `adfbe55` 用 `git archive` 冻结源码，在独立 source/build/run 目录编译，Homebrew OpenBLAS/OpenMP，`OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=1`，编译并行 2。保存源文件、配置、binary、mesh 哈希和 linkage。仅修改冻结副本的 case 配置：GAUSS3D、关闭 DRIFT、whole-mesh stepping、t=.05、四个输出间隔。

实际输入为周期 8³ 规则点，共 **512 vertices / 3072 tetrahedra**，每个 cube 用六个 Freudenthal tetrahedra 划分。构建和运行均完成，末时间 .05；五个保存的快照全部有限，rho/p 为正。

原生总量日志（12 位精度）首末 mass/energy 数值相同；不能据此声称已测得机器精度守恒。快照输出精度更低，不能用其舍入后的 dual volume 和来判定真实体积覆盖精度。

**证据的边界：** `setup3D.cpp:136` 的 GAUSS3D 实际使用 `S=abs(.5−X)`，所以是三维网格上的一维脉冲；y/z 速度为 1e-8。没有测试斜向传播、三维涡旋、移动网格或重连。旧 code 的 clipping 保留，不能据“输出为正”宣称有正性保证。当前 standalone README 还记录了粗规则网格 3D Sedov 的 NaN 失败；本轮没有重跑该强激波案例。

### 3.2 旧 kernel 的零速度负探针

用同一冻结源码直接调用真实 `TRIANGLE::calculate_first_half`：一个非退化四面体，均匀 rho=p=1，三速度严格为零。得到 `MATRIX CANNOT BE INVERTED`，没有到达完成标记；旧程序通过 `exit(0)` 返回了 0。

因此旧 3D solver **不能作为零速度、低 Mach 或网格随流运动情形的未经审查的数值基准**。`rd/inverse.cpp:10–26` 的 LU+显式逆需要换成当前 AREPO 那类带 rank/兼容性诊断的 LU/SVD 求解，而不是添加微小速度或掩盖失败。AREPO 当前求解器 `rd_solve_upwind_system` 也要从 4×4 推广为 5×5。

此外，源码中的 `vertex3D.h:248–285` 会直接裁剪守恒密度/总能量；pressure 也有 floor。移植时不能带入这些不保守裁剪。`main3D.cpp:266–270` 的 timestep 循环每个顶点都会重置 `NEXT_DT`，没有实现整组顶点的持续 minimum reduction，也应沿用 AREPO 的时间步组织而非复制这个 main loop。

### 3.3 三维运动几何代数

对 1000 个正体积四面体及小幅线性顶点运动，独立计算面法向、体积变化和面速度积分：

| 检查 | 最大归一化缺陷 |
|---|---:|
| 面法向闭合 | 5.44e-16 |
| 线性函数几何恒等式 | 2.89e-15 |
| 两点 Gauss 的体积变化/GCL 恒等式 | 1.13e-15 |
| 同一区间分成三段后积分的可加性 | 1.35e-16 |
| 直接中点积分的体积变化缺陷 | 2.85e-3 |

一个无需随机数的例子：初始单位轴四面体，`x_i(t)=(1+t)x_i(0)`、t∈[0,1]。

```text
V(t)=(1+t)^3/6
V(1)−V(0)=7/6
midpoint integral of V'(t)=9/8
two half-interval midpoint integrals=1.15625
two-point Gauss integral=7/6 (up to rounding)
```

所以 3D 中“时间二阶”与“几何上精确守恒”不同。两点 Gauss/Simpson 对这种几何多项式足够；也可构造与精确端点体积差一致的等价离散几何。必须把法向、mesh transport、几何 ledger、Campoli/F1 时间项一起核对，不能仅在一个积分函数里加 Gauss 点就宣布完整 ALE RK2 得到验证。

### 3.4 五分量 transfer 的三维局部重连

独立 NumPy 模型，对一个凸三角双锥的 2↔3 四面体剖分做 500 组随机仿射几何，每组测试双方向、mode 0/1：共 **2000 个随机状态 transfer 案例**，另检查同样几何上的均匀态与仿射态。

- 质量使用 tetra volume/4，加正的 cavity 外 star volume；动量含完整 x/y/z，内能扣除三分量动能。
- 同 cavity 体积/一阶矩匹配缺陷 ≤7.41e-16/4.03e-16。
- 转移后全五分量守恒缺陷 ≤9.46e-16；所有随机案例保持正性，mode 1 donor 逐位不变。
- 1444 案例触发 limiting；均匀/仿射状态的最大变化 3.56e-15/5.33e-15。

这支持 transfer 代数推广；**不是 production C kernel 测试，更不是 AREPO 3D moving solver 验证**。还缺 4↔4、实际 Delaunay 变化的较大 cavity、周期像和三维 mesh lifecycle。

## 4. 必须现在考虑的设计改变

1. **把空间维数、顶点数、守恒量数分开。** 建议明确 `RD_NDIM`、`RD_NVERT=RD_NDIM+1`、`RD_NVAR=RD_NDIM+2` 和 energy index。现有常量 4 既可能是二维守恒量数，也可能成为三维顶点数，不能全局替换。独立 kernel 与 AREPO state adapter 分离；保持二维数值回归。
2. **明确几何量的定义。** 面面积向量、signed volume、真实几何体积与时间离散所用 mass weight 分开保存。`V/4` 的 lumped mass 与 `A_i/3` 的梯度/特征矩阵几何因子是不同系数，不能统一用一个“除以顶点数”。
3. **三维面与时间积分。** 二维边上的 Gauss3/5 不能原样成为三维三角形面 quadrature；三维 mesh velocity 通量与相邻面方向必须一致。几何时间积分先通过 GCL 与任意区间拆分测试，再进入非线性流体更新。
4. **重连按 cavity 处理。** 使用旧/新 tetra 的差集和 cavity 守恒体积/一阶矩验证，不依赖单一 2→3 模式。AREPO 建网格时的临时 1→4 插入操作不等于物理粒子 refinement；第一版固定粒子集合，比较完整旧/新剖分。
5. **周期像进入持久几何约定。** 四 ID key 在小、唯一展开的 simplex 条件下可工作，但不能无条件忽略 winding。保留 CCW/正 orientation 与相对 image offsets，检查每个 simplex 只计一次；存实际网格用于分析。
6. **三维退化与运动倒置。** 面积不小但体积很小的四面体仍可能存在；需要 volume/face/CFL 质量指标。线性轨迹下 signed volume 是 cubic，区间最小值要检查端点和导数二次式的区间实根。只查 old/mid/new 不足够。关闭 lazy 不会自动消除这些问题。
7. **复用稳健求解，不复用旧主循环。** 迁移五分量特征分解时做旋转协变、`K+ + K− = K`、常量残差、零速度 singular compatibility 等测试。保留 AREPO 的 timestep、状态刷新和更新账本；避免旧 clipping 与失效时返回 0。

## 5. 最小推进路线与通过条件

以下是下一步实施顺序；表中“native”尚未执行。它把 3D 的关键风险提前，同时不要求一次移植所有模式。

| 阶段 | 具体交付与规模 | 需要证明的事 |
|---|---|---|
| P0：几何/代数接口 | 本轮独立探针已有；下一步从 AREPO 真实 8³、16³ 周期网格提取 owned tetra，做只读 adapter/诊断 | 唯一 ownership、体积覆盖、法向/线性精确性、周期展开；用真实 old/new 网格验证 cavity，而非只用制造例。 |
| P1：native 静态 3D | 单 rank，全局等步长，先 N/lumped；均匀静止和非零三分量速度，斜向平滑密度平流；8³→16³ | 完整五分量更新和 Q 总量、零速度稳健性、实际末时刻、无隐藏 floor；斜向测试必须依赖 x/y/z。保留同分辨率 timestep sensitivity。 |
| P2：早期 moving gate | 在优化 2D 精度前进入：规定的网格平移/形变均匀态、无重连与有重连；关闭 lazy | 三维 DGCL、静网格退化、重连前后守恒；明确记录 tetra/cavity 数；没有实际重连的算例不能算 remap gate。 |
| P3：moving 流动 | N + mode1 transfer 的三维斜向平流；再 LDA/B 精度，Sod 沿不同轴/斜向 | 控制 transfer 与运动几何影响，真正三维误差与守恒；不能仅复制 GAUSS3D 的 x-only 初值。 |
| P4：扩展物理与调度 | HLLC/Rusanov 对照及弱/强 3D Sedov；之后 interval hierarchy、1/2/4 rank 比较 | 激波正性与精度另验；hierarchy 做不同区间 face cancellation/完整 star 闭合；MPI 做 ownership/migration，再讨论性能。 |

建议首轮明确门槛：固定/规定运动均匀态缺陷约 1e-12 内；有限正体积覆盖与守恒用以总质量/总能量、绝对动量和为尺度的约 1e-12 门槛起步，并报告实际数值与步数。不要用接近零的净动量作分母。完整物理流动还需自己的精度/正性判据，不能只凭守恒通过。

工作量判断：静态单 rank N 的端到端接入是可切分的中等规模改造；完整三维 moving + hierarchy + MPI 是明显更大的任务。最大风险是几何/时间积分一致性、退化几何与状态/ownership 生命周期，并非简单的 5×5 算术成本。现在先做 P0–P2，正好能在广泛二维扫描前发现这些风险。

## 6. 复现与限制

证据文件：

- `run_standalone_probe.py`、`standalone_base.tar`、`standalone_provenance.json`、`standalone_results.json`：冻结、配置差别、命令和逐文件哈希。
- `configure.log`、`build.log`、`linkage.txt`、`gauss_run.log`：真实 standalone 编译/运行。
- `zero_velocity.cpp`、`zero_build.log`、`zero_run.log`：调用旧 kernel 的零速度失败探针，失败如实保留。
- `probe_algebra.py`、`algebra_results.json`：三维 GCL/区间可加性、制造 cavity 上五分量 transfer 的独立模型。
- `baseline_configs.json`：八份新二维无 lazy baseline Config 的哈希。

本轮没有新的 AREPO 3D binary/水动力运行，没有宣称 native moving 3D 已完成。已有 2D 代码和历史结果保留；新 baseline 配置和本文是当前交接依据。

## 7. 进入 3D 前的文件组织建议（尚未实施）

用户要求先提交本地 AREPO 改动，保持干净工作区，再开始 3D。当前
`src/hydro/residual_distribution_solver.c` 已有 8286 行。建议按职责渐进拆分，
2D/3D 共用接口，只在确有维数差异的 kernel 内分支；不复制整份 solver。

| 文件/模块 | 职责与边界 |
|---|---|
| `src/hydro/residual_distribution_solver.c` | 保留 AREPO 入口、推进阶段、粒子状态更新和通信调度；逐步移出纯数值与几何运算。 |
| 建议新增 `src/hydro/rd_euler.c/.h` | Euler 状态、通量、特征矩阵与局部线性求解，用明确的 NDIM/NVERT/NVAR 和 energy index。若矩阵求解被多个 kernel 复用，再独立为 `rd_linalg.c/.h`，无需先拆成大量小文件。 |
| 建议新增 `src/mesh/rd_simplex_geometry.c/.h`，配合现有 `rd_ale_geometry.c/.h` | 前者处理 triangle/tetra 的有向测度、面法向和梯度等空间几何；后者处理线性轨迹、时间积分和 GCL。几何接口不依赖流体状态。 |
| 现有 `src/hydro/rd_flip_transfer.h`；后续按需要抽取 topology/interval 模块 | transfer 保持可独立测试的纯代数接口，并推广到五分量；旧/新 simplex registry、cavity 构建、周期像与 hierarchy 生命周期属于 AREPO 接入逻辑，不混入 transfer 代数。 |

第一步只抽取原有二维几何/Euler kernel，保持公式、求和顺序和更新路径，先通过已有
代数与相关 native 2D 回归；之后接入 tetra 几何和五分量 N。每次提取与新增 3D
行为分开提交，方便区分结构改动与数值改变。初期不要求同时抽取全部 hierarchy，
也不另建各自演化的完整 `solver_2d.c` / `solver_3d.c`。现有 ownership、状态数组
和 predictor 通信仍需逐项适配；文件拆分本身不解决这些维数依赖。
