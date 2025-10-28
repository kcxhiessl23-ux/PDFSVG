# PDF Label Cropper for Glowforge

Automated batch processing of solar installation PDFs to extract "CAUTION: MULTIPLE SOURCES OF POWER" labels as clean SVG files for laser engraving.

## Overview

This tool processes ~200 PDFs/month using Roboflow AI to automatically detect and crop label regions, then adds addresses from a Google Sheet lookup.

### What It Does

1. **Detects** label bounding boxes using Roboflow object detection
2. **Crops** the vector PDF (not rasterized) to the detected region
3. **Exports** as clean SVG for Glowforge scoring
4. **Adds** address text from Google Sheets based on job code

## Requirements

### Python Libraries

**Required:**
```bash
pip install pymupdf roboflow
```

**Optional (only if using Google Sheets instead of CSV):**
```bash
pip install gspread google-auth
```

### Accounts & APIs

- **Roboflow Account**: For object detection model (required)
- **Google Cloud Project**: Only needed if using Google Sheets (optional, see GOOGLE_SHEETS_SETUP.md)

## Quick Start

### 1. Configure Settings

Edit `label_processor.py`:

```python
INPUT_FOLDER = r"C:\path\to\PDFs"
OUTPUT_FOLDER = r"C:\path\to\SVGs"
TEMP_FOLDER = r"C:\path\to\temp"

CONFIDENCE_THRESHOLD = 40  # Detection confidence (30-50 recommended)
DPI_FOR_DETECTION = 96     # Image quality for detection

ENABLE_ADDRESS_LOOKUP = True  # Set False to skip address lookup
```

### 2. Test Roboflow Connection

```bash
python test_roboflow.py
```

You should see:
```
✓ Workspace loaded: placardcleanup
✓ Project loaded: placard_cleanup-imhpc
✓ Version loaded: 2
✓ Model object created
✓ SUCCESS: All checks passed!
```

### 3. Set Up Address Lookup (Choose One)

#### Option A: Google Sheets (Recommended - Easy Weekly Updates!)

See **GOOGLE_SHEETS_SETUP_SIMPLE.md** for step-by-step setup (10 minutes).

**Why Google Sheets?**
- ✅ 100% FREE (no credit card, no charges)
- ✅ Edit from anywhere (phone, tablet, computer)
- ✅ Perfect for weekly updates
- ✅ No comma/formatting issues
- ✅ Version history included

Quick version:
1. Create a Google Sheet with your job codes and addresses
2. Follow GOOGLE_SHEETS_SETUP_SIMPLE.md (10 min setup)
3. Download `google_credentials.json`
4. Share sheet with service account email
5. Test with: `python test_google_sheets.py`
6. Done! (Already configured by default)

#### Option B: CSV File (For Simple Local Use)

See **CSV_SETUP.md** for detailed instructions.

Good if you:
- Don't need weekly updates
- Want everything offline
- Prefer editing in Excel/Notepad

To use CSV:
1. Edit `job_codes.csv`
2. Change in `label_processor.py`:
   ```python
   ADDRESS_LOOKUP_METHOD = "CSV"
   ```

### 4. Run the Processor

```bash
python label_processor.py
```

Example output:
```
============================================================
Processing: C:\PDFs\002KALA.pdf
============================================================
→ Creating preview...
→ Running detection...
✓ Detection found (confidence: 87.23%)
→ Converting coordinates...
→ Extracting vector region...
→ Looking up address...
✓ Address found: 123 Main St, Los Angeles, CA 90001
→ Adding address to SVG...
✓ SUCCESS: C:\SVGs\002KALA.svg
```

## Project Files

- **label_processor.py** - Main batch processing script
- **test_roboflow.py** - Test Roboflow connection
- **test_google_sheets.py** - Test Google Sheets connection (with helpful error messages!)
- **GOOGLE_SHEETS_SETUP_SIMPLE.md** - Simplified Google Sheets setup (10 min, RECOMMENDED)
- **job_codes.csv** - Example CSV file for local address lookup
- **csv_address_lookup.py** - CSV lookup module with testing
- **CSV_SETUP.md** - CSV setup guide (2 minutes, for offline use)
- **GOOGLE_SHEETS_SETUP.md** - Original detailed Google Sheets guide (more technical)

## Configuration Options

### Detection Settings

```python
CONFIDENCE_THRESHOLD = 40
```
- **Lower (30)**: More detections, may include false positives
- **Higher (50)**: Only confident detections, may miss some labels

```python
DPI_FOR_DETECTION = 96
```
- **Lower (96)**: Faster processing
- **Higher (150)**: Better detection accuracy for small details

### Address Lookup

```python
ENABLE_ADDRESS_LOOKUP = True
```
- **True**: Look up addresses from CSV or Google Sheets
- **False**: Skip address lookup entirely (fastest)

```python
ADDRESS_LOOKUP_METHOD = "CSV"  # or "GOOGLE_SHEETS"
```
- **"CSV"**: Use simple CSV file (recommended, default)
- **"GOOGLE_SHEETS"**: Use Google Sheets (requires setup)

## Improving Detection Accuracy

### Immediate Fixes (No Retraining)

1. **Adjust confidence threshold**:
   ```python
   CONFIDENCE_THRESHOLD = 35  # Try lower value
   ```

2. **Increase detection quality**:
   ```python
   DPI_FOR_DETECTION = 150  # Higher quality image
   ```

### Long-term Improvements (Requires Retraining)

1. **Add training data**:
   - Upload failed PDFs to Roboflow
   - Draw bounding boxes around labels
   - Retrain as Version 3

2. **Enable augmentations**:
   - In Roboflow project settings
   - Enable rotation, brightness, contrast variations

3. **Use larger model**:
   - Switch from YOLOv8n to YOLOv8m or YOLOv8l
   - Slower but more accurate

## Troubleshooting

### "Model is None"
- Check you're using the correct version number (currently 2)
- Verify the version is trained and deployed in Roboflow
- Run `python test_roboflow.py` to diagnose

### "No detection found"
- Try lowering `CONFIDENCE_THRESHOLD` to 30
- Increase `DPI_FOR_DETECTION` to 150
- Check if the PDF layout is significantly different from training data

### "Address not found"
- Verify job code matches exactly in Google Sheet (case-insensitive)
- Check Google Sheet is shared with service account
- Run `python address_lookup.py` to test connection

### "Permission denied" (Google Sheets)
- Ensure you shared the sheet with the service account email
- Check `google_credentials.json` is in the correct location
- Verify sheet name matches `GOOGLE_SHEET_NAME` in config

## Workflow

```
PDF (002KALA.pdf)
    ↓
[Convert to PNG preview at 96 DPI]
    ↓
[Roboflow detects label bounding box]
    ↓
[Convert pixel coords → PDF points]
    ↓
[Crop vector PDF to bbox]
    ↓
[Export cropped region as SVG]
    ↓
[Look up address from Google Sheet]
    ↓
[Add address text to SVG]
    ↓
SVG (002KALA.svg) → Glowforge
```

## Tech Stack

- **Python 3.12+**
- **PyMuPDF (fitz)**: PDF manipulation and SVG export
- **Roboflow**: Cloud-based object detection API
- **gspread**: Google Sheets API client
- **xml.etree**: SVG text manipulation

## Current Status

- ✅ Roboflow detection working (Version 2)
- ✅ Vector PDF cropping working
- ✅ SVG export working
- ✅ Google Sheets address lookup implemented
- ✅ Address text added to SVG output
- 🔧 Fine-tuning detection accuracy

## License

Internal tool for solar installation label processing.
