# ❄️ Project SnowFlake FTP

Project SnowFlake, siberpunk estetiğine ve karlı bir görsel atmosfere sahip, hafif, güvenli ve esnek bir yerel/uzak dosya yönetim (FTP) ve paylaşım sistemidir. Flask altyapısıyla geliştirilmiş olup, Raspberry Pi ve harici disk depolama senaryoları için özel olarak optimize edilmiştir.

---

## 🚀 Eklenen Başlıca Özellikler

* **🔐 Otomatik Kurulum ve Konfigürasyon (`setup.py`):** 
  * Proje ilk kez klonlandığında veya sıfır bir ortama kurulduğunda `python setup.py` komutuyla tüm dizinleri, çevresel değişkenleri ve şifreleme anahtarlarını otomatik oluşturur.
* **🛡️ Güvenli Harddisk ve Depo Taraması:** 
  * İlk kurulumda bağlı olan harddisk veya `tmp` deposundaki tüm mevcut dosyaları/yedekleri tarar ve varsayılan olarak **sadece admin (`admin`) kullanıcısının görebileceği şekilde kilitli (`public_access: False`)** olarak kaydeder.
* **🔑 PBKDF2 Şifreleme ve Benzersiz Salt:** 
  * Tüm kullanıcı şifreleri (varsayılan: `Helelele!`) rastgele 16-byte salt değerleriyle PBKDF2-HMAC-SHA256 algoritmasıyla hash'lenerek saklanır.
* **📁 77 MB Parçalı (Chunked) Yüksek Boyutlu Dosya Yükleme:** 
  * Büyük boyutlu video ve arşiv dosyalarını tarayıcı üzerinden parçalara bölerek (`XMLHttpRequest`) hata almadan yükler, gerçek zamanlı yüzdelik ilerleme çubuğu sunar.
* **🔗 Doğrudan (Direct) Public Link Paylaşımı:** 
  * İzin verilen dosyalar için ` /share/<yol> ` üzerinden doğrudan indirme ve görüntüleme linkleri üretilebilir. Paylaşıma kapalı dosyalara erişilmek istendiğinde sistem özel **404 Not Found** sayfasına yönlendirir.
* **⚡ Siberpunk Arayüz ve Dinamik Efektler:** 
  * HTML5 Canvas tabanlı interaktif kar yağışı efekti, kare simetrik grid (`200px x 200px`) kart yapısı, ekran ortası neon bildirimler (Toast) ve hatalı girişlerde / yetkisiz link kopyalamalarda 3 saniyelik kırmızı sallanma (shake) animasyonu.
* **⚙️ Hesap Yönetimi ve Özelleştirme:** 
  * Kullanıcıların kendi profil fotoğraflarını yükleyebilmesi (`.png`, `.jpg`), şifrelerini güvenli bir şekilde güncelleyebilmesi ve varsayılan şifre uyarı banner sistemi.