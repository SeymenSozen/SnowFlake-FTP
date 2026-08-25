const canvas = document.getElementById('snowCanvas');
if (canvas) {
    const ctx = canvas.getContext('2d');
    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;
    let mouseX = width / 2;

    window.addEventListener('resize', () => { width = canvas.width = window.innerWidth; height = canvas.height = window.innerHeight; mouseX = width / 2; });
    window.addEventListener('mousemove', (e) => { mouseX = e.clientX; });

    const particles = [];
    const colors = ['rgba(255,255,255,0.2)', 'rgba(102,252,241,0.25)', 'rgba(69,243,255,0.15)'];

    for (let i = 0; i < 90; i++) {
        particles.push({
            x: Math.random() * width, y: Math.random() * height,
            r: Math.random() * 1.5 + 0.5, d: Math.random() * 0.2 + 0.05,
            color: colors[Math.floor(Math.random() * colors.length)], tilt: Math.random() * 10
        });
    }

    let angle = 0;
    function drawParticles() {
        ctx.clearRect(0, 0, width, height);
        angle += 0.005;
        const wind = (mouseX - width / 2) * 0.001;
        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];
            ctx.beginPath(); ctx.fillStyle = p.color; ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2, true); ctx.fill();
            p.y += p.d; p.x += Math.sin(angle + p.tilt) * 0.2 + wind;
            if (p.x > width + 5 || p.x < -5 || p.y > height) {
                particles[i] = { x: Math.random() * width, y: -10, r: p.r, d: p.d, color: p.color, tilt: p.tilt };
            }
        }
        requestAnimationFrame(drawParticles);
    }
    drawParticles();
}

function showToast(message) {
    const toast = document.getElementById('toast-notification');
    const toastText = document.getElementById('toast-text');
    if (toast && toastText) {
        toastText.textContent = message;
        toast.classList.remove('hidden');
        setTimeout(() => {
            toast.classList.add('hidden');
        }, 2500);
    }
}

function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        return navigator.clipboard.writeText(text);
    } else {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed";
        textArea.style.left = "-999999px";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        return new Promise((resolve, reject) => {
            document.execCommand('copy') ? resolve() : reject();
            textArea.remove();
        });
    }
}

window.isDragging = false;

function handleDragStart(event, relPath) {
    window.isDragging = true;
    event.dataTransfer.setData('text/plain', relPath);
    document.querySelectorAll('.card-menu-popup').forEach(el => el.classList.add('hidden'));
}

document.addEventListener('dragend', () => {
    setTimeout(() => { window.isDragging = false; }, 100);
});

function handleDragOver(event) {
    event.preventDefault();
}

async function handleDrop(event, targetFolderRel) {
    event.preventDefault();
    window.isDragging = false;
    const sourceRel = event.dataTransfer.getData('text/plain');

    if (!sourceRel || sourceRel === targetFolderRel) return;

    try {
        const res = await fetch("/api/move-item", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ source_rel: sourceRel, target_folder_rel: targetFolderRel })
        });
        const data = await res.json();

        if (res.ok) {
            showToast("Öğe başarıyla taşındı.");
            setTimeout(() => { location.reload(); }, 600);
        } else {
            alert(data.message || "Taşıma başarısız!");
        }
    } catch (err) {
        alert("Bağlantı hatası oluştu!");
    }
}

async function handleDropToBin(event) {
    event.preventDefault();
    window.isDragging = false;
    const sourceRel = event.dataTransfer.getData('text/plain');

    if (!sourceRel) return;

    try {
        const res = await fetch("/api/move-item", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ source_rel: sourceRel, target_folder_rel: "bin" })
        });
        const data = await res.json();

        if (res.ok) {
            showToast("Öğe çöp kutusuna taşındı.");
            setTimeout(() => { location.reload(); }, 600);
        } else {
            alert(data.message || "Çöp kutusuna taşınamadı!");
        }
    } catch (err) {
        alert("Bağlantı hatası oluştu!");
    }
}

function toggleCardMenu(event, relPath) {
    event.stopPropagation();
    event.preventDefault();
    
    document.querySelectorAll('.card-menu-popup').forEach(el => {
        if (el.id !== `menu-${relPath}`) el.classList.add('hidden');
    });

    const menu = document.getElementById(`menu-${relPath}`);
    if (menu) {
        menu.classList.toggle('hidden');
    }
}

