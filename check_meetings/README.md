# Google Calendar Meeting Timer

This script checks your Google Calendar for recent and upcoming meetings,
extracts their timestamps, and sends them to an external HTTP endpoint (e.g.,
a smart display or a meeting timer device).

To prevent unnecessary network traffic, the script caches the last sent update
locally and only sends a POST request when the timestamps actually change.

## Features

- **Automated OAuth2**: Authenticates securely with the Google Calendar API.
- **Headless friendly**: Once authorized, it runs automatically without user
  interaction, making it perfect for cron jobs.
- **Event Filtering**: Excludes all-day events, declined meetings, and
  long/multi-day events.
- **Deduplication**: Only hits your external webhook when there is a real
  change in meeting times.

______________________________________________________________________

## Timestamp Selection Algorithm

The script determines which timestamps to send using the following logic:

1. **Fetch Window**: It queries your primary calendar for events within a
   20-day window centered around the current time (10 days in the past to
   10 days in the future).
1. **Filtering**: It filters out:
   - Events that do not have a specific start or end time (all-day events).
   - Events where your response status is `declined`.
   - Events that are 8 hours or longer (multi-day events or holiday blocks).
1. **Sorting & Splitting**:
   - The remaining events are sorted by their start time.
   - They are split into two lists relative to the current time (`now`):
     - **Past events**: Events that started in the past (at or before `now`),
       which can actually be a meeting that is currently in progress.
     - **Future events**: Events that start after `now`.
1. **Timestamp Extraction**:
   - **`prev_timestamp`**: The Unix timestamp of the **end time** of the *last*
     past event (an event that started in the past, which can actually be a
     meeting that is in progress). Defaults to `0`.
   - **`next_timestamp`**: The Unix timestamp of the **start time** of the
     *first* event in the future list (next meeting start). Defaults to `0`.
1. **Update Check**: The script compares `prev_timestamp` and `next_timestamp`
   with `last_update.json`. If they match, it exits. If they differ, it sends
   a POST request to your webhook and updates `last_update.json`.

______________________________________________________________________

## Setup Instructions

### 1. Get `credentials.json` from Google Cloud

To access the Google Calendar API, you need to create a Desktop Application
client ID in the Google Cloud Console:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
1. Create a new project (e.g., `Meeting Timer`) or select an existing one.
1. Enable the **Google Calendar API**:
   - Go to **APIs & Services** > **Library**.
   - Search for **Google Calendar API** and click **Enable**.
1. Configure the **OAuth Consent Screen**:
   - Go to **APIs & Services** > **OAuth consent screen**.
   - Select User Type (**External** for personal, **Internal** for Workspace).
   - Fill out required app details (App name, support email) and click **Save**.
   - **Important**: If **External**, add your email under **Test Users**.
     Otherwise, Google blocks authentication for unverified apps.
1. Create Credentials:
   - Go to **APIs & Services** > **Credentials**.
   - Click **+ Create Credentials** > **OAuth client ID**.
   - Set the application type to **Desktop app**.
   - Name it (e.g., `Meeting Timer Desktop App`) and click **Create**.
1. Download the JSON file:
   - Click download next to your new client ID in the Credentials list.
   - Rename the downloaded file to exactly `credentials.json`.
   - Place this file in your data directory (defaults to project directory).

______________________________________________________________________

### 2. First Run (Initial Authorization)

The very first time you run the script, **you must run it manually in a
terminal with web browser access**.

The script launches a local web server and opens your browser to complete the
OAuth 2.0 authorization flow with Google.

Run the script from your terminal:

```bash
python3 check_meetings.py --email your_email@gmail.com \
  --url https://your-endpoint.com/webhook --data-dir path/to/data-dir
```

*Note: If `--data-dir` is omitted, it defaults to `.` (current directory).
Make sure `credentials.json` is in this directory before running.*

Once you log in and authorize the app in the browser:

- The script will complete the run.
- It automatically saves tokens into `token.json` inside `--data-dir`.
- Subsequent runs use `token.json` to authenticate and refresh automatically
  in the background without manual interaction.

______________________________________________________________________

### 3. Automating with Cron

Now that `token.json` is generated, the script can run headlessly on a schedule.

Set up a cron job to run periodically. Because cron runs in a minimal
environment, **you must use absolute paths** for Python, the script, and the
data directory in your crontab entry.

To edit your crontab, run:

```bash
crontab -e
```

Add this entry (note: crontab entries must be on a single line):

```cron
* * * * 1-5 /path/to/python3 /path/to/check_meetings.py \
  --email your_email@gmail.com --url https://your-endpoint.com/webhook \
  --data-dir /path/to/data >> /path/to/data/timer.log 2>&1
```

#### Crontab Timespec Breakdown (`* * * * 1-5`):

- `*` (1st): Run every minute.
- `*` (2nd): Run every hour.
- `*` (3rd): Run every day of the month.
- `*` (4th): Run every month.
- `1-5` (5th): Run only from Monday (1) to Friday (5).

*Replace `/path/to/python3`, `/path/to/check_meetings.py`, and `/path/to/data`
with actual absolute paths on your system.*
