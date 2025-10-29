"""
SAFE TEST - Clean SVG Extraction
Removes page backgrounds and bounding boxes, keeps only placard content

USAGE:
1. Copy 1-2 PDFs to TEST_PDFs folder
2. Run this script
3. Check TEST_SVGs folder
4. Run svg_diagnostics.py on output
5. Share svgdiag.txt with Claude for fine-tuning
"""

import fitz  # PyMuPDF
from roboflow import Roboflow
import os
from pathlib import Path
import xml.etree.ElementTree as ET
import re

# ========== TEST CONFIG ==========
ROBOFLOW_API_KEY = "L93UjMpMcsqujZ2mRU6N"
WORKSPACE = "placardcleanup"
PROJECT = "placard_cleanup-imhpc"
VERSION = 4

TEST_INPUT = r"C:\Users\kschi\OneDrive\Desktop\Placards\TEST_PDFs"
TEST_OUTPUT = r"C:\Users\kschi\OneDrive\Desktop\Placards\TEST_SVGs"
TEMP_FOLDER = r"C:\Users\kschi\OneDrive\Desktop\Placards\PDFSVGTEMP"

CONFIDENCE_THRESHOLD = 40
DPI_FOR_DETECTION = 96

# Google Sheets
ENABLE_ADDRESS_LOOKUP = True
GOOGLE_CREDENTIALS = r"C:\Users\kschi\OneDrive\Desktop\Placards\Pys\google_credentials.json"
GOOGLE_SHEET_NAME = "Job Codes"
GOOGLE_WORKSHEET = "Sheet1"


def estimate_path_area(d):
    """
    Estimate path area from bounding box
    Used to filter out large rectangles (page backgrounds, borders)
    """
    if not d:
        return 0

    # Extract all numbers
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
        area = abs(width * height)

        return area
    except:
        return 0


def extract_clean_svg(pdf_path, bbox, output_path):
    """
    NEW APPROACH: Keep defs intact, filter paths by COORDINATES not area
    Remove paths that are outside the SVG viewBox bounds
    """
    print("  → Clean extraction (removing out-of-bounds paths)")

    pdf = fitz.open(pdf_path)
    page = pdf[0]

    crop_rect = fitz.Rect(bbox['x_min'], bbox['y_min'], bbox['x_max'], bbox['y_max'])
    page.set_cropbox(crop_rect)
    svg_content = page.get_svg_image()
    pdf.close()

    # Parse SVG
    root = ET.fromstring(svg_content)

    svg_width = float(root.get('width', '0').replace('pt', ''))
    svg_height = float(root.get('height', '0').replace('pt', ''))

    print(f"  → Placard size: {svg_width:.0f}x{svg_height:.0f}pt")

    # Get viewBox - this is our "in bounds" area
    original_viewBox = root.get('viewBox', f"0 0 {svg_width} {svg_height}")
    vb_parts = original_viewBox.split()
    vb_x = float(vb_parts[0]) if len(vb_parts) > 0 else 0
    vb_y = float(vb_parts[1]) if len(vb_parts) > 1 else 0
    vb_w = float(vb_parts[2]) if len(vb_parts) > 2 else svg_width
    vb_h = float(vb_parts[3]) if len(vb_parts) > 3 else svg_height

    # Add margin to viewBox to prevent cutoff
    margin = 2
    viewBox_x = vb_x - margin
    viewBox_y = vb_y - margin
    viewBox_w = vb_w + (margin * 2)
    viewBox_h = vb_h + (margin * 2)

    print(f"  → ViewBox bounds: x={vb_x}, y={vb_y}, w={vb_w}, h={vb_h}")

    stats = {'kept': 0, 'skipped': 0, 'skipped_meta': 0}

    def is_path_in_bounds(d):
        """Check if path coordinates are within viewBox"""
        if not d:
            return True  # Keep empty paths

        nums = re.findall(r'-?\d+\.?\d*', d)
        if len(nums) < 2:
            return True

        try:
            coords = [float(n) for n in nums]
            xs = coords[::2]
            ys = coords[1::2]

            if not xs or not ys:
                return True

            # Get path bounding box
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)

            # Allow 50% margin - if path center is way outside bounds, skip it
            # This catches page-size elements that extend far beyond the placard
            path_center_x = (min_x + max_x) / 2
            path_center_y = (min_y + max_y) / 2

            margin = 0.5  # 50% outside is OK

            x_in_bounds = (vb_x - vb_w * margin) < path_center_x < (vb_x + vb_w * (1 + margin))
            y_in_bounds = (vb_y - vb_h * margin) < path_center_y < (vb_y + vb_h * (1 + margin))

            return x_in_bounds and y_in_bounds
        except:
            return True  # Keep on error

    def process_group(parent_elem):
        """Recursively process group, filtering out-of-bounds paths"""
        new_group = ET.Element(parent_elem.tag, parent_elem.attrib)

        if parent_elem.text:
            new_group.text = parent_elem.text
        if parent_elem.tail:
            new_group.tail = parent_elem.tail

        for child in parent_elem:
            tag = child.tag.lower()

            # Recursively process groups
            if tag.endswith('g'):
                filtered_group = process_group(child)
                if len(filtered_group) > 0 or filtered_group.text:
                    new_group.append(filtered_group)
                continue

            # Filter paths by coordinates
            if tag.endswith('path'):
                d = child.get('d', '')
                if is_path_in_bounds(d):
                    new_group.append(child)
                    stats['kept'] += 1
                else:
                    stats['skipped'] += 1
                continue

            # Keep everything else (text, use, etc.)
            new_group.append(child)
            stats['kept'] += 1

        return new_group

    # Create clean SVG
    NS = "http://www.w3.org/2000/svg"
    XLINK = "http://www.w3.org/1999/xlink"

    clean_root = ET.Element(f'{{{NS}}}svg')
    clean_root.set('xmlns', NS)
    clean_root.set('xmlns:xlink', XLINK)
    clean_root.set('width', f"{svg_width}pt")
    clean_root.set('height', f"{svg_height}pt")
    clean_root.set('viewBox', f"{viewBox_x} {viewBox_y} {viewBox_w} {viewBox_h}")

    # Copy elements
    for elem in root:
        tag = elem.tag.lower()

        # Keep ALL defs completely untouched (fonts, clipPaths, everything!)
        if tag.endswith('defs'):
            clean_root.append(elem)
            stats['kept'] += 1
            continue

        # Skip metadata
        if tag.endswith(('metadata', 'title', 'desc')):
            stats['skipped_meta'] += 1
            continue

        # Process groups recursively
        if tag.endswith('g'):
            filtered_group = process_group(elem)
            if len(filtered_group) > 0:
                clean_root.append(filtered_group)
                stats['kept'] += 1
            continue

        # Keep other root elements
        clean_root.append(elem)
        stats['kept'] += 1

    print(f"  → Kept {stats['kept']} elements, filtered {stats['skipped']} out-of-bounds paths")

    tree = ET.ElementTree(clean_root)
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    return True