function toggleBinMenu(event) {
    event.stopPropagation();
    event.preventDefault();
    const menu = document.getElementById('binDropdownMenu');
    if (menu) {
        menu.classList.toggle('hidden');
    }
}

function emptyBin() {
    if (!confirm("Çöp kutusundaki tüm öğeler kalıcı olarak silinecek. Emin misiniz?")) return;

    fetch('/api/empty-bin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            showToast("Çöp kutusu boşaltıldı.");
            setTimeout(() => { location.reload(); }, 800);
        } else {
            alert(data.message || "Bir hata oluştu.");
        }
    })
    .catch(err => {
        alert("Bağlantı hatası oluştu!");
    });
}

document.addEventListener('click', (e) => {
    if (!e.target.closest('.card-menu-popup') && !e.target.closest('.menu-trigger-btn') && !e.target.closest('.bin-menu-container')) {
        document.querySelectorAll('.card-menu-popup').forEach(el => el.classList.add('hidden'));
        const binMenu = document.getElementById('binDropdownMenu');
        if (binMenu) binMenu.classList.add('hidden');
    }
});

function copyShareLink(relPath, isPublic, menuId, btnElement) {
    const popupMenu = document.getElementById(menuId);
    const errorMsg = document.getElementById(`share-error-${relPath}`);

    if (!isPublic) {
        popupMenu.classList.add('shake-error');
        btnElement.classList.add('btn-error');
        if (errorMsg) errorMsg.classList.remove('hidden');

        setTimeout(() => {
            popupMenu.classList.remove('shake-error');
            btnElement.classList.remove('btn-error');
            if (errorMsg) errorMsg.classList.add('hidden');
        }, 3000);
        return;
    }

    const serverBaseUrl = document.getElementById('server-base-url').value;
    const shareUrl = `${serverBaseUrl}/share/${relPath}`;

    copyToClipboard(shareUrl).then(() => {
        showToast(`Bağlantı kopyalandı!\n${shareUrl}`);
        const svg = btnElement.querySelector('.copy-svg-icon');
        if (svg) svg.setAttribute('stroke', '#45f3ff');
        
        setTimeout(() => {
            if (svg) svg.setAttribute('stroke', '#66fcf1');
        }, 2000);
    }).catch(err => {
        showToast("Link kopyalanamadı!");
    });
}

function deleteItem(relPath, itemName) {
    const existingModal = document.getElementById('custom-confirm-modal');
    if (existingModal) existingModal.remove();

    const backdrop = document.createElement('div');
    backdrop.id = 'custom-confirm-modal';
    backdrop.className = 'custom-confirm-backdrop';

    backdrop.innerHTML = `
        <div class="custom-confirm-card">
            <h4>SİSTEM UYARISI</h4>
            <p>"<strong>${itemName}</strong>" adlı öğeyi çöp kutusuna taşımak istediğinize emin misiniz?</p>
            <div class="custom-confirm-btns">
                <button type="button" class="confirm-no-btn" id="confirm-cancel">VAZGEÇ</button>
                <button type="button" class="confirm-yes-btn" id="confirm-ok">EMİNİM</button>
            </div>
        </div>
    `;

    document.body.appendChild(backdrop);

    document.getElementById('confirm-cancel').onclick = () => {
        backdrop.remove();
    };

    document.getElementById('confirm-ok').onclick = async () => {
        backdrop.remove();
        try {
            const res = await fetch("/api/delete-item", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ rel_path: relPath })
            });
            const data = await res.json();

            if (res.ok) {
                showToast("Öğe çöp kutusuna taşındı.");
                setTimeout(() => { location.reload(); }, 1000);
            } else {
                alert(data.message || "Silinemedi!");
            }
        } catch (err) {
            alert("Bağlantı hatası oluştu!");
        }
    };
}

function triggerBinLockEffect(element) {
    const cardBox = element.closest('.box');
    if (cardBox) {
        cardBox.classList.add('shake-error');
        showToast("Çöp kutusundaki dosyalar doğrudan açılamaz!");
        setTimeout(() => {
            cardBox.classList.remove('shake-error');
        }, 400);
    }
}

