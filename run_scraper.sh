#!/bin/bash

# Bbeox.com Ürün Kazıyıcı
# Bu betiği bbeox.com'dan ürün verilerini kazımak için çalıştırın

echo "Bbeox.com Ürün Kazıyıcı başlatılıyor..."
echo "======================================"

# Python'un yüklü olup olmadığını kontrol edin
if ! command -v python3 &> /dev/null
then
    echo "Python3 bulunamadı. Lütfen Python3'ü yükleyin."
    exit 1
fi

# Gerekli paketleri yükleyin
echo "Gerekli paketler yükleniyor..."
pip install -r requirements.txt

# Kazıyıcıyı çalıştırın
echo "Kazıyıcı çalıştırılıyor..."
python3 final_scraper.py

echo "Kazıma tamamlandı!"
echo "Sonuçlar için bbeox_all_products.csv dosyasını kontrol edin."