def add_address_to_svg(svg_path, address_text):
    """Add address text (9pt)"""
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()

        width = float(root.get('width', '0').replace('pt', ''))
        height = float(root.get('height', '0').replace('pt', ''))

        if width == 0 or height == 0:
            viewbox = root.get('viewBox', '0 0 0 0').split()
            width = float(viewbox[2])
            height = float(viewbox[3])

        text_elem = ET.Element('{http://www.w3.org/2000/svg}text')
        text_elem.set('x', str(width / 2))
        text_elem.set('y', str(height + 15))
        text_elem.set('text-anchor', 'middle')
        text_elem.set('font-family', 'Arial')
        text_elem.set('font-size', '9')
        text_elem.set('fill', 'black')
        text_elem.text = address_text

        if root.get('viewBox'):
            viewbox = root.get('viewBox').split()
            new_height = float(viewbox[3]) + 25
            root.set('viewBox', f"{viewbox[0]} {viewbox[1]} {viewbox[2]} {new_height}")

        if root.get('height'):
            new_height = height + 25
            root.set('height', f"{new_height}pt")

        root.append(text_elem)
        tree.write(svg_path, encoding='utf-8', xml_declaration=True)
        return True
    except Exception as e:
        print(f"  ⚠ Could not add address: {e}")
        return False


def has_address_text(pdf_path, bbox):
    """Check if PDF already has address"""
    try:
        doc = fitz.open(pdf_path)
        page = doc[0]
        crop_rect = fitz.Rect(bbox['x_min'], bbox['y_min'], bbox['x_max'], bbox['y_max'])
        text = page.get_text("text", clip=crop_rect)
        doc.close()

        address_pattern = r"\d{1,5}\s+[A-Za-z]+\s+(St|Ave|Rd|Cir|Dr|Pl|Way|Ct|Ln|Blvd)"
        return bool(re.search(address_pattern, text, re.IGNORECASE))
    except:
        return False


# Helper functions
def initialize_roboflow():
    print("→ Initializing Roboflow...")
    rf = Roboflow(api_key=ROBOFLOW_API_KEY)
    workspace = rf.workspace(WORKSPACE)
    project = workspace.project(PROJECT)
    version = project.version(VERSION)
    model = version.model
    print(f"✓ Roboflow v{VERSION} ready")
    return model


def pdf_to_preview_image(pdf_path, output_path, dpi=96):
    pdf = fitz.open(pdf_path)
    page = pdf[0]
    mat = fitz.Matrix(dpi/72, dpi/72)
    pix = page.get_pixmap(matrix=mat)
    pix.save(output_path)
    page_width = page.rect.width
    page_height = page.rect.height
    img_width = pix.width
    img_height = pix.height
    pdf.close()
    return page_width, page_height, img_width, img_height


