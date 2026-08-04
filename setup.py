import os
import json
import base64
import hashlib

try:
    import yaml
except ImportError:
    yaml = None

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class DummyColor:
        def __getattr__(self, name): return ""
    Fore = Style = DummyColor()

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

DATABASE_DIR = os.path.abspath("database")
KEYS_DIR = os.path.abspath("keys")
PP_DIR = os.path.abspath("static/img/pp")
SCHEMAS_DIR = os.path.abspath("schemas")
FTP_DIR = os.path.abspath(os.getenv("FTP_DIR", "tmp"))

USERS_FILE = os.path.join(DATABASE_DIR, "users.json")
PERMISSIONS_FILE = os.path.join(DATABASE_DIR, "perms.json")

def log_info(msg): print(f"{Fore.CYAN}[SETUP INFO]{Style.RESET_ALL} {msg}")
def log_success(msg): print(f"{Fore.GREEN}[SETUP SUCCESS]{Style.RESET_ALL} {msg}")
def log_warning(msg): print(f"{Fore.YELLOW}[SETUP WARNING]{Style.RESET_ALL} {msg}")
def log_error(msg): print(f"{Fore.RED}[SETUP ERROR]{Style.RESET_ALL} {msg}")

def hash_password(password: str, salt: bytes = None) -> str:
    if salt is None:
        salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return "HASH_" + base64.b64encode(salt + key).decode('utf-8')

def init_directories():
    directories = [DATABASE_DIR, KEYS_DIR, PP_DIR, SCHEMAS_DIR, FTP_DIR]
    for d in directories:
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
            log_info(f"Dizin oluşturuldu: {d}")

    # default.yml yoksa schemas içine otomatik oluştur
    default_yml_path = os.path.join(SCHEMAS_DIR, "default.yml")
    if not os.path.exists(default_yml_path):
        default_yaml_content = (
            "users:\n"
            "  admin:\n"
            "    password: \"admin\"\n"
            "    role: \"admin\"\n"
            "  user:\n"
            "    password: \"user\"\n"
            "    role: \"user\"\n"
        )
        with open(default_yml_path, "w", encoding="utf-8") as f:
            f.write(default_yaml_content)
        log_success("Varsayılan şema oluşturuldu -> schemas/default.yml")

    env_path = os.path.abspath(".env")
    has_setup_flag = False
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            if "SETUP=True" in f.read():
                has_setup_flag = True

    if not has_setup_flag:
        default_env = (
            "# Setup ( Buraya dokunma )\n"
            "SETUP=True\n\n"
            "PORT=33337\n"
            "FTP_DIR=tmp\n"
            "SECRET_KEY_PATH=keys/secret.key\n"
            "PUBLIC_IP=\n"
        )
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(default_env)
        log_success(".env dosyasına '# Setup ( Buraya dokunma )' ve SETUP=True eklendi.")

def setup_keys():
    os.makedirs(KEYS_DIR, exist_ok=True)

    secret_key_path = os.path.join(KEYS_DIR, "secret.key")
    if not os.path.exists(secret_key_path) or os.path.getsize(secret_key_path) == 0:
        with open(secret_key_path, "w", encoding="utf-8") as f:
            f.write(os.urandom(32).hex())
        log_success(f"Session gizli anahtarı oluşturuldu -> {secret_key_path}")

    wget_key_path = os.path.join(KEYS_DIR, "wget.key")
    if not os.path.exists(wget_key_path) or os.path.getsize(wget_key_path) == 0:
        hashed_wget_key = hash_password("admin")
        with open(wget_key_path, "w", encoding="utf-8") as f:
            f.write(hashed_wget_key)
        log_success(f"Wget yetki anahtarı oluşturuldu -> {wget_key_path}")

    private_pem_path = os.path.join(KEYS_DIR, "private.pem")
    public_pem_path = os.path.join(KEYS_DIR, "public.pem")

    if not os.path.exists(private_pem_path) or not os.path.exists(public_pem_path):
        if HAS_CRYPTOGRAPHY:
            private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            pem_private = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            with open(private_pem_path, "wb") as f: f.write(pem_private)

            public_key = private_key.public_key()
            pem_public = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            with open(public_pem_path, "wb") as f: f.write(pem_public)
            log_success("RSA Anahtar çifti üretildi (private.pem / public.pem)")
        else:
            log_warning("'cryptography' kütüphanesi kurulu olmadığı için .pem anahtarları atlandı.")

