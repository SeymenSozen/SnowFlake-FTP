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