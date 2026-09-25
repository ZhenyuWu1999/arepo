# 真正两阶段方案的 Arpaia 推广：需另补端点质量转换项

作者：Codex。日期：2026-09-14。对应 log3 §52，补充
[上一轮 Campoli 探索](RD_TRUE_ALE_SPLIT_EXPLORATION_20260914.md)。

**答复：两阶段的执行顺序对 Arpaia 也可行；上一轮仅在翻边区域实施的修正，
对 Arpaia 一般不充分。保留 Arpaia 内部质量配对时，还需要一个节点级端点修正。**
本轮推导并单步核对了这个推广。它是基于 Arpaia 的新修正变体，不是原始 Arpaia
自动具有的新性质；也没有证明完整时间二阶或正性。没有改动 native C / Config。

## 1. 当前代码中两套配对的差别

对同一连接关系的三角形 T，定义其起点、中点、终点面积为
\(A_T^n,A_T^{n+1/2},A_T^{n+1}\)。两种方法都使用中点法向量计算物理残差。
它们在质量和除数上分别取：

| 配对 | F1/lumped 时间质量中的三角形面积系数 | 该三角形对节点更新分母的贡献 |
| --- | --- | --- |
| Campoli | \((A_T^n+A_T^{n+1})/2\) | \(A_T^{n+1}/3\) |
| Arpaia | \(A_T^{n+1/2}\) | \([A_T^{n+1/2}+(A_T^{n+1}-A_T^n)/2]/3\) |