def get_bounding_box(model, image_path, confidence_threshold=40):
    result = model.predict(image_path, confidence=confidence_threshold).json()
    if not result.get('predictions'):
        return None
    pred = result['predictions'][0]
    x_center = pred['x']
    y_center = pred['y']
    width = pred['width']
    height = pred['height']
    return {
        'x_min': x_center - (width / 2),
        'y_min': y_center - (height / 2),
        'x_max': x_center + (width / 2),
        'y_max': y_center + (height / 2),
        'confidence': pred['confidence']
    }


def convert_image_coords_to_pdf(bbox, page_width, page_height, img_width, img_height):
    x_scale = page_width / img_width
    y_scale = page_height / img_height
    return {
        'x_min': bbox['x_min'] * x_scale,
        'y_min': bbox['y_min'] * y_scale,
        'x_max': bbox['x_max'] * x_scale,
        'y_max': bbox['y_max'] * y_scale
    }


def test_process_pdf(pdf_path, model, address_lookup):
    """Process a single test PDF"""
    job_code = Path(pdf_path).stem

    print(f"\n{'='*60}")
    print(f"TESTING: {job_code}.pdf")
    print(f"{'='*60}")

    temp_image = os.path.join(TEMP_FOLDER, f"{job_code}_test_preview.png")
    print("→ Creating preview...")
    page_w, page_h, img_w, img_h = pdf_to_preview_image(pdf_path, temp_image, DPI_FOR_DETECTION)

    print("→ Running detection...")
    bbox = get_bounding_box(model, temp_image, CONFIDENCE_THRESHOLD)

    if not bbox:
        print("✗ No detection found")
        os.remove(temp_image)
        return False

    print(f"✓ Detection (confidence: {bbox['confidence']:.2%})")

    pdf_bbox = convert_image_coords_to_pdf(bbox, page_w, page_h, img_w, img_h)

    output_svg = os.path.join(TEST_OUTPUT, f"{job_code}_clean.svg")
    extract_clean_svg(pdf_path, pdf_bbox, output_svg)

    # Add address
    if address_lookup:
        if has_address_text(pdf_path, pdf_bbox):
            print("  ✓ Address already present")
        else:
            address = address_lookup.get_address(job_code)
            if address:
                print(f"  → Adding: {address}")
                add_address_to_svg(output_svg, address)

    print(f"✓ SAVED: {output_svg}")
    os.remove(temp_image)
    return True


def main():
    print("\n" + "="*60)
    print("CLEAN SVG EXTRACTION TEST")
    print("="*60)

    Path(TEST_OUTPUT).mkdir(parents=True, exist_ok=True)
    Path(TEMP_FOLDER).mkdir(parents=True, exist_ok=True)

    model = initialize_roboflow()

    # Address lookup
    address_lookup = None
    if ENABLE_ADDRESS_LOOKUP:
        try:
            import gspread
            from google.oauth2.service_account import Credentials

            class GoogleSheetsLookup:
                def __init__(self):
                    self.cache = {}

                def connect(self):
                    try:
                        scopes = ['https://www.googleapis.com/auth/spreadsheets',
                                  'https://www.googleapis.com/auth/drive']
                        creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS, scopes=scopes)
                        client = gspread.authorize(creds)
                        sheet = client.open(GOOGLE_SHEET_NAME).worksheet(GOOGLE_WORKSHEET)
                        for row in sheet.get_all_values()[1:]:
                            if len(row) >= 2:
                                self.cache[row[0].strip().upper()] = row[1].strip()
                        print(f"✓ Loaded {len(self.cache)} addresses\n")
                        return True
                    except Exception as e:
                        print(f"⚠ Address lookup disabled: {e}\n")
                        return False

                def get_address(self, code):
                    return self.cache.get(code.strip().upper())

            address_lookup = GoogleSheetsLookup()
            address_lookup.connect()
        except:
            pass

    test_pdfs = list(Path(TEST_INPUT).glob("*.pdf"))

    if not test_pdfs:
        print(f"\n✗ No PDFs in {TEST_INPUT}")
        print("\nCreate TEST_PDFs folder and copy 1-2 PDFs there")
        return

    print(f"Found {len(test_pdfs)} test PDF(s)\n")

    success = 0
    for pdf in test_pdfs:
        try:
            if test_process_pdf(str(pdf), model, address_lookup):
                success += 1
        except Exception as e:
            print(f"✗ ERROR: {e}")

    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    print(f"✓ Success: {success}/{len(test_pdfs)}")
    print(f"\nResults: {TEST_OUTPUT}")
    print("\nNEXT STEPS:")
    print("1. Open SVGs in Inkscape - check content")
    print("2. Run: python svg_diagnostics.py")
    print("3. Share svgdiag.txt for fine-tuning")


if __name__ == "__main__":
    main()
