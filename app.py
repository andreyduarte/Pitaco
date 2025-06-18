from flask import Flask, request
from llm_inference import _make_embedding_call
import json
import message
from database import init_db, close_db, add_notification

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!', 200

@app.route('/send', methods=['POST'])
def webhook():
    """
    Webhook endpoint to receive strings.
    """
    data = request.get_data(as_text=True)

    if not data:
        return "No data received", 400

    ignore_channels = [
        'NETWORK_ALERTS',
        'CHR'
    ]
    ignore_apps = [
        'Instagram'
    ]

    try:
        # Attempt to load the data as JSON
        json_data = json.loads(data)

        if json_data.get('channel') in ignore_channels or json_data.get('app') in ignore_apps:
            print("Ignoring notification.")
            return "Ignored Notification", 200

        embedding = _make_embedding_call(data)

        if embedding:
            add_notification(data, embedding)
            print("Notification and embedding saved to database.")
        else:
            print("Failed to generate embedding or save to database.")

        return "String received!", 200

    except json.decoder.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        print(f"Received data: {data}")
        return "Invalid JSON received", 400

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.teardown_appcontext(close_db)
    app.run(debug=True, port=8080, host='0.0.0.0')
