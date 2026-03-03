"""
Koordinat Bulucu - Can barının yerini bulmak için
Mouse pozisyonunu gösterir ve SPACE tuşuna basarak kaydet
"""
import pyautogui
import keyboard
import time

print("=" * 60)
print("🎯 KOORDİNAT BULUCU")
print("=" * 60)
print()
print("NASIL KULLANILIR:")
print("1. Oyunu aç ve can barını görebileceğin şekilde konumlan")
print("2. Mouse'u can numarasının SOL ÜST köşesine getir")
print("3. SPACE tuşuna bas (1. nokta kaydedilir)")
print("4. Mouse'u can numarasının SAĞ ALT köşesine getir")
print("5. SPACE tuşuna tekrar bas (2. nokta kaydedilir)")
print("6. Koordinatlar otomatik hesaplanacak!")
print()
print("Çıkmak için ESC tuşuna bas")
print("=" * 60)
print()

time.sleep(2)
print("🖱️  Mouse pozisyonu gösteriliyor... (SPACE = kaydet, ESC = çık)")
print()

points = []

while len(points) < 2:
    if keyboard.is_pressed('esc'):
        print("\n❌ İptal edildi!")
        break
        
    # Mouse pozisyonunu göster
    pos = pyautogui.position()
    print(f"\r🖱️  X: {pos.x:4d}  Y: {pos.y:4d}  ", end="", flush=True)
    
    # SPACE tuşuna basılınca kaydet
    if keyboard.is_pressed('space'):
        points.append((pos.x, pos.y))
        if len(points) == 1:
            print(f"\n✅ 1. NOKTA kaydedildi: ({pos.x}, {pos.y})")
            print("   Şimdi SAĞ ALT köşeye getir ve tekrar SPACE'e bas...")
            time.sleep(0.5)  # Çift basışı önle
        elif len(points) == 2:
            print(f"\n✅ 2. NOKTA kaydedildi: ({pos.x}, {pos.y})")
            time.sleep(0.5)
    
    time.sleep(0.05)

if len(points) == 2:
    # Koordinatları hesapla
    x1, y1 = points[0]
    x2, y2 = points[1]
    
    x = min(x1, x2)
    y = min(y1, y2)
    width = abs(x2 - x1)
    height = abs(y2 - y1)
    
    print()
    print("=" * 60)
    print("🎉 KOORDİNATLAR BULUNDU!")
    print("=" * 60)
    print()
    print(f"📍 X:      {x}")
    print(f"📍 Y:      {y}")
    print(f"📍 Width:  {width}")
    print(f"📍 Height: {height}")
    print()
    print("Bu değerleri bot GUI'deki 'Set Health Bar Region' penceresine gir!")
    print("=" * 60)
    
    # Dosyaya da kaydet
    with open("health_region.txt", "w", encoding="utf-8") as f:
        f.write(f"X: {x}\n")
        f.write(f"Y: {y}\n")
        f.write(f"Width: {width}\n")
        f.write(f"Height: {height}\n")
    print("\n💾 Koordinatlar 'health_region.txt' dosyasına da kaydedildi!")

print("\n✨ Program sonlandı. Enter'a bas...")
input()
