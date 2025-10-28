"""
Simple CSV Address Lookup Module
No Google Cloud, no API keys, no complexity!
Just a simple CSV file on your computer.
"""
import csv
import os

class CSVAddressLookup:
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.address_cache = {}
        self.connected = False

    def connect(self):
        """Load addresses from CSV file"""
        if not os.path.exists(self.csv_file):
            print(f"⚠ CSV file not found: {self.csv_file}")
            print(f"  Create a file called '{self.csv_file}' with this format:")
            print(f"  Job Code,Address")
            print(f"  002KALA,123 Main Street, Los Angeles, CA 90001")
            print(f"  053FAIR,456 Oak Avenue, Sacramento, CA 95814")
            return False

        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                # Check if required columns exist
                if 'Job Code' not in reader.fieldnames or 'Address' not in reader.fieldnames:
                    print(f"✗ CSV file must have 'Job Code' and 'Address' columns")
                    print(f"  Current columns: {reader.fieldnames}")
                    return False

                # Load data
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
        """Get address for a job code"""
        if not self.connected:
            return None
        return self.address_cache.get(job_code.strip().upper())


# Test function
def test_csv_lookup():
    """Test the CSV address lookup"""
    print("="*60)
    print("TESTING CSV ADDRESS LOOKUP")
    print("="*60)

    lookup = CSVAddressLookup("job_codes.csv")

    if not lookup.connect():
        print("\n✗ Failed to load CSV file")
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
    test_csv_lookup()