def get_target_schema_file():
    default_yml = os.path.join(SCHEMAS_DIR, "default.yml")

    if yaml is None:
        log_warning("PyYAML kütüphanesi yüklü değil, doğrudan default.yml şeması kullanılacak.")
        return default_yml

    try:
        if not os.path.exists(SCHEMAS_DIR):
            return default_yml

        yml_files = [f for f in os.listdir(SCHEMAS_DIR) if f.endswith(".yml") or f.endswith(".yaml")]
        custom_files = [f for f in yml_files if f.lower() not in ["default.yml", "default.yaml"]]

        if custom_files:
            custom_filename = custom_files[0]
            custom_path = os.path.join(SCHEMAS_DIR, custom_filename)
            
            try:
                with open(custom_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and isinstance(data, dict) and "users" in data:
                        log_info(f"Özel şema dosyası bulundu: {custom_filename}. Veritabanı buna göre kurulacaktır.")
                        return custom_path
                    else:
                        log_warning(f"'{custom_filename}' dosyası boş veya geçersiz formatta!")
            except Exception as parse_err:
                log_error(f"'{custom_filename}' dosyasında hata bulundu: {parse_err}")
                log_warning("Güvenli geçiş yapılıyor: 'default.yml' çalıştırılacaktır.")
        
        log_info("Veritabanı 'default.yml' şemasına göre kurulacaktır.")
    except Exception as e:
        log_error(f"Şemalar taranırken hata oluştu: {e}")
        log_warning("Güvenli geçiş yapılıyor: 'default.yml' çalıştırılacaktır.")

    return default_yml

def setup_users():
    if not os.path.exists(USERS_FILE):
        schema_path = get_target_schema_file()
        users_dict = {}

        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                raw_data = yaml.safe_load(f) or {}
                raw_users = raw_data.get("users", {})
                
                for uname, udata in raw_users.items():
                    raw_pass = udata.get("password", "user")
                    role = udata.get("role", "user")
                    users_dict[uname] = {
                        "password_hash": hash_password(raw_pass),
                        "role": role,
                        "default_password_plain": raw_pass,
                        "is_default_password": True,
                        "bytes_uploaded": 0,
                        "bytes_downloaded": 0
                    }
            log_success(f"Kullanıcı veritabanı şema dosyasından yüklendi -> {os.path.basename(schema_path)}")
        except Exception as e:
            log_error(f"Şema okunurken kritik hata: {e}")

        if not users_dict:
            users_dict = {
                "admin": {
                    "password_hash": hash_password("admin"),
                    "role": "admin",
                    "default_password_plain": "admin",
                    "is_default_password": True,
                    "bytes_uploaded": 0,
                    "bytes_downloaded": 0
                },
                "user": {
                    "password_hash": hash_password("user"),
                    "role": "user",
                    "default_password_plain": "user",
                    "is_default_password": True,
                    "bytes_uploaded": 0,
                    "bytes_downloaded": 0
                }
            }

        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users_dict, f, indent=2, ensure_ascii=False)
        log_success(f"Kullanıcı veritabanı kaydedildi -> {USERS_FILE}")

def setup_permissions_scan():
    perms = {}
    if os.path.exists(PERMISSIONS_FILE):
        try:
            with open(PERMISSIONS_FILE, "r", encoding="utf-8") as f:
                perms = json.load(f)
        except Exception:
            perms = {}

    log_info(f"Depo klasörü taranıyor: {FTP_DIR}")
    scanned_count = 0

    for root, dirs, files in os.walk(FTP_DIR):
        for item in dirs + files:
            if item.startswith("."):
                continue
            full_path = os.path.join(root, item)
            rel_path = os.path.relpath(full_path, FTP_DIR)

            if rel_path not in perms:
                perms[rel_path] = {
                    "owner": "admin",
                    "public_access": False,
                    "public": False
                }
                scanned_count += 1

    with open(PERMISSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(perms, f, indent=2, ensure_ascii=False)

    if scanned_count > 0:
        log_success(f"{scanned_count} adet dosya/klasör taranıp 'admin'e kilitli olarak kaydedildi -> {PERMISSIONS_FILE}")
    else:
        log_info(f"Tüm izinler güncel -> {PERMISSIONS_FILE}")

if __name__ == "__main__":
    print(f"\n{Fore.MAGENTA}==========================================")
    print(f"{Fore.MAGENTA}   SNOWFLAKE FTP OTO-KURULUM SCRIPTI     ")
    print(f"{Fore.MAGENTA}=========================================={Style.RESET_ALL}\n")
    
    init_directories()
    setup_keys()
    setup_users()
    setup_permissions_scan()

    print(f"\n{Fore.GREEN}[✓] Kurulum başarıyla tamamlandı, Luffy! Proje çalışmaya hazır.{Style.RESET_ALL}\n")