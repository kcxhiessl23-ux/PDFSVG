import fitz  # PyMuPDF
from roboflow import Roboflow
import os
from pathlib import Path

# ========== CONFIG ==========
ROBOFLOW_API_KEY = "L93UjMpMcsqujZ2mRU6N"
WORKSPACE = "placardcleanup"
PROJECT = "placard_cleanup-imhpc"  # ← Find this in Roboflow (it's the model name)
VERSION = 1

INPUT_FOLDER = r"C:\Users\kschi\OneDrive\Desktop\Placards\PDFs"  # ← Your PDF folder
OUTPUT_FOLDER = r"C:\Users\kschi\OneDrive\Desktop\Placards\SVGs"
TEMP_FOLDER = r"C:\Users\kschi\OneDrive\Desktop\Placards\PDFSVGTEMP"

CONFIDENCE_THRESHOLD = 40
DPI_FOR_DETECTION = 96

# ========== SCRIPT ==========

def setup_folders():
    Path(OUTPUT_FOLDER).mkdir(parents=True, exist_ok=True)
    Path(TEMP_FOLDER).mkdir(parents=True, exist_ok=True)

def initialize_roboflow():
    rf = Roboflow(api_key=ROBOFLOW_API_KEY)
    project = rf.workspace(WORKSPACE).project(PROJECT)
    model = project.version(VERSION).model
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
    
    print(f"✓ SUCCESS: {output_svg}")
    
    os.remove(temp_image)
    return True

def process_batch():
    setup_folders()
    
    print("\n" + "="*60)
    print("INITIALIZING ROBOFLOW")
    print("="*60)
    model = initialize_roboflow()
    print("✓ Model loaded\n")
    
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