# Web Proctor: Pengawasan Ujian Online dengan Facial Landmark Detection

Aplikasi web sederhana untuk memantau peserta ujian online secara *real-time* menggunakan kamera. Sistem memanfaatkan **MediaPipe Face Mesh** untuk mendeteksi arah pandangan (*gaze direction*) dan **MediaPipe Face Detection** untuk menghitung jumlah wajah yang terlihat, lalu mencatat pelanggaran ke file Excel.

> Judul proyek: *Pemanfaatan Facial Landmark Detection Sebagai Alat Pengawasan Ujian Online*

---

## Fitur

- Akses webcam langsung dari browser (tanpa instalasi aplikasi tambahan di sisi peserta).
- Deteksi arah pandangan: `Left`, `Center`, atau `Right`.
- Deteksi jumlah wajah di depan kamera.
- Pencatatan pelanggaran otomatis ketika pandangan tidak ke tengah atau terdeteksi lebih dari satu wajah.
- Tampilan status deteksi (arah pandangan dan jumlah wajah) secara langsung di halaman ujian.
- Jawaban ujian dan log pengawasan disimpan ke file `.xlsx` saat peserta menekan **Submit**.
- Kamera dinonaktifkan di sisi server setelah ujian dikumpulkan.

## Cara Kerja

```
Browser (webcam)                         Server Flask
      |                                       |
      |-- frame JPEG setiap 1 detik --------> /process_frame
      |                                       |-- MediaPipe Face Mesh  -> arah pandangan
      |                                       |-- MediaPipe Face Detection -> jumlah wajah
      |<-- gaze_direction + num_faces --------|-- hitung pelanggaran, catat ke DataFrame
      |                                       |
      |-- jawaban ujian (JSON) -------------> /submit_exam
      |                                       |-- simpan exam_answers.xlsx
      |                                       |-- simpan gaze_tracking_data.xlsx
      |<-- pesan sukses ----------------------|-- kamera dinonaktifkan
```

**Aturan deteksi**

1. Browser menangkap satu frame dari webcam setiap 1 detik dan mengirimkannya ke server.
2. Posisi tengah kedua mata dihitung dari landmark Face Mesh (koordinat ternormalisasi 0 sampai 1 pada sumbu X).
3. Arah pandangan ditentukan dari posisi tersebut:
   - X < 0.4 → `Right`
   - X > 0.6 → `Left`
   - selain itu → `Center`
4. Satu pelanggaran dicatat jika arah pandangan **bukan** `Center` atau jumlah wajah **lebih dari 1**.

## Kebutuhan Sistem

### Perangkat Keras

| Komponen  | Minimum              | Direkomendasikan         |
|-----------|----------------------|--------------------------|
| Prosesor  | Dual-core            | Intel i5/i7 atau setara  |
| RAM       | 4 GB                 | 8 GB atau lebih          |
| Kamera    | Resolusi VGA         | Resolusi HD              |

### Perangkat Lunak

| Komponen        | Rincian                                   |
|-----------------|-------------------------------------------|
| Sistem Operasi  | Windows 10/11, Linux                      |
| Python          | Versi 3.12                                |
| Browser         | Chrome, Firefox, Brave                    |

### Pustaka Python

| Pustaka                  | Versi      |
|--------------------------|------------|
| Flask                    | 3.1.0      |
| opencv-python-headless   | 3.4.18.65  |
| mediapipe                | 0.10.20    |
| numpy                    | 1.26.4     |
| pandas                   | 2.2.3      |
| gunicorn                 | 23.0.0     |
| openpyxl                 | 3.1.5      |

Daftar lengkap dependensi tersedia di file [`requirements.txt`](requirements.txt).

> **Catatan:**
> - Pastikan browser sudah diberi izin untuk mengaktifkan kamera.
> - Semua pustaka Python yang diperlukan sudah ada di `requirements.txt`, sehingga cukup diinstal dengan satu perintah di terminal (lihat langkah instalasi di bawah).

## Instalasi

1. **Clone repositori**

   ```bash
   git clone https://github.com/arckotama/simple-web-proctor.git
   cd simple-web-proctor
   ```

