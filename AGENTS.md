# AREPO-RD project instructions

This repository implements a residual-distribution hydrodynamics solver in
AREPO. Keep this file short and stable: it is the working-rules and navigation
entry point, not a second development log. Explicit user instructions take
precedence over project guidance here and in the linked documents.

## Start here

1. Check the current directory, Git branch, status and staged changes. Preserve
   work from the user or other agents; do not switch branches, restore files or
   commit unrelated changes merely to obtain a clean tree.
2. Read [project context](dev_log/context.md) for the project and thesis scope.
   On the local Mac, read [local context](dev_log/context_localMac.md) for actual
   paths, tools and the current handoff. For COSMA work also read
   [COSMA context](dev_log/context_cosma.md); other cluster guidance is in the
   project context. Do not apply historical cluster paths/settings to the Mac.
3. Read the latest relevant entries and reviewer corrections in
   [development log 3](dev_log/RD_DEVELOPMENT_LOG_3_localMac.md), then follow
   references into older logs or focused reports as needed. Do not read every
   historical log in full by default.
4. For static Chapter 4 work, consult the
   [baseline choices and limitations](dev_log/RD_STATIC_BASELINE_CHAPTER4.md)
   together with later log reviews. Check the source and artifact provenance
   before treating a reported method or result as the current implementation.

Older sections labelled "current" describe their writing date. Distinguish
user decisions, reviewed derivations, proposed fixes, independent model tests
and native solver evidence. A newer review identifies claims to check; it does
not automatically turn a proposed algorithm into a validated result.

## Scope and scientific record

- Append current work to **log 3**, preserving authorship and existing entries.
  Logs 1 and 2 are historical; do not append current local work there. Put long
  derivations/results in a focused Markdown report and link it from log 3.
- Update the local context when the working environment, baseline or handoff
  changes. Keep evolving conclusions, branch hashes and numerical tables in
  the context/reports/log, rather than duplicating them in this file.
- Do not modify thesis files without an explicit thesis-edit request. Chapters
  1--3 require authorization for the specific chapters; Chapter 4 remains a
  mathematical working draft until the user chooses otherwise. A solver review
  or baseline discussion does not itself authorize editing the thesis.
- State what each test establishes and its limits. Conservation, uniform-state
  preservation, positivity, convergence order, MPI agreement and efficiency are
  separate properties. Preserve failed attempts and distinguish setup failures
  from numerical failures. Do not loosen assertions just to obtain a pass.
- Record actual resolution, coordinates, time normalization, norm weights,
  timestep selection and method flags in comparisons; do not substitute a
  setup's nominal resolution or a different method's validation results.

## Builds, runs and Git

- Follow the environment-specific context before compiling or launching jobs.
  On clusters, compile/run on compute nodes using the documented scheduler,
  not on login nodes. On the Mac, use native binaries and local toolchains.
- For solver comparisons, freeze identifiable source before building and use
  separate `BUILD_DIR`, executable, working directory and `OutputDir` per
  configuration/run. Preserve the Config, generated header, source revision,
  binary hash, linkage, parameters and logs. Do not trust the mutable root
  `Arepo` or a shared build header as proof of the binary's configuration.
- On this Mac set **both** `OMP_NUM_THREADS=1` and
  `OPENBLAS_NUM_THREADS=1`. Stay within the resource budget in the local context;
  reduce concurrency for larger meshes. Do not overwrite archived run outputs.
- Run checks appropriate to the change. `make check_rd` is the existing algebra
  target; numerical changes also need the relevant native gates. Documentation
  changes alone do not require compiling or rerunning hydrodynamics.
- Keep experimental configurations explicit; do not silently replace the
  default Config or merge unrelated research code. Verify the current branch
  rather than relying on a historical branch name in a report.
- Follow the commit-authorship convention in `dev_log/context.md`: credit
  Zhenyu Wu and the contributing agent/model per commit, with a co-author
  trailer. Do not change repository-wide identity or include another author's
  staged work in your commit. Check staged paths before committing.

Paths above are relative to this repository root. The outer workspace's
`AGENTS.md` only points here; maintain the substantive rules in this file.
