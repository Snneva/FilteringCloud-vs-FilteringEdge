import socket
import time
import numpy as np
import matplotlib.pyplot as plt

# ================= KONFIGURASI =================
UDP_IP = "0.0.0.0"
UDP_PORT = 12345
MAX_SAMPLES = 250        # Jumlah data yang direkam sebelum plotting
NUM_PARTICLES = 1000     # Parameter PF Cloud
PROCESS_NOISE = 0.1      # Variansi pergerakan
MEASUREMENT_NOISE = 1.0  # Variansi sensor
# ===============================================

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print(f"=== SKENARIO A: CLOUD-SIDE FILTERING ===")
    print(f"Menunggu aliran data UDP mentah (Raw) di port {UDP_PORT}...\n")

    # Inisialisasi Partikel awal (Asumsi gravitasi 9.8)
    particles = np.random.normal(9.8, PROCESS_NOISE, NUM_PARTICLES)
    weights = np.ones(NUM_PARTICLES) / NUM_PARTICLES

    raw_z_history = []
    filtered_z_history = []
    esp_process_times = []   
    raspi_process_times = [] 

    samples_collected = 0

    try:
        while samples_collected < MAX_SAMPLES:
            data, addr = sock.recvfrom(1024)
            payload = data.decode('utf-8').split(',')
            
            # Memastikan data yang masuk adalah Tipe 0 (Raw dari Skenario A)
            if len(payload) == 5 and payload[0] == '0':
                esp_time_us = float(payload[1]) 
                z_raw = float(payload[4])       
                
                # --- MULAI MENGHITUNG BEBAN KOMPUTASI CLOUD ---
                start_pf_time = time.perf_counter()

                # TAHAP 1 & 2: Prediction dan Update
                particles += np.random.normal(0, PROCESS_NOISE, NUM_PARTICLES)
                weights = np.exp(-((particles - z_raw)**2) / (2 * MEASUREMENT_NOISE**2))
                weights += 1e-300 
                weights /= np.sum(weights) 

                # TAHAP 3: Estimation
                z_filtered = np.sum(particles * weights)

                # TAHAP 4: Resampling
                indices = np.random.choice(NUM_PARTICLES, NUM_PARTICLES, p=weights)
                particles = particles[indices]
                
                raspi_time_ms = (time.perf_counter() - start_pf_time) * 1000
                # --- SELESAI KOMPUTASI CLOUD ---

                raw_z_history.append(z_raw)
                filtered_z_history.append(z_filtered)
                esp_process_times.append(esp_time_us / 1000.0) 
                raspi_process_times.append(raspi_time_ms)
                
                samples_collected += 1
                if samples_collected % 25 == 0:
                    print(f"Progress: {samples_collected}/{MAX_SAMPLES} sampel diproses.")

        print("\n=== HASIL PROCESSING TIME ===")
        print(f"Rata-rata Waktu ESP32 (Hanya Baca Sensor) : {np.mean(esp_process_times):.3f} ms")
        print(f"Rata-rata Waktu RasPi (Komputasi PF 1000) : {np.mean(raspi_process_times):.3f} ms")
        print("=============================\n")

        # Membuat Grafik Visualisasi
        plt.figure(figsize=(10, 6))
        plt.plot(raw_z_history, label='Raw Data Masuk (Dari ESP32)', color='red', alpha=0.5, linestyle='dashed')
        plt.plot(filtered_z_history, label='Output Particle Filter (Dihitung di Cloud)', color='blue', linewidth=2)
        plt.title('Skenario A: Cloud-Side Filtering (Beban Komputasi di Server)')
        plt.xlabel('Jumlah Sampel (Waktu)')
        plt.ylabel('Akselerasi Sumbu Z (m/s^2)')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    except KeyboardInterrupt:
        print("\nSistem dihentikan.")
    finally:
        sock.close()

if __name__ == "__main__":
    main()