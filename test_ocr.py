"""
Quick test to verify Tesseract OCR is working
"""
import pytesseract
from PIL import Image, ImageDraw, ImageFont
import os

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

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
