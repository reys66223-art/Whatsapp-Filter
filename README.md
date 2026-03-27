# WhatsApp Universal Number Validator (Ghost Validator) 🚀

Tool CLI Python berkecepatan tinggi untuk memvalidasi apakah daftar nomor telepon aktif di WhatsApp atau tidak menggunakan metode **Pairing Code**.

> [!IMPORTANT]
> **Zero-Message Policy:** Tool ini murni melakukan pengecekan ke server tanpa mengirim pesan apa pun ke target. Ini menjamin akun Anda **aman dari blokir** karena aktivitas spamming.

---

## ✨ Fitur Utama

*   **Universal Input Support:** Membaca nomor dari file Excel (`.xlsx`), CSV (`.csv`), teks biasa (`.txt`, `.log`), atau input manual di terminal.
*   **Intelligent Auto-Formatter:** Otomatis membersihkan karakter aneh (spasi, strip, kurung) dan menormalisasi prefix (contoh: `0812...` atau `812...` otomatis dikonversi ke format internasional `62812...`).
*   **Pairing Code Auth:** Tidak perlu scan QR Code yang lambat, cukup masukkan nomor HP Anda dan gunakan 8-digit kode pairing di aplikasi WhatsApp (Linked Devices).
*   **High-Speed Filter:** Mengecek nomor secara batch (asynchronous) dengan jeda acak (*smart delay*) untuk stabilitas koneksi.
*   **Beautiful UI:** Antarmuka terminal cantik menggunakan sistem tabel dan progress bar dari library `Rich`.
*   **Auto-Save & Reports:** Hasil divalidasi langsung disimpan ke folder `results/` dalam format teks dan statistik JSON.

---

## 🛠️ Instalasi & Persiapan

Pastikan Anda memiliki **Python 3.10** atau versi di atasnya.

### 💻 Di Laptop/PC (Windows/Linux/Mac)

1.  Buka terminal/CMD dan masuk ke folder project.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Jalankan tool:
    ```bash
    python main.py
    ```

### 📱 Di Android (Termux)

1.  Update & Install dependencies sistem:
    ```bash
    pkg update && pkg upgrade
    pkg install python clang make libffi openssl golang -y
    ```
2.  Masuk ke folder project, lalu install requirements:
    ```bash
    pip install -r requirements.txt
    ```
3.  Jalankan tool:
    ```bash
    python main.py
    ```

---

## 🚀 Alur Kerja

1.  **Step 1: Auth** — Masukkan nomor HP pemicu (untuk pairing). Tool akan menampilkan 8-digit kode. Masukkan kode tersebut di WhatsApp HP Anda (Settings > Linked Devices > Link with phone number).
2.  **Step 2: Input** — Pilih apakah ingin mengetik nomor secara manual atau membaca file (Excel/CSV/TXT). Tool akan otomatis membersihkan dan men-duplikat nomor jika ada yang ganda.
3.  **Step 3: Validasi** — Tool akan mencocokkan nomor dengan database WhatsApp dan menampilkan progress secara real-time.

---

## 📊 Hasil Output

Setiap kali validasi selesai, file akan otomatis tersimpan di folder `results/`:

*   `active_wa.txt`: Daftar nomor yang terbukti memiliki akun WhatsApp aktif.
*   `invalid_wa.txt`: Daftar nomor yang tidak terdaftar di WhatsApp.
*   `summary.json`: Statistik lengkap (Total input, Jumlah Aktif, Waktu Proses, dll).

---

## 📦 Tech Stack

*   **Language:** Python 3.10+
*   **WA Engine:** `neonize` (Python wrapper for `whatsmeow` written in Go)
*   **Data Processor:** `pandas` & `openpyxl`
*   **UI/UX:** `Rich` (Terminal Interface)
*   **Database:** `SQLite3` (Session manager)

---

## 📝 Catatan (Disclaimer)

Tool ini dibuat untuk tujuan efisiensi manajemen data kontak. Penyalahgunaan untuk aktivitas yang melanggar ketentuan privasi WhatsApp adalah tanggung jawab pengguna sepenuhnya.
