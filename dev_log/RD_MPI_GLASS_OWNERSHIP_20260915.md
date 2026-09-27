# Native glass triangulation and MPI responsibility, four ranks

2026-09-15. Author: Codex. Requested by Zhenyu for the Chapter 4.1 MPI illustration.

## Result and figure files

已完成一个真实 glass IC 的4-rank原生运行，直接从 RD 求解器导出节点归属和三角形。
绘图使用原生三角形的顶点及坐标；Python 周期 Delaunay 重建只用于独立核对。
**4608个物理三角形逐一相同，2304个节点的 rank 归属全部核对通过。**

- `figures/rd_mpi_glass_rank4_overview_20260915.pdf`：左为节点 primary owner，右为三角形计算 owner。
- `figures/rd_mpi_glass_rank4_boundary_20260915.pdf`：真实边界放大，给出两个相邻三角形及其 ParticleID。
- 两图均有同名 SVG 和 PNG。文字采用英文，白色背景；PDF/SVG 保留矢量网格。

资源交付目录：
`/Users/zhenyuwu/Desktop/MyThesis/useful_resources/Arepo_document/RD_MPI_glass_rank4_20260915/`。
没有改 thesis 正文或重新同步 Overleaf；用户继续在 Overleaf 编写4.1。

完整运行档案：
`/Users/zhenyuwu/arepo_rd/local_runs/mpi_glass_ownership_20260915_v1/`。
其中 `analysis/native_nodes.csv`、`analysis/native_triangles.csv` 是合并的原生初始节点/
三角形表，`analysis/native_mesh.json` 为方便重画的结构化数据，
`analysis/audit.json` 包含所有核对值和边界示例。逐rank、逐stage的原始CSV在
`runs/rank4_capture/output/mpi_mesh/`。

## Initial conditions and actual run

| Item | Actual setting |
| --- | --- |
| Glass | Archived SWIFT `glassPlane_48.hdf5`, 2304 nodes |
| Glass SHA256 | `157e1a4767f4678df4cd80d2df9aa248fa520899e12e777a448e17f31e47d88f` |
| AREPO IC | `yee_glass48.hdf5`; same glass positions, modulo the periodic box and scaled by10 |
| IC SHA256 | `91e64bee13896308d60afeb3340f34a76fdd3ebf36864e3d67be56f1f0efad66` |
| Fluid | Advected Yee vortex, gamma1.4, beta5, boost(1,0), centre(5,5) |
| Geometry | Static 2-D periodic box, Lx=Ly=10; plots use x/L and y/L |
| Method | LDA/F1, Gauss3 physical contour, split equal-step RK2 |
| Mesh configuration | `VORONOI_STATIC_MESH`, `CREATE_FULL_MESH` |
| Decomposition settings | 4 MPI ranks, `MultipleDomains=2`, `TopNodeFactor=4` |
| Clock | Two steps of0.001953125, endpoint0.00390625 |
| Captured stages | First predictor at t=0; first corrector at t=0.001953125 |
| Thread budget | `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1` |

没有由随机抖动规则点阵来代替glass，也没有抽稀。历史 Yee 生成器按源文件行序重新赋予
1–2304的 ParticleID，所以源glass的原始ID和AREPO IC的ID不能直接对齐。以周期坐标作
一一匹配后，2304个源glass位置全部找到，归一化坐标最大距离1.57e-16；映射保存在
`analysis/glass_id_mapping.csv`。此后的所有拓扑、rank和通信核对均使用实际AREPO ID。

## What the colours mean

AREPO的domain decomposition首先给每个节点一个 primary owning rank。RD随后为每个
三角形选择负责计算的rank。这是两个相关但不同的分配层次。

本次完整局部网格配置的实际规则位于
`src/hydro/residual_distribution_solver.c::rd_simplex_claimed()`：

1. 比较三个顶点的 `(ParticleID, task)`，选取最小键。本例所有物理节点ID唯一，因而
   由最小 ParticleID 决定；task只是实现中的额外排序键。
2. 最小ID节点所属的rank负责此物理三角形，并且只有包含该节点 **primary copy** 的
   三角形实例可以claim。该节点的周期像不再claim，避免周期边界重复。
3. owner计算整个三角形残差并向三个顶点分别分配贡献。自己rank的顶点就地累计；
   远端顶点通过 `FluxRD_list` 按 `DP.task` 和 `DP.originalindex` 路由，再由
   `apply_FluxRD_list()` 在接收rank累计到正确节点。

图中的三角形填色表示第2步的计算owner；放大图节点颜色表示第1层的节点owner。
同色区域不要求是连续块。节点/网格点经Peano–Hilbert域分解和实际粒子交换后的归属
直接从 `P[]` 导出，没有用空间象限、Python分区或snapshot文件编号猜测rank。

| MPI rank | Primary nodes | Owned physical triangles | Remote vertex contributions sent per captured stage |
| --- | ---: | ---: | ---: |
| 0 | 576 | 1210 | 256 |
| 1 | 576 | 1144 | 150 |
| 2 | 576 | 1155 | 134 |
| 3 | 576 | 1099 | 109 |
| Total | 2304 | 4608 | 649 |

