#include <WiFi.h>
#include <HTTPClient.h>
#include "time.h"
#include <ESP32Servo.h>

// Cloud Function endpoint that serves meeting timestamps (start_time,end_time).
const char* cloudFunctionUrl = "https://example.org/";

// WiFi credentials configuration.
// Networks will be attempted sequentially in the order defined below.
const int NUM_NETWORKS = 4;
const char* ssids[NUM_NETWORKS] = {"ssid1", "ssid2", "ssid3", "ssid4"};
const char* passwords[NUM_NETWORKS] = {"password1", "password2", "password3", "password4"};

// NTP (Network Time Protocol) server configuration for time synchronization.
const char* ntpServer = "pool.ntp.org";
// UTC offset in seconds (0 for GMT/UTC)
const long gmtOffset_sec = 0;
// Daylight savings offset in seconds
const int daylightOffset_sec = 0;

// Servo motor angle definitions (in degrees) corresponding to dial positions.
// 15 minutes until beginning of meeting
const int SERVO_FIFTEEN_MINUTES = 152;
// 0 minutes until beginning of meeting
const int SERVO_ZERO_MINUTES = 65;
// Meeting in progress
const int SERVO_MEETING = 50;
// No meeting within 15 minutes
const int SERVO_NO_MEETING = 17;

// Hardware pin assignments
// Onboard status LED
const int LED_PIN = 2;
// GPIO pin connected to the servo signal wire
const int SERVO_PIN = 21;
Servo myservo;

// Tracks the index of the successfully connected WiFi network (-1 indicates disconnected)
int connectedNetworkIndex = -1;

void setup() {
  // Initialize serial communication for debugging output
  Serial.begin(115200);

  // Configure status LED and ensure it starts turned off
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  // Attach servo motor to its designated GPIO pin
  myservo.attach(SERVO_PIN);

  // Allow hardware and power supply to stabilize before initiating WiFi
  delay(3000);

  // Iterate through the configured WiFi networks to find an available connection
  for (int i = 0; i < NUM_NETWORKS; i++) {
    Serial.print("Attempting to connect to Network ");
    Serial.print(i + 1);
    Serial.print(": ");
    Serial.println(ssids[i]);

    // Reset WiFi interface to station mode to ensure a clean connection attempt
    WiFi.mode(WIFI_OFF);
    delay(500);
    WiFi.mode(WIFI_STA);
    delay(500);

    WiFi.begin(ssids[i], passwords[i]);
    delay(5000);

    // Poll WiFi status for up to 10 seconds (20 attempts * 500ms)
    int attempt = 0;
    while (WiFi.status() != WL_CONNECTED && attempt < 20) {
      delay(500);
      Serial.print(".");
      attempt++;
    }

    if (WiFi.status() == WL_CONNECTED) {
      Serial.println("\nSuccess! Connected.");

      // Synchronize system clock with NTP server
      configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
      Serial.print("IP Address: ");
      Serial.println(WiFi.localIP());

      // Store the index of the connected network for status indication in loop()
      connectedNetworkIndex = i;

      // Successfully connected; exit network search loop
      break;
    } else {
      Serial.println("\nFailed. Trying next...");
    }
  }

  if (connectedNetworkIndex == -1) {
    Serial.println("Could not connect to any network.");
  }

  // Perform startup dial animation to verify servo movement and indicate readiness
  myservo.write(SERVO_FIFTEEN_MINUTES);
  delay(1000);
  myservo.write(SERVO_ZERO_MINUTES);
  delay(1000);
}

void loop() {
  // Verify active WiFi connection before executing main logic
  if (WiFi.status() != WL_CONNECTED || connectedNetworkIndex == -1) {
    // Turn off status LED if connection is lost
    digitalWrite(LED_PIN, LOW);
    return;
  }

  // Calculate blink count based on connected network
  // (Network 1 = 1 blink, Network 2 = 2 blinks, etc.)
  int blinks = connectedNetworkIndex + 1;

  // Blink status LED to indicate active network connection
  for (int j = 0; j < blinks; j++) {
    digitalWrite(LED_PIN, HIGH);
    delay(200);
    digitalWrite(LED_PIN, LOW);
    delay(200);
  }

  // Fetch current meeting schedule timestamps from Cloud Function
  HTTPClient http;
  http.begin(cloudFunctionUrl);
  int httpCode = http.GET();
  if (httpCode == HTTP_CODE_OK) {
    String payload = http.getString();
    int commaIndex = payload.indexOf(',');
    if (commaIndex != -1) {
      // Parse comma-separated UNIX timestamps from response payload
      // Meeting start time
      time_t time1 = payload.substring(0, commaIndex).toInt();
      // Meeting end time
      time_t time2 = payload.substring(commaIndex + 1).toInt();
      // Current system time
      time_t now = time(nullptr);

      Serial.print("--- ");
      Serial.println(time1);
      Serial.println(time2);
      Serial.println(now);

      // Check if current time is outside the active meeting window
      if (now < time1 || now > time2) {
        myservo.write(SERVO_MEETING);
      } else {
        // Calculate remaining meeting duration in seconds
        time_t diff = time2 - now;
        if (diff > 15 * 60) {
          // More than 15 minutes remaining
          myservo.write(SERVO_NO_MEETING);
        } else {
          // Linearly interpolate servo angle between 15 minutes and 0 minutes remaining
          myservo.write(SERVO_ZERO_MINUTES +
                        (SERVO_FIFTEEN_MINUTES - SERVO_ZERO_MINUTES) * diff /
                            (15 * 60));
        }
      }
    }
  }
  http.end();

  // Wait 30 seconds before polling the Cloud Function again
  delay(30000);
}
