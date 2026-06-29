#!/usr/bin/python3
"""Checks Google Calendar for recent and upcoming meetings, and sends timestamps to an external display."""

import argparse
import datetime
import json
import os.path
import requests

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def is_declined(event, email):
    """Returns True if the attendee with the given email has declined the event."""
    if not event.get('attendees'):
        return False
    attendee = next((a for a in event['attendees'] if a['email'] == email), None)
    return attendee is not None and attendee.get('responseStatus') == 'declined'

def get_start(event):
    return datetime.datetime.fromisoformat(event['start']['dateTime'][:-1] + '+00:00')

def get_end(event):
    return datetime.datetime.fromisoformat(event['end']['dateTime'][:-1] + '+00:00')

def duration(event):
    return get_end(event) - get_start(event)

def to_json(creds):
    """Serializes Credentials object to a JSON string, filtering out empty fields."""
    prep = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }

    # Remove empty entries
    prep = {k: v for k, v in prep.items() if v is not None}

    return json.dumps(prep)


def main():
    parser = argparse.ArgumentParser(description='Check upcoming Google Calendar events.')
    parser.add_argument('--email', required=True, help='Email address to check attendee status for')
    parser.add_argument('--data-dir', default='.', help='Directory containing credentials.json and storing token.json')
    parser.add_argument('--url', required=True, help='URL of the HTTP function to update')
    args = parser.parse_args()

    credentials_file = os.path.join(args.data_dir, 'credentials.json')
    token_file = os.path.join(args.data_dir, 'token.json')
    last_update_file = os.path.join(args.data_dir, 'last_update.json')

    # Load cached OAuth credentials from token.json if it exists.
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    # If credentials are not available or expired, perform the OAuth flow.
    if not creds:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_file, 'w') as token:
            token.write(to_json(creds))

    try:
        service = build('calendar', 'v3', credentials=creds)

        # Retrieve primary calendar events in a 20-day window centered around now
        now = datetime.datetime.utcnow()
        timeMin = (now - datetime.timedelta(days=10)).isoformat() + 'Z'
        timeMax = (now + datetime.timedelta(days=10)).isoformat() + 'Z'
        print(f"Fetching events between {timeMin} and {timeMax}...")
        events_result = service.events().list(calendarId='primary', timeMin=timeMin, timeMax=timeMax,
                                              maxResults=100, singleEvents=True,
                                              orderBy='startTime', timeZone='UTC').execute()
        events = events_result.get('items', [])

        # Filter events:
        # 1. Must have start and end time (excludes all-day events).
        # 2. Must not be declined by the user.
        # 3. Must be shorter than 8 hours (excludes multi-day events).
        events = [e for e in events if e['start'].get('dateTime') and e['end'].get('dateTime')]
        events = [e for e in events if not is_declined(e, args.email)]
        events = [e for e in events if duration(e) < datetime.timedelta(hours=8)]        

        if not events:
            print('No upcoming events found.')
            return

        # Split events into those that have started/ended vs those in the future
        past = [e for e in events if datetime.datetime.fromisoformat(e['start']['dateTime'][:-1]) <= now]
        future = [e for e in events if datetime.datetime.fromisoformat(e['start']['dateTime'][:-1]) > now]

        prev_timestamp = 0
        next_timestamp = 0

        # Get the end timestamp of the most recent past event
        if past:
            prev = past[-1]
            prev_end = datetime.datetime.fromisoformat(prev['end']['dateTime'][:-1])
            print(f"Last meeting: '{prev['summary']}' (ended at {prev_end} UTC)")
            prev_timestamp = int(get_end(prev).timestamp())

        # Get the start timestamp of the next upcoming event
        if future:
            next = future[0]
            next_start = datetime.datetime.fromisoformat(next['start']['dateTime'][:-1])
            print(f"Next meeting: '{next['summary']}' (starts at {next_start} UTC)")
            next_timestamp = int(get_start(next).timestamp())

        update_data = {"prev_timestamp": prev_timestamp, "next_timestamp": next_timestamp}

        # Load the last sent update to avoid sending duplicate requests
        try:
            prev_update = json.load(open(last_update_file))
        except:
            prev_update = None

        if update_data == prev_update:
            print("No changes in timestamps. Skipping update.")
        else:
            # Send the new timestamps to the external HTTP display function and cache them locally
            print(f"Sending update to {args.url} (prev: {prev_timestamp}, next: {next_timestamp})...")
            response = requests.post(
                args.url,
                json=update_data)
            print(f"Update response: {response.text.strip()}")

            json.dump(update_data, open(last_update_file, 'w'))



    except HttpError as error:
        print('An error occurred: %s' % error)


if __name__ == '__main__':
    main()
