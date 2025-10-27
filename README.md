# domain.com Ürün Kazıyıcı

Bu proje,  adresinden ürün adları, fiyatlar, açıklamalar, resimler, varyasyonlar ve beden bilgileri gibi ürün verilerini kazır. Veriler, kolay analiz ve kullanım için CSV formatında dışa aktarılır.

## Özellikler

- domain.com'dan ürün bilgilerini çıkarır
- Ürün adları, fiyatlar, açıklamalar ve resimleri toplar
- Verileri CSV formatında düzenler
- Ürün varyasyonlarını ve beden seçeneklerini işler
- Yüksek kaliteli ürün resimlerini dışa aktarır

## Dosyalar

- `domain_all_products.csv` - Tam ürün verisi (149 ürün)
- `scrape_domain.py` - requests ve BeautifulSoup kullanan temel kazıma betiği
- `advanced_scraper.py` - Geliştirilmiş seçicilerle daha iyi kazıma betiği
- `final_scraper.py` - Son ve kapsamlı kazıma betiği
- `selenium_scraper.py` - Dinamik içerik için Selenium tabanlı kazıma betiği

## Veri Örneği

CSV dosyası aşağıdaki sütunları içerir:
- Ürün URL'si
- Ürün Adı
- Fiyat
- Açıklama
- Resimler (noktalı virgülle ayrılmış URL'ler)
- Varyasyonlar
- Bedenler

Örnek ürünler:
- Kadife Gold Detay Elbise: ₺999,99
- Kolsuz Balıkçı Yumoş Triko: ₺399,99
- Asimetrik Yaka Poliamid Bluz: ₺399,99

## Gereksinimler

- Python 3.x
- requests
- beautifulsoup4
- pandas
- selenium (selenium_scraper.py için)
- webdriver-manager (selenium_scraper.py için)

## Kurulum

```bash
pip install -r requirements.txt
```

## Kullanım

Kazıma betiğini çalıştırmak için:

```bash
python final_scraper.py
```

Bu işlem tam ürün verilerini içeren bir CSV dosyası oluşturacaktır.

Dinamik içerik kazıması için:
```bash
python selenium_scraper.py
```

## Proje Yapısı

```
├── domain_all_products.csv      # 149 ürünle ana çıktı dosyası
├── scrape_domain.py             # requests kullanan temel kazıyıcı
├── advanced_scraper.py         # Geliştirilmiş seçicilerle kazıyıcı
├── final_scraper.py            # Son ve kapsamlı kazıyıcı
├── selenium_scraper.py         # JS içeriği için Selenium tabanlı kazıyıcı
├── requirements.txt            # Python bağımlılıkları
├── README.md                   # Bu dosya
├── LICENSE                     # MIT Lisansı
└── .gitignore                  # Git yoksay dosyası
```

## Lisans

Bu proje MIT Lisansı altında lisanslanmıştır - detaylar için [LICENSE](LICENSE) dosyasına bakın.

## Feragatname

Bu proje yalnızca eğitim amaçlıdır. Veri kazırken lütfen web sitesinin hizmet şartlarına ve robots.txt dosyasına uyun. Her zaman bir web sitesinden kazıma yapma izniniz olduğundan emin olun ve kullanım politikalarına uygun davranın.
