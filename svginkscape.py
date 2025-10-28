import xml.etree.ElementTree as ET
from pathlib import Path

INPUT_FOLDER = r"C:\Users\kschi\OneDrive\Desktop\Placards\SVGs"
OUTPUT_FILE = r"C:\Users\kschi\OneDrive\Desktop\Placards\Merged\placards_sheet.svg"

PAGE_W, PAGE_H = 8.5 * 96, 11 * 96
CELL_W, CELL_H = 4 * 96, 4 * 96
MARGIN = 0.05 * 96
TARGET_WIDTH = 3.9 * 96
COLUMNS, ROWS = 4, 2

files = sorted(Path(INPUT_FOLDER).glob("*.svg"))[:8]
Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)

sheet = ET.Element("svg", xmlns="http://www.w3.org/2000/svg",
                   width=str(PAGE_W), height=str(PAGE_H))

for i, f in enumerate(files):
    tree = ET.parse(f)
    root = tree.getroot()

    # Wrap everything inside one <g> so text+diagram scale together
    wrapper = ET.Element("g")
    for child in list(root):
        wrapper.append(child)

    # Compute width from viewBox or attribute
    vb = root.get("viewBox")
    if vb:
        _, _, vb_w, vb_h = map(float, vb.split())
    else:
        vb_w = float(root.get("width", "0").replace("pt", "").replace("px", "") or 1)
        vb_h = float(root.get("height", "0").replace("pt", "").replace("px", "") or 1)

    scale = TARGET_WIDTH / vb_w

    col = i % COLUMNS
    row = i // COLUMNS
    x = col * CELL_W + MARGIN
    y = PAGE_H - ((row + 1) * CELL_H - MARGIN)

    g = ET.Element("g", transform=f"translate({x},{y}) scale({scale})")
    g.append(wrapper)
    sheet.append(g)

ET.ElementTree(sheet).write(OUTPUT_FILE, encoding="utf-8", xml_declaration=True)
print("✓ Merged:", OUTPUT_FILE)
