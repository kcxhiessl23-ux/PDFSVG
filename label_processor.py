import fitz  # PyMuPDF
from roboflow import Roboflow
import os
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
import re

import subprocess
import xml.etree.ElementTree as ET

INKSCAPE_EXE = r"C:\Program Files\Inkscape\bin\inkscape.exe"


ROBOFLOW_API_KEY = "L93UjMpMcsqujZ2mRU6N"
WORKSPACE = "placardcleanup"
PROJECT = "placard_cleanup-imhpc"  # model name in Roboflow
VERSION = 4  # active version


def clean_svg(svg_path):
    """
    Cleans and flattens an SVG:
    - Converts text to paths
    - Removes invisible or duplicate paths
    - Removes redundant strokes on filled paths
    """
    try:
        # --- Flatten text to paths ---
        print(f"→ Converting text to paths...")
        subprocess.run([
            INKSCAPE_EXE,
            svg_path,
            "--export-plain-svg", svg_path,
            "--actions=select-all;object-to-path;export-do"
        ], check=True, capture_output=True)

        # --- Parse XML ---
        tree = ET.parse(svg_path)
        root = tree.getroot()
        seen_d = set()

        def clean_node(node):
            for child in list(node):
                tag = child.tag.lower()
                
                # Remove FULLY invisible elements only
                fill_opacity = child.attrib.get("fill-opacity", "1")
                stroke_opacity = child.attrib.get("stroke-opacity", "1")
                
                try:
                    # Only remove if BOTH are exactly 0
                    if float(fill_opacity) == 0 and float(stroke_opacity) == 0:
                        node.remove(child)
                        continue
                except:
                    pass
                
                # Remove duplicate paths
                if tag.endswith('path') and "d" in child.attrib:
                    d = child.attrib["d"]
                    if d in seen_d:
                        node.remove(child)
                        continue
                    seen_d.add(d)
                    
                    # FIX THE DOUBLING: Remove stroke if element has fill
                    # (PyMuPDF often adds BOTH which makes text look bold)
                    fill = child.attrib.get("fill", "none")
                    if fill != "none":
                        # Has fill, remove stroke to prevent doubling
                        child.attrib.pop("stroke", None)
                        child.attrib.pop("stroke-width", None)
                
                # Recurse
                clean_node(child)

        clean_node(root)
        tree.write(svg_path, encoding="utf-8", xml_declaration=True)
        print(f"✓ Cleaned: removed {len(seen_d)} duplicates")

    except Exception as e:
        print(f"⚠ SVG cleanup failed: {e}")


def has_address_text(svg_path):
    # Convert SVG to temporary PNG for OCR
    temp_png = svg_path.replace(".svg", "_ocr.png")
    os.system(f'magick "{svg_path}" "{temp_png}"')  # ImageMagick required
    text = pytesseract.image_to_string(Image.open(temp_png))
    os.remove(temp_png)

    # --- OCR street pattern check ---
    if re.search(
        r"\d{1,5}\s+[A-Za-z]+\s+(St|Ave|Rd|Cir|Dr|Pl|Way|Ct|Ln|Blvd|Pkwy|Terr|Trail|Hwy|Place|Drive|Court|Road|Street|Lane)",
        text, re.I):
        return True

    # --- Hidden text-layer fallback (vector PDFs) ---
    try:
        pdf_path = svg_path.replace(".svg", ".pdf")
        if os.path.exists(pdf_path):
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_path)
            text_layer = doc[0].get_text("text")
            doc.close()
            if re.search(
                r"\d{1,5}\s+[A-Za-z]+\s+(St|Ave|Rd|Cir|Dr|Pl|Way|Ct|Ln|Blvd|Pkwy|Terr|Trail|Hwy|Place|Drive|Court|Road|Street|Lane)",
                text_layer, re.I):
                return True
    except Exception:
        pass

    return False

# ⚠ WINDOWS USERS: Use r"..." (raw strings) for paths with backslashes!
# Good: r"C:\Users\Name\Desktop\Folder"  or  "C:/Users/Name/Desktop/Folder"
# Bad:  "C:\Users\Name\Desktop\Folder"  ← Will cause syntax errors!

