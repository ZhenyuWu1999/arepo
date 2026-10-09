# Claude flip / moving hierarchy 工作独立审核

作者：Codex（GPT-6），为 Zhenyu Wu。日期：2026-10-09。

审核范围：`feature/ale-flip-conservation-hierarchy`，`eacc3f9..9672ad7`；
重点为 `src/hydro/rd_flip_transfer.h`、`residual_distribution_solver.c` 的新路径、
冻结 gate 与 [Claude 报告](RD_FLIP_HIERARCHY_REPORT_20261009.md)。开始时工作树干净。
用户已提交 thesis，要求先审核 Claude 的工作；本轮没有改动求解器或 thesis。

## 1. 审核结论

**这是有可复现证据的实质进展。Campoli 配对、局部 conservative flip transfer、
实际区间闭合三者构成的守恒主路径，在已测试的 2D、周期边界、单 rank 范围内成立。**
没有发现足以否定该主路径的代码错误或守恒反例。旧 primitive refresh bug 的修复正确。
receiver-only 高阶端作为研究默认值有合理依据。

这还不是完整、通用、保证精度与正性的 moving-mesh RD：LDA–KH 的失败、
分层接口的精度损失、MPI/restart 缺失、极端几何时中止，以及最终组合的验证覆盖均须保留。
尤其不要把「精确守恒」「正性条件」「轨迹差异」「空间收敛阶」合并成一个通过结论。

本次发现两项工程问题和两项科学表述/指标问题，详见下文；均为 P2。
未修改 Claude 原报告，以保留原作者记录。本审核中的更正应与原报告一起阅读。

## 2. 需要处理的发现

### R1 / P2：默认改为 mode 1 后，模式比较脚本退化为同一方法的重复运行

位置：`tests/rd/run_lazy_flip_gates.py:35–42`；同类问题也出现在
`run_flip_gates.py`、`examples/gresho_2d/run_kh_flip_resolution.py` 的隐式 mode-0 标签。

`N_plain` 不写 `RD_FLIP_HIGH_MODE`，`N_plain_h1` 写 `=1`；`N_lazy` 与
`N_lazy_h1` 同理。当前求解器的默认已是 1。因此在当前 HEAD 重新 prepare，
两对配置的有效宏集合分别完全相同。独立脚本已重现这两个相等关系。

此前冻结档案有自己的旧源码，使用默认 0，**其历史数值结果没有因此失效**。
问题是原报告 §11 的当前脚本复现命令会悄悄改变实验定义，无法重现所声称的 0/1 对照。

建议：实验矩阵为两个端点都显式写入 `RD_FLIP_HIGH_MODE=0/1`；在 campaign 元数据中
记录有效 mode，并断言对照配置确实不同。默认策略与实验标签应独立。

### R2 / P2：冻结顶点的 CFL ledger 超限仅计数，尚未形成执行约束

位置：`src/hydro/residual_distribution_solver.c:4277–4280`。

`ratio = RD_CFLLedger / DualArea` 超过 1 时只增加 `n_cfl_ledger_over`，随后
立即将 ledger 清零。代码会拒绝已经不可容许的刷新态，但不会拒绝仍为正、已经超出
凸组合充分条件的刷新态，也没有缩短时间步/重试/唤醒逻辑。

这是有条件正性论证与运行机制之间的缺口。对被强制刷新的 inactive 顶点继续保留
原 timebin/VelVertex，与区间几何一致；但新热态可能需要更短时间步，不能仅从
自然 bin 来推定 ledger 条件必然成立。

现有数据未触发该问题：本次核查的冻结 runs 均 `cfl_ledger_over=0`；
HLLC natural 最大约 0.108，lazy 最大约 0.129。因此本发现**不推翻现有 Sedov 正性结果**，
也不是已复现的负压失败。

建议：研究 gate 至少将冻结顶点的非有限 ratio 或 ratio>1 设为硬失败，并增加
受控超限测试；如要自动完成强激波计算，再设计有明确守恒语义的提前闭合或步长重试。
报告应区分「记录并检查最终正性」与「执行 CFL 充分条件」。

### R3 / P2：Arpaia 守恒缺陷推导漏了步初质量重设

位置：原报告 §3.1，尤其 `RD_FLIP_HIERARCHY_REPORT_20261009.md:99`。

