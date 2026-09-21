# 🚀 AutoPost Matrix (DSE Automation)

Sistem otomasi publikasi konten dan backlink generator multi-platform berbasis **Web Dashboard (Flask)** yang ditenagai oleh **Google Gemini AI** dan **Playwright Browser Automation (Chrome CDP Mode)**.

Aplikasi ini dirancang untuk membaca ratusan target website dari file Excel (`tracker-posting.xlsx`), mengkategorikan dan menganalisis tingkat kesulitan tiap situs, mempelajari struktur DOM secara mandiri (Phase A), lalu mengeksekusi pengunggahan konten secara otomatis (Phase B) sambil mencatat kembali tautan publikasi ke dalam tracker.

---

## 📑 Daftar Isi Dokumen

Proyek ini dilengkapi dengan dokumentasi teknis dan operasional yang lengkap:
1. **[README.md](file:///d:/Kerja%20praktek/dse%20automation/README.md)** (Dokumen ini) — Ringkasan fitur, instalasi, dan panduan cepat.
2. **[DOKUMENTASI_TEKNIS.md](file:///d:/Kerja%20praktek/dse%20automation/DOKUMENTASI_TEKNIS.md)** — Arsitektur detail, diagram alir, alur Phase A & Phase B, bedah modul kode, dan skema data.
3. **[EVALUASI_DAN_ROADMAP.md](file:///d:/Kerja%20praktek/dse%20automation/EVALUASI_DAN_ROADMAP.md)** — **Analisis mendalam mengenai apa yang belum sempurna/kelemahan saat ini**, bug teridentifikasi, batasan teknis, dan rencana peningkatan sistem di masa depan.
4. **[PANDUAN_OPERASIONAL.md](file:///d:/Kerja%20praktek/dse%20automation/PANDUAN_OPERASIONAL.md)** — Panduan langkah demi langkah penggunaan harian, tips anti-blokir Chrome Robot, dan troubleshooting.
5. **[sosmed_app_blueprint.md](file:///d:/Kerja%20praktek/dse%20automation/sosmed_app_blueprint.md)** — Cetak biru arsitektur khusus untuk platform media sosial (Instagram, Pinterest, Twitter, Facebook, dll.).

---

## 🌟 Fitur Utama

| Fitur | Deskripsi |
| :--- | :--- |
| 📊 **Matrix Tracker Terintegrasi** | Membaca & menulis langsung ke `tracker-posting.xlsx`. Kolom kampanye baru dibuat secara dinamis saat kampanye baru diluncurkan. |
| 🧠 **Phase A: AI Site Learner** | Menggunakan Playwright untuk merender halaman, memangkas DOM menjadi pohon interaktif ringkas, lalu meminta Gemini AI mendeteksi tombol create/post/upload secara otomatis tanpa penulisan selektor manual. |
| ⚡ **Phase B: Dual-Engine Executor** | **Tier Mudah:** Menggunakan direct multipart REST API (sangat cepat, tanpa browser).<br>**Tier Sedang & Sulit:** Menggunakan browser Playwright dengan CDP mode (Chrome DevTools Protocol), profil Chrome robot mandiri, kurva mouse Bezier, dan simulasi pengetikan manusia. |
| 🔍 **Site Inspector & Mass Audit** | Memindai status HTTP (200, 403, 404), mendeteksi redirect, dan mengelompokkan situs berdasarkan kategori (Image Host, Paste Host, Cloud Storage, Blog/CMS). |
| 🛡️ **Filter & Blacklist Cerdas** | Menyaring situs non-upload dan jejaring sosial kompleks via `blacklist.txt` agar eksekusi fokus pada hosting file, artikel, dan paste. |
| 🔗 **Link Verifier** | Memverifikasi apakah link hasil publikasi benar-benar aktif dan dapat diakses publik (HTTP 200) atau error. |

---

## 🛠️ Tech Stack

- **Backend:** Python 3.12, Flask
- **Browser Automation:** Playwright (Chromium / CDP via Port 9222)
- **AI Engine:** Google Gemini Flash (Vision & Condensed DOM Reasoning)
- **Excel Engine:** OpenPyXL
- **Networking:** Requests, HTTP/2 Support
- **Frontend UI:** HTML5, Modern CSS (Glassmorphism), Vanilla JavaScript

---

## ⚙️ Persyaratan Sistem & Instalasi

### 1. Prasyarat
- Windows 10 / 11 (64-bit)
- Python 3.10 atau lebih baru (Disarankan Python 3.12)
- Google Chrome terinstal di direktori standar:
  `C:\Program Files\Google\Chrome\Application\chrome.exe`
- Koneksi Internet stabil
- API Key Google Gemini (didapatkan gratis di [Google AI Studio](https://aistudio.google.com/))

### 2. Langkah Instalasi

1. **Clone / Buka Direktori Proyek**:
   ```bash
   cd "d:\Kerja praktek\dse automation"
   ```

2. **Buat & Aktifkan Virtual Environment (Opsional tapi Disarankan)**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Instal Dependensi**:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

4. **Konfigurasi Environment Variable (`.env`)**:
   Buat atau pastikan file `.env` di root direktori memiliki konfigurasi berikut:
   ```env
   GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

---

## 🚀 Cara Menjalankan Aplikasi

Aplikasi menggunakan arsitektur dua komponen: **Chrome Robot (CDP Mode)** dan **Web Server (Flask)**.

### Langkah 1: Jalankan Chrome Robot
Buka file batch berikut dengan klik ganda:
```text
Jalankan_Chrome_Robot.bat
```
*Script ini akan membuka jendela Google Chrome khusus robot dengan port debugging 9222 dan direktori profil terisolasi (`BotProfile`).*

> [!TIP] Login Pertama Kali
> Jika Anda hendak memposting ke situs yang membutuhkan login (misal Imgur, WordPress, dll.), lakukan login satu kali saja di dalam jendela Chrome Robot ini. Sesi login akan tersimpan permanen di folder `BotProfile`.

### Langkah 2: Jalankan Server Dashboard
Buka terminal/PowerShell di folder proyek, lalu jalankan:
```bash
python app.py
```
Output terminal akan menampilkan:
```text
Starting AutoPost Matrix Server on http://0.0.0.0:5000
 * Running on http://127.0.0.1:5000
```

### Langkah 3: Buka Dashboard di Browser
Buka browser Anda dan akses:
👉 **`http://localhost:5000`**

---

## 🖥️ Panduan Antarmuka (Tabs Dashboard)

1. **Matrix Tracker Tab:**
   - Menampilkan tabel seluruh situs dari `tracker-posting.xlsx`.
   - Menampilkan status link per kampanye.
   - Tombol **+ Add Campaign** untuk menambah kolom kampanye baru secara otomatis di Excel.
   - Kolom dapat diedit langsung dan disimpan kembali ke Excel.

2. **Campaign Uploader Tab (Phase B):**
   - Pilih kampanye target.
   - Masukkan Judul Post, Konten Teks / Markdown, dan lampirkan File / Gambar.
   - Pilih mode browser: *Visible Headed Window* (dapat dipantau secara visual) atau *Headless Background*.
   - Tekan **Start Batch Upload**: Sistem otomatis memilah situs Mudah -> Sedang -> Sulit dan mengeksekusi upload secara berurutan.

3. **Phase A: AI Learning Lab:**
   - Memindai struktur situs baru yang belum ada di `site_knowledge.json`.
   - Menggunakan AI Gemini untuk mencari tombol "Upload" / "Create Post" dan menyimpan selektornya.
   - Menyimpan hasil pemindaian agar eksekusi Phase B berikutnya berjalan instan tanpa perlu bantuan AI lagi.

4. **Site Inspector & Audit Tab:**
   - Menjalankan audit konektivitas cepat ke semua target website.
   - Memetakan situs yang masih hidup (200 OK), redirect (301/302), atau mati/diblokir (403, 404, 500).

5. **Link Verifier Tab:**
   - Mengecek validitas tautan yang sudah berhasil diposting pada kampanye tertentu.
   - Memastikan tautan tidak dihapus (*taken down*) oleh penyedia hosting.

---

## 📂 Struktur Direktori Proyek

```text
dse automation/
├── .env                                # Konfigurasi kunci API (Gemini API Key)
├── app.py                              # Server web Flask utama & API endpoints
├── blacklist.txt                       # Daftar domain yang dilewati (sosmed & non-upload)
├── Jalankan_Chrome_Robot.bat           # Launcher Chrome CDP Port 9222
├── Reset_Lalu_Jalankan_Chrome_Robot.bat# Launcher Chrome dengan reset cache
├── link_verifier.py                    # Modul pengecekan keaktifan URL hasil post
├── requirements.txt                    # Dependensi Python
├── search_hints.json                   # Petunjuk kata kunci tombol UI
├── site_capabilities.json              # Basis data kapabilitas dan tier kesulitan situs
├── site_inspector.py                   # Modul pemeriksa status HTTP & tiering situs
├── site_knowledge.json                 # Knowledge base selektor DOM hasil pembelajaran AI
├── sosmed_app_blueprint.md             # Blueprint sistem otomatisasi sosial media terpisah
├── tracker-posting.xlsx                # Database Excel aktif kampanye & status posting
├── tracker_manager.py                  # Handler pembacaan dan penulisan file Excel
│
├── automation/                         # Core Automation Engine
│   ├── __init__.py
│   ├── audit_engine.py                 # Mass audit Playwright untuk 100+ situs
│   ├── browser_human.py                # Playwright automation, form fill & human behavior
│   ├── cloud_storage.py                # Direct uploader untuk hosting cloud (Gofile, Catbox)
│   ├── cookies/                        # Penyimpanan cookie sesi browser
│   ├── engine.py                       # Mesin orkestrasi Phase B (Mudah -> Sedang -> Sulit)
│   ├── gemini_vision.py                # Klien AI Gemini dengan rate-limit protection
│   ├── human_behavior.py               # Algoritma kurva mouse Bezier & ritme ketukan
│   ├── image_hosts.py                  # Direct API uploader (ImgBB, Catbox, Pixeldrain, dll.)
│   ├── learn_sites.py                  # Mesin Phase A (Pengekstrakan DOM & Gemini Reasoning)
│   └── paste_hosts.py                  # Direct API uploader (Telegraph, JustPaste, dll.)
│
├── BotProfile/                         # Direktori User Data profil Chrome Robot
├── static/                             # Aset frontend (CSS modern, JavaScript app.js)
├── templates/                          # Template HTML (index.html)
└── uploads/                            # Folder penampung sementara file upload
```

---

## 🧭 Panduan Lanjutan

Untuk memahami arsitektur mendalam, analisis bug yang belum tuntas, dan rencana perbaikan, silakan pelajari dokumen pendukung:
- 📖 **[DOKUMENTASI_TEKNIS.md](file:///d:/Kerja%20praktek/dse%20automation/DOKUMENTASI_TEKNIS.md)**
- ⚠️ **[EVALUASI_DAN_ROADMAP.md](file:///d:/Kerja%20praktek/dse%20automation/EVALUASI_DAN_ROADMAP.md)**
- 🛠️ **[PANDUAN_OPERASIONAL.md](file:///d:/Kerja%20praktek/dse%20automation/PANDUAN_OPERASIONAL.md)**