INPUT_FOLDER = r"C:\Users\kschi\OneDrive\Desktop\Placards\PDFs"  # ← Your PDF folder
OUTPUT_FOLDER = r"C:\Users\kschi\OneDrive\Desktop\Placards\SVGs"
TEMP_FOLDER = r"C:\Users\kschi\OneDrive\Desktop\Placards\PDFSVGTEMP"

CONFIDENCE_THRESHOLD = 40
DPI_FOR_DETECTION = 96

# Address lookup (optional)
ENABLE_ADDRESS_LOOKUP = True  # Set to False to disable address lookup
ADDRESS_LOOKUP_METHOD = "GOOGLE_SHEETS"  # "GOOGLE_SHEETS" or "CSV"

# Google Sheets method (RECOMMENDED for weekly updates!)
# See GOOGLE_SHEETS_SETUP_SIMPLE.md for setup (10 min, 100% FREE)
GOOGLE_SHEET_NAME = "Job Codes"  # Name of your Google Sheet
GOOGLE_WORKSHEET = "Sheet1"  # Worksheet tab name (check bottom of your sheet)

# Credentials file - just filename if in same folder, or full path with r"..."
GOOGLE_CREDENTIALS = r"C:\Users\kschi\OneDrive\Desktop\Placards\Pys\google_credentials.json"  # Same folder as this scrip

# CSV method (alternative - simple local file)
CSV_FILE = "job_codes.csv"  # Path to your CSV file

# ========== SCRIPT ==========

# Address lookup initialization
address_lookup = None

if ENABLE_ADDRESS_LOOKUP:
    if ADDRESS_LOOKUP_METHOD == "CSV":
        # Simple CSV method (no external dependencies)
        import csv

        class CSVAddressLookup:
            def __init__(self):
                self.address_cache = {}
                self.connected = False

            def connect(self):
                if not os.path.exists(CSV_FILE):
                    print(f"⚠ CSV file not found: {CSV_FILE}")
                    print(f"  Create '{CSV_FILE}' with columns: Job Code, Address")
                    return False

                try:
                    with open(CSV_FILE, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)

                        if 'Job Code' not in reader.fieldnames or 'Address' not in reader.fieldnames:
                            print(f"✗ CSV must have 'Job Code' and 'Address' columns")
                            return False

                        for row in reader:
                            job_code = row['Job Code'].strip().upper()
                            address = row['Address'].strip()
                            if job_code and address:
                                self.address_cache[job_code] = address

                    self.connected = True
                    print(f"✓ CSV loaded: {len(self.address_cache)} addresses found")
                    return True

                except Exception as e:
                    print(f"✗ Failed to read CSV: {e}")
                    return False

            def get_address(self, job_code):
                if not self.connected:
                    return None
                return self.address_cache.get(job_code.strip().upper())

        address_lookup = CSVAddressLookup()

    elif ADDRESS_LOOKUP_METHOD == "GOOGLE_SHEETS":
        # Google Sheets method (requires setup)
        try:
            import gspread
            from google.oauth2.service_account import Credentials

            class GoogleSheetsAddressLookup:
                def __init__(self):
                    self.sheet = None
                    self.address_cache = {}

                def connect(self):
                    try:
                        # Use full scopes to avoid permission errors
                        scopes = [
                            'https://www.googleapis.com/auth/spreadsheets',
                            'https://www.googleapis.com/auth/drive'
                        ]
                        creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS, scopes=scopes)
                        client = gspread.authorize(creds)
                        self.sheet = client.open(GOOGLE_SHEET_NAME).worksheet(GOOGLE_WORKSHEET)
                        self._load_cache()
                        print(f"✓ Google Sheets connected: {len(self.address_cache)} addresses loaded")
                        return True
                    except Exception as e:
                        print(f"⚠ Address lookup disabled: {e}")
                        print(f"  (See GOOGLE_SHEETS_SETUP.md for setup instructions)")
                        return False

                def _load_cache(self):
                    all_data = self.sheet.get_all_values()
                    for row in all_data[1:]:  # Skip header
                        if len(row) >= 2:
                            job_code = row[0].strip().upper()
                            address = row[1].strip()
                            if job_code and address:
                                self.address_cache[job_code] = address

                def get_address(self, job_code):
                    return self.address_cache.get(job_code.strip().upper())

            address_lookup = GoogleSheetsAddressLookup()
        except ImportError:
            print("⚠ Google Sheets libraries not installed. Run: pip install gspread google-auth")
            print("  Or use ADDRESS_LOOKUP_METHOD = 'CSV' instead")

