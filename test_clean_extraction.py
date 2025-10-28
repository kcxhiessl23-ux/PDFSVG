"""
TEST SCRIPT - Clean SVG Extraction
Tests new method: Extract ONLY vectors inside bounding box

SAFE TESTING:
1. Copy 2-3 PDFs to TEST_PDFs folder
2. Run this script
3. Check TEST_SVGs folder
4. Compare in Glowforge
5. Main code stays untouched!
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

# TEST FOLDERS (separate from main processing!)
TEST_INPUT = r"C:\Users\kschi\OneDrive\Desktop\Placards\TEST_PDFs"
TEST_OUTPUT = r"C:\Users\kschi\OneDrive\Desktop\Placards\TEST_SVGs"
TEMP_FOLDER = r"C:\Users\kschi\OneDrive\Desktop\Placards\PDFSVGTEMP"

CONFIDENCE_THRESHOLD = 40
DPI_FOR_DETECTION = 96

# Google Sheets lookup (using existing setup)
ENABLE_ADDRESS_LOOKUP = True
GOOGLE_CREDENTIALS = r"C:\Users\kschi\OneDrive\Desktop\Placards\Pys\google_credentials.json"
GOOGLE_SHEET_NAME = "Job Codes"
GOOGLE_WORKSHEET = "Sheet1"


def extract_clean_svg(pdf_path, bbox, output_path):
    """
    NEW METHOD: Extract ONLY vectors inside bounding box
    Creates clean SVG from scratch with only label content

    Args:
        pdf_path: Original PDF
        bbox: Bounding box dict (x_min, y_min, x_max, y_max in PDF points)
        output_path: Where to save clean SVG
    """
    print("  → Using CLEAN EXTRACTION method (only vectors in bbox)")

    pdf = fitz.open(pdf_path)
    page = pdf[0]

    # Crop to exact bbox
    crop_rect = fitz.Rect(bbox['x_min'], bbox['y_min'], bbox['x_max'], bbox['y_max'])
    page.set_cropbox(crop_rect)

    # Get SVG (still contains ALL vectors, but we'll parse and filter)
    svg_content = page.get_svg_image()
    pdf.close()

    # Parse the SVG
    root = ET.fromstring(svg_content)

    # Get SVG dimensions (this is our bbox size)
    svg_width = float(root.get('width', '0').replace('pt', ''))
    svg_height = float(root.get('height', '0').replace('pt', ''))

    print(f"  → SVG size: {svg_width:.1f}x{svg_height:.1f}pt")

    # Create NEW clean SVG with ONLY content inside viewBox
    clean_root = ET.Element('svg',
                            xmlns="http://www.w3.org/2000/svg",
                            width=f"{svg_width}pt",
                            height=f"{svg_height}pt",
                            viewBox=f"0 0 {svg_width} {svg_height}")

    # Copy elements that are within bounds
    # Strategy: Keep elements whose coordinates are inside the viewBox
    elements_kept = 0
    elements_skipped = 0

    for elem in root:
        # Skip metadata/defs
        if elem.tag.endswith(('defs', 'metadata')):
            continue

        # Check if element is in bounds
        if is_element_in_bounds(elem, svg_width, svg_height):
            clean_root.append(elem)
            elements_kept += 1
        else:
            elements_skipped += 1

    print(f"  → Kept {elements_kept} elements, skipped {elements_skipped} out-of-bounds")

    # Write clean SVG
    tree = ET.ElementTree(clean_root)
    tree.write(output_path, encoding='utf-8', xml_declaration=True)

    return True


def is_element_in_bounds(elem, width, height):
    """
    Check if an SVG element is within the viewBox bounds

    Simple heuristic: If it has coordinates, check if they're reasonable.
    If it's a group or has no clear coordinates, keep it (safe default).
    """
    tag = elem.tag.lower()

    # Always keep text elements (labels)
    if tag.endswith('text'):
        return True

    # Always keep groups (they contain multiple things)
    if tag.endswith('g'):
        return True

    # For paths, check if coordinates seem in bounds
    if tag.endswith('path'):
        d = elem.get('d', '')
        if not d:
            return True  # Empty path, keep it

        # Extract numbers from path
        numbers = re.findall(r'-?\d+\.?\d*', d)
        if not numbers:
            return True

        # Check if any coordinate is way outside bounds (indicates page background)
        for num_str in numbers[:10]:  # Check first 10 coords
            try:
                num = float(num_str)
                # If coordinate is more than 2x the viewport, probably outside
                if abs(num) > max(width, height) * 2:
                    return False
            except:
                pass

        return True

    # For rects, check position
    if tag.endswith('rect'):
        try:
            x = float(elem.get('x', '0'))
            y = float(elem.get('y', '0'))
            w = float(elem.get('width', '0'))
            h = float(elem.get('height', '0'))

            # If rect is way outside viewport, skip it
            if x < -width or y < -height or x > width * 2 or y > height * 2:
                return False

            # If rect is the full page size, it's probably background
            if w > width * 1.5 or h > height * 1.5:
                return False
        except:
            pass

        return True

    # Default: keep it (safe)
    return True


def add_address_to_svg(svg_path, address_text):
    """Add address text to bottom of SVG (9pt font)"""
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()

        width = float(root.get('width', '0').replace('pt', ''))
        height = float(root.get('height', '0').replace('pt', ''))

        if width == 0 or height == 0:
            viewbox = root.get('viewBox', '0 0 0 0').split()
            width = float(viewbox[2])
            height = float(viewbox[3])

        # Create text element
        text_elem = ET.Element('{http://www.w3.org/2000/svg}text')
        text_elem.set('x', str(width / 2))
        text_elem.set('y', str(height + 15))
        text_elem.set('text-anchor', 'middle')
        text_elem.set('font-family', 'Arial')
        text_elem.set('font-size', '9')
        text_elem.set('fill', 'black')
        text_elem.text = address_text

        # Extend viewBox
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
    """Check if PDF already has address in the cropped region"""
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


# Copy other helper functions from label_processor.py
def initialize_roboflow():
    print("→ Initializing Roboflow...")
    rf = Roboflow(api_key=ROBOFLOW_API_KEY)
    workspace = rf.workspace(WORKSPACE)
    project = workspace.project(PROJECT)
    version = project.version(VERSION)
    model = version.model
    print(f"✓ Roboflow Model v{VERSION} ready")
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

    # Create temp preview
    temp_image = os.path.join(TEMP_FOLDER, f"{job_code}_test_preview.png")
    print("→ Creating preview...")
    page_w, page_h, img_w, img_h = pdf_to_preview_image(pdf_path, temp_image, DPI_FOR_DETECTION)

    # Run detection
    print("→ Running Roboflow detection...")
    bbox = get_bounding_box(model, temp_image, CONFIDENCE_THRESHOLD)

    if not bbox:
        print("✗ No detection found")
        os.remove(temp_image)
        return False

    print(f"✓ Detection found (confidence: {bbox['confidence']:.2%})")

    # Convert coordinates
    pdf_bbox = convert_image_coords_to_pdf(bbox, page_w, page_h, img_w, img_h)

    # Extract clean SVG (NEW METHOD)
    output_svg = os.path.join(TEST_OUTPUT, f"{job_code}_clean.svg")
    extract_clean_svg(pdf_path, pdf_bbox, output_svg)

    # Add address if needed
    if address_lookup:
        if has_address_text(pdf_path, pdf_bbox):
            print("  ✓ Address already present")
        else:
            address = address_lookup.get_address(job_code)
            if address:
                print(f"  → Adding address: {address}")
                add_address_to_svg(output_svg, address)
            else:
                print(f"  ⚠ No address in sheet for {job_code}")

    print(f"✓ SUCCESS: {output_svg}")
    os.remove(temp_image)
    return True


def main():
    print("\n" + "="*60)
    print("SVG CLEAN EXTRACTION TEST")
    print("="*60)
    print("\nThis is a SAFE TEST - main code is not touched!")
    print(f"Reading from: {TEST_INPUT}")
    print(f"Writing to:   {TEST_OUTPUT}\n")

    # Setup folders
    Path(TEST_OUTPUT).mkdir(parents=True, exist_ok=True)
    Path(TEMP_FOLDER).mkdir(parents=True, exist_ok=True)

    # Initialize Roboflow
    model = initialize_roboflow()

    # Initialize address lookup
    address_lookup = None
    if ENABLE_ADDRESS_LOOKUP:
        try:
            import gspread
            from google.oauth2.service_account import Credentials

            class GoogleSheetsAddressLookup:
                def __init__(self):
                    self.address_cache = {}

                def connect(self):
                    try:
                        scopes = [
                            'https://www.googleapis.com/auth/spreadsheets',
                            'https://www.googleapis.com/auth/drive'
                        ]
                        creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS, scopes=scopes)
                        client = gspread.authorize(creds)
                        sheet = client.open(GOOGLE_SHEET_NAME).worksheet(GOOGLE_WORKSHEET)
                        all_data = sheet.get_all_values()
                        for row in all_data[1:]:
                            if len(row) >= 2:
                                self.address_cache[row[0].strip().upper()] = row[1].strip()
                        print(f"✓ Loaded {len(self.address_cache)} addresses\n")
                        return True
                    except Exception as e:
                        print(f"⚠ Address lookup disabled: {e}\n")
                        return False

                def get_address(self, job_code):
                    return self.address_cache.get(job_code.strip().upper())

            address_lookup = GoogleSheetsAddressLookup()
            address_lookup.connect()
        except:
            print("⚠ Google Sheets not available\n")

    # Find test PDFs
    test_pdfs = list(Path(TEST_INPUT).glob("*.pdf"))

    if not test_pdfs:
        print(f"\n✗ No PDFs found in {TEST_INPUT}")
        print("\nTo test:")
        print("1. Create folder: TEST_PDFs")
        print("2. Copy 2-3 PDFs there")
        print("3. Run this script again")
        return

    print(f"Found {len(test_pdfs)} test PDF(s)\n")

    # Process each test PDF
    success = 0
    for pdf in test_pdfs:
        try:
            if test_process_pdf(str(pdf), model, address_lookup):
                success += 1
        except Exception as e:
            print(f"✗ ERROR: {e}")

    # Summary
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    print(f"✓ Success: {success}/{len(test_pdfs)}")
    print(f"\nCheck results in: {TEST_OUTPUT}")
    print("\nNext steps:")
    print("1. Open SVGs in Inkscape - verify all content present")
    print("2. Upload to Glowforge - check if it only sees label")
    print("3. If good → integrate into main label_processor.py")
    print("4. If bad → we'll tweak and test again!")


if __name__ == "__main__":
    main()
