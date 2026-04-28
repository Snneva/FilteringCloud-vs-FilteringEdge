#include <Arduino.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <math.h>

const char* ssid = "Wokwi-GUEST"; 
const char* password = "";        

const char* hostRaspi = "192.168.1.7"; 
const int portUDP = 12345;

Adafruit_MPU6050 mpu;
WiFiUDP udp;

// --- PARAMETER PARTICLE FILTER ---
#define NUM_PARTICLES 1000
float particles[NUM_PARTICLES];
float weights[NUM_PARTICLES];
const float PROCESS_NOISE = 0.1;
const float MEASUREMENT_NOISE = 1.0;

// Fungsi untuk membuat angka random Gaussian (Box-Muller transform)
float generateGaussian(float mean, float stdDev) {
  float u1 = (float)random(1, 10000) / 10000.0; 
  float u2 = (float)random(1, 10000) / 10000.0;
  float z0 = sqrt(-2.0 * log(u1)) * cos(2.0 * PI * u2);
  return mean + z0 * stdDev;
}

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
  }
  Serial.println("\nWiFi Terhubung!");

  if (!mpu.begin()) {
    Serial.println("MPU6050 tidak terdeteksi!");
    while (1) { delay(10); }
  }
  
  // Inisialisasi Partikel Awal (Asumsi Z dekat dengan gravitasi 9.8)
  for(int i = 0; i < NUM_PARTICLES; i++) {
    particles[i] = generateGaussian(9.8, PROCESS_NOISE);
    weights[i] = 1.0 / NUM_PARTICLES;
  }
}

void loop() {
  unsigned long startProcess = micros();

  // 1. Baca Sensor
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);
  float z_raw = a.acceleration.z;

  // --- MULAI PARTICLE FILTER 1000 PARTIKEL ---
  float sum_weights = 0.0;
  float max_weight = 0.0;

  // TAHAP 1 & 2: Prediksi dan Update Bobot
  for(int i = 0; i < NUM_PARTICLES; i++) {
    particles[i] += generateGaussian(0, PROCESS_NOISE);
    // Kalkulasi probabilitas Gaussian
    float diff = particles[i] - z_raw;
    weights[i] = exp(-(diff * diff) / (2.0 * MEASUREMENT_NOISE * MEASUREMENT_NOISE));
    sum_weights += weights[i];
  }

  // TAHAP 3: Normalisasi dan Estimasi State
  float z_filtered = 0.0;
  for(int i = 0; i < NUM_PARTICLES; i++) {
    weights[i] /= sum_weights; // Normalisasi
    z_filtered += particles[i] * weights[i];
    if(weights[i] > max_weight) max_weight = weights[i]; // Cari bobot tertinggi untuk resampling
  }

  // TAHAP 4: Resampling (Metode Roda Rolet / Systematic Resampling)
  float new_particles[NUM_PARTICLES];
  int index = random(0, NUM_PARTICLES);
  float beta = 0.0;
  
  for(int i = 0; i < NUM_PARTICLES; i++) {
    beta += ((float)random(0, 10000) / 10000.0) * 2.0 * max_weight;
    while(beta > weights[index]) {
      beta -= weights[index];
      index = (index + 1) % NUM_PARTICLES;
    }
    new_particles[i] = particles[index];
  }
  
  // Timpa partikel lama dengan partikel hasil seleksi
  for(int i = 0; i < NUM_PARTICLES; i++) {
    particles[i] = new_particles[i];
  }
  // --- SELESAI PARTICLE FILTER ---

  // 2. Hitung waktu komputasi Skenario B (Akan jauh lebih lama)
  unsigned long processTime = micros() - startProcess;

  // 3. Format Data: "1(Filtered), Waktu(us), X, Y, Z_Filtered"
  char payload[100];
  snprintf(payload, sizeof(payload), "1,%lu,%.4f,%.4f,%.4f", 
           processTime, a.acceleration.x, a.acceleration.y, z_filtered);

  // 4. Kirim via UDP
  udp.beginPacket(hostRaspi, portUDP);
  udp.print(payload);
  udp.endPacket();

  Serial.println(payload);
  
  // Kurangi delay untuk kompensasi waktu proses yang sudah lama
  // Jika prosesnya makan waktu 15ms, delay sisa 5ms agar total 20ms (50Hz)
  unsigned long delayTime = 20 - (processTime / 1000);
  if (delayTime > 0 && delayTime <= 20) {
    delay(delayTime); 
  }
}