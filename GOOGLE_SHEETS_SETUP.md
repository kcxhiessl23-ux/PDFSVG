# Google Sheets Setup Guide

This guide explains how to set up Google Sheets integration for address lookup.

## Overview
The system will:
1. Look up job codes in a Google Sheet
2. Find the matching address
3. Add the address text to the bottom of the SVG output

## Step 1: Create Your Google Sheet

1. Go to https://sheets.google.com
2. Create a new sheet called **"Job Codes"** (or any name you prefer)
3. Set up columns:
   ```
   Column A: Job Code (002KALA, 053FAIR, etc.)
   Column B: Address (full address text)
   ```

Example:
```
| Job Code | Address                                    |
|----------|--------------------------------------------|
| 002KALA  | 123 Main Street, Los Angeles, CA 90001     |
| 053FAIR  | 456 Oak Avenue, Sacramento, CA 95814       |
| 003ESTR  | 789 Pine Road, San Diego, CA 92101         |
```

## Step 2: Set Up Google Cloud Project

### 2.1 Create a Project
1. Go to https://console.cloud.google.com/
2. Click "Select a project" → "New Project"
3. Name it "Placard Processor" (or anything you want)
4. Click "Create"

### 2.2 Enable Google Sheets API
1. In the Google Cloud Console, click "APIs & Services" → "Library"
2. Search for "Google Sheets API"
3. Click on it and press "Enable"

### 2.3 Create Service Account
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Fill in:
   - **Service account name**: placard-processor
   - **Service account ID**: (auto-filled)
4. Click "Create and Continue"
5. Skip the optional steps (click "Continue" then "Done")

### 2.4 Create JSON Key
1. Click on the service account you just created
2. Go to the "Keys" tab
3. Click "Add Key" → "Create new key"
4. Choose **JSON** format
5. Click "Create"
6. A JSON file will download - **save this as `google_credentials.json`**

### 2.5 Share Sheet with Service Account
1. Open the downloaded `google_credentials.json` file
2. Find the line with `"client_email"` - it looks like:
   ```json
   "client_email": "placard-processor@your-project.iam.gserviceaccount.com"
   ```
3. Copy that email address
4. Go back to your Google Sheet
5. Click "Share" button (top right)
6. Paste the service account email
7. Give it **Viewer** access (it only needs to read)
8. Click "Send"

## Step 3: Install Python Libraries

Open your command prompt and run:
```bash
pip install gspread google-auth
```

## Step 4: Configure the Script

Edit `address_lookup.py` and update these settings:

```python
GOOGLE_SHEET_NAME = "Job Codes"  # ← Your sheet name
WORKSHEET_NAME = "Sheet1"        # ← Your worksheet tab name
JOB_CODE_COLUMN = "A"            # ← Column with job codes
ADDRESS_COLUMN = "B"             # ← Column with addresses
CREDENTIALS_FILE = "google_credentials.json"  # ← Path to your credentials
```

## Step 5: Test the Connection

Put your `google_credentials.json` file in the same folder as your Python scripts, then run:

```bash
python address_lookup.py
```

You should see:
```
✓ Connected to Google Sheet: Job Codes
✓ Loaded 200 job codes
✓ 002KALA: 123 Main Street, Los Angeles, CA 90001
...
```

## Step 6: Run the Main Processor

Once the test works, run your main processor:
```bash
python label_processor.py
```

Now it will automatically look up addresses and add them to the SVGs!

## Troubleshooting

### "Credentials file not found"
- Make sure `google_credentials.json` is in the same folder as your Python scripts
- Check the filename is exactly `google_credentials.json`

### "Permission denied" or "Unable to open spreadsheet"
- Make sure you shared the sheet with the service account email
- Double-check the sheet name matches exactly (case-sensitive)

### "Job code not found"
- Check that job codes in your sheet match your PDF filenames exactly
- Job codes are matched case-insensitively (002KALA = 002kala)
- Leading/trailing spaces are automatically trimmed

## Security Note

**NEVER** commit `google_credentials.json` to git! It contains sensitive credentials.

To protect it:
1. Add to `.gitignore`:
   ```
   google_credentials.json
   ```
