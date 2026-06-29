# ESP32 Meeting Timer Dial

This directory contains the Arduino sketch ([dial.ino](./dial.ino)) for an
ESP32-based physical meeting countdown timer. The USB connection is used
**only for power**; all schedule data is received wirelessly via WiFi. The
device polls a remote Cloud Function for timestamps and controls a servo
motor to move a dial indicating countdown time.

## Overview of Operation

1. **Startup & Network Selection**:
   - On boot, the ESP32 attempts to connect to configured WiFi networks in
     sequential order.
   - Once connected, it synchronizes its internal system clock using NTP
     (Network Time Protocol).
   - The status LED blinks to indicate which network index was successfully
     connected (1 blink for network 1, 2 blinks for network 2, etc.).
   - The servo performs an initial test sweep between 15 and 0 min positions.

2. **Main Loop & Polling**:
   - Every 30 seconds, the ESP32 makes an HTTP GET request to the configured
     Cloud Function endpoint.
   - The endpoint returns comma-separated UNIX timestamps:
     `prev_timestamp,next_timestamp`, where:
     - **`prev_timestamp`**: The Unix timestamp of the **end time** of the
       *last* past event (refers to events that started in the past, which can
       actually be a meeting that is in progress). Defaults to `0`.
     - **`next_timestamp`**: The Unix timestamp of the **start time** of the
       *first* future event (next meeting start). Defaults to `0`.
   - Based on current system time (`now`), the servo dial is positioned:
     - **Meeting in Progress**: If `now` is outside the window between
       `prev_timestamp` and `next_timestamp`, the dial moves to
       `SERVO_MEETING` (50°).
     - **No Upcoming Meeting**: If more than 15 minutes remain, the dial
       moves to `SERVO_NO_MEETING` (17°).
     - **Countdown (15 to 0 Mins)**: If 15 minutes or less remain, the servo
       angle is linearly interpolated between `SERVO_FIFTEEN_MINUTES` (152°)
       and `SERVO_ZERO_MINUTES` (65°).

## Configuration

Before flashing the code to your ESP32, update the following constants at the
top of [dial.ino](./dial.ino):

### 1. Cloud Function Endpoint
```cpp
const char* cloudFunctionUrl = "https://example.org/";
```
Replace `"https://example.org/"` with the actual URL of your Cloud Function.

### 2. WiFi Credentials
```cpp
const int NUM_NETWORKS = 4;
const char* ssids[NUM_NETWORKS] = {"ssid1", "ssid2", "ssid3", "ssid4"};
const char* passwords[NUM_NETWORKS] = {"pass1", "pass2", "pass3", "pass4"};
```
Update `ssids` and `passwords` with your local WiFi network credentials. The
ESP32 will try connecting to them in order.

### 3. Servo Angles (Calibration)
```cpp
const int SERVO_FIFTEEN_MINUTES = 152;
const int SERVO_ZERO_MINUTES = 65;
const int SERVO_MEETING = 50;
const int SERVO_NO_MEETING = 17;
```
Adjust these angles (in degrees) based on the physical mounting and dial face
calibration of your servo motor.

## Hardware Pin Configuration

The ESP32 GPIO pins are configured as follows:

| Pin Name | GPIO Pin | Mode / Function | Description |
| :--- | :--- | :--- | :--- |
| `LED_PIN` | GPIO 2 | `OUTPUT` | Status LED. Blinks network index. |
| `SERVO_PIN` | GPIO 21 | PWM (Servo) | Servo signal wire for dial pointer. |

## Dependencies

Ensure the following libraries are available in your Arduino / PlatformIO setup:
- **WiFi** (Built-in ESP32 core)
- **HTTPClient** (Built-in ESP32 core)
- **ESP32Servo** (Install via Arduino Library Manager)
