import socket
import time
import numpy as np
import matplotlib.pyplot as plt

# ================= KONFIGURASI =================
UDP_IP = "0.0.0.0"
UDP_PORT = 12345
MAX_SAMPLES = 250        # Jumlah data yang direkam sebelum plotting
# ===============================================

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print(f"=== SKENARIO B: EDGE-SIDE FILTERING ===")
    print(f"Menunggu aliran data BERSIH dari ESP32 di port {UDP_PORT}...\n")

    filtered_z_history = []
    esp_process_times = []   
    raspi_parsing_times = [] 

    samples_collected = 0

    try:
        while samples_collected < MAX_SAMPLES:
            data, addr = sock.recvfrom(1024)
            payload = data.decode('utf-8').split(',')
            
            # Memastikan data yang masuk adalah Tipe 1 (Filtered dari Skenario B)
            if len(payload) == 5 and payload[0] == '1':
                esp_time_us = float(payload[1]) 
                
                # --- MENGHITUNG BEBAN SERVER (HANYA TERIMA DATA) ---
                start_recv_time = time.perf_counter()
                
                z_filtered_edge = float(payload[4]) # Data sudah difilter oleh ESP32
                
                raspi_time_ms = (time.perf_counter() - start_recv_time) * 1000
                # --- SELESAI ---

                filtered_z_history.append(z_filtered_edge)
                esp_process_times.append(esp_time_us / 1000.0) 
                raspi_parsing_times.append(raspi_time_ms)
                
                samples_collected += 1
                if samples_collected % 25 == 0:
                    print(f"Progress: {samples_collected}/{MAX_SAMPLES} sampel diterima.")

        print("\n=== HASIL PROCESSING TIME ===")
        print(f"Rata-rata Waktu ESP32 (Komputasi PF 1000) : {np.mean(esp_process_times):.3f} ms")
        print(f"Rata-rata Waktu RasPi (Hanya Terima Data) : {np.mean(raspi_parsing_times):.5f} ms")
        print("INFO: Seluruh probabilitas dihitung oleh ESP32.")
        print("=============================\n")

        # Membuat Grafik Visualisasi
        plt.figure(figsize=(10, 6))
        plt.plot(filtered_z_history, label='Data Filtered dari UDP (Diproses di ESP32)', color='green', linewidth=2)
        plt.title('Skenario B: Edge-Side Filtering (Beban Jaringan Ringan)')
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