「update conserves ΣD U^{n+1}」和仅用 `Σ(S^{n+1}−D)U^{n+1}` 表示完整
物理守恒缺陷不成立。后者只是末端 rebase；`rd_ale_prepare_step` 还会在
步初将 `S^n U^n` 重设为 `D U^n`。必须计入两端和 RK 残差的整体平衡。

固定连接、无源、共同时间区间内，令 `ΔS=S^{n+1}−S^n`，`δU=U*−U^n`。
利用 residual 的列和恒等式及 `D−M=ΔS/2`，两遍更新给出（逐守恒分量）：

\[
 \sum_i D_i U_i^{n+1}
 =\sum_i(D_i-\Delta S_i)U_i^n.
\]

记 `ε_i=S_i^{n+1}−D_i`，实际端点缺陷为

\[
 \boxed{\sum_i S_i^{n+1}U_i^{n+1}-\sum_i S_i^nU_i^n
       =\sum_i\epsilon_i(U_i^{n+1}-U_i^n).}
\]

Campoli 的 ε=0，因此正确的守恒结论仍成立。Arpaia 有
`ε_i=Σ_{T∋i} c₂,T/12`；在光滑时间演化下 ε=O(Δt²)、状态增量 O(Δt)，
故此项每步是 O(Δt³)，不能从单独的末端 rebase 推断其阶数。

独立三节点代数检查同时满足 residual 列和与均匀态恒等式：实际端点变化
`−0.0013224918523953022`，上述完整公式 `−0.0013224918523953154`；
仅末端转换给出 `−0.016322491852395316`。这是平衡恒等式测试，不是新的 Euler native gate。

原报告的质量权重表、`D−M` 恒等式、改用 Campoli 的方向正确。
「Sedov 中 conversion 很小」应由相应直接预算或匹配控制限定，不能表述成所有
非均匀形变必然有非零缺陷；存在 c₂=0 或加权抵消等情形。

### R4 / P2：按粒子 ID 的差包含坐标变化，不能直接当作共同空间上的 L1 场差

位置：`tests/rd/analyze_flip_gates.py:105–109`；分层分析脚本有相同计算。

脚本确认 ID 相同后直接算 `Σw |ρ_A(ID)−ρ_B(ID)|`，没有使 `x_A` 与 `x_B`
相同。流体解改变网格速度，故相同 ID 的末坐标不同。这是有意义的节点轨迹比较，
但不是 Eulerian 场差，也不能单独验证 flip 算子的空间收敛阶。

独立重算 Yee、t=1、glass48 的 N mode 1：

- 同 ID 密度差：`1.3708703375e−4`；
- 平均坐标位移：`5.5834464980e−4`（box=10）；
- **仅将解析解分别采样到两套坐标**，其密度差已有 `4.4389194315e−5`，
  约为报告指标的 32%。这些绝对值不能线性相减来作误差分解。

各运行在自己末坐标上对解析 Yee 解求面积加权 L1 的计算是正确的，应继续保留。
48→96 的节点差比值 2.5–3.8 是支持性的两分辨率证据，但不是严格二阶收敛验证。
建议将当前指标改称 matched-ID difference；另在共同空间重建场，增加第三个分辨率
和时间步控制。KH 的 16×16 mass-weighted 网格距离也只能说明该粗尺度上的敏感性；
48/96 之间的距离不是已知真解误差，不能据此建立严格误差上界。

## 3. 数学与实现核查中支持的部分

### Flip 内核

两种高阶端的守恒、仿射精确性和 mode 0 的加权 L2 / max-norm 最小性成立。
正性低阶端对 receiver 是旧状态的凸组合，donor 状态保持不变；同一 cavity 的
所有节点和守恒分量共用 θ，所以 high/low 混合继续守恒。
只有 mode 0 的高阶端有已检验的固定几何可逆性；不要把该性质推广到 mode 1。

receiver-only 对 KH 的改善有数据支持，但「不需要 limiting」限于相应 KH runs；
Sedov 明确会触发 limiter。它不是普遍 entropy bound。

