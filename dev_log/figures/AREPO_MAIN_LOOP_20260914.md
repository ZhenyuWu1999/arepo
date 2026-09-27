# Loop-only flowchart revision

Author: Zhenyu Wu; revision with Codex (GPT-6), 2026-09-14.

The requested new PDF is saved beside the original:
`/Users/zhenyuwu/Desktop/MyThesis/useful_resources/Arepo_document/Arepo_flowchart_main_loop_RD_20260914.pdf`.
An identical working output is retained at
`/Users/zhenyuwu/arepo_rd/arepo/output/pdf/Arepo_flowchart_main_loop_RD_20260914.pdf`.

The original `Arepo_flowchart.pdf` was copied before editing and was never
overwritten. Its SHA256 remains
`48d19858dcd4d93a478c4dd2105d4556803a78e7c01cec3132f962dca7af5d9a`.
The delivered revision SHA256 is
`718c231c340926e239f2fe7c703b422038622ed40a303534203fa7444f9b1e15`.

Changes are deliberately limited to the main-loop presentation:

- Retain the original coloured vector boxes, loop layout and connectors;
  crop out initialization and the pre-loop setup.
- Replace verbose node text with short descriptions and mark the two red
  blocks as RD predictor/corrector, alongside their FV contributions.
- Use node timebins and nodal conserved increments. The diagram does not
  imply that a frozen node refreshes its primitive state on every fine tick.
- Merge the old synchronized-bin side box into the next-sync-point box,
  matching the call inside `find_next_sync_point()` and removing a crossing.
- Remove the seven old FV-only formula annotations, which were PDF /Stamp
  annotations rather than ordinary page text.
- Label optional gravity/source and mesh operations, and state the scope:
  static N/LDA using split equal or static hierarchical timesteps. Moving
  RD and the old unsplit equal variants are not represented by those RD labels.

The source-code basis is log3 §42 and `src/main/run.c`. No solver or thesis
chapter was modified for this figure request. The new figure is a one-page
vector PDF with embedded Liberation Sans for its revised text. The full page
was rendered and visually checked for stale equations, clipping, connectors
and text alignment; extracted text contains only the revised loop labels.

To change the wording, edit `LABELS` in
`build_arepo_main_loop_flowchart.py` and run it with the bundled Python:

```sh
/Users/zhenyuwu/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  /Users/zhenyuwu/arepo_rd/arepo/dev_log/figures/build_arepo_main_loop_flowchart.py
```

The builder verifies the original checksum, creates its own temporary copy,
and writes only the workspace output. It does not overwrite the delivered
Desktop revision; a later reviewed revision can be saved under a new name.

## Native draw.io source (2026-09-14)

At Zhenyu's request, the revised main-loop figure is also reconstructed as
`Arepo_flowchart_main_loop_RD_20260914.drawio` in this directory, with an
identical delivered copy beside the PDFs in the thesis resource directory.
Use that Desktop copy for manual edits; the PDF remains the earlier export.

The diagram has 14 independent process blocks, 14 attached connectors forming
the loop, and one entry arrow. The title, legend, frame and scope notes are
editable objects. Three layers separate process blocks, connectors, and frame
and notes. No raster image or flattened PDF is embedded. All revised wording,
box geometry and colours follow the current PDF; rounded connector routes are
native draw.io routes rather than the PDF's original drawing paths.

The page background is explicitly `#FFFFFF`. Also selected Light appearance
in the user's installed draw.io after the user requested a white background;
the initial dark canvas was the editor's automatic dark appearance. Opened
and saved in draw.io 31.4.5, inspected the complete white-background layout,
and moved the predictor box to verify that both attached arrows follow it,
then undid the move. Re-read the saved XML and checked all 14 stage texts and
positions, all connector endpoints, the restored title and white background.
Both existing PDFs retain their documented SHA256 values.

Delivered draw.io SHA256:
`9e17fc08018e39f0b45094fe21dec585d66ed5d342d75a13375b995557b47c5b`.