节点数相同并不使三角形计算量严格相同。这些计数描述本次几何分工；没有测量MPI加速比。
649表示远端顶点贡献记录数，MPI会批量打包，并不代表649次MPI调用。

## Two native boundary examples

图中两个相邻三角形位于 x/L约0.49–0.51、y/L约0.49–0.51，共享ID1142/1146的边。

| Triangle | Vertex IDs and primary ranks | Computing rank | Remote destinations |
| --- | --- | --- | --- |
| A | 1142→rank1; 1146→rank2; 1147→rank2 | Rank1, because1142 is smallest | Two contributions from rank1 to rank2 |
| B | 1142→rank1; 1146→rank2; 1150→rank3 | Rank1, because1142 is smallest | One contribution to rank2, one to rank3 |

A只有一个顶点属于rank1，但仍由rank1计算；规则不取“多数顶点所在rank”。B的三个
顶点分别属于三个rank，仍然有唯一owner。两个例子的原生顶点次序和本地triangle slot
保存在audit.json中，表格为方便比较按ID排列。

第一predictor的实际远端质量贡献如下；完整四分量值在audit.json。
这里的质量贡献是分配给某一顶点的积分量增量，不要求某个单独三角形的三个增量之和为零。

| Triangle / target ID | Route | Captured mass increment |
| --- | --- | ---: |
| A /1146 | Rank1→rank2 | -8.920380529104804e-06 |
| A /1147 | Rank1→rank2 | 7.181583175412484e-06 |
| B /1146 | Rank1→rank2 | -6.9331168631473825e-06 |
| B /1150 | Rank1→rank3 | -2.971893432932018e-07 |

## Validation and its scope

- **Native ownership:** each exported triangle belongs to the minimum-ID node's rank, and that
  winning vertex is a local primary in the selected instance. All three vertices agree with
  the captured primary-node owner and destination-local index. Periodic coordinate mismatch:0.
- **Native topology:**4608 unique physical triangles,6912 unique periodic edges, two incident
  triangles per edge; total triangle area99.99999999999994 for box area100. Keys include
  sorted IDs and relative periodic-image shifts, so the check is not based only on centroids.
- **Independent Python reconstruction:**SciPy Delaunay on3×3 periodic copies of the captured
  primary positions gives exactly the same4608 canonical triangle keys. No missing or extra key.
  Every triangle's rank is then checked against the actual primary ownership table.
- **Actual evaluations and MPI:**both captured stages evaluate every owned triangle once.
  The expected remote vertex contributions from the actual residual loop, the real export
  buffer records and the real receive buffer records match exactly as multisets, including
  source, destination, destination-local index and all four conserved components. Received
  indices resolve to the intended ParticleID. There are649 remote contributions in each stage.
- **Rank reference:**the1-rank native triangle set matches the4-rank set exactly. After two
  steps, maximum matched-ID field difference is2.665e-15 (internal energy).
- **Capture control:**turning capture off in the same instrumented binary produces bit-identical
  ParticleIDs, coordinates, masses, density, velocities, internal energy and pressure at the
  endpoint. The helper does only file I/O, with no additional MPI collectives or state updates.

473 triangles touch vertices on more than one rank;168 have two ranks represented but the
computing rank owns only one of the three vertices;8 touch three ranks. The overview contains
295 edges between triangles with different computing owners.

This establishes the geometry, ownership and communication correspondence for this **static,
full-local-mesh, equal-timestep** case. A full local mesh includes the required ghosts, not a
replica of the complete global mesh on every rank. The same activity-independent minimum-ID
choice is used by the current static full-mesh hierarchy. The separately guarded active-only
static rebuild path restricts the owner candidates to the finest-bin vertices; this figure
does not validate that path, moving-mesh migration or large-rank scaling.

## Implementation provenance and reproduction

Working branch:`develop_pureC_RD`; base commit:`adc424ba93f8cb98ff494dd8e98b41fafcd2e98b`.
Existing working-source changes were included and archived before building. The working solver
was not edited; SHA256 remains
`1ca5e428a0578752a18fc7af6b34e0341dbb3b6ce1d1d7d5a10d27dbe9e13636`.

The capture runner copies the current source to an isolated directory and injects five read-only
hooks plus `mpi_mesh_capture.h`. The frozen instrumented source tar SHA256 is
`0e3eb5c3b3cbc9c0479ccfa672bad4a8f79559e67a355ead5fafc24d7780e953`;
binary SHA256 is `37e1bb25eb3a18a1d0d3c4a0ec227db2f866b5afbbdc873b5659af4a04553c86`.
Build logs, effective configuration header, Apple Silicon dynamic-library linkage and each
run's parameter file/command are retained. No source/default-config commit or push was made.

Scripts under `tests/rd/`:

