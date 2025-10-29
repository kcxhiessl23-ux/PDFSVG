"""
Debug script to show SVG structure
Run this AFTER test_clean_extraction.py to see what's in the cleaned SVG
"""
import xml.etree.ElementTree as ET
import re
from pathlib import Path

def estimate_path_area(d):
    if not d:
        return 0
    nums = re.findall(r'-?\d+\.?\d*', d)
    if len(nums) < 4:
        return 0
    try:
        coords = [float(n) for n in nums]
        xs = coords[::2]
        ys = coords[1::2]
        if not xs or not ys:
            return 0
        width = max(xs) - min(xs)
        height = max(ys) - min(ys)
        return abs(width * height)
    except:
        return 0

def show_structure(elem, indent=0, parent_chain=""):
    """Recursively show SVG structure with areas"""
    tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
    id_str = f" id='{elem.get('id')}'" if elem.get('id') else ""

    # Show area for paths
    area_str = ""
    if tag == 'path':
        d = elem.get('d', '')
        area = estimate_path_area(d)
        if area > 1000:  # Only show large areas
            area_str = f" [AREA: {area:.0f}]"

    print(f"{'  ' * indent}<{tag}{id_str}>{area_str}")

    for child in elem:
        show_structure(child, indent + 1, f"{parent_chain}/{tag}")

# Find cleaned SVG
TEST_OUTPUT = r"C:\Users\kschi\OneDrive\Desktop\Placards\TEST_SVGs"
svg_files = list(Path(TEST_OUTPUT).glob("*_clean.svg"))

if not svg_files:
    print("No cleaned SVG files found!")
    print(f"Looking in: {TEST_OUTPUT}")
else:
    for svg_file in svg_files[:1]:  # Just show first one
        print(f"\n{'='*60}")
        print(f"STRUCTURE OF: {svg_file.name}")
        print(f"{'='*60}\n")

        tree = ET.parse(svg_file)
        root = tree.getroot()

        show_structure(root)

        print(f"\n{'='*60}")
        print("LEGEND:")
        print("  Large areas (>1000) are shown in brackets")
        print("  Look for paths with [AREA: xxxxx] inside clipPaths")
        print(f"{'='*60}")
