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
FILES_FILE = os.path.join(DATABASE_DIR, "files.json")
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

def save_users(users_data):
    if not os.path.exists(DATABASE_DIR):
        os.makedirs(DATABASE_DIR, exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users_data, f, indent=2, ensure_ascii=False)

def load_files_meta():
    if not os.path.exists(FILES_FILE):
        return {}
    try:
        with open(FILES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_files_meta(file_data):
    if not os.path.exists(DATABASE_DIR):
        os.makedirs(DATABASE_DIR, exist_ok=True)
    with open(FILES_FILE, "w", encoding="utf-8") as f:
        json.dump(file_data, f, indent=2, ensure_ascii=False)

def get_item_permission(rel_path):
    files_meta = load_files_meta()
    current_user = session.get("username", "user")
    default_perm = {
        "owner": current_user, 
        "public_access": False, 
        "public": False,
        "is_edited": False,    # İlk yüklemede kapalı (False) gelsin
        "is_priority": False,  # Öncelikli varsayılan kapalı (False) gelsin
        "color": ""
    }
    perm = files_meta.get(rel_path, default_perm)
    if "public" not in perm:
        perm["public"] = False
    if "is_edited" not in perm:
        perm["is_edited"] = False  # Eksikse False atasın
    if "is_priority" not in perm:
        perm["is_priority"] = False
    if "color" not in perm:
        perm["color"] = ""
    return perm

def can_user_access_item(username, user_role, rel_path):
    if user_role == "admin":
        return True
    
    if user_role == "editor":
        video_extensions = ('.mkv', '.mp4', '.mov', '.zip', '.avi', '.wmv', '.flv', '.webm', '.mpeg', '.mpg', '.3gp', '.m4v','mp3','wav','flac','aac','ogg')
        if rel_path.lower().endswith(video_extensions):
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

    bin_info = {"size": "0 MB", "count": 0}
    bin_folder_path = os.path.join(FTP_DIR, "bin")
    if rel_path == "" and os.path.exists(bin_folder_path):
        b_size = 0
        b_count = 0
        for root, dirs, files in os.walk(bin_folder_path):
            for file in files:
                fp = os.path.join(root, file)
                if os.path.isfile(fp):
                    b_size += os.path.getsize(fp)
                    b_count += 1
        
        if b_size >= (1024 ** 3):
            bin_size_formatted = f"{b_size / (1024**3):.2f} GB"
        else:
            bin_size_formatted = f"{b_size / (1024**2):.1f} MB"
            
        bin_info = {"size": bin_size_formatted, "count": b_count}

    try:
        for item in os.listdir(target_dir):
            if item.startswith("."):
                continue
            
            if item == "bin" and rel_path == "":
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
                    "owner": perm_info.get("owner", current_username)
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
                    "owner": perm_info.get("owner", current_username),
                    "is_edited": perm_info.get("is_edited", False),
                    "is_priority": perm_info.get("is_priority", False),
                    "color": perm_info.get("color", "")
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
        bin_info=bin_info,
        server_base_url=server_base_url
    )

def get_unique_path(dest_dir, filename):
    base, ext = os.path.splitext(filename)
    counter = 1
    destination_path = os.path.join(dest_dir, filename)
    while os.path.exists(destination_path):
        filename = f"{base}_{counter}{ext}"
        destination_path = os.path.join(dest_dir, filename)
        counter += 1
    return destination_path, filename

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

    target_dir = os.path.abspath(os.path.join(FTP_DIR, current_path))
    destination_path, unique_folder_name = get_unique_path(target_dir, folder_name)

    if not destination_path.startswith(FTP_DIR):
        return jsonify({"status": "error", "message": "Geçersiz dizin!"}), 400

    try:
        os.makedirs(destination_path, exist_ok=True)
        rel_path = os.path.relpath(destination_path, FTP_DIR)
        files_meta = load_files_meta()
        files_meta[rel_path] = {"owner": session["username"], "public_access": public_access, "public": False, "is_edited": False, "is_priority": False, "color": ""}
        save_files_meta(files_meta)
        return jsonify({"status": "success", "message": "Klasör oluşturuldu."})
    except Exception as e:
        return jsonify({"status": "error", "message": "Oluşturulamadı."}), 500

