import socket
import time
import numpy as np
import matplotlib.pyplot as plt

# ================= KONFIGURASI =================
UDP_IP = "0.0.0.0"
UDP_PORT = 12345
MAX_SAMPLES = 150        # Jumlah sampel sebelum plotting
NUM_PARTICLES = 1000     # Parameter PF Cloud

PROCESS_NOISE = 0.1
MEASUREMENT_NOISE = 1.0
# ===============================================

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print(f"Menunggu aliran data UDP di port {UDP_PORT}...")
    
    # Variabel Log
    raw_z_history = []
    filtered_z_history = []
    esp_process_times = []
    raspi_process_times = []

    # Inisialisasi Partikel (Hanya dipakai jika Skenario A)
    particles = np.random.normal(9.8, PROCESS_NOISE, NUM_PARTICLES)
    weights = np.ones(NUM_PARTICLES) / NUM_PARTICLES

    samples_collected = 0
    scenario_mode = None # Akan otomatis mendeteksi '0' (Skenario A) atau '1' (Skenario B)

    try:
        while samples_collected < MAX_SAMPLES:
            data, addr = sock.recvfrom(1024)
            payload = data.decode('utf-8').split(',')
            
            if len(payload) == 5:
                # Membaca Tipe Payload (0 = Skenario A/Raw, 1 = Skenario B/Filtered)
                pkt_type = int(payload[0])
                esp_time_us = float(payload[1])
                z_value = float(payload[4])
                
                # Deteksi Skenario Otomatis saat paket pertama tiba
                if scenario_mode is None:
                    scenario_mode = pkt_type
                    if scenario_mode == 0:
                        print(">> Terdeteksi: Skenario A (Cloud-Side Filtering)")
                    else:
                        print(">> Terdeteksi: Skenario B (Edge-Side Filtering)")
                    print(f"Mengumpulkan {MAX_SAMPLES} sampel...\n")

                # --- LOGIKA SKENARIO A (Cloud Bekerja Keras) ---
                if scenario_mode == 0:
                    start_pf_time = time.perf_counter()
                    
                    # Particle Filter Algorithm
                    particles += np.random.normal(0, PROCESS_NOISE, NUM_PARTICLES)
                    weights = np.exp(-((particles - z_value)**2) / (2 * MEASUREMENT_NOISE**2))
                    weights += 1e-300 
                    weights /= np.sum(weights)
                    z_filtered = np.sum(particles * weights)
                    
                    indices = np.random.choice(NUM_PARTICLES, NUM_PARTICLES, p=weights)
                    particles = particles[indices]
                    
                    raspi_time_ms = (time.perf_counter() - start_pf_time) * 1000
                    
                    raw_z_history.append(z_value)
                    filtered_z_history.append(z_filtered)
                    esp_process_times.append(esp_time_us / 1000.0)
                    raspi_process_times.append(raspi_time_ms)

                # --- LOGIKA SKENARIO B (Edge Bekerja Keras, Cloud Hanya Menerima) ---
                elif scenario_mode == 1:
                    start_recv_time = time.perf_counter()
                    
                    # Nilai Z yang masuk SUDAH difilter oleh ESP32
                    z_filtered_edge = z_value 
                    
                    raspi_time_ms = (time.perf_counter() - start_recv_time) * 1000
                    
                    filtered_z_history.append(z_filtered_edge)
                    esp_process_times.append(esp_time_us / 1000.0) # Waktu PF di ESP32
                    raspi_process_times.append(raspi_time_ms) # Waktu raspi hanya parsing data

                samples_collected += 1
                if samples_collected % 25 == 0:
                    print(f"Progress: {samples_collected}/{MAX_SAMPLES}")

        # --- SELESAI PENGUMPULAN DATA, MULAI PLOTTING ---
        print("\n=== HASIL ANALISIS PROCESSING TIME ===")
        avg_esp_time = np.mean(esp_process_times)
        avg_raspi_time = np.mean(raspi_process_times)
        
        if scenario_mode == 0:
            print(f"Skenario A (Cloud Filtering):")
            print(f"-> Waktu Baca Sensor (ESP32)  : {avg_esp_time:.3f} ms")
            print(f"-> Waktu Komputasi PF (RasPi) : {avg_raspi_time:.3f} ms")
        else:
            print(f"Skenario B (Edge Filtering):")
            print(f"-> Waktu Komputasi PF (ESP32) : {avg_esp_time:.3f} ms")
            print(f"-> Waktu Terima Data (RasPi)  : {avg_raspi_time:.3f} ms")
        print("======================================\n")

        # Visualisasi
        plt.figure(figsize=(10, 6))
        
        if scenario_mode == 0:
            plt.plot(raw_z_history, label='Raw Data (ESP32 Input)', color='red', alpha=0.5, linestyle='dashed')
            plt.plot(filtered_z_history, label='Particle Filter (RasPi Output)', color='blue', linewidth=2)
            plt.title('Skenario A: Cloud-Side Filtering (1000 Partikel)')
        else:
            plt.plot(filtered_z_history, label='Particle Filter (ESP32 Output)', color='green', linewidth=2)
            plt.title('Skenario B: Edge-Side Filtering (1000 Partikel)')

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