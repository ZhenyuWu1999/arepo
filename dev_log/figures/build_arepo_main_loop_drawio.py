#!/usr/bin/env python3
"""Rebuild the revised flowchart as native, connected draw.io objects.

Reads the existing PDF builder's literal labels without importing its PDF
dependencies. Writes a separate draw.io source; never modifies either PDF.
Manual edits should be made in a copy: rerunning this builder replaces its output.
"""

import ast
import hashlib
import html
from pathlib import Path
import xml.etree.ElementTree as ET


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "Arepo_flowchart_main_loop_RD_20260914.drawio"
PDF = HERE.parents[1] / "output/pdf/Arepo_flowchart_main_loop_RD_20260914.pdf"
PDF_SHA = "718c231c340926e239f2fe7c703b422038622ed40a303534203fa7444f9b1e15"


def main():
    before = hashlib.sha256(PDF.read_bytes()).hexdigest()
    assert before == PDF_SHA, "Review changed PDF before rebuilding its editable source"
    tree = ast.parse((HERE / "build_arepo_main_loop_flowchart.py").read_text())
    labels = next(ast.literal_eval(node.value) for node in tree.body
                  if isinstance(node, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == "LABELS" for t in node.targets))
    document = ET.Element("mxfile", host="Electron", agent="AREPO-RD native diagram builder",
                          version="29.0.0", type="device", compressed="false")
    diagram = ET.SubElement(document, "diagram", id="arepo-main-loop-rd", name="AREPO main loop")
    model = ET.SubElement(diagram, "mxGraphModel", dx="884", dy="822", grid="0",
                          gridSize="10", guides="1", tooltips="1", connect="1", arrows="1",
                          fold="1", page="1", pageScale="1", pageWidth="884", pageHeight="822",
                          background="#FFFFFF", math="0", shadow="0")
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", id="0")
    for layer, name in [("1", "Frame and notes"), ("connections", "Flow connectors"),
                        ("process", "Process blocks")]:
        ET.SubElement(root, "mxCell", id=layer, value=name, parent="0")

    def vertex(key, value, x, y, w, h, style, parent="1"):
        cell = ET.SubElement(root, "mxCell", id=key, value=value,
                             style=style, vertex="1", parent=parent)
        ET.SubElement(cell, "mxGeometry", x=f"{x:g}", y=f"{y:g}",
                      width=f"{w:g}", height=f"{h:g}", **{"as": "geometry"})
        return cell

    text_style = ("text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;"
                  "whiteSpace=wrap;rounded=0;fontFamily=Arial;fontColor=#303B47;spacing=0;")
    vertex("title", "AREPO main loop", 38, 15, 650, 27, text_style + "fontSize=23;fontStyle=1;")
    vertex("subtitle", "RD predictor and corrector at the two hydrodynamic update points",
           38, 45, 808, 16, text_style + "fontSize=11.5;")
    legend = [(38, "#4397FF", "Timesteps", 110), (166, "#3FB8B9", "Domain / mesh", 135),
              (330, "#FC9432", "Fluid state", 110), (465, "#FF8F8F", "Hydrodynamics", 160),
              (644, "#E08FFF", "Gravity / sources (optional)", 200)]
    for i, (x, color, label, width) in enumerate(legend):
        vertex(f"legend-dot-{i}", "", x, 69, 8, 8,
               f"ellipse;fillColor={color};strokeColor=none;")
        vertex(f"legend-text-{i}", label, x + 15, 66, width, 15, text_style + "fontSize=10;")
    vertex("frame", "", 23.6, 92.5, 835.8, 684.6,
           "rounded=0;fillColor=none;strokeColor=#505862;strokeWidth=0.7;connectable=0;")
    vertex("loop-ribbon", "", 23.6, 92.5, 19.8, 684.6,
           "rounded=0;fillColor=#69ACF6;strokeColor=#505862;strokeWidth=0.7;")
    vertex("loop-label", "Main loop", -116.5, 424.8, 300, 20,
           text_style + "align=center;rotation=270;fontColor=#FFFFFF;fontSize=10.5;fontStyle=1;")
    vertex("scope", "RD labels: static N/LDA with split equal or hierarchical timesteps.",
           76, 733, 730, 15, text_style + "fontSize=10;")
    vertex("scope-conditional", "Mesh motion and gravity / source terms are conditional; static RD keeps the vertices fixed.",
           76, 748, 754, 15, text_style + "fontSize=10;")

    ids = ["outputs", "node-timebins", "sources-first", "gradients-first", "vertex-velocity",
           "exchange-predictor", "rd-predictor", "next-sync", "active-nodes", "domain-mesh",
           "exchange-corrector", "rd-corrector", "recover-primitives", "sources-second"]
    fills = ["#707782", "#4097FF", "#E08FFF", "#FF9429", "#3FB8B9", "#FF9429",
             "#FF8F8F", "#4097FF", "#4097FF", "#3FB8B9", "#FF9429", "#FF8F8F",
             "#FF9429", "#E08FFF"]
    boxes = {}
    for key, fill, (rect, lines, size) in zip(ids, fills, labels):
        x0, y0, x1, y1 = rect
        boxes[key] = (x0 - 14, y0 - 492, x1 - x0, y1 - y0)
        body = "<div style=\"line-height:132%;\">" + "<br>".join(
            f"<b>{html.escape(line)}</b>" if line.startswith("RD:") else html.escape(line)
            for line in lines) + "</div>"
        rounded = 0 if key.startswith("sources-") else 1
        style = (f"rounded={rounded};arcSize=8;whiteSpace=wrap;html=1;fillColor={fill};"
                 f"strokeColor=none;fontColor=#FFFFFF;fontSize={size};fontFamily=Arial;"
                 "align=center;verticalAlign=middle;spacing=5;overflow=visible;shadow=0;")
        vertex(key, body, *boxes[key], style, parent="process")

    def edge(key, source, target, exit_xy=(0.5, 1), entry_xy=(0.5, 0), points=(), start=None):
        style = ("edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;"
                 "endArrow=block;endFill=1;endSize=7;strokeColor=#505862;strokeWidth=0.8;"
                 f"exitX={exit_xy[0]};exitY={exit_xy[1]};exitDx=0;exitDy=0;"
                 f"entryX={entry_xy[0]};entryY={entry_xy[1]};entryDx=0;entryDy=0;")
        attrs = dict(id=key, value="", style=style, edge="1", parent="connections", target=target)
        if source:
            attrs["source"] = source
        cell = ET.SubElement(root, "mxCell", **attrs)
        geom = ET.SubElement(cell, "mxGeometry", relative="1", **{"as": "geometry"})
        if start:
            ET.SubElement(geom, "mxPoint", x=str(start[0]), y=str(start[1]), **{"as": "sourcePoint"})
        if points:
            array = ET.SubElement(geom, "Array", **{"as": "points"})
            for x, y in points:
                ET.SubElement(array, "mxPoint", x=str(x), y=str(y))

    routes = {
        ("vertex-velocity", "exchange-predictor"): ((1, .5), (0, .5), [(265, 543.18), (265, 183.18)]),
        ("domain-mesh", "exchange-corrector"): ((1, .5), (0, .5), [(546, 678.18), (546, 183.18)]),
        ("sources-second", "outputs"): ((1, .5), (1, .5), [(807.5, 544.46), (807.5, 138)]),
    }
    for i, source in enumerate(ids):
        target = ids[(i + 1) % len(ids)]
        exit_xy, entry_xy, points = routes.get((source, target), ((.5, 1), (.5, 0), []))
        edge(f"flow-{i+1:02d}", source, target, exit_xy, entry_xy, points)
    edge("entry-from-setup", None, "outputs", start=(149.98, 92.5))

    ET.indent(document, space="  ")
    ET.ElementTree(document).write(OUTPUT, encoding="utf-8", xml_declaration=True)
    # Verify actual node/edge semantics, not just a visually similar PDF image.
    check = ET.parse(OUTPUT)
    cells = check.findall(".//mxCell")
    cell_ids = {cell.get("id") for cell in cells}
    stages = [c for c in cells if c.get("vertex") == "1" and c.get("parent") == "process"]
    connections = [c for c in cells if c.get("edge") == "1"]
    assert len(stages) == 14 and len(connections) == 15
    assert all(c.get("source") in cell_ids and c.get("target") in cell_ids
               for c in connections if c.get("id") != "entry-from-setup")
    assert not any("image=" in c.get("style", "") for c in cells)
    assert hashlib.sha256(PDF.read_bytes()).hexdigest() == before
    print(f"{OUTPUT}\n14 editable process blocks; 14 connected cycle edges plus one entry arrow.")


if __name__ == "__main__":
    main()