@app.route("/api/toggle-permission", methods=["POST"])
def toggle_permission():
    if "username" not in session:
        return jsonify({"status": "error", "message": "Oturum açın."}), 401

    data = request.get_json() or {}
    rel_path = data.get("rel_path")
    key_name = data.get("key")
    val = data.get("val")

    if not rel_path or not key_name or val is None:
        return jsonify({"status": "error", "message": "İşlem yapılamaz."}), 400

    files_meta = load_files_meta()
    default_perm = {
        "owner": session["username"], 
        "public_access": False, 
        "public": False,
        "is_edited": False,
        "is_priority": False,
        "color": ""
    }
    
    item_perm = files_meta.get(rel_path, default_perm.copy())

    if session.get("role") != "admin" and item_perm.get("owner") != session["username"]:
        return jsonify({"status": "error", "message": "Yetkiniz yok."}), 403

    if key_name in ["public_access", "public", "is_edited", "is_priority"]:
        item_perm[key_name] = bool(val)
    elif key_name == "color":
        item_perm[key_name] = str(val).strip()

    files_meta[rel_path] = item_perm
    save_files_meta(files_meta)
    return jsonify({"status": "success"})

@app.route("/api/delete-item", methods=["POST"])
def delete_item():
    if "username" not in session:
        return jsonify({"status": "error", "message": "Oturum açın."}), 401

    data = request.get_json() or {}
    rel_path = data.get("rel_path", "").strip()

    if not rel_path:
        return jsonify({"status": "error", "message": "Geçersiz dosya/klasör."}), 400

    target_path = os.path.abspath(os.path.join(FTP_DIR, rel_path))
    if not target_path.startswith(FTP_DIR) or not os.path.exists(target_path):
        return jsonify({"status": "error", "message": "Öğe bulunamadı."}), 404

    if rel_path == "bin" or rel_path.startswith("bin" + os.sep):
        return jsonify({"status": "error", "message": "Çöp kutusu dizini silinemez!"}), 403

    try:
        bin_dir = os.path.join(FTP_DIR, "bin")
        os.makedirs(bin_dir, exist_ok=True)

        item_name = os.path.basename(target_path)
        destination_path, new_filename = get_unique_path(bin_dir, item_name)

        shutil.move(target_path, destination_path)

        files_meta = load_files_meta()
        if rel_path in files_meta:
            del files_meta[rel_path]
            save_files_meta(files_meta)

        log_success(f"Öğe çöp kutusuna taşındı: {rel_path} -> bin/{new_filename}")
        return jsonify({"status": "success", "message": "Öğe çöp kutusuna taşındı."})
    except Exception as e:
        log_error(f"Silme hatası: {e}")
        return jsonify({"status": "error", "message": "Öğe taşınamadı."}), 500

