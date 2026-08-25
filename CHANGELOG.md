# 📜 Changelog

Project SnowFlake FTP ile ilgili tüm sürüm değişiklikleri bu dosyada kronolojik olarak listelenmektedir.


## [1.3.0] - 2026-08-25

### ✨ Eklenenler ve Yenilikler

* **Çoklu Dosya Yükleme ve İşlemler Paneli:** Aynı anda birden fazla dosyanın sürükle-bırak veya dosya seçici ile yüklenebilmesi sağlandı; sağ altta anlık ilerleme yüzdelerini ve ayrı ayrı yatay progress bar'ları gösteren **İşlemler (Yüklemeler)** paneli eklendi.
* **Yükleme Kontrolü (İptal Desteği):** Sağ alttaki işlemler paneline eklenen **Durdur** butonu sayesinde devam eden dosya yüklemelerinin anlık olarak iptal edilebilmesi sağlandı.
* **Akıllı Sıralı Kuyruk (Queue) Mimarisi:** Çoklu dosya yüklemelerinde sunucu tarafında çakışmaların (race condition) önlenmesi için dosyaların eşzamanlı yerine sırasıyla (teker teker) yüklenmesi sağlandı.
* **Dinamik Panel Gizleme:** Sağ alttaki işlemler paneli yalnızca aktif bir yükleme varken görünür hale getirildi; yüklemeler tamamlandığında otomatik olarak gizlenip sayfanın güncel içeriği listelemesi sağlandı.
* **Gelişmiş Dosya Yönetimi ve Yeniden Adlandırma:** Dosya ayarları menüsüne uzantı korumalı yeniden adlandırma inputu entegre edildi.
* **Özelleştirilmiş Varsayılan Durumlar:** Yeni yüklenen dosya ve klasörlerin varsayılan olarak düzenleme durumu (`is_edited`) kapalı (`False`) gelecek şekilde güncellendi.
* **Rol Tabanlı Erişim Güncellemeleri:** `user3` kullanıcısı `editor` rolüyle sisteme dahil edilerek video/arşiv uzantılı dosyalara erişim yetkisi yapılandırıldı.

## [1.2.0] - 2026-08-04

### ✨ Eklenenler ve Yenilikler
* **Sürükle-Bırak Desteği:** Dosya ve klasörleri fareyle tutup doğrudan başka bir klasörün veya en alttaki **Geri Dönüştür** kutusunun üzerine bırakarak taşıma özelliği eklendi.
* **Akıllı Çakışma Önleme (Collision Handling):** Aynı isimde dosya/klasör yüklenirken, taşınırken veya çöp kutusuna atılırken üzerine yazma engellendi; otomatik olarak `_1`, `_2` şeklinde numaralandırma sistemi getirildi.
* **Geri Dönüştür (Çöp Kutusu) Entegrasyonu:** Admin ana dizininde ham `bin` klasörü gizlenerek yerine şık, temaya uygun özel bir **Geri Dönüştür** kartı yerleştirildi.
* **Çöp Kutusu Güvenliği:** Çöp kutusu içerisindeki dosyalara doğrudan tıklanması engellendi; tıklandığında kart kırmızı renkte titreşerek uyarı vermesi sağlandı.

### 🎨 Arayüz ve Tasarım İyileştirmeleri
* **Hizalama Düzenlemeleri:** Kart içi ayarlar menüsünde bulunan başlık satırı ve çöp kutusu ikonu aynı satıra (en sağa) hizalandı.
* **Siberpunk Onay Mekanizması:** Klasik tarayıcı `confirm` pencereleri kaldırılarak projeye özel cyberpunk tarzı onay kartları entegre edildi.

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

