#include <Arduino.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>
#include <WiFi.h>
#include <WiFiUdp.h>

const char* ssid = "Wokwi-GUEST"; // Ganti jika pakai WiFi fisik
const char* password = "";        // Ganti jika pakai WiFi fisik

const char* hostRaspi = "192.168.1.7"; // IP Raspberry Pi VM
const int portUDP = 12345;

Adafruit_MPU6050 mpu;
WiFiUDP udp;

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);

  WiFi.begin(ssid, password);
  Serial.print("Menghubungkan ke WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
  }
  Serial.println("\nWiFi Terhubung!");

  if (!mpu.begin()) {
    Serial.println("MPU6050 tidak terdeteksi!");
    while (1) { delay(10); }
  }
  mpu.setAccelerometerRange(MPU6050_RANGE_2_G);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
}

void loop() {
  unsigned long startProcess = micros();

  // 1. Baca Sensor
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  // 2. Hitung waktu komputasi Skenario A (Sangat cepat)
  unsigned long processTime = micros() - startProcess;

  // 3. Format Data: "0(Raw), Waktu(us), X, Y, Z"
  char payload[100];
  snprintf(payload, sizeof(payload), "0,%lu,%.4f,%.4f,%.4f", 
           processTime, a.acceleration.x, a.acceleration.y, a.acceleration.z);

  // 4. Kirim via UDP
  udp.beginPacket(hostRaspi, portUDP);
  udp.print(payload);
  udp.endPacket();

  Serial.println(payload);
  delay(20); // Sampling rate ~50Hz
}