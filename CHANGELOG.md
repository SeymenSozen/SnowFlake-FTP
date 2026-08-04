# 📜 Changelog

Project SnowFlake FTP ile ilgili tüm sürüm değişiklikleri bu dosyada kronolojik olarak listelenmektedir.

---

## [Alpha v1.0.0] - 2026-08-04

### ✨ Eklenenler ve Özellikler
* **Oto-Kurulum (`setup.py`):** `.env` dosyasına `SETUP=True` bayrağı eklendi; eksik dizinlerin ve anahtarların otomatik üretilmesi sağlandı.
* **Güvenlik Mimarisi:** Harddisk taraması ile mevcut dosyaların varsayılan olarak yalnızca `admin` (admin) kullanıcısına kilitlenmesi sağlandı.
* **Şifreleme:** `1234!` varsayılan şifresi için her kullanıcıya özel rastgele salt değerleriyle PBKDF2 SHA-256 hash altyapısı kuruldu.
* **Dosya Yönetimi:** 77 MB chunk tabanlı kesintisiz yükleme altyapısı ve klasör bazlı izin (`perms.json`) yönetimi entegre edildi.
* **UI / UX Geliştirmeleri:** 
  * İnteraktif Canvas kar efekti eklendi.
  * Siberpunk tarzı glitch efektli özel `404 Not Found` sayfası tasarlandı.
  * Hatalı girişlerde ve yetkisiz kopyalamalarda kırmızı shake (sallanma) animasyonları devreye alındı.
  * Sandviç menü (3 nokta) üzerinden dosya/klasör izinleri ve paylaşım linki kopyalama özellikleri eklendi.

## [1.2.0] - 2026-08-04

### ✨ Eklenenler ve Yenilikler
* **Sürükle-Bırak Desteği:** Dosya ve klasörleri fareyle tutup doğrudan başka bir klasörün veya en alttaki **Geri Dönüştür** kutusunun üzerine bırakarak taşıma özelliği eklendi.
* **Akıllı Çakışma Önleme (Collision Handling):** Aynı isimde dosya/klasör yüklenirken, taşınırken veya çöp kutusuna atılırken üzerine yazma engellendi; otomatik olarak `_1`, `_2` şeklinde numaralandırma sistemi getirildi.
* **Geri Dönüştür (Çöp Kutusu) Entegrasyonu:** Admin ana dizininde ham `bin` klasörü gizlenerek yerine şık, temaya uygun özel bir **Geri Dönüştür** kartı yerleştirildi.
* **Çöp Kutusu Güvenliği:** Çöp kutusu içerisindeki dosyalara doğrudan tıklanması engellendi; tıklandığında kart kırmızı renkte titreşerek uyarı vermesi sağlandı.

### 🎨 Arayüz ve Tasarım İyileştirmeleri
* **Hizalama Düzenlemeleri:** Kart içi ayarlar menüsünde bulunan başlık satırı ve çöp kutusu ikonu aynı satıra (en sağa) hizalandı.
* **Siberpunk Onay Mekanizması:** Klasik tarayıcı `confirm` pencereleri kaldırılarak projeye özel cyberpunk tarzı onay kartları entegre edildi.