def setup_folders():
    Path(OUTPUT_FOLDER).mkdir(parents=True, exist_ok=True)
    Path(TEMP_FOLDER).mkdir(parents=True, exist_ok=True)

def initialize_roboflow():
    print("loading Roboflow workspace...")
    rf = Roboflow(api_key=ROBOFLOW_API_KEY)

    # Try method 1: Using workspace name
    try:
        workspace = rf.workspace(WORKSPACE)
        print(f"✓ Workspace loaded: {WORKSPACE}")
    except Exception as e:
        print(f"⚠ Failed with workspace name '{WORKSPACE}': {e}")
        # Try method 2: Use default workspace (no parameter)
        print("→ Trying default workspace...")
        try:
            workspace = rf.workspace()
            print(f"✓ Using default workspace")
        except Exception as e2:
            print(f"✗ Failed to load workspace: {e2}")
            print("\nTroubleshooting:")
            print("  1. Check workspace name in Roboflow dashboard")
            print("  2. Verify API key has access to the workspace")
            raise

    try:
        print("loading Roboflow project...")
        project = workspace.project(PROJECT)
        print(f"✓ Project loaded: {PROJECT}")
    except Exception as e:
        print(f"✗ Failed to load project '{PROJECT}': {e}")
        print("\nTroubleshooting:")
        print("  1. Verify project name in Roboflow dashboard")
        print("  2. Check project exists in your workspace")
        raise

    try:
        version = project.version(VERSION)
        if version is None:
            raise ValueError(f"Version {VERSION} returned None")
        print(f"✓ Version loaded: {VERSION}")
    except Exception as e:
        print(f"✗ Failed to load version {VERSION}: {e}")
        print("\nTroubleshooting:")
        print(f"  1. Check if version {VERSION} exists")
        print("  2. Ensure the version is deployed")
        raise

    try:
        model = version.model
        if model is None:
            raise ValueError("Model object is None - check your Roboflow project has a trained model")
        print(f"✓ Model object created")
        return model
    except Exception as e:
        print(f"✗ Failed to get model: {e}")
        print("\nTroubleshooting:")
        print("  1. Ensure model is trained and deployed")
        print("  2. Check version has an active model")
        raise

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
    
    x_min = x_center - (width / 2)
    y_min = y_center - (height / 2)
    x_max = x_center + (width / 2)
    y_max = y_center + (height / 2)
    
    return {
        'x_min': x_min,
        'y_min': y_min,
        'x_max': x_max,
        'y_max': y_max,
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

def crop_pdf_to_svg(pdf_path, bbox, output_path):
    pdf = fitz.open(pdf_path)
    page = pdf[0]

    crop_rect = fitz.Rect(
        bbox['x_min'],
        bbox['y_min'],
        bbox['x_max'],
        bbox['y_max']
    )

    page.set_cropbox(crop_rect)
    svg_content = page.get_svg_image()

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)

    pdf.close()
    return True

def add_address_to_svg(svg_path, address_text):
    """
    Add address text to the bottom of an SVG file

    Args:
        svg_path: Path to the SVG file
        address_text: Address text to add
    """
    try:
        # Parse the SVG
        tree = ET.parse(svg_path)
        root = tree.getroot()

        # Get SVG namespace
        namespace = {'svg': 'http://www.w3.org/2000/svg'}

        # Get SVG dimensions
        width = float(root.get('width', '0').replace('pt', ''))
        height = float(root.get('height', '0').replace('pt', ''))

        if width == 0 or height == 0:
            # Try viewBox if width/height not found
            viewbox = root.get('viewBox', '0 0 0 0').split()
            width = float(viewbox[2])
            height = float(viewbox[3])

        # Create text element
        text_elem = ET.Element('{http://www.w3.org/2000/svg}text')
        text_elem.set('x', str(width / 2))  # Center horizontally
        text_elem.set('y', str(height + 15))  # Position below the main content
        text_elem.set('text-anchor', 'middle')  # Center alignment
        text_elem.set('font-family', 'Arial')
        text_elem.set('font-size', '16')
        text_elem.set('fill', 'black')
        text_elem.text = address_text

        # Extend viewBox to include the address
        if root.get('viewBox'):
            viewbox = root.get('viewBox').split()
            new_height = float(viewbox[3]) + 25  # Add space for text
            root.set('viewBox', f"{viewbox[0]} {viewbox[1]} {viewbox[2]} {new_height}")

        # Update height attribute
        if root.get('height'):
            new_height = height + 25
            root.set('height', f"{new_height}pt")

        # Add text to SVG
        root.append(text_elem)

        # Save modified SVG
        tree.write(svg_path, encoding='utf-8', xml_declaration=True)
        return True

    except Exception as e:
        print(f"⚠ Warning: Could not add address to SVG: {e}")
        return False