代码依据：`src/mesh/rd_ale_geometry.c` 的 `rd_ale_triangle_geometry_build()`，
以及 `src/hydro/residual_distribution_solver.c` 的 `rd_ale_prepare_step()` / `rd_ale_finish_step()`。
后一个函数保持计算出的节点密度，再乘实际终点面积写回广延量。
文献参照为 [Arpaia 等论文的作者上传预印本，Proposition 4.1](https://www.researchgate.net/publication/257292092_An_ALE_Formulation_for_Explicit_Runge-Kutta_Residual_Distribution)。
以下缺口分析针对**本项目的具体两扫描更新与 endpoint Q 存储**，不把它概括为
对论文所有离散守恒定义的否定。

## 2. Arpaia 多出的总量缺口

沿用前报告符号：\(U_i^n\) 为步初守恒量密度，\(U_i^*\) 为 predictor，
\(\widehat U_i^{n+1}\) 为未施加本文修正的 corrector 结果。
定义 \(\delta U_i=U_i^*-U_i^n\)。实际存储的广延量是 \(Q_i=S_iU_i\)。

下面四个面积对应**新连接关系**：

- \(\widetilde S_i^n\)：拉回起点的 median-dual 面积；
- \(S_i^{n+1/2,\mathrm{new}}\)：步中点面积；
- \(S_i^{n+1}\)：实际终点面积；
- \(D_i^A=S_i^{n+1/2,\mathrm{new}}+(S_i^{n+1}-\widetilde S_i^n)/2\)：Arpaia 更新分母。

定义面积差

\[
d_i=S_i^{n+1}-D_i^A
=\frac{\widetilde S_i^n+S_i^{n+1}}2-S_i^{n+1/2,\mathrm{new}}.
\tag{A1}
\]

为便于检查，另记 \(B_i=(\widetilde S_i^n+S_i^{n+1})/2\)。
Arpaia 分母为 \(S_i^{n+1}-d_i\)，质量矩阵的列和则为 \((B_i-d_i)I\)，
\(I\) 是守恒分量的单位矩阵。二者相减时 d 抵消，仍有

\[
D_i^A-(B_i-d_i)=\frac12(S_i^{n+1}-\widetilde S_i^n).
\]

因此把旧 predictor 残差、新 corrector 残差和 Arpaia 时间质量项求和，
再将内部更新转换为实际终点广延量，得到

\[
\boxed{
\sum_iS_i^{n+1}\widehat U_i^{n+1}-\sum_iS_i^nU_i^n
=\sum_PC_P+\sum_id_i(\widehat U_i^{n+1}-U_i^n).
}
\tag{A2}
\]

右侧第一项是前报告相同的**拓扑缺口**。其中 P 是完整 changed cavity，
\(\bar S_i^{n+1}\) 是旧连接关系前移到终点后的面积，\(S_i^n\) 是实际起点面积：

\[
C_P=\frac12\sum_{i\in P}
[(\widetilde S_i^n-S_i^n)+(S_i^{n+1}-\bar S_i^{n+1})]U_i^n.
\]

第二项是 **Arpaia 内部权重与 endpoint Q 的转换缺口**。
即使不翻边、所有 C 都为零，这一项仍可能非零。它正是既有固定连接关系
Arpaia 端点问题的推广，不是这次把两个 hook 分开才产生的新问题。
全域 \(\sum_i d_i=0\) 也不能使非均匀的面积加权状态变化自动相消。

推导采用与前报告相同的条件：二维周期区域、线性节点轨迹、有效一致的旧/新三角剖分、
P1 状态和速度插值、守恒的残差分配及正确的时间质量列和。
旧 predictor 可以使用旧连接关系对应的 Arpaia 分母；式 (A2) 中 predictor 的
\(\delta U\) 项仍然抵消，不需要强行换成 Campoli predictor。

## 3. 保留 Arpaia 内部配对时如何修正

在原来拓扑修正之外，逐节点再扣除 \(d_i(\widehat U_i^{n+1}-U_i^n)\)：

\[
\boxed{
Q_i^{n+1}=S_i^{n+1}\widehat U_i^{n+1}
-d_i(\widehat U_i^{n+1}-U_i^n)-w_iC_P,
\quad U_i^{n+1}=Q_i^{n+1}/S_i^{n+1}.
}
\tag{A3}
\]

区域 P 内仍取 \(w_i=S_i^{n+1}/\sum_{j\in P}S_j^{n+1}\)；区域外令最后一项为零。
**d 项使用未修正的 corrector 结果**，不能误用修正后的最终状态。
式 (A2) 立即给出总量守恒；均匀流时两个修正项都为零。

这仍然是一次新 Delaunay 构造、两次物理残差扫描；新增项可在写回节点 Q 的循环内计算。
它一般作用于所有变形节点，不能只放在翻边区域。d 只需已有中点/端点面积，不需第三次构网。

这不是“修正后完全等于 Campoli”：内部 predictor 分母、F1 质量作用和产生的 stage
状态仍不同。下面的逐点差值也确认两者没有成为同一个更新。
二维线性轨迹下 d 为 O(dt²)；平滑时间变化时新增 d 乘状态变化为单步 O(dt³)。
这只是该项的局部量级，不是整个含 F1/翻边的方法已经时间二阶的证明。
两套质量权重在静止或纯平移时相同；一般变形下不能假设 d 为零。

## 4. 单步独立核对

新增脚本 `tests/rd/probe_true_ale_split_arpaia.py`。采用前报告同一周期单位盒、
144 个 jittered Cartesian 节点、288 三角形、固定变形速度，单步 dt=1/16。
两组几何分别保持旧连接关系，以及实际重建新 Delaunay（删除26个旧三角形）。
N/lumped 与 LDA/F1，标量与独立 Euler，均匀与非均匀状态，组成16组 Arpaia 检查；
每组另计算相同设置的已修正 Campoli 参考，共32个单步更新。
标量非均匀初值为前报告的正弦波，Euler 为核心半径.07、参数3的 Yee 型涡旋。
固定连接组只是隔离几何配对的对照，不要求移动后的旧网格仍满足 Delaunay 条件。

逐组验证：

1. 直接测量的总量缺口等于式 (A2)，最大绝对差 `1.76e-15`。
2. 只扣拓扑项后，剩余缺口等于 d 项；无翻边 Euler N 对照的能量分量为 `-1.626e-6`。
3. 两项都扣除后，最大绝对总量误差 `2.22e-15`。
4. 均匀状态最大绝对密度向量误差 `3.11e-15`。
5. 非均匀修正后 Arpaia / Campoli 的逐点最大差：标量约 `5.8e-6`–`7.5e-6`，
   Euler 约 `2.3e-4`–`4.1e-4`，证实两个更新并不等价。

这些是符号与单步求和核对，**没有新增多步稳定性、时间/空间收敛、激波正性或 native
验证**。上一轮局部拓扑修正的正性反例仍适用；这个新增节点修正本身也没有正性保证。
Euler 模型仍未覆盖 native 的完整 Uhat/frame/奇异矩阵处理。

档案：`/Users/zhenyuwu/arepo_rd/local_runs/true_ale_split_arpaia_20260914_v1/`，
含冻结脚本、依赖脚本 SHA256、summary 和每组两种最终状态；旁边 `.log` 为原始输出。
命令从仓库根执行，最后一个参数必须为未存在的新目录：

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
 /Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python \
 tests/rd/probe_true_ale_split_arpaia.py /path/to/NEW_OUTPUT
```

未修改上一轮报告或其冻结档案。当前 native solver、Config 和流程图保持原状。
