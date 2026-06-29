import functions_framework
from google.cloud import datastore

# Initialize the Datastore client globally.
# Cloud Functions will reuse this client and its connection pools across warm starts,
# significantly reducing latency and resource usage.
client = datastore.Client()

@functions_framework.http
def calendar_timestamps(request):
    # Restrict allowed HTTP methods
    if request.method not in ('GET', 'POST'):
        return 'Method Not Allowed', 405

    if request.method == 'POST':
        request_json = request.get_json(silent=True)
        print(f"got POST request with payload: {request_json}")

        # Validate the incoming payload
        if not request_json or 'prev_timestamp' not in request_json or 'next_timestamp' not in request_json:
            return 'Bad Request', 400

        print(f"setting new values: {request_json['prev_timestamp']}, {request_json['next_timestamp']}")
        entity = datastore.Entity(client.key('meeting-timer', 'default'))
        entity['prev_timestamp'] = request_json['prev_timestamp']
        entity['next_timestamp'] = request_json['next_timestamp']
        client.put(entity)

    # Retrieve and return the current state for both GET and successful POST requests
    entity = client.get(client.key('meeting-timer', 'default'))
    if not entity:
        return '0,0'
    return f'{entity.get("prev_timestamp", 0)},{entity.get("next_timestamp", 0)}'