@app.route("/api/empty-bin", methods=["POST"])
def empty_bin():
    if "username" not in session:
        return jsonify({"status": "error", "message": "Oturum açın."}), 401
    
    bin_dir = os.path.abspath(os.path.join(FTP_DIR, "bin"))
    if not os.path.exists(bin_dir):
        return jsonify({"status": "success", "message": "Çöp kutusu zaten boş."})

    try:
        for item in os.listdir(bin_dir):
            item_path = os.path.join(bin_dir, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
                
        log_success("Çöp kutusu başarıyla boşaltıldı.")
        return jsonify({"status": "success", "message": "Çöp kutusu boşaltıldı."})
    except Exception as e:
        log_error(f"Çöp kutusu boşaltılamadı: {e}")
        return jsonify({"status": "error", "message": "Çöp kutusu boşaltılırken hata oluştu."}), 500

@app.route("/api/move-item", methods=["POST"])
def move_item():
    if "username" not in session:
        return jsonify({"status": "error", "message": "Oturum açın."}), 401

    data = request.get_json() or {}
    source_rel = data.get("source_rel", "").strip()
    target_folder_rel = data.get("target_folder_rel", "").strip()

    if not source_rel:
        return jsonify({"status": "error", "message": "Geçersiz kaynak."}), 400

    source_path = os.path.abspath(os.path.join(FTP_DIR, source_rel))
    if not source_path.startswith(FTP_DIR) or not os.path.exists(source_path):
        return jsonify({"status": "error", "message": "Kaynak öğe bulunamadı."}), 404

    if target_folder_rel == "bin":
        dest_dir = os.path.abspath(os.path.join(FTP_DIR, "bin"))
    else:
        dest_dir = os.path.abspath(os.path.join(FTP_DIR, target_folder_rel))

    if not dest_dir.startswith(FTP_DIR) or not os.path.exists(dest_dir):
        return jsonify({"status": "error", "message": "Hedef dizin bulunamadı."}), 404

    try:
        item_name = os.path.basename(source_path)
        destination_path, new_filename = get_unique_path(dest_dir, item_name)

        if source_path == destination_path or destination_path.startswith(source_path + os.sep):
            return jsonify({"status": "error", "message": "Bir klasör kendi içine taşınamaz!"}), 400

        shutil.move(source_path, destination_path)

        files_meta = load_files_meta()
        new_rel_path = os.path.relpath(destination_path, FTP_DIR)
        if source_rel in files_meta:
            files_meta[new_rel_path] = files_meta.pop(source_rel)
            save_files_meta(files_meta)

        log_success(f"Öğe taşındı: {source_rel} -> {new_rel_path}")
        return jsonify({"status": "success", "message": "Öğe başarıyla taşındı."})
    except Exception as e:
        log_error(f"Taşıma hatası: {e}")
        return jsonify({"status": "error", "message": "Öğe taşınamadı."}), 500

@app.route("/api/change-password", methods=["POST"])
def change_password():
    if "username" not in session:
        return jsonify({"status": "error", "message": "Oturum açın."}), 401
    
    data = request.get_json() or {}
    old_password = data.get("old_password", "").strip()
    new_password = data.get("new_password", "").strip()

    users = load_users()
    username = session["username"]
    user_data = users.get(username)

    if not verify_password(user_data["password_hash"], old_password):
        return jsonify({"status": "error", "message": "Mevcut şifreniz hatalı."}), 400

    default_plain = user_data.get("default_password_plain", "")
    is_still_default = (new_password == default_plain)

    user_data["password_hash"] = hash_password(new_password)
    user_data["is_default_password"] = is_still_default
    
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

    unique_avatar_path, unique_avatar_name = get_unique_path(PP_DIR, f"{session['username']}{ext}")
    file.save(unique_avatar_path)
    return jsonify({"status": "success"})


@app.route("/api/update-color", methods=["POST"])
def update_color():
    if "username" not in session:
        return jsonify({"status": "error", "message": "Oturum açın."}), 401
    
    data = request.get_json() or {}
    color = data.get("color", "").strip()

    if not color:
        return jsonify({"status": "error", "message": "Geçersiz renk."}), 400

    users = load_users()
    username = session["username"]
    
    if username in users:
        users[username]["color"] = color
        save_users(users)
        return jsonify({"status": "success", "message": "Renk kaydedildi!"})
    
    return jsonify({"status": "error", "message": "Kullanıcı bulunamadı."}), 404

@app.route("/api/rename-item", methods=["POST"])
def rename_item():
    if "username" not in session:
        return jsonify({"status": "error", "message": "Oturum açın."}), 401

    data = request.get_json() or {}
    rel_path = data.get("rel_path", "").strip()
    new_name_base = data.get("new_name", "").strip()

    if not rel_path or not new_name_base:
        return jsonify({"status": "error", "message": "Geçersiz veriler."}), 400

    target_path = os.path.abspath(os.path.join(FTP_DIR, rel_path))
    if not target_path.startswith(FTP_DIR) or not os.path.exists(target_path):
        return jsonify({"status": "error", "message": "Dosya bulunamadı."}), 404

    dir_name = os.path.dirname(target_path)
    old_filename = os.path.basename(target_path)
    ext = os.path.splitext(old_filename)[1]

    new_filename = new_name_base + ext
    new_path = os.path.join(dir_name, new_filename)

    if os.path.exists(new_path):
        return jsonify({"status": "error", "message": "Bu isimde bir dosya zaten var!"}), 400

    try:
        os.rename(target_path, new_path)
        
        parent_dir_rel = os.path.dirname(rel_path)
        new_rel_path = os.path.join(parent_dir_rel, new_filename) if parent_dir_rel else new_filename
        
        files_meta = load_files_meta()
        if rel_path in files_meta:
            files_meta[new_rel_path] = files_meta.pop(rel_path)
            save_files_meta(files_meta)

        log_success(f"Dosya yeniden adlandırıldı: {old_filename} -> {new_filename}")
        return jsonify({"status": "success", "message": "Dosya yeniden adlandırıldı."})
    except Exception as e:
        log_error(f"Yeniden adlandırma hatası: {e}")
        return jsonify({"status": "error", "message": "Dosya yeniden adlandırılamadı."}), 500

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

    mode = "wb" if chunk_index == 0 else "ab"
    
    session_key = f"active_upload_{filename}"
    
    if chunk_index == 0:
        file_path, unique_filename = get_unique_path(upload_dir, filename)
        session[session_key] = unique_filename
    else:
        active_name = session.get(session_key, filename)
        file_path = os.path.join(upload_dir, active_name)

    with open(file_path, mode) as f:
        f.write(file_chunk.read())

    if chunk_index + 1 == total_chunks:
        final_filename = session.get(session_key, filename)
        final_file_path = os.path.join(upload_dir, final_filename)
        rel_path = os.path.relpath(final_file_path, FTP_DIR)
        
        files_meta = load_files_meta()
        files_meta[rel_path] = {
            "owner": session["username"], 
            "public_access": False, 
            "public": False,
            "is_edited": False,  # İlk yüklemede kapalı gelsin
            "is_priority": False,
            "color": ""
        }
        save_files_meta(files_meta)
        log_success(f"Dosya yüklendi: {final_filename}")
        
        session.pop(session_key, None)

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