const createFolderBtn = document.getElementById('create-folder-btn');
if (createFolderBtn) {
    createFolderBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const popupMenu = document.getElementById('menu-upload-zone');
        const folderNameInput = document.getElementById('new-folder-input');
        const folderPublicInput = document.getElementById('new-folder-public');
        const folderErrorMsg = document.getElementById('folder-error-msg');
        const currentPath = document.getElementById('current-path').value;

        const folder_name = folderNameInput.value.trim();
        const public_access = folderPublicInput.checked;

        if (!folder_name) {
            triggerErrorEffect("Lütfen bir isim girin!");
            return;
        }

        try {
            const res = await fetch("/api/create-folder", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    folder_name: folder_name,
                    current_path: currentPath,
                    public_access: public_access
                })
            });
            const data = await res.json();

            if (res.ok) {
                location.reload();
            } else {
                triggerErrorEffect(data.message || "Bu isimde bir klasör zaten var!");
            }
        } catch (err) {
            triggerErrorEffect("Bağlantı koptu!");
        }

        function triggerErrorEffect(msgText) {
            popupMenu.classList.add('shake-error');
            folderNameInput.classList.add('input-error');
            createFolderBtn.classList.add('btn-error');
            
            folderErrorMsg.textContent = msgText;
            folderErrorMsg.classList.remove('hidden');

            setTimeout(() => {
                popupMenu.classList.remove('shake-error');
                folderNameInput.classList.remove('input-error');
                createFolderBtn.classList.remove('btn-error');
                folderErrorMsg.classList.add('hidden');
            }, 3000);
        }
    });
}

async function handlePermToggle(relPath, keyName, isChecked, copyBtnId = null) {
    try {
        const res = await fetch("/api/toggle-permission", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ rel_path: relPath, key: keyName, val: isChecked })
        });
        const data = await res.json();

        if (res.ok) {
            if (keyName === 'public' && copyBtnId) {
                const copyBtn = document.getElementById(copyBtnId);
                if (copyBtn) {
                    copyBtn.setAttribute('onclick', `copyShareLink('${relPath}', ${isChecked}, 'menu-${relPath}', this)`);
                }
            }
        } else {
            alert(data.message || "İzin güncellenemedi!");
            location.reload();
        }
    } catch (err) {
        alert("Bağlantı hatası oluştu!");
    }
}

async function handleFileMetaToggle(relPath, key, val) {
    try {
        const res = await fetch("/api/toggle-permission", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ rel_path: relPath, key: key, val: val })
        });
        if (res.ok) {
            location.reload();
        } else {
            alert("Güncellenemedi!");
        }
    } catch (err) {
        alert("Bağlantı hatası!");
    }
}

async function handleFileColorChange(relPath, color) {
    try {
        const res = await fetch("/api/toggle-permission", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ rel_path: relPath, key: "color", val: color })
        });
        if (res.ok) {
            location.reload();
        } else {
            alert("Renk atanamadı!");
        }
    } catch (err) {
        alert("Bağlantı hatası!");
    }
}

async function renameFile(relPath, fileExt, inputId) {
    const inputElement = document.getElementById(inputId);
    const newBaseName = inputElement.value.trim();

    if (!newBaseName) {
        alert("Dosya adı boş olamaz!");
        return;
    }

    try {
        const res = await fetch("/api/rename-item", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ rel_path: relPath, new_name: newBaseName })
        });
        const data = await res.json();

        if (res.ok) {
            showToast("Öğe yeniden adlandırıldı.");
            setTimeout(() => { location.reload(); }, 600);
        } else {
            alert(data.message || "Yeniden adlandırılamadı!");
        }
    } catch (err) {
        alert("Bağlantı hatası oluştu!");
    }
}

// ==========================================
// ÇOKLU DOSYA YÜKLEME VE İŞLEMLER PANELİ (Sıralı Kuyruk)
// ==========================================
window.activeXHRs = window.activeXHRs || {};

function handleFilesFromInput(input) {
    if (input.files && input.files.length > 0) {
        handleFiles(input.files);
        input.value = ''; 
    }
}

function handleFiles(files) {
    if (files.length > 0) {
        const panel = document.getElementById('uploads-panel');
        if (panel) panel.classList.remove('hidden');

        // Dosyaları gerçek bir JavaScript dizisine çeviriyoruz
        const fileArray = Array.from(files);
        
        // Sırayla teker teker yükleyerek %0'da kalma ve çakışma sorunlarını önlüyoruz
        processUploadQueue(fileArray, 0);
    }
}

function processUploadQueue(fileArray, currentIndex) {
    if (currentIndex >= fileArray.length) {
        return; 
    }

    const currentFile = fileArray[currentIndex];
    uploadSingleFile(currentFile, function() {
        processUploadQueue(fileArray, currentIndex + 1);
    });
}