def process_single_pdf(pdf_path, model, job_code):
    print(f"\n{'='*60}")
    print(f"Processing: {pdf_path}")
    print(f"{'='*60}")
    
    temp_image = os.path.join(TEMP_FOLDER, f"{job_code}_preview.png")
    print("→ Creating preview...")
    page_w, page_h, img_w, img_h = pdf_to_preview_image(pdf_path, temp_image, DPI_FOR_DETECTION)
    
    print("→ Running detection...")
    bbox = get_bounding_box(model, temp_image, CONFIDENCE_THRESHOLD)
    
    if not bbox:
        print("✗ No detection found")
        return False
    
    print(f"✓ Detection found (confidence: {bbox['confidence']:.2%})")
    
    print("→ Converting coordinates...")
    pdf_bbox = convert_image_coords_to_pdf(bbox, page_w, page_h, img_w, img_h)
    
    output_svg = os.path.join(OUTPUT_FOLDER, f"{job_code}.svg")
    print("→ Extracting vector region...")
    crop_pdf_to_svg(pdf_path, pdf_bbox, output_svg)

    # Add address if lookup is enabled
    if address_lookup:
        print("→ Checking for existing address text...")
        if has_address_text(output_svg):
            print("✓ Address already present — skipping add.")
        else:
            print("→ Looking up address...")
            address = address_lookup.get_address(job_code)
            if address:
                print(f"✓ Address found: {address}")
                print("→ Adding address to SVG...")
                add_address_to_svg(output_svg, address)
            else:
                print(f"⚠ No address found for {job_code}")
                add_address_to_svg(output_svg, f"ADDRESS NOT FOUND: {job_code}")
            
            clean_svg(output_svg)
    print(f"✓ SUCCESS: {output_svg}")

    os.remove(temp_image)
    return True

def process_batch():
    setup_folders()

    print("\n" + "="*60)
    print("INITIALIZING ROBOFLOW")
    print("="*60)

    try:
        model = initialize_roboflow()
        print("="*60)
        print("✓ Roboflow ready\n")
    except Exception as e:
        print(f"\n✗ FATAL: Failed to initialize Roboflow: {e}")
        return

    # Initialize address lookup if enabled
    if address_lookup:
        print("="*60)
        print("INITIALIZING ADDRESS LOOKUP")
        print("="*60)
        if not address_lookup.connect():
            print("⚠ Continuing without address lookup\n")
        else:
            print()

    pdf_files = list(Path(INPUT_FOLDER).glob("*.pdf"))
    
    if not pdf_files:
        print(f"✗ No PDFs in {INPUT_FOLDER}")
        return
    
    print(f"Found {len(pdf_files)} PDFs\n")
    
    success_count = 0
    failed_files = []
    
    for pdf_file in pdf_files:
        job_code = pdf_file.stem
        
        try:
            if process_single_pdf(str(pdf_file), model, job_code):
                success_count += 1
        except Exception as e:
            print(f"✗ ERROR: {e}")
            failed_files.append(str(pdf_file))
    
    print("\n" + "="*60)
    print("COMPLETE")
    print("="*60)
    print(f"✓ Success: {success_count}/{len(pdf_files)}")
    
    if failed_files:
        print(f"✗ Failed: {len(failed_files)}")
        for f in failed_files:
            print(f"  - {f}")

if __name__ == "__main__":
    process_batch()