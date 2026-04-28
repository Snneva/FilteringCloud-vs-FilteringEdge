# Komparasi Arsitektur Edge vs Cloud Computing: Particle Filter IMU MPU6050

Repositori ini berisi implementasi kode untuk membandingkan arsitektur **Edge-Side Filtering** dan **Cloud-Side Filtering** dalam memproses data dari sensor MPU6050 menggunakan algoritma **Particle Filter (1000 Partikel)**. Pengiriman data dilakukan secara nirkabel menggunakan protokol UDP untuk meminimalkan latensi.

Proyek ini dikembangkan untuk memenuhi tugas mata kuliah Sistem Berbasis Mikroprosesor di Institut Teknologi Sepuluh Nopember (ITS).

## 📊 Deskripsi Skenario

Terdapat dua arsitektur yang diuji dan dibandingkan:

1. **Skenario A (Cloud-Side Filtering):**
   * ESP32 bertindak murni sebagai pengumpul data (*Edge*).
   * Data mentah (*raw data*) MPU6050 dikirim via UDP.
   * Raspberry Pi bertindak sebagai server (*Cloud*) yang memproses komputasi berat Particle Filter dan visualisasi.
2. **Skenario B (Edge-Side Filtering):**
   * ESP32 memproses komputasi Particle Filter secara mandiri.
   * Data yang dikirim ke Raspberry Pi via UDP adalah data yang sudah bersih (*filtered*).
   * Raspberry Pi hanya bertugas menerima data dan menampilkan visualisasi.

## 📁 Struktur Repositori

* `Skenario_A_Raw_Sender.ino` : Kode C++ ESP32 untuk mengirim data mentah (Skenario A).
* `Skenario_B_Edge_Filtering.ino` : Kode C++ ESP32 untuk memfilter data lokal dengan 1000 partikel (Skenario B).
* `udp_receiver_A.py` : Script Python penerima UDP Skenario A (Memproses Particle Filter di RasPi).
* `udp_receiver_B.py` : Script Python penerima UDP Skenario B (Hanya mem-parsing data dari ESP32).

## 🚀 Cara Menjalankan

1. Upload kode `.ino` yang diinginkan ke board ESP32 (atau jalankan di simulator Wokwi).
2. Pastikan IP target (Raspberry Pi) dan Port UDP sudah sesuai di konfigurasi kode ESP32 dan Python.
3. Jalankan script Python penerima yang sesuai di terminal Raspberry Pi:
   ```bash
   python udp_receiver_A.py
   # atau
   python udp_receiver_B.py
