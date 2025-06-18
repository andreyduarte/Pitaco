from flask import Flask, request
from llm_inference import _make_embedding_call
import json
from database import init_db, close_db, add_notification

app = Flask(__name__)

@app.route('/send', methods=['POST'])
def webhook():
    """
    Webhook endpoint to receive strings.
    """
    data = request.get_data(as_text=True)
    print(f"Received string: {data}")

    if not data:
        return "No data received", 400

    # Escape newline and carriage return characters to prevent JSONDecodeError
    data = data.replace('\n', '\\n').replace('\r', '\\r')

    ignore_channels = [
        'NETWORK_ALERTS',
        'CHR'
    ]
    ignore_apps = [
        'Instagram'
    ]

    if json.loads(data)['channel'] in ignore_channels or json.loads(data)['app'] in ignore_apps: 
        print("Ignoring notification.")
        return "Ignored Notification", 200
    
    embedding = _make_embedding_call(data)

    if embedding:
        add_notification(data, embedding)
        print("Notification and embedding saved to database.")
    else:
        print("Failed to generate embedding or save to database.")

    return "String received!", 200

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.teardown_appcontext(close_db)
    app.run(debug=True, port=8080, host='0.0.0.0')