2. **Buat virtual environment (disarankan)**

   Linux / macOS:
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate
   ```

   Windows (PowerShell):
   ```powershell
   py -3.12 -m venv venv
   venv\Scripts\Activate.ps1
   ```

3. **Instal seluruh dependensi dengan satu perintah**

   ```bash
   pip install -r requirements.txt
   ```

## Menjalankan Aplikasi

**Mode pengembangan (Flask):**

```bash
python app.py
```

**Mode produksi (Gunicorn, Linux):**

```bash
gunicorn --workers 1 --bind 0.0.0.0:8000 app:app
```

> Gunakan `--workers 1` karena data pelanggaran disimpan di memori proses. Jika memakai lebih dari satu *worker*, data akan terpecah di tiap proses.

Lalu buka browser dan akses:

- Flask: `http://127.0.0.1:5000`
- Gunicorn: `http://127.0.0.1:8000`

Saat halaman terbuka, klik **Allow** pada permintaan izin kamera dari browser.

## Penggunaan

1. Buka halaman ujian dan izinkan akses kamera.
2. Pastikan wajah terlihat jelas di kamera. Status *Gaze Direction* dan *Number of Faces* tampil di pojok layar.
3. Jawab pertanyaan ujian.
4. Klik **Submit** untuk mengumpulkan jawaban. Setelah itu kamera dinonaktifkan di sisi server.

## Keluaran Data

Dua file Excel dibuat di direktori kerja aplikasi saat ujian dikumpulkan:

| File                     | Isi                                                                 |
|--------------------------|---------------------------------------------------------------------|
| `exam_answers.xlsx`      | Pertanyaan dan jawaban peserta                                      |
| `gaze_tracking_data.xlsx`| Log pengawasan: `Time`, `Gaze Direction`, `Number of Faces`, `Total Violation` |

`gaze_tracking_data.xlsx` bersifat akumulatif (data baru ditambahkan ke file yang sudah ada), sedangkan `exam_answers.xlsx` ditimpa setiap kali ujian dikumpulkan.

## Endpoint API

| Method | Endpoint          | Deskripsi                                                                 |
|--------|-------------------|---------------------------------------------------------------------------|
| GET    | `/`               | Halaman ujian                                                             |
| POST   | `/process_frame`  | Menerima frame (`multipart/form-data`, field `file`), mengembalikan `gaze_direction` dan `num_faces` |
| POST   | `/submit_exam`    | Menerima JSON `{"answers": [...]}`, menyimpan hasil ke Excel dan menonaktifkan kamera |

## Struktur Proyek

```
.
├── app.py              # Server Flask + kelas FocusDetector (MediaPipe)
├── requirements.txt    # Daftar dependensi Python
├── templates/
│   └── index.html      # Halaman ujian
└── static/
    ├── script.js       # Akses webcam, kirim frame, submit ujian
    └── style.css       # Gaya tampilan
```

## Teknologi

- **Backend:** Python 3.12, Flask, Gunicorn
- **Computer vision:** MediaPipe (Face Mesh, Face Detection), OpenCV, NumPy
- **Pengolahan data:** pandas, openpyxl
- **Frontend:** HTML, CSS, JavaScript (WebRTC `getUserMedia`)

## Keterbatasan dan Rencana Pengembangan

Proyek ini masih berupa prototipe. Beberapa hal yang perlu diperhatikan:

- Status pelanggaran dan status kamera disimpan di variabel global, sehingga aplikasi saat ini ditujukan untuk **satu peserta dalam satu waktu**.
- Belum ada autentikasi peserta maupun pemisahan data antar sesi ujian.
- Estimasi arah pandangan memakai ambang batas posisi mata pada frame, sehingga hasilnya dapat dipengaruhi posisi duduk, pencahayaan, dan kualitas kamera.
- Mode `debug=True` pada `app.py` hanya untuk pengembangan, jangan dipakai di produksi.

Ide pengembangan: dukungan multi-peserta, autentikasi, dashboard pengawas, deteksi tambahan (misalnya posisi kepala atau objek mencurigakan), serta penyimpanan ke database.
