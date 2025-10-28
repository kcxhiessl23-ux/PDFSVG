# CSV Address Lookup Setup (EASY!)

**This is the recommended method** - no Google Cloud, no API keys, just a simple file!

## Why CSV Instead of Google Sheets?

- ✅ **FREE** - No Google Cloud account needed
- ✅ **SIMPLE** - Just edit a file, no API setup
- ✅ **FAST** - Loads instantly
- ✅ **OFFLINE** - Works without internet
- ✅ **NO COST** - Zero dollars, forever

## Setup (2 minutes)

### Step 1: Create Your CSV File

You already have an example file called `job_codes.csv`!

Open it in **Excel**, **Notepad**, or any text editor:

```csv
Job Code,Address
002KALA,123 Main Street, Los Angeles, CA 90001
053FAIR,456 Oak Avenue, Sacramento, CA 95814
003ESTR,789 Pine Road, San Diego, CA 92101
```

### Step 2: Add Your Addresses

Edit the file and add all your job codes:

- **Column A**: Job Code (matches your PDF filenames)
- **Column B**: Full address

**Important**:
- First line MUST be `Job Code,Address` (the header)
- Job codes are case-insensitive (002KALA = 002kala)
- Use commas to separate columns

### Step 3: Save the File

Save as `job_codes.csv` in the same folder as `label_processor.py`

### Step 4: Done!

That's it! Run your processor:

```bash
python label_processor.py
```

You'll see:

```
============================================================
INITIALIZING ADDRESS LOOKUP
============================================================
✓ CSV loaded: 200 addresses found
```

## Editing Your CSV

### Option 1: Excel (Easiest)

1. Open `job_codes.csv` in Excel
2. Edit the cells
3. **File → Save As → CSV (Comma delimited)**

### Option 2: Google Sheets (Then Export)

1. Open Google Sheets
2. **File → Import → Upload `job_codes.csv`**
3. Edit online
4. **File → Download → CSV**
5. Save as `job_codes.csv`

### Option 3: Text Editor

Just edit the text file directly:

```csv
Job Code,Address
002KALA,123 Main St, Los Angeles, CA 90001
053FAIR,456 Oak Ave, Sacramento, CA 95814
```

## Testing

Test your CSV file:

```bash
python csv_address_lookup.py
```

You should see:

```
✓ CSV loaded: 9 addresses found
✓ 002KALA: 123 Main Street, Los Angeles, CA 90001
✓ 053FAIR: 456 Oak Avenue, Sacramento, CA 95814
...
```

## Troubleshooting

### "CSV file not found"

- Make sure `job_codes.csv` is in the same folder as `label_processor.py`
- Check the filename is exactly `job_codes.csv` (not `job_codes.csv.txt`)

### "CSV must have 'Job Code' and 'Address' columns"

- First line must be: `Job Code,Address`
- Check spelling and capitalization
- Make sure there's a comma between them

### "Address not found for 002KALA"

- Check the job code in the CSV matches your PDF filename exactly
- Job codes are matched case-insensitively
- Make sure there's no extra spaces

### CSV won't open in Excel

- The file might be corrupted
- Delete it and create a new one
- Or use Notepad to fix it

## Adding More Addresses

Just add new lines to the CSV:

```csv
Job Code,Address
002KALA,123 Main Street, Los Angeles, CA 90001
053FAIR,456 Oak Avenue, Sacramento, CA 95814
NEW9999,New Address Here, City, State ZIP    ← Add this line
```

Save and run again!

## Switching to Google Sheets Later

If you want to use Google Sheets later (for team collaboration, etc.):

1. Keep using your CSV for now
2. Later, follow GOOGLE_SHEETS_SETUP.md
3. Change one line in `label_processor.py`:
   ```python
   ADDRESS_LOOKUP_METHOD = "GOOGLE_SHEETS"  # Changed from "CSV"
   ```

## Is Google Sheets Really Free?

**Yes!** Google Sheets API is 100% free for reasonable usage:
- Free quota: 500 requests/100 seconds
- You won't hit this limit (you're reading once at startup)
- No credit card needed for the free tier

But CSV is still simpler if you don't need real-time collaboration!
