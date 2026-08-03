import os
import sys
import json
import base64
import hashlib
import shutil
import socket
from functools import wraps
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, send_from_directory

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

is_setup_done = os.getenv("SETUP", "").strip().lower() in ["true", "1"]
if not is_setup_done:
    print(f"\n{Fore.RED}[HATA] Sistem henüz kurulmamış veya setup tamamlanmamış!{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Lütfen önce 'python setup.py' komutunu çalıştırarak kurulumu tamamlayın.{Style.RESET_ALL}\n")
    sys.exit(1)

app = Flask(__name__)
app.secret_key = os.urandom(32)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

FTP_DIR = os.path.abspath(os.getenv("FTP_DIR", "tmp"))
PORT = int(os.getenv("PORT", 33337))

env_ip = os.getenv("PUBLIC_IP", "").strip()
PUBLIC_IP = env_ip if env_ip else get_local_ip()

DATABASE_DIR = os.path.abspath("database")
USERS_FILE = os.path.join(DATABASE_DIR, "users.json")
PERMISSIONS_FILE = os.path.join(DATABASE_DIR, "perms.json")
PP_DIR = os.path.abspath("static/img/pp")

def log_info(msg: str): print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} {msg}")
def log_success(msg: str): print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} {msg}")
def log_warning(msg: str): print(f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL} {msg}")
def log_error(msg: str): print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {msg}")

def hash_password(password: str, salt: bytes = None) -> str:
    if salt is None:
        salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return "HASH_" + base64.b64encode(salt + key).decode('utf-8')

def verify_password(stored_hash_with_prefix: str, password_attempt: str) -> bool:
    try:
        if not stored_hash_with_prefix.startswith("HASH_"):
            return False
        raw_b64 = stored_hash_with_prefix.replace("HASH_", "")
        decoded = base64.b64decode(raw_b64.encode('utf-8'))
        salt = decoded[:16]
        stored_key = decoded[16:]
        new_key = hashlib.pbkdf2_hmac('sha256', password_attempt.encode('utf-8'), salt, 100000)
        return new_key == stored_key
    except Exception:
        return False