- `capture_mpi_mesh.py`:prepare a **new** archive, build, run4-rank capture/control and1-rank capture.
- `mpi_mesh_capture.h`:native geometry, evaluation and MPI-buffer output.
- `analyse_mpi_mesh.py`:exact identity checks, periodic topology reconstruction and examples.
- `plot_mpi_mesh.py`:plot the audited native triangles, not newly triangulated polygons.

Example from the AREPO repository, with a new archive path in place of `NEW_ARCHIVE`:

```sh
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python tests/rd/capture_mpi_mesh.py NEW_ARCHIVE prepare
/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python tests/rd/capture_mpi_mesh.py NEW_ARCHIVE build
/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python tests/rd/capture_mpi_mesh.py NEW_ARCHIVE run
/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python tests/rd/analyse_mpi_mesh.py NEW_ARCHIVE
/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python tests/rd/plot_mpi_mesh.py NEW_ARCHIVE
```

The runner expects the documented retained glass/IC archive. Matplotlib, NumPy, SciPy and h5py
are available in that local environment; pandas is not needed. Native MPI launching from Codex
requires its normal local-socket permission. No simulation result failed. The first overview
layout had overlapping heading/legend text and was replaced after PDF rendering; the old layout
is retained only under `figures/layout_v1/`. Both final PDFs were visually checked.

## Suggested English captions

**Overview:**

MPI ownership in a four-rank AREPO-RD calculation using a periodic glass initial condition
with 2304 nodes. The Delaunay triangulation is exported directly from the native RD solver.
Panel (a) colours the nodes by their primary owning rank, whereas panel (b) colours each
physical triangle by the rank responsible for evaluating its residual. For this full-mesh
configuration, the computing rank owns the triangle's smallest-ParticleID vertex. The dashed
box marks the region enlarged in the boundary illustration. Each rank owns 576 primary nodes,
but the number of assigned triangles differs between ranks.

**Boundary detail:**

Two adjacent triangles at an MPI-rank boundary. Node colours indicate primary ownership,
and triangle fills indicate the rank that evaluates the residual. Both triangles are assigned
to rank 1 because their smallest ParticleID is 1142. Triangle A has its other two vertices on
rank 2; triangle B has its other vertices on ranks 2 and 3. Rank 1 therefore evaluates both
residuals and returns the remote vertices' contributions to their primary owners. Node IDs,
triangle connectivity and the communication destinations are taken from the native run.

For final thesis layout, the two-panel overview benefits from a landscape page or separate
subfigures at adequate width. The detail figure is explanatory material that can be shortened
once the accompanying prose defines the ownership rule.

## Thesis figure version and insertion (2026-09-15, log3 §61)

Zhenyu requested shorter figures and insertion into Section 4.1.2. The new
copies are named `rd_mpi_glass_rank4_overview_thesis_20260915` and
`rd_mpi_glass_rank4_boundary_thesis_20260915`, in PDF/SVG/PNG. The original
annotated figures above remain unchanged.

- Overview: removed the main heading and the bottom `2,304 nodes ...` line.
  Panel headings, dashed detail box and per-rank count legend remain.
- Detail: removed the main heading, panel (a) subtitle, the entire right-hand
  panel (b) “Responsibility and routing”, and the footer prose. The native
  mesh, highlighted triangles A and B, four node-ID/rank annotations and the
  Rank 0--3 colour legend remain. Lower-case panel (b) is the explanatory
  column; it is distinct from the actual triangle labelled B.
- Compact figure canvases remove the empty space left by those deletions.
  Colours, native coordinates, triangle connectivity and owners are unchanged.

The figures now appear as Figure 4.2 (landscape overview, p.145) and Figure 4.3
(portrait detail, p.146) in Section 4.1.2, with English captions and a brief
explanation of the minimum-ID rule and the two actual communication examples.
The caption carries the sample size and periodic-domain information removed
from the overview graphic. No additional MPI performance claim was added.

The plotter retains its original default output and adds an explicit mode:

```sh
/Users/zhenyuwu/miniconda3/envs/21cmfast/bin/python tests/rd/plot_mpi_mesh.py \
  ../local_runs/mpi_glass_ownership_20260915_v1 \
  --thesis --output-dir ../local_runs/thesis_mpi_figures_20260915_v1/figures
```

New copies are under `dev_log/figures/` and the existing thesis
`useful_resources/Arepo_document/RD_MPI_glass_rank4_20260915/` resource folder;
two PDFs are also in `zhenyu_thesis/chapter4/figures/`.
Full XeLaTeX compilation succeeds (239 pages), with references resolved and
no new overfull boxes or oversized floats. Both standalone PDFs and the four
review pages (143--146) were rendered and visually inspected. Automated PDF
text checks confirm the requested removals and the retained node/rank labels.
All original figure/data/solver hashes are unchanged. No native simulation
rerun, source solver edit, Config change, commit or push.

Archive: `../../local_runs/thesis_mpi_figures_20260915_v1/`; it includes source
backups, the previous plotting script, the patch for this turn, hash manifests,
new graphics, the isolated full build and `output/pdf/chapter4_1_2_mpi_review.pdf`.
