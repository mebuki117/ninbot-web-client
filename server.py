import threading
import json
import time
import os
import copy

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


def run_flask():
    def run():
        app.run(host='0.0.0.0', port=PORT, debug=False)
        
    flask_thread = threading.Thread(target=run, daemon=True)
    flask_thread.start()

def load_options():
    global server_options
    with open(f'{os.getcwd()}\\config.json','r') as f:
        server_options = json.load(f)


app = Flask(__name__)

sse_fetcher = EventDataFetcher(SSE_URL)
sse_fetcher.start()

server_options = {
    'use_chunk_coords': False,
    'show_angle': True
}

load_options()

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
        with open(f'{os.getcwd()}\\config.json','w+') as f:
            json.dump(server_options, f)
        return jsonify({"status": "success", "message": f"{option} updated"}), 200
    
    return jsonify({"status": "error", "message": "Invalid option"}), 400

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_data')
def proxy_events():
    if (sse_fetcher.error):
        return jsonify({'error': sse_fetcher.error }), 500
    
    data = copy.deepcopy(sse_fetcher.get_data())

    
    use_chunk_coords = server_options.get('use_chunk_coords', False)
    new_preds = list(map(lambda x: {
        "certainty": x['certainty'],
        "x": x['chunkX'] * (1 if use_chunk_coords else 16),
        "z": x['chunkZ'] * (1 if use_chunk_coords else 16),
        "netherX":  x['chunkX'] * 2,
        "netherZ":  x['chunkZ'] * 2,
        "overworldDistance": x['overworldDistance']
    }, data['predictions']))
    
    data['predictions'] = new_preds
    
    return jsonify(data), 200
