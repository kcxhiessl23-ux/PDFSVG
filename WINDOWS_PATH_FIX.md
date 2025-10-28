# Common Windows Path Errors - QUICK FIX

## The Problem

If you see this error:
```
SyntaxError: (unicode error) 'unicodeescape' codec can't decode bytes...
```

**You have a Windows path with backslashes that Python is trying to interpret as escape codes!**

---

## The Solution (Pick One)

### Option 1: Use Raw Strings (Easiest!)

Add `r` before the opening quote:

❌ **WRONG:**
```python
CREDENTIALS_FILE = "C:\Users\kschi\Desktop\file.json"
```

✅ **RIGHT:**
```python
CREDENTIALS_FILE = r"C:\Users\kschi\Desktop\file.json"
```

The `r` tells Python "this is a raw string, don't interpret backslashes"

---

### Option 2: Use Forward Slashes

Windows accepts forward slashes too!

✅ **ALSO RIGHT:**
```python
CREDENTIALS_FILE = "C:/Users/kschi/Desktop/file.json"
```

---

### Option 3: Use Double Backslashes

Escape each backslash with another backslash:

✅ **ALSO WORKS:**
```python
CREDENTIALS_FILE = "C:\\Users\\kschi\\Desktop\\file.json"
```

(But this is annoying to type!)

---

## For This Project

### You Don't Need Full Paths!

Just put these files in the same folder as your Python scripts:
- `google_credentials.json`
- `job_codes.csv`

Then use:
```python
GOOGLE_CREDENTIALS = "google_credentials.json"  # ← No path needed!
CSV_FILE = "job_codes.csv"
```

**Much simpler!**

---

## Where Are My Python Scripts?

You're running from:
```
C:\Users\kschi\OneDrive\Desktop\Placards\Pys\
```

So put `google_credentials.json` in that folder!

---

## Quick Test

After fixing, run this to test:
```bash
python address_lookup.py
```

If you see the setup message instead of an error, you fixed it!

---

## Examples from This Project

### ✅ Already Correct in label_processor.py:
```python
INPUT_FOLDER = r"C:\Users\kschi\OneDrive\Desktop\Placards\PDFs"
OUTPUT_FOLDER = r"C:\Users\kschi\OneDrive\Desktop\Placards\SVGs"
```

Notice the `r` before each string!

### ✅ Also Correct:
```python
GOOGLE_CREDENTIALS = "google_credentials.json"  # No path = same folder
```

---

## Why Does This Happen?

In Python strings, backslash (`\`) is an escape character:
- `\n` = newline
- `\t` = tab
- `\U` = Unicode character

So `"C:\Users\..."` tries to interpret `\U` as Unicode, which fails!

Using `r"C:\Users\..."` tells Python to ignore the backslashes as special characters.

---

## Bottom Line

**Always use `r"..."` for Windows paths in Python!**

Or just use filenames without paths if files are in the same folder.