function uploadSingleFile(file, onCompleteCallback) {
    const chunkSize = 10 * 1024 * 1024; // 10MB chunk boyutu
    const totalChunks = Math.ceil(file.size / chunkSize);
    let currentChunk = 0;

    const container = document.getElementById('uploads-list-container');
    const fileId = 'upload-' + Math.random().toString(36).substring(2, 9);
    const currentPath = document.getElementById('current-path') ? document.getElementById('current-path').value : "";

    const itemHtml = `
        <div class="upload-item" id="${fileId}">
            <div class="upload-item-info">
                <span class="upload-filename" title="${file.name}">${file.name}</span>
                <span class="upload-pct" style="color: #66fcf1; font-weight: bold;">%0</span>
                <button type="button" class="upload-cancel-btn" onclick="cancelUpload('${fileId}')">Durdur</button>
            </div>
            <div class="upload-progress-bg">
                <div class="upload-progress-fill" id="bar-${fileId}" style="width: 0%;"></div>
            </div>
        </div>
    `;
    
    if (container) container.insertAdjacentHTML('beforeend', itemHtml);
    updateActiveUploadsCount();

    function uploadNextChunk() {
        if (window.activeXHRs[fileId] && window.activeXHRs[fileId].isCancelled) {
            onCompleteCallback(); 
            return;
        }

        const start = currentChunk * chunkSize;
        const end = Math.min(start + chunkSize, file.size);
        const chunk = file.slice(start, end);

        const formData = new FormData();
        formData.append('video_chunk', chunk);
        formData.append('filename', file.name);
        formData.append('chunkIndex', currentChunk);
        formData.append('totalChunks', totalChunks);
        formData.append('current_path', currentPath);

        const xhr = new XMLHttpRequest();
        window.activeXHRs[fileId] = { xhr: xhr, isCancelled: false };
        xhr.open('POST', '/yukle', true);

        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const chunkProgress = e.loaded / e.total;
                const totalPercent = Math.round(((currentChunk + chunkProgress) / totalChunks) * 100);
                
                const bar = document.getElementById(`bar-${fileId}`);
                const pctSpan = document.querySelector(`#${fileId} .upload-pct`);
                if (bar) bar.style.width = Math.min(totalPercent, 100) + '%';
                if (pctSpan) pctSpan.innerText = `%${Math.min(totalPercent, 100)}`;
            }
        });

        xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
                currentChunk++;
                if (currentChunk < totalChunks) {
                    uploadNextChunk();
                } else {
                    const pctSpan = document.querySelector(`#${fileId} .upload-pct`);
                    const cancelBtn = document.querySelector(`#${fileId} .upload-cancel-btn`);
                    if (pctSpan) {
                        pctSpan.innerText = "Tamamlandı";
                        pctSpan.style.color = "#45f3ff";
                    }
                    if (cancelBtn) cancelBtn.remove();
                    
                    const bar = document.getElementById(`bar-${fileId}`);
                    if (bar) bar.style.width = '100%';

                    setTimeout(() => {
                        const el = document.getElementById(fileId);
                        if (el) el.remove();
                        updateActiveUploadsCount();
                    }, 1500);

                    onCompleteCallback(); 
                }
            } else {
                handleUploadError(fileId, "Hata (" + xhr.status + ")");
                onCompleteCallback(); 
            }
        });

        xhr.addEventListener('error', () => {
            handleUploadError(fileId, "Bağlantı koptu");
            onCompleteCallback(); 
        });

        xhr.send(formData);
    }

    window.activeXHRs[fileId] = { xhr: null, isCancelled: false, startUpload: uploadNextChunk };
    uploadNextChunk();
}

function cancelUpload(fileId) {
    if (window.activeXHRs && window.activeXHRs[fileId]) {
        window.activeXHRs[fileId].isCancelled = true;
        if (window.activeXHRs[fileId].xhr) {
            window.activeXHRs[fileId].xhr.abort();
        }
        
        const el = document.getElementById(fileId);
        if (el) {
            const pctSpan = el.querySelector('.upload-pct');
            const cancelBtn = el.querySelector('.upload-cancel-btn');
            if (pctSpan) {
                pctSpan.innerText = "Durduruldu";
                pctSpan.style.color = "#ff4a4a";
            }
            if (cancelBtn) cancelBtn.remove();
            
            setTimeout(() => {
                el.remove();
                updateActiveUploadsCount();
            }, 1500);
        }
    }
}

