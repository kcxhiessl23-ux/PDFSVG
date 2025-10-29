@echo off
echo ========================================
echo SAFE SVG EXTRACTION TEST
echo ========================================
echo.
echo This tests the new clean extraction method
echo WITHOUT touching your main code!
echo.
echo Make sure you have:
echo - Created TEST_PDFs folder
echo - Copied 2-3 PDFs there for testing
echo.
pause

cd /d "C:\Users\kschi\OneDrive\Desktop\Placards\Pys"
"C:\Users\kschi\AppData\Local\Programs\Python\Python312\python.exe" test_clean_extraction.py

echo.
echo ========================================
echo Check TEST_SVGs folder for results!
echo ========================================
pause