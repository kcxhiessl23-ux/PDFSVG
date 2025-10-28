# Google Sheets Setup - SIMPLIFIED (10 minutes)

**Google Sheets API is 100% FREE** - no credit card, no charges, no tricks!

You get 500 requests per 100 seconds for free. You only use 1 request at startup. You'll never pay.

---

## Quick Overview

1. Create a Google Cloud project (free, 2 min)
2. Enable Google Sheets API (30 seconds)
3. Create a service account (1 min)
4. Download credentials file (30 seconds)
5. Share your Google Sheet with the service account email (30 seconds)
6. Done!

---

## Step-by-Step Setup

### Step 1: Create Your Google Sheet (2 minutes)

1. Go to https://sheets.google.com
2. Create a new sheet
3. Name it **"Job Codes"** (or whatever you want)
4. Set up like this:

```
|  A (Job Code) |  B (Address)                              |
|---------------|-------------------------------------------|
| 002KALA       | 123 Main Street, Los Angeles, CA 90001    |
| 053FAIR       | 456 Oak Avenue, Sacramento, CA 95814      |
| 003ESTR       | 789 Pine Road, San Diego, CA 92101        |
```

**Important**:
- Row 1 is headers: `Job Code` | `Address`
- Put your job codes in column A
- Put addresses in column B
- That's it!

### Step 2: Go to Google Cloud Console (30 seconds)

1. Open: https://console.cloud.google.com/
2. You'll see "Select a project" at the top
3. Click it, then click **"New Project"**
4. Name it: **"Placard Processor"**
5. Click **"Create"**
6. Wait 10 seconds for it to create

### Step 3: Enable Google Sheets API (30 seconds)

1. In the search bar at the top, type: **"Google Sheets API"**
2. Click on the first result (Google Sheets API)
3. Click the big blue **"Enable"** button
4. Wait for it to enable (5 seconds)

### Step 4: Create Service Account (2 minutes)

1. In the left menu, click **"Credentials"**
2. At the top, click **"Create Credentials"** → **"Service Account"**
3. Fill in:
   - **Service account name**: `placard-processor`
   - **Service account ID**: (auto-filled, leave it)
4. Click **"Create and Continue"**
5. **Skip the next two steps** - just click **"Continue"** then **"Done"**

### Step 5: Download Credentials (1 minute)

1. You should see your service account listed (placard-processor@...)
2. **Click on it** (click the email address)
3. Go to the **"Keys"** tab at the top
4. Click **"Add Key"** → **"Create new key"**
5. Choose **"JSON"**
6. Click **"Create"**
7. A file downloads - **save it as `google_credentials.json`**
8. **Move this file to the same folder as your Python scripts**

### Step 6: Share Sheet with Service Account (1 minute)

This is the most important step!

1. **Open the `google_credentials.json` file** you just downloaded (open in Notepad)
2. Find the line that says `"client_email"`
3. Copy that entire email address (looks like: `placard-processor@your-project-123456.iam.gserviceaccount.com`)
4. Go back to your **Google Sheet**
5. Click the **"Share"** button (top right)
6. Paste the email address
7. Make sure it says **"Viewer"** (or "Editor" is fine too)
8. Click **"Send"**

### Step 7: Configure the Script (30 seconds)

Open `label_processor.py` and find this section (around line 20-30):

```python
ADDRESS_LOOKUP_METHOD = "CSV"  # ← Change this!
```

Change it to:

```python
ADDRESS_LOOKUP_METHOD = "GOOGLE_SHEETS"
```

And update the sheet name if you used a different name:

```python
GOOGLE_SHEET_NAME = "Job Codes"  # ← Your sheet name
GOOGLE_WORKSHEET = "Sheet1"      # ← Tab name (usually "Sheet1")
```

### Step 8: Test It! (30 seconds)

```bash
python test_roboflow.py
```

Should see:
```
✓ Roboflow ready
✓ Google Sheets connected: 200 addresses loaded
```

Then run the full processor:
```bash
python label_processor.py
```

---

## Troubleshooting

### "Permission denied" or "Spreadsheet not found"

**99% of the time this is the issue**: You forgot to share the sheet!

1. Open your Google Sheet
2. Click "Share"
3. Check if the service account email is listed
4. If not, add it again

### "Credentials file not found"

- Make sure `google_credentials.json` is in the same folder as `label_processor.py`
- Check the filename is exactly: `google_credentials.json`
- No `.txt` at the end!

### "Invalid grant" or "Authentication failed"

- Download the credentials file again
- Make sure you shared the sheet with the exact email from the JSON file

### Sheet name doesn't match

- Check your sheet is named exactly what you put in `GOOGLE_SHEET_NAME`
- Check the tab name (bottom of Google Sheet) matches `GOOGLE_WORKSHEET`

---

## Security Notes

**NEVER** share `google_credentials.json` with anyone or commit it to git!

The `.gitignore` file already protects it, but be careful:
- Don't email it
- Don't post it online
- Don't commit it to GitHub

If you accidentally expose it, you can delete the service account and create a new one.

---

## Benefits of Google Sheets

✅ **Update from anywhere** - Edit on phone, tablet, computer
✅ **Team collaboration** - Multiple people can update
✅ **Version history** - See who changed what
✅ **Easy editing** - No need to deal with commas or formatting
✅ **Weekly updates** - Just edit the sheet, no need to sync files

---

## Need Help?

If you get stuck, show me:
1. The exact error message
2. Which step you're on
3. Screenshot if helpful

I'll help you fix it!
