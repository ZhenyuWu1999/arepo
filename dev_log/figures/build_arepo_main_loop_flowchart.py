#!/usr/bin/env python3
"""Revise a separate copy of Zhenyu's 2023 flowchart; retain its vector layout.

Only the while-loop body is placed on the new page. Original source is read
only and its checksum is verified. Node wording is editable in LABELS below.
Run with the bundled Python (pypdf + reportlab).
"""

import hashlib
import io
import json
import shutil
from pathlib import Path

from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import ContentStream, RectangleObject
from pypdf._text_extraction import mult
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

REPO = Path(__file__).resolve().parents[2]
QA = REPO / "tmp/pdfs/arepo_main_loop_20260914"
OUTPUT = REPO / "output/pdf/Arepo_flowchart_main_loop_RD_20260914.pdf"
ORIGINAL = Path("/Users/zhenyuwu/Desktop/MyThesis/useful_resources/Arepo_document/Arepo_flowchart.pdf")
ORIGINAL_SHA256 = "48d19858dcd4d93a478c4dd2105d4556803a78e7c01cec3132f962dca7af5d9a"

# Original page coordinates, with y measured downwards from its upper edge.
# The rectangles and connecting arrows themselves remain the original vectors.
LABELS = [
    ((112.5, 603, 215.46, 657), ["Write outputs;", "stop at final time"], 11.5),
    ((80.06, 675, 254.57, 801.94), ["Select hydro timesteps", "from the CFL condition;", "assign node timebins", "(equal or hierarchical)"], 12),
    ((95.44, 820.35, 239.22, 897.44), ["Gravity / source terms:", "first half-step", "(if enabled)"], 11.5),
    ((103.95, 927, 230.67, 981.36), ["Exchange primitives;", "calculate gradients"], 11.5),
    ((101.43, 1008, 233.19, 1062.36), ["Set vertex velocities;", "update neighbour tree"], 11.3),
    ((324, 648, 495, 702.36), ["Exchange primitives,", "vertex velocities", "and gradients"], 11.5),
    ((322.2, 732.6, 496.71, 845.06), ["FV: first flux contribution", "RD: predictor", "Distribute triangle residuals;", "accumulate nodal", "conserved increments"], 11.3),
    ((305.24, 871.65, 431.96, 998.6), ["Advance to the next", "synchronization time;", "mark active timebins"], 11.5),
    ((315, 1017, 486, 1114.92), ["Build active-node list;", "drift nodes to the", "current time"], 12),
    ((280.26, 1143, 520.74, 1197.36), ["Update domain / tree (when due);", "construct or rebuild mesh (if needed)"], 11.5),
    ((603, 648, 785.48, 702.36), ["Exchange primitives", "and gradients"], 12),
    ((599.85, 732.6, 787.82, 845.06), ["FV: second flux contribution", "RD: corrector", "Include the temporal residual;", "accumulate nodal", "conserved increments"], 11.3),
    ((607.5, 891, 780.8, 959.89), ["Recover primitives for", "synchronized nodes;", "close the hydro step"], 11.5),
    ((630, 999, 803.3, 1073.92), ["Gravity / source terms:", "second half-step", "(if enabled)"], 11.5),
]

PAGE_W, PAGE_H = 884, 822
ORIGINAL_H = 1302
TX, TY = -14, 12
WHITE = (1, 1, 1)
INK = (.19, .23, .28)
FONT_DIR = Path("/Users/zhenyuwu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/pdfjs-dist/standard_fonts")
pdfmetrics.registerFont(TTFont("FigureSans", str(FONT_DIR / "LiberationSans-Regular.ttf")))
pdfmetrics.registerFont(TTFont("FigureSans-Bold", str(FONT_DIR / "LiberationSans-Bold.ttf")))


def overlay():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(PAGE_W, PAGE_H))
    c.setTitle("AREPO main loop with static RD predictor and corrector")
    c.setAuthor("Zhenyu Wu; revision with Codex (GPT-6), 2026-09-14")
    c.setFillColorRGB(*INK)
    c.setFont("FigureSans-Bold", 23)
    c.drawString(38, 788, "AREPO main loop")
    c.setFont("FigureSans", 11.5)
    c.drawString(38, 768, "RD predictor and corrector at the two hydrodynamic update points")

    legend = [
        (38, (.2627, .5921, 1), "Timesteps"),
        (166, (.247, .7215, .7254), "Domain / mesh"),
        (330, (.9882, .5803, .196), "Fluid state"),
        (465, (1, .5607, .5607), "Hydrodynamics"),
        (644, (.8784, .5607, 1), "Gravity / sources (optional)"),
    ]
    for x, color, label in legend:
        c.setFillColorRGB(*color)
        c.circle(x+4, 749, 4, stroke=0, fill=1)
        c.setFillColorRGB(*INK)
        c.setFont("FigureSans", 10)
        c.drawString(x+15, 745.5, label)

    for rect, lines, size in LABELS:
        x0, y0, x1, y1 = rect
        center_x = (x0+x1)/2+TX
        center_y = ORIGINAL_H-(y0+y1)/2+TY
        leading = size*1.32
        baseline = center_y+(len(lines)-1)*leading/2-size*.35
        c.setFillColorRGB(*WHITE)
        for index, line in enumerate(lines):
            font = "FigureSans-Bold" if line.startswith("RD:") else "FigureSans"
            assert stringWidth(line, font, size) < x1-x0-10, line
            c.setFont(font, size)
            c.drawCentredString(center_x, baseline-index*leading, line)

    # Retain the original blue lane, with a short label replacing run()/while(1).
    c.saveState()
    c.translate(47.5+TX, ORIGINAL_H-(585+1268.6)/2+TY)
    c.rotate(90)
    c.setFillColorRGB(*WHITE)
    c.setFont("FigureSans-Bold", 10.5)
    c.drawCentredString(0, -3.7, "Main loop")
    c.restoreState()

    c.setFillColorRGB(*INK)
    c.setFont("FigureSans", 10)
    c.drawString(76, 79, "RD labels: static N/LDA with split equal or hierarchical timesteps.")
    c.drawString(76, 64, "Mesh motion and gravity / source terms are conditional; static RD keeps the vertices fixed.")
    c.save()
    buffer.seek(0)
    return PdfReader(buffer).pages[0]


