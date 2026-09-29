# Toplu Barkod & Kargo Etiket Sistemi - Proje Hafızası

Bu doküman, "toplu_barkod" projesinin mimari yapısını, etiket formatlarını, iş kurallarını ve geliştirme standartlarını kalıcı olarak hafızaya kaydeder.

---

## 1. Proje Mimarisi ve Çalışma Prensibi

* **Konum:** `C:\Users\ugurk\OneDrive\Masaüstü\toplu_barkod`
* **Web Arayüzü & Sunucu:** `app.py` (Flask tabanlı, 127.0.0.1:5005 portunda çalışır).
* **Çekirdek Motor:** `core_barcode.py` (Excel/CSV okuma, dinamik sütun tespiti ve ReportLab 100mm x 100mm PDF üretim motoru).
* **Ön Yüz (Frontend):**
  * `templates/index.html`
  * `static/css/style.css`
  * `static/js/app.js`
  * `static/js/JsBarcode.all.min.js` (Tamamen internetsiz / offline çalışan vektörel barkod kütüphanesi).
* **Başlatıcılar:**
  * Proje içindeki `baslat.bat`.
  * Masaüstündeki doğrudan başlatıcı: `C:\Users\ugurk\OneDrive\Masaüstü\Toplu_Barkod_Programi.bat`.

---

## 2. Etiket Formatı & Düzeni (10cm x 10cm Termal Rulo)

Kullanıcının talep ettiği kargo etiket şablonuna göre 10cm x 10cm (100mm x 100mm) yerleşim şu şekildedir:

1. **ÜST KISIM (Müşteri & Sevk Bilgileri - Ortalanmış):**
   - **Müşteri Adı Soyadı:** Kalın (Bold), 13pt (Örn: `mehmet ali tezcan`).
   - **Adres:** 10pt (Örn: `çelebiler mahalesi 1409 sokak no:2 MERKEZ`).
   - **(İlçe) İl:** 10pt (Örn: `(Isparta) Isparta`).
   - **Telefon:** 10.5pt (Örn: `0(532) 231 78 65`).
2. **ORTA KISIM (Barkod):**
   - Standart 1D Barkod (Code 128), yüksek okunabilirlik, 24mm yükseklik.
   - Altında ortalanmış okunabilir barkod numarası (Örn: `1092488`).
3. **ALT KISIM (Kullanıcının Kırmızı ile Çizdiği Alan):**
   - **Ürün Adı:** Kalın (Bold), 12pt, ortalanmış, uzun ürün adlarında otomatik küçülen ve sarılan tipografi (Örn: `Tefal FV5715 Easygliss Plus 2400 W Buharlı Ütü Kırmızı/Siyah`).
   - Çoklu adet durumunda ince Adet belirteci (`Adet: 1/2`).

---

## 3. Dinamik Sütun Tespiti (Pazaryeri & Excel Uyumu)

* **Müşteri:** `sevk - müşteri`, `müşteri`, `alıcı`, `ad soyad`, `isim`, `customer`
* **Adres:** `sevk - adres`, `adres`, `teslimat adresi`, `address`
* **İlçe:** `sevk - ilçe`, `ilçe`, `district`
* **İl:** `sevk - il`, `il`, `şehir`, `city`
* **Telefon:** `sevk - telefon`, `sevk - tel`, `telefon`, `tel`, `gsm`
* **Barkod:** `kargo barkod`, `paket no`, `kargo takip no`, `barkod`, `barcode`, `sipariş no`
* **Ürün Adı:** `ürün`, `ürün adı`, `product name`, `title`, `başlık`
* **Adet:** `adet`, `miktar`, `sipariş adedi`, `qty`

* **Çoklu Paket Oranı (1/2, 2/2 Kuralı):** Yalnızca aynı sipariş numarasına sahip etiket adedi 1'den fazla ise (örneğin 2 paket/parça ise) barkodun sağ tarafında kalın olarak `1/2`, `2/2` yazılır. Tekil siparişlerde (`tot == 1`) sağ taraf tamamen boş bırakılır.
