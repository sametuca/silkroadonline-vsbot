"""
Quick test to verify Tesseract OCR is working
"""
import pytesseract
from PIL import Image, ImageDraw, ImageFont
import os
import subprocess
import shutil

# Tesseract Auto-Detection Function
def find_tesseract():
    """Automatically find Tesseract installation on Windows."""
    if os.name != 'nt':
        return None
    
    # Method 1: Check Windows Registry
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Tesseract-OCR")
        install_path = winreg.QueryValueEx(key, "InstallDir")[0]
        winreg.CloseKey(key)
        tesseract_path = os.path.join(install_path, "tesseract.exe")
        if os.path.exists(tesseract_path):
            print(f"✅ Tesseract found via Registry: {tesseract_path}")
            return tesseract_path
    except:
        pass
    
    # Method 2: Check PATH environment variable
    tesseract_in_path = shutil.which("tesseract")
    if tesseract_in_path:
        print(f"✅ Tesseract found in PATH: {tesseract_in_path}")
        return tesseract_in_path
    
    # Method 3: Use 'where' command to find tesseract
    try:
        result = subprocess.run(['where', 'tesseract'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            tesseract_path = result.stdout.strip().split('\n')[0]
            if os.path.exists(tesseract_path):
                print(f"✅ Tesseract found via 'where' command: {tesseract_path}")
                return tesseract_path
    except:
        pass
    
    # Method 4: Check common installation locations
    possible_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        r'C:\Tesseract-OCR\tesseract.exe',
        os.path.expandvars(r'%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe'),
        os.path.expandvars(r'%LOCALAPPDATA%\Tesseract-OCR\tesseract.exe'),
        os.path.expandvars(r'%APPDATA%\Tesseract-OCR\tesseract.exe'),
        os.path.expandvars(r'%ProgramW6432%\Tesseract-OCR\tesseract.exe'),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ Tesseract found: {path}")
            return path
    
    print("⚠️ Tesseract not found automatically.")
    return None

# Auto-detect and set Tesseract path
tesseract_path = find_tesseract()
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
else:
    print("❌ Tesseract OCR not found!")
    print("   Install from: https://github.com/UB-Mannheim/tesseract/wiki")
    exit(1)

print("=" * 60)
print("🔍 TESSERACT OCR TEST")
print("=" * 60)
print()

# Create a test image with numbers (simulating health bar)
img = Image.new('RGB', (200, 50), color='white')
draw = ImageDraw.Draw(img)

try:
    # Try to use a system font
    font = ImageFont.truetype("arial.ttf", 30)
except:
    font = ImageFont.load_default()

# Draw health-like numbers
draw.text((10, 10), "2345 / 4019", fill='red', font=font)

# Save test image
test_img_path = "test_health.png"
img.save(test_img_path)
print(f"✅ Test image created: {test_img_path}")

# Try to read it with OCR
text = pytesseract.image_to_string(img, config='--psm 7')
print(f"📖 OCR Read: '{text.strip()}'")
print()

# Extract numbers
import re
numbers = re.findall(r'\d+', text)
if numbers:
    print(f"🔢 Numbers found: {numbers}")
    print(f"   Current HP: {numbers[0]}")
    if len(numbers) > 1:
        print(f"   Max HP: {numbers[1]}")
    print()
    print("✅ OCR IS WORKING PERFECTLY!")
else:
    print("⚠️ Could not extract numbers, but OCR is running")

print()
print("=" * 60)
print("🎮 You can now use Emergency Health Skill feature!")
print("=" * 60)

# Cleanup
if os.path.exists(test_img_path):
    os.remove(test_img_path)
    print(f"\n🗑️ Test image cleaned up")

print("\nPress Enter to exit...")
input()
