#!/usr/bin/env python3
"""Create a separate function-name comparison version; preserve the concise one."""

import ast
import hashlib
import html
from pathlib import Path
import re
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "Arepo_flowchart_main_loop_RD_20260914.drawio"
OUTPUT = HERE / "Arepo_flowchart_main_loop_RD_functions_20260914.drawio"

# Rectangles retain the same three-column loop and process ordering, with
# additional space for complete source names and stage arguments.
BLOCKS = [
    ("outputs", (80, 145, 370, 105), ["create_snapshot_if_desired()", "produce_dump(); create_end_file()  [at final time]"]),
    ("node-timebins", (80, 280, 370, 155), ["find_timesteps_without_gravity()"]),
    ("sources-first", (80, 465, 370, 165), ["find_gravity_timesteps_and_do_gravity_step_first_half()", "do_second_order_source_terms_first_half()"]),
    ("gradients-first", (80, 660, 370, 115), ["exchange_primitive_variables()", "calculate_gradients()"]),
    ("vertex-velocity", (80, 805, 370, 115), ["set_vertex_velocities()", "ngb_update_velocities()"]),
    ("exchange-predictor", (510, 215, 370, 120), ["exchange_primitive_variables_and_gradients()"]),
    ("rd-predictor", (510, 365, 370, 190), ["FV: compute_interface_fluxes(&Mesh)", "RD: compute_residuals(&Mesh,", "    RD_RK_STAGE_PREDICTOR)"]),
    ("next-sync", (510, 585, 370, 165), ["find_next_sync_point()", "  includes mark_active_timebins()"]),
    ("active-nodes", (510, 780, 370, 155), ["make_list_of_active_particles()"]),
    ("domain-mesh", (510, 965, 370, 170), ["drift_all_particles(); domain_Decomposition()", "ngb_treebuild(NumGas)", "create_mesh(); mesh_setup_exchange()"]),
    ("exchange-corrector", (940, 215, 370, 120), ["exchange_primitive_variables_and_gradients()"]),
    ("rd-corrector", (940, 365, 370, 190), ["FV: compute_interface_fluxes(&Mesh)", "RD: compute_residuals(&Mesh,", "    RD_RK_STAGE_CORRECTOR)"]),
    ("recover-primitives", (940, 605, 370, 145), ["update_primitive_variables()"]),
    ("sources-second", (940, 790, 370, 155), ["do_second_order_source_terms_second_half()", "do_gravity_step_second_half()"]),
]


def style_set(cell, **changes):
    parts = [p for p in cell.get("style", "").split(";") if p]
    parts = [p for p in parts if p.split("=", 1)[0] not in changes]
    cell.set("style", ";".join(parts + [f"{k}={v}" for k, v in changes.items()]) + ";")


def geometry(cell, rect):
    g = cell.find("mxGeometry")
    for k, v in zip(("x", "y", "width", "height"), rect):
        g.set(k, str(v))


def main():
    before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    doc = ET.parse(SOURCE)
    diagram = doc.find("diagram")
    diagram.set("id", "arepo-main-loop-functions")
    diagram.set("name", "AREPO main loop - functions")
    model = diagram.find("mxGraphModel")
    assert model is not None, "Use the uncompressed native source"
    model.attrib.update(dx="1400", dy="1280", pageWidth="1400", pageHeight="1280", background="#FFFFFF")
    root = model.find("root")
    cells = {c.get("id"): c for c in root.findall("mxCell")}
    literal = ast.parse((HERE / "build_arepo_main_loop_flowchart.py").read_text())
    labels = next(ast.literal_eval(n.value) for n in literal.body if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == "LABELS" for t in n.targets))
    run_source = (HERE.parents[1] / "src/main/run.c").read_text()
    predict_source = (HERE.parents[1] / "src/time_integration/predict.c").read_text()
    for (key, rect, calls), (_, lines, _) in zip(BLOCKS, labels):
        cell = cells[key]
        geometry(cell, rect)
        description = "<br>".join(f"<b>{html.escape(s)}</b>" if s.startswith("RD:") else html.escape(s) for s in lines)
        # Soft break opportunities keep complete function identifiers editable.
        code = "<br>".join(html.escape(s).replace("_", "_<wbr>") for s in calls)
        cell.set("value", '<div style="font-size:14px;line-height:125%;">' + description + '</div>'
                 '<div style="height:9px;"></div>'
                 '<div style="font-family:Courier New;font-size:12px;line-height:135%;">' + code + '</div>')
        style_set(cell, fontSize="14", spacing="10")
        for call in calls:
            for name in re.findall(r"\b([A-Za-z_]\w*)\(", call):
                assert re.search(r"\b" + re.escape(name) + r"\s*\(", run_source + predict_source), name

    geometry(cells["title"], (38, 20, 1100, 34))
    cells["title"].set("value", "AREPO main loop - function names")
    style_set(cells["title"], fontSize="28")
    geometry(cells["subtitle"], (38, 59, 1300, 20))
    cells["subtitle"].set("value", "The same loop with current function calls; static RD predictor and corrector at the two hydro hooks")
    style_set(cells["subtitle"], fontSize="14")
    for i, x in enumerate((38, 230, 470, 680, 940)):
        geometry(cells[f"legend-dot-{i}"], (x, 94, 10, 10))
        geometry(cells[f"legend-text-{i}"], (x + 19, 90, 350 if i == 4 else 215, 18))
        style_set(cells[f"legend-text-{i}"], fontSize="12")
    geometry(cells["frame"], (26, 125, 1348, 1120))
    geometry(cells["loop-ribbon"], (26, 125, 24, 1120))
    geometry(cells["loop-label"], (-112, 673, 300, 24))
    cells["loop-label"].set("value", "run(): while (1)")
    style_set(cells["loop-label"], fontSize="13")
    geometry(cells["scope"], (80, 1165, 1250, 20))
    geometry(cells["scope-conditional"], (80, 1189, 1250, 20))
    for key in ("scope", "scope-conditional"):
        style_set(cells[key], fontSize="12")
    note = ET.SubElement(root, "mxCell", id="function-scope", value="Selected calls from src/main/run.c; optional operations depend on configuration. mark_active_timebins() is called inside find_next_sync_point().",
                         vertex="1", parent="1", style=cells["scope"].get("style"))
    ET.SubElement(note, "mxGeometry", x="80", y="1213", width="1250", height="20", **{"as": "geometry"})
    style_set(note, fontSize="11")

    routes = {
        "flow-05": [(480, 862.5), (480, 275)],
        "flow-10": [(910, 1050), (910, 275)],
        "flow-14": [(1340, 867.5), (1340, 197.5)],
    }
    for edge in [c for c in cells.values() if c.get("edge") == "1"]:
        g = edge.find("mxGeometry")
        for child in list(g):
            g.remove(child)
        if edge.get("id") == "entry-from-setup":
            ET.SubElement(g, "mxPoint", x="265", y="125", **{"as": "sourcePoint"})
        if edge.get("id") in routes:
            arr = ET.SubElement(g, "Array", **{"as": "points"})
            for x, y in routes[edge.get("id")]:
                ET.SubElement(arr, "mxPoint", x=str(x), y=str(y))
        style_set(edge, strokeWidth="1.2", endSize="9")

    ET.indent(doc, space="  ")
    doc.write(OUTPUT, encoding="utf-8", xml_declaration=True)
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == before
    print(OUTPUT)
    print("Concise source unchanged; 14 process blocks with verified function names.")


if __name__ == "__main__":
    main()