补充数值精度限定：production-default 随机探针中的 9,654 个有效凸四边形均保持
正密度/正内能，最大相对守恒误差 `9.04e−16`，6,591 次 θ<1。
但 strict NumPy 内能 floor 对照在 416 例中略低于 `0.5 min(e_input)`，
最大绝对差 `1.82e−12`、最大 deficit/能量尺度 `4.60e−16`，符合不同浮点
求值次序的舍入尺度。原严格断言的失败样本已保留；未将这一项宣称为严格 floor gate 通过。
461 例在混合后 donor 发生 ulp 级变化：`(1−θ)u+θu` 不保证逐位等于 u。
因此「donor bit-for-bit」只适用于当前端点构造；若最终输出也需要此保证，应对
相等端点直接复制。上述探针没有出现不可容许输出。

### 实际区间的守恒与 frame

可以补全原报告 §9.1 要求的核心论证。设三角形 T 在区间 h 内节点线性运动，
`A'_mid h=ΔA`；空间离散的 element total 可写成

\[
 \Phi_T(U)=\mathcal B_T(U)+\frac{A'_{mid}}3\sum_{i\in T}U_i,
\]

其中 `B_T` 是三角形边界的 ALE 通量：physical flux 使用所选相同边 quadrature，
mesh 部分精确积分 P1 的 U 与线性 mesh velocity 的乘积。
element-mean mesh velocity 形式与此表达通过 P1 几何恒等式一致。

集中式更新的几何贡献是
`ΔA/3 ΣU^0 + ΔA/6 ΣδU = ΔA/6 Σ(U^0+U*)`，恰好抵消
两阶段 `h/2(Φ^0+Φ*)` 的体积项，留下 `−h/2(B^0+B*)`。
LDA/F1 与 B 的额外分配在 element 内列和为零，不改变这一总量平衡。

共享边若两侧区间不同，两个端点被冻结。端点状态和其 mesh velocity 在被跨越的
区间内保持一致，边法向随时间线性变化，因此 midpoint 时间积分在粗/细划分两侧
相加一致。若端点 live，其完整星形同起点、同终点，两侧阶段状态相同。
闭合整颗星形后才刷新，以及在顶点重新赋 mesh velocity 之前闭合相关区间，
正是此论证成立的条件。frame map 是线性的，两个 sweep 使用相同 mesh-mean frame，
变回 lab 后保留上述总量恒等式。

代码的 B stage-0 数组保存、corrector 减去已沉积 blend、重新构造 F1 target，
与该代数一致。没有发现 B 两次调用之间的 frame 错配。

### 冻结顶点正性的充分条件

对两次 refresh 之间一直冻结的节点，U_i^0 不变；其所有几何沉积相加后，
HLLC/Rusanov lumped 更新可表示为

\[
 Q_i^{new}=(g_i^{new}-\Lambda_i)U_i^0+\sum_\ell\lambda_\ell V_\ell,
 \qquad \sum_\ell\lambda_\ell=\Lambda_i,\quad\lambda_\ell\ge0.
\]

`V_l` 来自可容许的 pair/fan states，邻点可以采用已经检查的 live predictor。
故 `Λ_i≤g_i^{new}` 确实足以保证正性；邻点使用 predictor 本身不破坏该论证。
R2 指出的是代码尚未强制执行此条件。N/LDA/B 没有相同保证。

### Refresh、ledger 与 lazy

当前 RK2 residual 路径显式绕过 Taylor extrapolation，不读取 `TimeLastPrimUpdate`
作阶段外推；在目前单 rank、无额外物理的配置中，没有发现 inactive primitive refresh
导致 OldMass/gradient 参与错误阶段状态的证据。扩大物理模块或 MPI 前需重新审核。

采用 ledger 作除数与均匀态保持一致。几何面积仍用作独立误差检查；目前的漂移量
不足以支持增加任意周期性 re-anchoring。直接改面积或 Q 可能重新损害 GCL/守恒，
应先做长时漂移测试，再提出同时保持两者的修正。

lazy 的按 cavity 选择可在有效旧/新三角剖分上成立。其 15°/20° 阈值不是下一步
无翻转保证；全区间 signed quadratic area 检查会中止非法区间。这是故障检测，
还没有几何步长预测或恢复机制。不能据此承诺任意强剪切下都能完成。

## 4. 独立验证与证据范围

全部证据保存于 `../local_runs/codex_flip_review_20261009_v1/`。

- 重新执行 `make check_rd`，9 个脚本、现有 12 条 PASS 输出全部通过。
- `audit_archives.py` 核对下列冻结 source tree、source.tar、binary、Config、
  IC、param 的 SHA256 关联，并从快照重算首末量、从日志读取公共闭合量。
  没有覆盖或重写任何历史档案。

| 档案 | 完成 / 总数 | 未完成 |
|---|---:|---|
| flip_gates_20261009_v1 | 52 / 54 | 两个 LDA–KH |
| sedov_flip_gate_20261009_v1 | 15 / 15 | 无；含 5 个 uniform |
| flip_mode1_sedov_20261009_v1 | 2 / 2 | 无 |
| interval_hierarchy_gates_20261009_v2 | 65 / 70 | 五个 LDA–KH |
| lazy_flip_gates_20261009_v1 | 22 / 22 | 无 |

排除明确的 no-transfer 负对照后，分层公共闭合守恒最大约 `3.53e−14`；
lazy 约 `3.51e−14`。分层 Sedov1 的首末能量漂移约 `−3.73e−14`。
因此原报告摘要「全部 ≤2e−14」应放宽表述为「数个 1e−14、舍入级」，
不能照搬其统一上限。上述差别不改变数值守恒结论。

此外，冻结当前干净 `9672ad7` 的源码，新建独立 BUILD_DIR、binary、Config、
run dir 和 OutputDir，显式 mode 1 + lazy + natural bins，运行四项确认。
采用 Homebrew MPI，两个并发模拟，OMP/OPENBLAS 均为 1。

| Native 确认 | 实际点数 | 终点 | 接纳 cavities | 最大公共闭合守恒误差 | 其他 |
|---|---:|---:|---:|---:|---|
| uniform_random / N | 2304 | 0.25 | 404 | 5.15e−15 | 状态缺陷 4.89e−15 |
| Yee48 / N | 2304 | 1 | 64 | 5.06e−15 | 面积加权 rho L1=2.91870e−3 |
| Sedov21 / HLLC | 16384 | 0.005 | 89 | 1.09e−14 | CFL ledger max=.116，正性通过 |
| Sedov1 / HLLC | 16384 | 0.005 | 87 | 3.84e−14 | CFL ledger max=.128，正性通过 |

注意：Yee 的 natural bins 实际退化为等步长，work fraction=1；它不验证非平凡分层。
Sedov 的这两项仅到 t=.005（原长程 gate 是 .05），各有一次 flip limiting；
它们补充验证当前默认组合，不能替代终态 shell/profile 或长期安全性验证。
记录的工作量为 2.43%/2.30%，只针对这个早期区间，不与长程 7–8%直接作速度比较。

本轮第一次构建因 PATH 把 conda `mpicc` 放在 Homebrew 前，找不到 conda clang，
在产生 solver binary 前失败。失败日志保存为 `confirmation/failed_conda_mpicc_attempt/`。
调整 PATH 后对同一冻结源码构建成功；这是审核环境 setup failure，无数值含义。

原报告已明确当天存在超额并发；本审核没有把其 1.4× 墙钟或 17–37× CPU 比值
认定为可引用性能结果。元素工作量可以引用，但必须说明全网格重建仍然存在。

## 5. 建议的下一阶段顺序

1. 修复 R1 的实验模式固定和 R2 的执行约束；更正 R3、明确 R4 指标。
2. 对冻结最终配置做完整 t=.05 的两种 Sedov 注入，并覆盖 N/LDA/B 的 mode-1
   等步长退化、mixed bins 与负对照；新增受控 ledger 超限和几何翻转失败 gate。
3. 在共同空间比较光滑解，增加第三分辨率及时间步控制；之后再投入昂贵的 KH192+
   来检验 receiver-only 的收敛和分层接口误差。不能用低分辨率晚期 E_ky 排序方法。
4. 终稿中优先考虑经过上述验证的 2D 守恒结果；MPI、restart、3D 保持为后续工作。
   本轮没有编辑论文，也没有独立核查文献新颖性或 3D 推广的全部阶条件。

可供后续论文采用的保守表述是：在二维周期、单进程测试中，将 Campoli 端点质量
配对与局部守恒、正性受限的拓扑传递结合，消除了已测移动网格算例的总量漂移至
浮点舍入量级；分层扩展在公共闭合时保持该性质，其精度、正性适用条件和效率分别验证。
