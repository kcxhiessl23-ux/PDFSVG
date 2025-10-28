"""
Google Sheets Setup Verification Tool
Run this to make sure your Google Sheets connection is working!
"""
import os

print("="*60)
print("GOOGLE SHEETS SETUP VERIFICATION")
print("="*60)

# ========== CONFIG ==========
GOOGLE_SHEET_NAME = "Job Codes"  # ← Change if you used a different name
GOOGLE_WORKSHEET = "Sheet1"      # ← Change if you used a different tab name
GOOGLE_CREDENTIALS = "google_credentials.json"

# Step 1: Check credentials file exists
print("\n[Step 1/5] Checking credentials file...")
if not os.path.exists(GOOGLE_CREDENTIALS):
    print(f"✗ FAILED: {GOOGLE_CREDENTIALS} not found!")
    print("\nWhat to do:")
    print("1. Go to Google Cloud Console")
    print("2. Create service account (see GOOGLE_SHEETS_SETUP_SIMPLE.md)")
    print("3. Download JSON key file")
    print(f"4. Save it as '{GOOGLE_CREDENTIALS}' in this folder")
    print(f"\nCurrent folder: {os.getcwd()}")
    exit(1)
else:
    print(f"✓ Found: {GOOGLE_CREDENTIALS}")

# Step 2: Check if file is valid JSON
print("\n[Step 2/5] Validating credentials file...")
try:
    import json
    with open(GOOGLE_CREDENTIALS, 'r') as f:
        creds_data = json.load(f)

    if 'client_email' in creds_data:
        print(f"✓ Valid credentials file")
        print(f"  Service account email: {creds_data['client_email']}")
        print(f"\n  ⚠ IMPORTANT: Make sure you shared your Google Sheet with this email!")
    else:
        print("✗ Invalid credentials file (missing client_email)")
        exit(1)
except Exception as e:
    print(f"✗ Failed to read credentials: {e}")
    exit(1)

# Step 3: Check if required libraries are installed
print("\n[Step 3/5] Checking required libraries...")
try:
    import gspread
    print("✓ gspread installed")
except ImportError:
    print("✗ gspread not installed")
    print("\nRun: pip install gspread google-auth")
    exit(1)

try:
    from google.oauth2.service_account import Credentials
    print("✓ google-auth installed")
except ImportError:
    print("✗ google-auth not installed")
    print("\nRun: pip install gspread google-auth")
    exit(1)

# Step 4: Try to authenticate
print("\n[Step 4/5] Testing authentication...")
try:
    # Use full spreadsheets scope (not just readonly) and Drive scope as fallback
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS, scopes=scopes)
    client = gspread.authorize(creds)
    print("✓ Authentication successful")
except Exception as e:
    print(f"✗ Authentication failed: {e}")
    print("\nPossible issues:")
    print("- Credentials file is corrupted")
    print("- Service account was deleted")
    print("- Download the credentials file again")
    exit(1)

# Step 5: Try to open the sheet
print("\n[Step 5/5] Connecting to Google Sheet...")
try:
    sheet = client.open(GOOGLE_SHEET_NAME)
    print(f"✓ Found sheet: {GOOGLE_SHEET_NAME}")

    try:
        worksheet = sheet.worksheet(GOOGLE_WORKSHEET)
        print(f"✓ Found worksheet: {GOOGLE_WORKSHEET}")
    except Exception as e:
        print(f"✗ Worksheet '{GOOGLE_WORKSHEET}' not found")
        print(f"\nAvailable worksheets:")
        for ws in sheet.worksheets():
            print(f"  - {ws.title}")
        print(f"\nUpdate GOOGLE_WORKSHEET in your config to match one of these")
        exit(1)

    # Try to read data
    all_data = worksheet.get_all_values()

    if len(all_data) == 0:
        print("⚠ Sheet is empty!")
        print("\nAdd data to your sheet:")
        print("  Row 1: Job Code | Address")
        print("  Row 2: 002KALA | 123 Main St, Los Angeles, CA 90001")
        exit(1)

    print(f"✓ Successfully read {len(all_data)} rows")

    # Check if headers are correct
    if len(all_data) > 0:
        headers = all_data[0]
        print(f"\n  Headers found: {headers}")

        if len(headers) < 2:
            print("  ⚠ Warning: Expected at least 2 columns (Job Code, Address)")

        # Show first few rows
        print(f"\n  First 3 rows of data:")
        for i, row in enumerate(all_data[:4]):  # Show header + 3 data rows
            if i == 0:
                print(f"    Header: {row}")
            else:
                print(f"    Row {i}: {row}")

except gspread.exceptions.SpreadsheetNotFound:
    print(f"✗ Sheet '{GOOGLE_SHEET_NAME}' not found!")
    print("\nPossible issues:")
    print("1. Sheet name is wrong (check spelling and capitalization)")
    print("2. You didn't share the sheet with the service account email")
    print(f"\nService account email: {creds_data['client_email']}")
    print("\nWhat to do:")
    print("1. Open your Google Sheet")
    print("2. Click 'Share' button")
    print("3. Add the service account email above")
    print("4. Give it 'Viewer' or 'Editor' access")
    print("5. Click 'Send'")
    exit(1)

except Exception as e:
    print(f"✗ Failed to open sheet: {e}")
    exit(1)

# Success!
print("\n" + "="*60)
print("✓ SUCCESS! Google Sheets is ready!")
print("="*60)
print(f"\nConfiguration:")
print(f"  Sheet name: {GOOGLE_SHEET_NAME}")
print(f"  Worksheet: {GOOGLE_WORKSHEET}")
print(f"  Rows: {len(all_data)-1} (excluding header)")
print(f"\nYou can now run: python label_processor.py")
