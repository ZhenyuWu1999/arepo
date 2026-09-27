#!/usr/bin/env python3
"""Copy Zhenyu's edited figure and update the common RD hook annotations.

The input and any existing output are never overwritten. Number badges are
children of their process boxes, so moving a box in draw.io moves its number.
"""
import argparse
import hashlib
import html
from pathlib import Path
import re
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "Arepo_flowchart_main_loop_RD_functions_20260914.drawio"
SOURCE_SHA = "645d20cf7045140d18e680f2c7904eac1acc5f91eadf18fdb55a3fe3fdd651d6"
OUTPUT = HERE / "Arepo_flowchart_main_loop_RD_functions_reviewed_20260914.drawio"
ORDER = ["outputs", "node-timebins", "sources-first", "gradients-first", "vertex-velocity",
         "exchange-predictor", "rd-predictor", "next-sync", "active-nodes", "domain-mesh",
         "exchange-corrector", "rd-corrector", "recover-primitives", "sources-second"]


def label(description, calls, left=False):
    # Preserve complete identifiers; allow native HTML line wrapping at '_'.
    code = "<br>".join(html.escape(line).replace("_", "_<wbr>").replace("  ", "&nbsp;&nbsp;")
                       for line in calls)
    align = "text-align:left;margin-left:12px;" if left else ""
    return ('<div style="font-size:14px;line-height:125%;">' + description + '</div>'
            '<div style="height:9px;"></div>'
            '<div style="font-family:Courier New;font-size:12px;line-height:135%;' + align + '">'
            + code + '</div>')


def main(output):
    before = SOURCE.read_bytes()
    assert hashlib.sha256(before).hexdigest() == SOURCE_SHA, "Input changed: review the new manual edits first"
    doc = ET.ElementTree(ET.fromstring(before))
    diagram = doc.find("diagram")
    diagram.set("id", "arepo-main-loop-reviewed")
    diagram.set("name", "AREPO main loop - static and equal ALE")
    model = diagram.find("mxGraphModel")
    model.set("background", "#FFFFFF")
    root = model.find("root")
    cells = {c.get("id"): c for c in root.findall("mxCell")}
    assert [c.get("id") for c in cells.values() if c.get("parent") == "process"] == ORDER

    cells["subtitle"].set("value", "Common main-loop hooks for static and moving RD; numbered blocks for the Chapter 4 discussion")
    edits = {
        "rd-predictor": ("FV: first flux contribution<br><b>RD: begin step</b>", [
            "FV: compute_interface_fluxes(&Mesh)",
            "RD: rd_step_begin(&Mesh)",
            "  Static: compute_residuals(&Mesh,",
            "            RD_RK_STAGE_PREDICTOR)",
            "  Equal ALE: record endpoint; no sweep",
        ], True),
        "rd-corrector": ("FV: second flux contribution<br><b>RD: end step</b>", [
            "FV: compute_interface_fluxes(&Mesh)",
            "RD: rd_step_end(&Mesh)",
            "  Static: compute_residuals(&Mesh,",
            "            RD_RK_STAGE_CORRECTOR)",
            "  Equal ALE: compute_residuals(&Mesh)",
            "             (predictor + corrector)",
        ], True),
        "active-nodes": ("Build active-node lists;<br>drift synchronized nodes<br>to the current time", [
            "make_list_of_active_particles()",
            "  calls drift_particle(i, All.Ti_Current)",
        ], False),
        "domain-mesh": ("Domain / tree update (when due);<br>mesh rebuild (once per moving step)", [
            "[when domain update is due]",
            "drift_all_particles()",
            "domain_Decomposition(); ngb_treebuild(NumGas)",
            "[moving: each step; static: when required]",
            "create_mesh(); mesh_setup_exchange()",
        ], False),
    }
    source = "\n".join((HERE.parents[1] / name).read_text() for name in (
        "src/main/run.c", "src/time_integration/predict.c", "src/hydro/residual_distribution_solver.c"))
    for key, (description, calls, left) in edits.items():
        cells[key].set("value", label(description, calls, left))
        for line in calls:
            for name in re.findall(r"\b([A-Za-z_]\w*)\(", line):
                assert re.search(r"\b" + re.escape(name) + r"\s*\(", source), name

    cells["scope"].set("value", "RD dispatch shown: static N/LDA split-equal or hierarchy; moving N/LDA equal-step with RD_RK2_SPLIT_STAGES.")
    cells["scope-conditional"].set("value", "Static meshes are reused unless domain decomposition requires rebuilding. Gravity / source terms depend on configuration.")
    cells["function-scope"].set("value", "Selected calls from run.c and the RD hooks; initialization and restart setup omitted. Equal ALE performs both sweeps on the single rebuilt mesh.")

    for number, key in enumerate(ORDER, 1):
        badge = ET.SubElement(root, "mxCell", id=f"step-number-{number:02d}", value=str(number),
                              vertex="1", parent=key,
                              style="ellipse;html=1;fillColor=#FFFFFF;strokeColor=none;fontColor=#364152;"
                                    "fontSize=11;fontStyle=1;align=center;verticalAlign=middle;resizable=0;")
        ET.SubElement(badge, "mxGeometry", x="7", y="7", width="22", height="22", **{"as": "geometry"})

    # Keep the user's gravity labels, every process rectangle, and every edge.
    old = {c.get("id"): c for c in ET.fromstring(before).findall("diagram/mxGraphModel/root/mxCell")}
    for key in ORDER:
        assert ET.tostring(cells[key].find("mxGeometry")) == ET.tostring(old[key].find("mxGeometry"))
    for key in ("sources-first", "sources-second"):
        assert ET.tostring(cells[key]) == ET.tostring(old[key])
    edges = [c for c in cells.values() if c.get("edge") == "1"]
    assert len(edges) == 15
    for edge in edges:
        assert ET.tostring(edge) == ET.tostring(old[edge.get("id")])
        assert edge.get("target") in ORDER and (edge.get("source") in ORDER or edge.get("id") == "entry-from-setup")
    ET.indent(doc, space="  ")
    with output.open("xb") as stream:
        doc.write(stream, encoding="utf-8", xml_declaration=True)
    assert SOURCE.read_bytes() == before
    print(output)
    print("Preserved the manual input, geometry and connectors; 14 numbered process boxes.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    main(parser.parse_args().output)
