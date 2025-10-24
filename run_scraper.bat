@echo off
title Bbeox.com Ürün Kazıyıcı

echo Bbeox.com Ürün Kazıyıcı başlatılıyor...
echo ======================================

REM Python'un yüklü olup olmadığını kontrol edin
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python bulunamadı. Lütfen Python'u yükleyin.
    pause
    exit /b 1
)

REM Gerekli paketleri yükleyin
echo Gerekli paketler yükleniyor...
pip install -r requirements.txt

REM Kazıyıcıyı çalıştırın
echo Kazıyıcı çalıştırılıyor...
python final_scraper.py

echo Kazıma tamamlandı!
echo Sonuçlar için bbeox_all_products.csv dosyasını kontrol edin.
pause