`build_arepo_main_loop_drawio.py` recreates the initial native diagram from
the existing PDF builder's labels using Python's standard library. It does
not modify PDFs or the delivered Desktop copy. Rebuilding overwrites only
its own workspace `.drawio` output, so preserve manual edits separately.

## Function-name comparison version

Zhenyu subsequently requests a second version retaining function names for
comparison. `Arepo_flowchart_main_loop_RD_functions_20260914.drawio` is saved
both here and beside the PDFs in the thesis resource directory. It preserves
the concise version's 14-node sequence, explanations, colours and attached
arrows, with wider boxes and monospaced current function calls below each
description. The main-loop ribbon identifies `run(): while (1)`.

Calls were checked against `src/main/run.c` and
`src/time_integration/predict.c`. The red boxes show the full
`compute_residuals(&Mesh, RD_RK_STAGE_PREDICTOR/CORRECTOR)` calls (one stage
per box), separately from FV's `compute_interface_fluxes(&Mesh)`.
`mark_active_timebins()` is explicitly identified as an internal call of
`find_next_sync_point()`. The diagram lists selected relevant calls, not every
diagnostic, allocation, conditional extension or restart branch in `run()`.

Opened successfully in draw.io and rendered with its native CLI using
`--theme light --size page`; the complete white-background image was visually
checked for clipping, long function names, routing and footnotes. The saved
file contains 14 process vertices and 15 valid edges, with #FFFFFF background.
Function-version SHA256:
`cf149b7e0a4713b41482609eb14c745e9aa3db86994462204d31406a071919c4`.
Builder: `build_arepo_main_loop_functions_drawio.py`; it leaves the concise
source unchanged. Both Desktop PDFs and the concise draw.io file remain intact.

## Latest generic RD / FV version, 2026-09-14 (log3 §53)

Use `Arepo_flowchart_main_loop_RD_FV_functions_20260914.drawio` and its matching
white-background PNG for the current generic main-loop discussion. This copies
the numbered §50 reviewed figure and removes static/ALE dispatch labels. Blocks
7/12 show the RD begin/end hooks and alternative FV flux call; the internal
numerical stages are not expanded. All14 numbered boxes,15 edges and manual
gravity edits are preserved. Matching files are in the user's thesis resource
directory; earlier sources and previews remain untouched.

Builder: `build_arepo_main_loop_rd_fv_drawio.py`. It checks the reviewed input
hash and rejects existing output paths. Do not regenerate over later manual
edits. Figure delivery/protection record is under workspace
`local_runs/flowchart_rd_fv_20260914_v1/delivery.json`.

The 2026-09-15 wording copy, `Arepo_flowchart_main_loop_RD_FV_functions_20260915.drawio`
and matching PNG, changes only the two hydro headings to First/Second
hydrodynamic stage. Use this latest copy for continued editing. The function
names remain rd_step_begin/end; the 2026-09-14 version is preserved. See log3 §54.

## Enlarged landscape thesis copy, 2026-09-15 (log3 §58)

The latest thesis layout is
`Arepo_flowchart_main_loop_RD_FV_functions_landscape_20260915.drawio`, with a
matching native vector PDF. Both files also reside in the thesis resource
directory; the PDF is included on a landscape page in Chapter4.1.
Use this new draw.io copy for further layout edits. All earlier files,
including the user-finalised `Arepo_flowchart_main_loop_RD_FV_functions.pdf`,
are preserved.

The source of this revision is the editable XML embedded in that final PDF,
including the user's deleted labels. The reflow keeps all14 numbered boxes,
15 connections and function names, aligns the three columns, reduces gaps,
increases label sizes and routes the return arrow above the boxes. Most box
labels use dark ink on the existing colours for contrast. The background is
white. Figure4.1 remains on printed page140; actual function labels grow from
about3.38pt to6.80pt in the compiled thesis.

`build_arepo_main_loop_landscape_drawio.py` accepts an input draw.io XML and a
new output path, checks label/edge identity and refuses an existing output.
The authoritative extracted source, before/after thesis text, native export,
compile and visual QA records are archived in workspace
`local_runs/thesis_flowchart_landscape_20260915_v1/`.
