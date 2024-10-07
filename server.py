import threading
import json
import time
import os
import copy
import math
import logging
import requests

from flask import Flask, jsonify, request, render_template
from sseclient import SSEClient

NINBOT_BASE_URL = 'http://localhost:52533'
STRONGHOLD_SSE_URL = f'{NINBOT_BASE_URL}/api/v1/stronghold/events' 
BOAT_SSE_URL = 'http://localhost:52533/api/v1/boat/events' 


PORT = 31621

class DataFetcher:
    def __init__(self):
        
        self.data = {}
        self.error = None
        self.t1 = threading.Thread(target=lambda: self._sse_worker(STRONGHOLD_SSE_URL, "stronghold"), daemon=True)
        self.t2 = threading.Thread(target=lambda: self._sse_worker(BOAT_SSE_URL, "boat"), daemon=True)
        self.t3 = threading.Thread(target=self.fetch_version, daemon=True)
    def start(self):
        self.t1.start()
        self.t2.start()
        self.t3.start()

    def _sse_worker(self, url, data_name):
        while True:
            try:
                client = SSEClient(url)
                self.error = None
                
                for msg in client:
                    if msg.event == 'message':
                        self.data[data_name] = json.loads(msg.data)
                
            except Exception as e:
                self.error = e.__str__()
                time.sleep(5) # wait 5s before rc

    def fetch_version(self):
        res = requests.get(f'{NINBOT_BASE_URL}/api/v1/version')
        if res.status_code == 200:
            self.data['version'] = res.json()['version']
    
    def get_data(self):
        return self.data



def run_flask():
    app.run(host='0.0.0.0', port=PORT, debug=False)

def load_options():
    global server_options
    if not os.path.exists(f'{os.getcwd()}\\config.json'):
        with open(f'{os.getcwd()}\\config.json','w+') as f:
            return json.dump(server_options, f)
        
    with open(f'{os.getcwd()}\\config.json','r') as f:
        server_options = json.load(f)

def get_angle_to(x1, z1, x2, z2):
    angleDegrees = math.degrees(math.atan2(z1 - z2, x1 - x2))
    angleDegrees -= 90
    if (angleDegrees > 180):
        angleDegrees -= 360
    elif (angleDegrees <= -180):
        angleDegrees += 360

    return round(angleDegrees * 10) / 10.0

app = Flask(__name__)

app.logger.setLevel(logging.WARNING)
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.WARNING)

sse_fetcher = DataFetcher()
sse_fetcher.start()

server_options = {
    'use_chunk_coords': False,
    'show_angle': True
}

load_options()

@app.route('/')
def index():
    return render_template('index.html')

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
        
        return jsonify({"message": f"{option} updated"}), 200
    
    return jsonify({"error":"Invalid option"}), 400

@app.route('/get_data')
def get_data():
    if (sse_fetcher.error):
        return jsonify({'error': sse_fetcher.error }), 500
    
    data = copy.deepcopy(sse_fetcher.get_data())
    use_chunk_coords = server_options.get('use_chunk_coords', False)

    sh_data = data['stronghold']
    
    playerData = sh_data['playerPosition']
    px = playerData.get('xInOverworld', 0)
    pz = playerData.get('zInOverworld', 0)
    
    new_preds = list(map(lambda x: {
        "certainty": x['certainty'],
        "x": x['chunkX'] * (1 if use_chunk_coords else 16) + (0 if use_chunk_coords else 4),
        "z": x['chunkZ'] * (1 if use_chunk_coords else 16) + (0 if use_chunk_coords else 4),
        "netherX":  x['chunkX'] * 2,
        "netherZ":  x['chunkZ'] * 2,
        "overworldDistance": x['overworldDistance'] / (8 if playerData.get('isInNether', False) else 1),
        "angle": get_angle_to(x['chunkX'] * 16, x['chunkZ'] * 16, px, pz) if server_options['show_angle'] else None
    }, sh_data['predictions']))

    sh_data['predictions'] = new_preds
    return jsonify(data), 200