function updateActiveUploadsCount() {
    const container = document.getElementById('uploads-list-container');
    const panel = document.getElementById('uploads-panel');
    const countBadge = document.getElementById('active-uploads-count');
    
    const count = container ? container.children.length : 0;
    if (countBadge) countBadge.innerText = count;

    if (panel) {
        if (count === 0) {
            panel.classList.add('hidden');
            location.reload(); 
        } else {
            panel.classList.remove('hidden');
        }
    }
}

function handleUploadError(fileId, msg) {
    const el = document.getElementById(fileId);
    if (el) {
        const pctSpan = el.querySelector('.upload-pct');
        const cancelBtn = el.querySelector('.upload-cancel-btn');
        if (pctSpan) {
            pctSpan.innerText = msg;
            pctSpan.style.color = "#ff4a4a";
        }
        if (cancelBtn) cancelBtn.remove();
        
        setTimeout(() => {
            el.remove();
            updateActiveUploadsCount();
        }, 3000);
    }
}

// Sürükle bırak olayları (Drop Zone)
const dropZone = document.getElementById('drop-zone');
if (dropZone) {
    ['dragenter', 'dragover'].forEach(eventName => { 
        dropZone.addEventListener(eventName, (e) => { e.preventDefault(); dropZone.classList.add('dragover'); }, false); 
    });
    ['dragleave', 'drop'].forEach(eventName => { 
        dropZone.addEventListener(eventName, (e) => { e.preventDefault(); dropZone.classList.remove('dragover'); }, false); 
    });

    dropZone.addEventListener('drop', (e) => { 
        e.preventDefault();
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleFiles(e.dataTransfer.files); 
        }
    });
}

const settingsModal = document.getElementById("settings-modal");
const openSettingsBtn = document.getElementById("open-settings-btn");
const closeSettingsBtn = document.getElementById("close-settings-btn");
const modalMsg = document.getElementById("modal-msg");

function openSettingsModal() {
    if (settingsModal) settingsModal.classList.remove("hidden");
}

if (openSettingsBtn) openSettingsBtn.addEventListener("click", openSettingsModal);
if (closeSettingsBtn) closeSettingsBtn.addEventListener("click", () => settingsModal.classList.add("hidden"));

const savePassBtn = document.getElementById("save-pass-btn");
if (savePassBtn) {
    savePassBtn.addEventListener("click", async () => {
        const old_password = document.getElementById("old-pass-input").value;
        const new_password = document.getElementById("new-pass-input").value;

        modalMsg.style.display = "none";

        try {
            const res = await fetch("/api/change-password", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ old_password, new_password })
            });
            const data = await res.json();

            if (res.ok) {
                modalMsg.style.color = "#66fcf1";
                modalMsg.textContent = data.message;
                modalMsg.style.display = "block";
                setTimeout(() => { location.reload(); }, 1200);
            } else {
                modalMsg.style.color = "#ff4a4a";
                modalMsg.textContent = data.message;
                modalMsg.style.display = "block";
            }
        } catch (e) {
            modalMsg.style.color = "#ff4a4a";
            modalMsg.textContent = "Bağlantı hatası!";
            modalMsg.style.display = "block";
        }
    });
}

const ppFileInput = document.getElementById("pp-file-input");
if (ppFileInput) {
    ppFileInput.addEventListener("change", async (e) => {
        if (e.target.files.length === 0) return;
        
        const formData = new FormData();
        formData.append("avatar", e.target.files[0]);

        try {
            const res = await fetch("/api/upload-avatar", {
                method: "POST",
                body: formData
            });
            const data = await res.json();

            if (res.ok) {
                location.reload();
            } else {
                alert(data.message);
            }
        } catch (err) {
            alert("Resim yüklenirken hata oluştu!");
        }
    });
}

const loginCard = document.getElementById('login-card');
const loginErrorMsg = document.getElementById('login-error-msg');
const loginSubmitBtn = document.getElementById('login-submit-btn');

if (loginCard && loginErrorMsg) {
    setTimeout(() => {
        loginCard.classList.remove('shake-error');
        if (loginSubmitBtn) loginSubmitBtn.classList.remove('btn-error');
        
        document.querySelectorAll('#login-card input').forEach(input => {
            input.classList.remove('input-error');
        });
        
        loginErrorMsg.style.display = 'none';
    }, 3000);
}