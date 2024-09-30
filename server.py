import threading
import json
import time
from flask import Flask, jsonify, request, render_template
from sseclient import SSEClient

SSE_URL = 'http://localhost:52533/api/v1/stronghold/events' 
PORT = 31621

class EventDataFetcher:
    def __init__(self, sse_url):
        self.sse_url = sse_url
        self.data = {}
        self.error = None
        self.thread = threading.Thread(target=self._sse_worker, daemon=True)
    
    def start(self):
        self.thread.start()
    
    def _sse_worker(self):
        while True:
            try:
                client = SSEClient(self.sse_url)
                self.error = None
                
                for msg in client:
                    if msg.event == 'message':
                        self.data = json.loads(msg.data)
                
            except Exception as e:
                self.error = e.__str__()
                time.sleep(5) # wait 5s before rc

    def get_data(self):
        return self.data


app = Flask(__name__)

server_options = {
    'use_chunk_coords': False,
    'show_angle': True
}

@app.route('/get_options', methods=['GET'])
def get_options():
    return jsonify(server_options), 200

@app.route('/update_option', methods=['POST'])
def update_option():
    data = request.json
    option = data.get('option')
    value = data.get('value')
    if option in server_options:
        server_options[option] = value
        return jsonify({"status": "success", "message": f"{option} updated"}), 200
    return jsonify({"status": "error", "message": "Invalid option"}), 400

sse_fetcher = EventDataFetcher(SSE_URL)
sse_fetcher.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/events')
def proxy_events():
    if (sse_fetcher.error):
        return jsonify({'error': sse_fetcher.error }), 500
    
    return jsonify(sse_fetcher.get_data()), 200

def run_flask():
    def run():
        app.run(host='0.0.0.0', port=PORT, debug=False)
    flask_thread = threading.Thread(target=run, daemon=True)
    flask_thread.start()