def get_user_avatar(username):
    for ext in ['.png', '.jpg', '.jpeg']:
        filename = f"{username}{ext}"
        if os.path.isfile(os.path.join(PP_DIR, filename)):
            return f"img/pp/{filename}"
    return "img/default.png"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def load_permissions():
    if not os.path.exists(PERMISSIONS_FILE):
        return {}
    try:
        with open(PERMISSIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_permissions(perm_data):
    if not os.path.exists(DATABASE_DIR):
        os.makedirs(DATABASE_DIR, exist_ok=True)
    with open(PERMISSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(perm_data, f, indent=2, ensure_ascii=False)

def get_item_permission(rel_path):
    perms = load_permissions()
    default_perm = {"owner": "luffy", "public_access": False, "public": False}
    perm = perms.get(rel_path, default_perm)
    if "public" not in perm:
        perm["public"] = False
    return perm

def can_user_access_item(username, user_role, rel_path):
    if user_role == "admin":
        return True
    perm = get_item_permission(rel_path)
    if perm.get("public_access", False):
        return True
    return perm.get("owner") == username

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        users = load_users()
        
        if username in users and verify_password(users[username]["password_hash"], password):
            session.clear()
            session["username"] = username
            session["role"] = users[username].get("role", "user")
            return redirect(url_for("index"))
        else:
            session.clear()
            return render_template("snowflake.html", error="Kullanıcı adı veya şifre hatalı!")

    if "username" not in session:
        return render_template("snowflake.html")

    users = load_users()
    current_username = session["username"]
    current_role = session.get("role", "user")
    
    if current_username not in users:
        session.clear()
        return redirect(url_for("index"))

    current_user = users.get(current_username, {})
    user_avatar = get_user_avatar(current_username)

    rel_path = request.args.get("path", "").strip()
    target_dir = os.path.abspath(os.path.join(FTP_DIR, rel_path))
    
    if not target_dir.startswith(FTP_DIR):
        target_dir = FTP_DIR
        rel_path = ""

    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)

    klasorler = []
    dosyalar = []

    try:
        for item in os.listdir(target_dir):
            if item.startswith("."):
                continue
            item_path = os.path.join(target_dir, item)
            item_rel = os.path.relpath(item_path, FTP_DIR)

            if not can_user_access_item(current_username, current_role, item_rel):
                continue

            perm_info = get_item_permission(item_rel)

            if os.path.isdir(item_path):
                klasorler.append({
                    "name": item, 
                    "rel_path": item_rel, 
                    "public_access": perm_info.get("public_access", False),
                    "owner": perm_info.get("owner", "luffy")
                })
            else:
                size_bytes = os.path.getsize(item_path)
                size_mb = f"{size_bytes / (1024 * 1024):.1f} MB"
                dosyalar.append({
                    "name": item, 
                    "rel_path": item_rel, 
                    "size": size_mb,
                    "public_access": perm_info.get("public_access", False),
                    "public": perm_info.get("public", False),
                    "owner": perm_info.get("owner", "luffy")
                })
    except Exception as e:
        log_error(f"Dizin listeleme hatası: {e}")

    parent_path = None
    if rel_path and rel_path != ".":
        parent_dir = os.path.dirname(rel_path)
        parent_path = parent_dir if parent_dir != "." else ""

    total, used, free = shutil.disk_usage(FTP_DIR)
    disk_info = {
        "used": f"{used / (1024**3):.1f} GB",
        "total": f"{total / (1024**3):.1f} GB",
        "free": f"{free / (1024**3):.1f} GB",
        "percent": int((used / total) * 100)
    }

    server_base_url = f"http://{PUBLIC_IP}:{PORT}"

    return render_template(
        "snowflake.html",
        session=session,
        user_info=current_user,
        user_avatar=user_avatar,
        disk=disk_info,
        current_path=rel_path,
        parent_path=parent_path,
        klasorler=klasorler,
        dosyalar=dosyalar,
        server_base_url=server_base_url
    )

@app.route("/share/<path:rel_path>")
def share_link(rel_path):
    file_path = os.path.abspath(os.path.join(FTP_DIR, rel_path))
    if not file_path.startswith(FTP_DIR) or not os.path.isfile(file_path):
        return render_template("404.html"), 404

    perm_info = get_item_permission(rel_path)
    if not perm_info.get("public", False):
        return render_template("404.html"), 404

    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    return send_from_directory(directory, filename, as_attachment=True)

@app.route("/api/create-folder", methods=["POST"])
def create_folder():
    if "username" not in session:
        return jsonify({"status": "error", "message": "Oturum açın."}), 401

    data = request.get_json() or {}
    folder_name = data.get("folder_name", "").strip()
    current_path = data.get("current_path", "").strip()
    public_access = bool(data.get("public_access", False))

    if not folder_name:
        return jsonify({"status": "error", "message": "Klasör adı boş olamaz."}), 400

    target_dir = os.path.abspath(os.path.join(FTP_DIR, current_path, folder_name))
    if not target_dir.startswith(FTP_DIR) or os.path.exists(target_dir):
        return jsonify({"status": "error", "message": "Bu isimde bir klasör veya dosya zaten var!"}), 400

    try:
        os.makedirs(target_dir, exist_ok=True)
        rel_path = os.path.relpath(target_dir, FTP_DIR)
        perms = load_permissions()
        perms[rel_path] = {"owner": session["username"], "public_access": public_access, "public": False}
        save_permissions(perms)
        return jsonify({"status": "success", "message": "Klasör oluşturuldu."})
    except Exception as e:
        return jsonify({"status": "error", "message": "Oluşturulamadı."}), 500

@app.route("/api/toggle-permission", methods=["POST"])
def toggle_permission():
    if "username" not in session:
        return jsonify({"status": "error", "message": "Oturum açın."}), 401

    data = request.get_json() or {}
    rel_path = data.get("rel_path")
    key_name = data.get("key", "public_access")
    val = data.get("val")

    if not rel_path or val is None:
        return jsonify({"status": "error", "message": "İşlem yapılamaz."}), 400

    perms = load_permissions()
    item_perm = perms.get(rel_path, {"owner": session["username"], "public_access": False, "public": False})

    if session.get("role") != "admin" and item_perm.get("owner") != session["username"]:
        return jsonify({"status": "error", "message": "Yetkiniz yok."}), 403

    item_perm[key_name] = bool(val)
    perms[rel_path] = item_perm
    save_permissions(perms)
    return jsonify({"status": "success"})

@app.route("/api/change-password", methods=["POST"])
def change_password():
    if "username" not in session:
        return jsonify({"status": "error", "message": "Oturum açın."}), 401
    
    data = request.get_json() or {}
    old_password = data.get("old_password", "").strip()
    new_password = data.get("new_password", "").strip()

    users = load_users()
    user_data = users.get(session["username"])

    if not verify_password(user_data["password_hash"], old_password):
        return jsonify({"status": "error", "message": "Mevcut şifreniz hatalı."}), 400

    user_data["password_hash"] = hash_password(new_password)
    user_data["is_default_password"] = False
    save_users(users)
    return jsonify({"status": "success", "message": "Şifre güncellendi!"})

@app.route("/api/upload-avatar", methods=["POST"])
def upload_avatar():
    if "username" not in session:
        return jsonify({"status": "error", "message": "Yetkisiz."}), 401

    if 'avatar' not in request.files:
        return jsonify({"status": "error", "message": "Dosya seçilmedi."}), 400

    file = request.files['avatar']
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.png', '.jpg', '.jpeg']:
        return jsonify({"status": "error", "message": "Sadece PNG veya JPG."}), 400

    for old_ext in ['.png', '.jpg', '.jpeg']:
        old_file = os.path.join(PP_DIR, f"{session['username']}{old_ext}")
        if os.path.exists(old_file):
            os.remove(old_file)

    file.save(os.path.join(PP_DIR, f"{session['username']}{ext}"))
    return jsonify({"status": "success"})

@app.route("/yukle", methods=["POST"])
def yukle():
    if "username" not in session:
        return jsonify({"error": "Yetkisiz"}), 401

    file_chunk = request.files.get("video_chunk")
    filename = request.form.get("filename")
    chunk_index = int(request.form.get("chunkIndex", 0))
    total_chunks = int(request.form.get("totalChunks", 1))
    current_path = request.form.get("current_path", "").strip()

    if not file_chunk or not filename:
        return jsonify({"error": "Eksik veri"}), 400

    upload_dir = os.path.abspath(os.path.join(FTP_DIR, current_path))
    if not upload_dir.startswith(FTP_DIR):
        upload_dir = FTP_DIR

    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)

    mode = "wb" if chunk_index == 0 else "ab"
    with open(file_path, mode) as f:
        f.write(file_chunk.read())

    if chunk_index + 1 == total_chunks:
        rel_path = os.path.relpath(file_path, FTP_DIR)
        perms = load_permissions()
        perms[rel_path] = {"owner": session["username"], "public_access": False, "public": False}
        save_permissions(perms)
        log_success(f"Dosya yüklendi: {filename}")

    return jsonify({"status": "success"})

@app.route("/indir")
def indir():
    if "username" not in session:
        return redirect(url_for("index"))

    rel_path = request.args.get("path", "").strip()
    file_path = os.path.abspath(os.path.join(FTP_DIR, rel_path))

    if not file_path.startswith(FTP_DIR) or not os.path.isfile(file_path):
        return "Dosya bulunamadı", 404

    if not can_user_access_item(session["username"], session.get("role", "user"), rel_path):
        return "Yetkiniz yok!", 403

    return send_from_directory(os.path.dirname(file_path), os.path.basename(file_path), as_attachment=True)

@app.route("/logout")
def logout():
    session.clear()
    res = redirect(url_for("index"))
    res.set_cookie(app.config.get("SESSION_COOKIE_NAME", "session"), "", expires=0)
    return res

if __name__ == "__main__":
    log_info(f"Yayınlanan IP/URL: http://{PUBLIC_IP}:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=True)