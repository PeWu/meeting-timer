# Google Calendar Meeting Timer - Cloud Function

This directory contains the Google Cloud Function that acts as a secure,
lightweight database bridge for the meeting timer.

It exposes a single HTTP endpoint that:
- **`POST`**: Accepts new meeting timestamps from your local calendar checker
  script and saves them to Google Cloud Datastore.
- **`GET`**: Returns current timestamps as a simple comma-separated string
  (`prev_timestamp,next_timestamp`), easily fetched by lightweight clients.

---

## Architecture & Database Setup

The function uses **Google Cloud Datastore** (Firestore in Datastore mode) to
persist the meeting timestamps.

### Step 1: Initialize Datastore
Before deploying, ensure Datastore is initialized in your Google Cloud Project:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Select your project.
3. Navigate to **Firestore** or **Datastore** in the sidebar.
4. You will be prompted to create a database:
   - **Database ID**: Must be **`(default)`** (default selection).
   - **Database Mode**: Select **Firestore in Datastore mode** (also called
     **Firestore with Datastore compatibility**).
   - **Location**: Select a region close to you (e.g., `europe-west1` or
     `us-central1`). Deploy database and function in the same region.
5. Click **Create Database**.

Once created, Datastore runs silently in the background. The Cloud Function
automatically connects to this `(default)` database.

---

## Deployment

You can deploy this function to Google Cloud using the `gcloud` CLI.

### Prerequisites
Ensure you have the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
installed and authenticated:
```bash
gcloud auth login
gcloud config set project [your-gcp-project-id]
```

### Deploy Command
Run the following command from within the `cloud_function/` directory:

```bash
gcloud functions deploy calendar-timestamps \
    --gen2 \
    --runtime=python310 \
    --region=europe-west1 \
    --trigger-http \
    --entry-point=calendar_timestamps \
    --allow-unauthenticated
```

*Note: Replace `europe-west1` with your preferred region if necessary.*

### Deployment Flags Explained:
- `--gen2`: Deploys as a 2nd generation Cloud Function (built on Cloud Run).
- `--runtime=python310`: Runs on Python 3.10.
- `--region=europe-west1`: Specifies the physical hosting location.
- `--trigger-http`: Exposes the function via a public HTTP URL.
- `--entry-point=calendar_timestamps`: Points to the Python function name
  inside `main.py` that handles the requests.
- `--allow-unauthenticated`: Allows public access to the URL (essential so
  your local script and display clients can reach it).

After successful deployment, the CLI outputs the public URL in the
`serviceConfig.uri` field. It looks like:
`https://calendar-timestamps-[hash]-[region].a.run.app`

---

## API Endpoints

Once deployed, you can interact with the function's URL.

### 1. Read Timestamps (GET)
To fetch currently stored timestamps, send a `GET` request to the URL:

```bash
curl https://[your-cloud-function-url]/
```

**Response**:
A plain-text comma-separated string containing previous and next meeting
timestamps (in Unix epoch format).
- If no data has been uploaded yet, it returns: `0,0`
- Once populated, it returns: `1719225000,1719232200`

---

### 2. Update Timestamps (POST)
To update timestamps, send a `POST` request with a JSON payload containing
`prev_timestamp` and `next_timestamp`:

```bash
curl -X POST https://[your-cloud-function-url]/ \
     -H "Content-Type: application/json" \
     -d '{"prev_timestamp": 1719225000, "next_timestamp": 1719232200}'
```

**Response**:
Returns the newly updated timestamps as a comma-separated string:
`1719225000,1719232200`
