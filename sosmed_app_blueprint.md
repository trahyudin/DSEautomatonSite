# Social Media Automation Bot - Architecture Blueprint

Dokumen ini adalah *blueprint* spesifikasi teknis untuk membangun aplikasi otomatisasi unggahan sosial media (Social Media Auto-Poster). 
Berikan dokumen ini kepada instance/AI Antigravity di folder atau *workspace* baru agar ia dapat mereplikasi dan menyesuaikan sistem dengan fokus pada jejaring sosial (seperti Facebook, Instagram, Twitter, Pinterest, LinkedIn, dsb.).

---

## 1. Konsep Utama & Tujuan
Membangun sebuah sistem (Flask + Playwright + Gemini AI) yang membaca baris-baris target dari file Excel, mempelajari cara kerja masing-masing situs sosial media (tombol login, tombol post), lalu secara otomatis melakukan login dan memposting konten secara *headless* (atau terlihat).

Perbedaan utama dengan versi File Hosting: **Sosial media sangat bergantung pada sesi login (Cookies/Auth) dan struktur *feed/timeline* yang kompleks.**

## 2. Arsitektur Sistem (Tech Stack)
- **Backend:** Python + Flask
- **Frontend UI:** HTML5, CSS3 (Glassmorphism, Modern UI), Vanilla Javascript (`fetch` API).
- **Automation:** Playwright (Python) sinkron atau asinkron.
- **AI Engine:** Google Gemini 1.5 Flash (menggunakan library terbaru `google.genai`).
- **Database:** `tracker-posting.xlsx` (dibaca/ditulis dengan `openpyxl`).
- **Penyimpanan State:** `site_knowledge.json` (untuk menyimpan peta klik/ID elemen situs) dan `blacklist.txt`.

## 3. Alur Kerja Inti (The Pipeline)

### Phase A: AI Hint Generation (Pemetaan DOM)
Karena situs sosmed sering berubah nama *class* (misal Facebook dan Twitter menggunakan React/Gatsby dengan *hash classes*), AI digunakan untuk membaca DOM dan menemukan elemen-elemen penting.
1. Playwright membuka URL sosmed.
2. Skrip Python (`dom_condenser.py`) mengekstrak HTML, membuang tag tidak penting (`<script>`, `<style>`, `<meta>`), dan memberikan ID unik untuk setiap elemen interaktif (`<button>`, `<a>`, `<input>`).
3. Mengirimkan "Condensed DOM JSON" ke Gemini 1.5 Flash dengan *prompt* untuk mencari:
   - Tombol **Login**
   - Kolom **Username** / **Password**
   - Tombol **New Post / Create / Tweet**
   - Kolom **Text Input / Caption**
   - Area **Upload Image**
4. Gemini mengembalikan JSON berisi `target_identifier` yang kemudian disimpan di `site_knowledge.json`.

> [!WARNING] Aturan Keamanan API (Rate Limit 429)
> Gemini *Free Tier* sangat sensitif terhadap *burst requests* (limit 15 RPM). Pastikan *script* Phase A menggunakan `time.sleep(4.5)` antar permintaan dan memiliki implementasi *Exponential Backoff with Jitter* ketika mendapat *Error 429*.

### Phase B: Playwright Execution (Eksekusi Posting)
1. Playwright membaca target dari Excel.
2. Skrip mengambil *hints* dari `site_knowledge.json`.
3. Skrip memuat `.env` atau `credentials.json` untuk mendapatkan *username* dan *password* target.
4. Robot mengklik dan mengetik berdasarkan panduan dari AI:
   - Login.
   - Klik "Create Post".
   - Isi Teks / Upload Gambar.
   - Submit dan ambil URL post (Share Link).
5. Tulis link tersebut kembali ke kolom kampanye (`Campaign`) yang sesuai di Excel.

## 4. Struktur Folder & File yang Harus Dibuat

```text
/
├── app.py                     # Entry point Flask Server (Routing, API)
├── tracker_manager.py         # Logika baca/tulis openpyxl
├── .env                       # (Jangan dicommit) Berisi kredensial sosmed & GEMINI_API_KEY
├── blacklist.txt              # Daftar domain yang diskip
├── /automation
│   ├── engine.py              # Orkestrator Playwright (Phase B)
│   ├── learn_sites.py         # Orkestrator Gemini DOM (Phase A)
│   ├── dom_condenser.py       # Helper untuk mengecilkan ukuran DOM HTML ke JSON
│   ├── site_knowledge.json    # Output AI untuk peta elemen
│   └── credentials.json       # (Opsional) Mapping situs ke username/password
├── /templates
│   └── index.html             # Dashboard UI utama
├── /static
│   ├── style.css              # Glassmorphism + Tailwind-like custom css
│   └── app.js                 # Logika fetch API & interaksi UI
└── /uploads                   # Tempat penyimpanan gambar/aset sementara untuk diposting
```

## 5. Instruksi Ekstraksi Khusus Sosial Media
Saat membangun ulang *Phase B*, Agent harus memperhatikan *edge cases* berikut pada sosmed:
- **Pop-up Modal:** Twitter dan Instagram sering memunculkan *modal pop-up* saat login atau membuat post.
- **Dynamic Content:** Elemen sering tidak langsung *render*. Pastikan Playwright menggunakan `page.wait_for_selector(..., state="visible")`.
- **Session / Cookies:** Menyarankan fitur tambahan untuk *Save/Load Browser Context* di Playwright agar tidak perlu login berulang-ulang setiap kali bot dijalankan.

## 6. Instruksi Prompt Awal untuk Agen Antigravity Baru
Jika Anda sudah berada di folder baru, kirimkan *prompt* ini ke AI:

> "Halo, saya ingin membuat aplikasi *Social Media Auto-Poster*. Silakan pelajari file `sosmed_app_blueprint.md` ini secara menyeluruh. Saya ingin Anda mulai dengan membuat struktur dasar `app.py`, `templates/index.html`, dan logika `tracker_manager.py` menggunakan `openpyxl`. Buat desain UI-nya modern, *dark-mode*, dengan *glassmorphism*. Fokus utama aplikasi ini adalah untuk Facebook, Twitter, Instagram, Pinterest, dll."
