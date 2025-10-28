"""
Google Sheets Address Lookup Module
Fetches addresses from a Google Sheet based on job codes
"""
import gspread
from google.oauth2.service_account import Credentials

# ========== CONFIG ==========
GOOGLE_SHEET_NAME = "Job Codes"  # ← Name of your Google Sheet
WORKSHEET_NAME = "Sheet1"  # ← Name of the worksheet tab
JOB_CODE_COLUMN = "A"  # ← Column containing job codes (e.g., "002KALA")
ADDRESS_COLUMN = "B"  # ← Column containing addresses

# Google Sheets API credentials file path
# Option 1: Just filename (file must be in same folder as this script)
CREDENTIALS_FILE = "google_credentials.json"

# Option 2: Full path (use raw string with r"..." or forward slashes)
# CREDENTIALS_FILE = r"C:\Users\YourName\Path\To\google_credentials.json"
# CREDENTIALS_FILE = "C:/Users/YourName/Path/To/google_credentials.json"


class AddressLookup:
    def __init__(self):
        self.sheet = None
        self.address_cache = {}

    def connect(self):
        """Connect to Google Sheets and load the address data"""
        try:
            # Define the scopes (use full access to avoid permission errors)
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]

            # Authenticate
            creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
            client = gspread.authorize(creds)

            # Open the sheet
            self.sheet = client.open(GOOGLE_SHEET_NAME).worksheet(WORKSHEET_NAME)

            # Load all data into cache
            self._load_cache()

            print(f"✓ Connected to Google Sheet: {GOOGLE_SHEET_NAME}")
            print(f"✓ Loaded {len(self.address_cache)} job codes")
            return True

        except FileNotFoundError:
            print(f"✗ Credentials file not found: {CREDENTIALS_FILE}")
            print("\nTo set up Google Sheets access:")
            print("1. Go to https://console.cloud.google.com/")
            print("2. Create a new project")
            print("3. Enable Google Sheets API")
            print("4. Create a Service Account")
            print("5. Download the JSON credentials file")
            print("6. Save it as 'google_credentials.json'")
            return False

        except Exception as e:
            print(f"✗ Failed to connect to Google Sheets: {e}")
            return False

    def _load_cache(self):
        """Load all job codes and addresses into memory for fast lookup"""
        # Get all values from columns A and B
        all_data = self.sheet.get_all_values()

        # Skip header row if it exists
        for row in all_data[1:]:  # Skip first row (header)
            if len(row) >= 2:
                job_code = row[0].strip().upper()
                address = row[1].strip()

                if job_code and address:
                    self.address_cache[job_code] = address

    def get_address(self, job_code):
        """
        Get address for a job code

        Args:
            job_code: Job code (e.g., "002KALA", "053FAIR")

        Returns:
            str: Address if found, None if not found
        """
        job_code = job_code.strip().upper()
        return self.address_cache.get(job_code)

    def get_address_with_fallback(self, job_code):
        """
        Get address with helpful error message if not found

        Args:
            job_code: Job code (e.g., "002KALA")

        Returns:
            str: Address if found, error message if not found
        """
        address = self.get_address(job_code)

        if address:
            return address
        else:
            return f"ADDRESS NOT FOUND FOR {job_code}"


# Simple test function
def test_lookup():
    """Test the address lookup functionality"""
    print("="*60)
    print("TESTING GOOGLE SHEETS ADDRESS LOOKUP")
    print("="*60)

    lookup = AddressLookup()

    if not lookup.connect():
        print("\n✗ Failed to connect to Google Sheets")
        return

    # Test with some job codes
    test_codes = ["002KALA", "053FAIR", "003ESTR", "999TEST"]

    print("\n" + "="*60)
    print("TESTING LOOKUPS")
    print("="*60)

    for code in test_codes:
        address = lookup.get_address(code)
        if address:
            print(f"✓ {code}: {address}")
        else:
            print(f"✗ {code}: NOT FOUND")


if __name__ == "__main__":
    test_lookup()
