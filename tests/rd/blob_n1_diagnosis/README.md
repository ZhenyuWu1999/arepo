# Static Blob / predecessor N1 diagnosis

These are offline scientific diagnostics, not new solver backends or a full
Blob benchmark. They freeze the COSMA source revision and a specified
`rdsolver` commit, compile the actual predecessor element class, reconstruct
the downloaded periodic mesh and compare N1/forward-Euler and lumped Heun.
No script submits jobs or launches AREPO. No source checkout is modified.

Dependencies: Git, C99/C++14 compilers, LAPACKE/BLAS, Python 3.12+ (for safe
tar extraction), numpy, scipy, h5py and matplotlib. The Mac's tested Python
3.10 runtime also backports the `tarfile` data filter. Homebrew OpenBLAS is
detected; other hosts use `-llapacke -llapack -lblas`. Compiler/linker paths
may need the host's module environment. Build/run on compute nodes on clusters.

Use a **new external output directory**. Supply the extracted data bundle,
the predecessor Git root, and the primary Figure 20 SVG saved for numerical
tracing from <https://arxiv.org/html/2204.01757v2/cloudMass.svg>. It is plotted
vector data, not original simulation data. The inspected SVG SHA256 is
`94755056a56524a5e41e4cad0db226d1073a2e0043bb38796adbaa9389ade17a`.

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export RD_BLOB_BUNDLE=/absolute/path/to/blob3d_mac_analysis_20261020_v1
export RD_BLOB_AUDIT_ROOT=/absolute/path/to/new/audit
python tests/rd/blob_n1_diagnosis/prepare_sources.py \
  --bundle "$RD_BLOB_BUNDLE" --predecessor /absolute/path/to/rdsolver \
  --reference-svg /absolute/path/to/cloudMass.svg --out "$RD_BLOB_AUDIT_ROOT"
python tests/rd/blob_n1_diagnosis/run_kernel_audit.py
python tests/rd/blob_n1_diagnosis/full_mesh_audit.py
python tests/rd/blob_n1_diagnosis/replay_updates.py
python tests/rd/blob_n1_diagnosis/contact_audit.py
python tests/rd/blob_n1_diagnosis/plot_diagnosis.py
python tests/rd/blob_n1_diagnosis/compare_published_curve.py
```

The sampled initial/evolved interface comparisons exercise 8260 tetrahedra;
the full-mesh check additionally covers all 221713 initial tetrahedra with
nonzero velocities. The separate contact probe includes exact rest in
the current kernel and tiny common velocities in the predecessor, whose old
inverse cannot reliably handle exact rest. `#define private public` in the
C++ diagnostic wrapper exposes results without changing numerical methods.
It is deliberately outside production sources.

Replay uses the recorded COSMA dt for four steps and eight half-steps, not a
cloud lifetime calculation. To compare an independently completed native
four-step control, set `RD_BLOB_NATIVE_RUN` to its directory, containing
`run.log` and `output/snap_*.hdf5`. That control must use the same IC, gamma,
N/equal Config, dt and target as the report, with identifiable native build
provenance. The scripts do not imply that a supplied arbitrary binary has
the required configuration. Do not transfer the Mac executable to Linux.

Outputs retain source/config/compiler commands, mesh coverage, residual
comparisons, timestep/IC/contact checks, CSV curves, and PNG/SVG sections.
P1-Z pressure in the sections is reconstructed from Roe parameters and can
differ from linearly interpolated nodal pressure. The published curve's fitted
time stretch is a shape diagnostic, **not a correction to its time units**.

See [the diagnosis report](../../../dev_log/RD_3D_BLOB_N1_DIAGNOSIS_20261020.md)
for the scientific conclusions and limitations. The default four-step probe
does not establish long-time N1/RK2 agreement, convergence or MPI scaling.
