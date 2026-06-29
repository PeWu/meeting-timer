# Frequently Asked Questions (FAQ)

## Architecture & Design

### Why do I need Cloud Functions? Can't the ESP check Calendar directly?

Beyond the memory and processing limits of microcontrollers, storing private
Google Calendar API credentials on the ESP device was intentionally avoided.
The ESP is designed to hold the least possible data required to operate (just
two UNIX timestamps).

### How much will Google Cloud cost me to run this?

Running this project should cost nothing. Polling every 30 seconds results in
roughly 2,880 requests per day, which is well within Google Cloud's free tier
limit of 2 million monthly invocations.

### Does this work with Outlook, Microsoft 365, or Apple Calendar?

Currently, the calendar checker script only supports the Google Calendar API.

## Hardware & Power

### Can I use an ESP8266 instead of an ESP32?

Yes, an ESP8266 would also work. You may need to adjust the library includes in
`dial.ino` for the ESP8266 core.

### Can I power the timer with a battery?

The device is designed for 5V USB power. Without implementing deep sleep modes,
maintaining an active WiFi connection and powering the servo motor would drain
a standard battery very quickly.

### Why does my servo motor buzz?

The servo buzzes when it moves the needle. It does not jitter if the power
supply is stable.

## Setup & Calibration

### How do I calibrate the servo angles?

Trial and error. Adjust the angle constants (`SERVO_FIFTEEN_MINUTES`,
`SERVO_ZERO_MINUTES`, etc.) at the top of `dial.ino` and re-upload until the
needle aligns accurately with your printed dial face.

### What happens if I have back-to-back or overlapping meetings?

For back-to-back meetings, the dial will stay on "in meeting".

### How do I automate `check_meetings.py` on Windows or macOS?

Automating the script outside of Linux cron is an exercise left to the reader.
Pull requests with instructions for Windows or macOS are very welcome!
