@echo off
title Tesseract OCR Kurulum Yardımcısı
echo ============================================================
echo   TESSERACT OCR KURULUM YARDIMCISI
echo ============================================================
echo.
echo Bu program Tesseract OCR'in kurulu olup olmadigini kontrol eder.
echo.
pause
echo.
echo Kontrol ediliyor...

REM Check if tesseract is installed
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo.
    echo ============================================================
    echo   ✅ TESSERACT ZATEN KURULU!
    echo ============================================================
    echo.
    echo Konum: C:\Program Files\Tesseract-OCR\tesseract.exe
    echo.
    echo Botu calistirabilirsin! run_gui.bat dosyasini calistir.
    echo.
    pause
    exit
)

echo.
echo ============================================================
echo   ❌ TESSERACT KURULU DEGIL!
echo ============================================================
echo.
echo Tesseract OCR programini indirip kurman gerekiyor.
echo.
echo İNDİRME LİNKİ:
echo https://github.com/UB-Mannheim/tesseract/wiki
echo.
echo VEYA DİREKT İNDİR:
echo https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe
echo.
echo KURULUM:
echo 1. Indirdigim .exe dosyasini calistir
echo 2. Varsayilan ayarlarla kur: C:\Program Files\Tesseract-OCR
echo 3. Kurulum bittikten sonra botu tekrar baslat
echo.
echo.
set /p answer="Indirme sayfasini tarayicida acmak ister misin? (E/H): "

if /i "%answer%"=="E" (
    echo.
    echo Tarayici aciliyor...
    start https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    echo Sayfadan indirip kurduktan sonra botu yeniden baslat!
)

echo.
echo ============================================================
pause
