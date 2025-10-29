# Safe Testing Instructions

## The Problem We're Solving

When PyMuPDF crops PDFs to SVG, it doesn't actually DELETE vectors outside the crop box - it just hides them. Glowforge sees ALL vectors in the file (including page backgrounds, borders, etc.) and tries to engrave them.

## The Solution

New method: Extract ONLY the vectors inside the bounding box. Create a clean SVG from scratch with only label content.

---

## How to Test (SAFE - Won't Break Anything!)

### Step 1: Create Test Folder

Create this folder:
```
C:\Users\kschi\OneDrive\Desktop\Placards\TEST_PDFs
```

### Step 2: Copy Test Files

Copy **2-3 PDFs** to the TEST_PDFs folder. Pick:
- One that works well (to make sure we don't break it)
- One with the thick/bold text issue (to see if we fix it)

### Step 3: Run Test

Double-click: `run_test_extraction.bat`

Or manually:
```bash
cd C:\Users\kschi\OneDrive\Desktop\Placards\Pys
python test_clean_extraction.py
```

### Step 4: Check Results

Results will be in:
```
C:\Users\kschi\OneDrive\Desktop\Placards\TEST_SVGs
```

Files will be named: `002KALA_clean.svg`

### Step 5: Verify

**In Inkscape:**
- Open the `_clean.svg` file
- Check that ALL content is there:
  - ✓ Text labels
  - ✓ Arrows
  - ✓ Equipment names
  - ✓ House outline
  - ✓ Panels
  - ✓ Diagrams
  - ✓ Address (if added)

**In Glowforge:**
- Upload the `_clean.svg` file
- Check that it ONLY shows:
  - ✓ The label itself
  - ✗ No white page background
  - ✗ No page borders
  - ✗ No extra rectangles

---

## What the Test Script Does

1. **Reads PDFs from TEST_PDFs** (not your main 200 files!)
2. **Detects label with Roboflow** (same as main script)
3. **NEW: Extracts ONLY vectors inside bounding box**
4. **Adds address from Google Sheets** (if not already there)
5. **Outputs to TEST_SVGs** (separate from main output)

---

## Main Code Status

✅ **Your main `label_processor.py` is UNTOUCHED**
✅ **Your 200 SVG files are UNTOUCHED**
✅ **You can test 100 times with zero risk**

---

## What's Different (Technical)

**Old Method (current):**
```python
page.set_cropbox(bbox)  # Hide stuff outside box
svg = page.get_svg_image()  # Still contains ALL vectors!
```

**New Method (testing):**
```python
svg = page.get_svg_image()  # Get all vectors
parse svg  # Look at each element
if element is inside bbox:
    keep it  # Copy to new clean SVG
else:
    discard it  # Don't include it
```

**Result:** New SVG contains ONLY vectors that are in the label area.

---

## Next Steps After Testing

### If Results Look Good:
1. Tell me it works
2. I'll integrate the new method into `label_processor.py`
3. We'll run it on all 200 PDFs

### If Results Look Bad:
1. Tell me what's wrong (missing content? wrong position?)
2. I'll tweak the extraction logic
3. Test again (still safe, still in TEST folder)

---

## Troubleshooting

### "No PDFs found in TEST_PDFs"
→ Create the folder and copy some PDFs there

### "Roboflow authentication error"
→ Make sure you're in the right folder (should have google_credentials.json)

### "Can't find module gspread"
→ Address lookup will be disabled, but SVG extraction will still work

### "Elements missing from output"
→ Good feedback! Tell me what's missing and I'll adjust the filtering logic

---

## Questions?

Just ask! The whole point is to test safely without breaking anything.