def main():
    before = hashlib.sha256(ORIGINAL.read_bytes()).hexdigest()
    assert before == ORIGINAL_SHA256
    assert OUTPUT.resolve() != ORIGINAL.resolve()
    QA.mkdir(parents=True, exist_ok=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if not (QA / "original_copy.pdf").exists():
        shutil.copy2(ORIGINAL, QA / "original_copy.pdf")
    assert hashlib.sha256((QA / "original_copy.pdf").read_bytes()).hexdigest() == before
    provenance = dict(source=str(ORIGINAL), source_sha256=before, working_copy=str(OUTPUT))
    source_copy = PdfWriter(clone_from=QA / "original_copy.pdf")
    page = source_copy.pages[0]
    contents = ContentStream(page.get_contents(), source_copy)

    # The source encodes its white node lettering as paths and also has text
    # operators. Remove both forms; preserve the coloured nodes and grey arrows.
    # The old FV-only math labels are separate /Stamp annotations, removed
    # below; they would otherwise be copied by merge_transformed_page().
    fill = (0, 0, 0)
    matrix = [1, 0, 0, 1, 0, 0]
    stack = []
    path_points = []
    revised = []
    for arguments, operator in contents.operations:
        if operator == b"q":
            stack.append((fill, matrix[:]))
        elif operator == b"Q":
            fill, matrix = stack.pop()
        elif operator == b"cm":
            matrix = mult([float(v) for v in arguments], matrix)
        elif operator == b"rg":
            fill = tuple(float(x) for x in arguments)
        elif operator == b"g":
            fill = (float(arguments[0]),)*3
        elif operator in (b"m", b"l", b"c", b"y", b"v"):
            for index in range(0, len(arguments), 2):
                x, y = map(float, arguments[index:index+2])
                path_points.append((x*matrix[0]+y*matrix[2]+matrix[4],
                                    ORIGINAL_H-(x*matrix[1]+y*matrix[3]+matrix[5])))
        if operator in (b"Tj", b"TJ", b"'", b'"'):
            continue
        discard_side_box = False
        if operator in (b"f", b"f*", b"S", b"s", b"n", b"B", b"B*"):
            if path_points:
                x0 = min(x for x, y in path_points)
                x1 = max(x for x, y in path_points)
                y0 = min(y for x, y in path_points)
                y1 = max(y for x, y in path_points)
                # The side box and its short link are merged into the main
                # clock box. Keep the domain-return arrow behind it intact.
                discard_side_box = (449.5 < x0 < 451 and 575 < x1 < 577 and
                                    900 < y0 < 902 and 969 < y1 < 971)
                discard_side_box |= (431.5 < x0 < 451 and x1 < 451 and
                                     900 < y0 < 970 and y1-y0 < 1)
            path_points = []
        if discard_side_box or (operator in (b"f", b"f*") and all(abs(v-1)<1e-6 for v in fill)):
            revised.append(([], b"n"))
        else:
            revised.append((arguments, operator))
    contents.operations = revised
    page.replace_contents(contents)
    if "/Annots" in page:
        del page["/Annots"]
    # Isolate the original while-loop body; exclude initialization and setup.
    page.cropbox = RectangleObject((37.6, 32.9, 873.4, 717.5))
    writer = PdfWriter()
    target = writer.add_blank_page(PAGE_W, PAGE_H)
    target.merge_transformed_page(page, Transformation().translate(TX, TY))
    target.merge_page(overlay())
    writer.add_metadata({"/Title": "AREPO main loop with static RD predictor and corrector",
                         "/Author": "Zhenyu Wu; revision with Codex (GPT-6)",
                         "/Subject": "Loop-only revision of the March 2023 flowchart; static split equal and hierarchical RD"})
    with OUTPUT.open("wb") as f:
        writer.write(f)
    assert hashlib.sha256(ORIGINAL.read_bytes()).hexdigest() == before
    provenance.update(output=str(OUTPUT), output_sha256=hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
                      original_unchanged=True)
    (QA / "provenance.json").write_text(json.dumps(provenance, indent=2)+"\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
