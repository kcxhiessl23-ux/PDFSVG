# Quick Start Guide

Get up and running in 15 minutes!

---

## Step 1: Install Python Libraries (2 min)

```bash
pip install pymupdf roboflow gspread google-auth
```

---

## Step 2: Test Roboflow (30 sec)

```bash
python test_roboflow.py
```

Should see:
```
✓ Workspace loaded
✓ Project loaded
✓ Version loaded: 2
✓ Model object created
✓ SUCCESS!
```

---

## Step 3: Set Up Google Sheets (10 min)

### 3a. Create Your Sheet

1. Go to https://sheets.google.com
2. Create new sheet named **"Job Codes"**
3. Add headers in row 1:
   - Column A: `Job Code`
   - Column B: `Address`
4. Add your data starting in row 2

### 3b. Set Up Google Cloud (5 min)

1. Go to https://console.cloud.google.com/
2. Create new project: **"Placard Processor"**
3. Search for and enable: **"Google Sheets API"**
4. Go to **Credentials** → **Create Credentials** → **Service Account**
5. Name it: `placard-processor`
6. Click through (skip optional steps)
7. Click on the service account → **Keys** tab
8. Add Key → Create new key → **JSON**
9. Save as `google_credentials.json` in your project folder

### 3c. Share Sheet (30 sec)

1. Open `google_credentials.json` in Notepad
2. Copy the `client_email` (looks like: `...@....iam.gserviceaccount.com`)
3. Go back to your Google Sheet
4. Click **Share**
5. Paste the email
6. Give **Viewer** access
7. Click **Send**

### 3d. Test Connection (30 sec)

```bash
python test_google_sheets.py
```

Should see:
```
✓ Found: google_credentials.json
✓ Valid credentials file
✓ Authentication successful
✓ Found sheet: Job Codes
✓ Successfully read X rows
✓ SUCCESS! Google Sheets is ready!
```

---

## Step 4: Configure Paths (1 min)

Edit `label_processor.py` lines 12-14:

```python
INPUT_FOLDER = r"C:\path\to\your\PDFs"
OUTPUT_FOLDER = r"C:\path\to\your\SVGs"
TEMP_FOLDER = r"C:\path\to\temp"
```

---

## Step 5: Run It! (30 sec)

```bash
python label_processor.py
```

You should see:
```
✓ Roboflow ready
✓ Google Sheets connected: 200 addresses loaded
Found 9 PDFs

Processing: 002KALA.pdf
✓ Detection found (87.23%)
✓ Address found: 123 Main Street...
✓ SUCCESS
```

---

## Done!

Your SVG files are in the output folder, ready for Glowforge!

---

## Weekly Updates

Just edit your Google Sheet - no need to do anything else!

The script reads the latest data every time it runs.

---

## Troubleshooting

### "Sheet not found"
→ Make sure you shared it with the service account email

### "Credentials file not found"
→ Put `google_credentials.json` in the same folder as the Python scripts

### "No detection found"
→ Try lowering `CONFIDENCE_THRESHOLD` to 30 in `label_processor.py`

### Need help?
→ Run `python test_google_sheets.py` for detailed diagnostics!
