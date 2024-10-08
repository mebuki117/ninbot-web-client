import threading
import json
import time
import os
import copy
import math
import logging
import re
import pyperclip

from flask import Flask, jsonify, request, render_template
from sseclient import SSEClient

API_VERSION = 1
STRONGHOLD_SSE_URL = f'http://localhost:52533/api/v{API_VERSION}/stronghold/events'
BLIND_SSE_URL = f'http://localhost:52533/api/v{API_VERSION}/blind/events'
BOAT_SSE_URL = f'http://localhost:52533/api/v{API_VERSION}/boat/events'
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
    app.run(host='0.0.0.0', port=PORT, debug=False)

def load_options():
    global server_options
    if not os.path.exists(f'{os.getcwd()}\\config.json'):
        with open(f'{os.getcwd()}\\config.json','w+') as f:
            return json.dump(server_options, f)
        
    with open(f'{os.getcwd()}\\config.json','r') as f:
        server_options = json.load(f)

def radians_to_degrees(radians):
    return round(radians * (180 / math.pi), 1)

def get_predictions(data):
    predictions = []
    command = pyperclip.paste()
    match = re.match(r'^/execute in minecraft:(overworld|the_nether) run tp @s [-+]?[0-9]*\.?[0-9]+ [-+]?[0-9]*\.?[0-9]+ [-+]?[0-9]*\.?[0-9]+ [-+]?[0-9]*\.?[0-9]+ [-+]?[0-9]*\.?[0-9]+$', command)
    
    if match:
        dimension = match.group(1)
        coords_and_angle = get_coords_and_angle(command)

        if coords_and_angle and all(item is not None for item in coords_and_angle):
            current_position = (coords_and_angle[0], coords_and_angle[1])
            current_angle = coords_and_angle[2]

            for pred in data['predictions']:
                chunkX = pred['chunkX']
                chunkZ = pred['chunkZ']
                target_position = ((chunkX * 16) + 4, (chunkZ * 16) + 4)

                direction = round(get_direction(current_position, target_position, current_angle), 2)

                if dimension == "the_nether":
                    distance = round(pred['overworldDistance'] / 8)
                else:
                    distance = pred['overworldDistance']

                predictions.append({
                    "certainty": pred['certainty'],
                    "x": chunkX if server_options['use_chunk_coords'] else (chunkX * 16 + 4),
                    "z": chunkZ if server_options['use_chunk_coords'] else (chunkZ * 16 + 4),
                    "netherX": chunkX * 2,
                    "netherZ": chunkZ * 2,
                    "overworldDistance": distance,
                    "angle": round(get_direction(current_position, target_position), 2) if server_options['show_angle'] else None,
                    "direction": direction,
                    "useChunk": True if server_options['use_chunk_coords'] else False
                })
    else:
        for pred in data['predictions']:
            chunkX = pred['chunkX']
            chunkZ = pred['chunkZ']

            predictions.append({
                "certainty": pred['certainty'],
                "x": chunkX if server_options['use_chunk_coords'] else (chunkX * 16 + 4),
                "z": chunkZ if server_options['use_chunk_coords'] else (chunkZ * 16 + 4),
                "netherX": chunkX * 2,
                "netherZ": chunkZ * 2,
                "overworldDistance": pred['overworldDistance'],
                "angle": '---' if server_options['show_angle'] else None,
                "direction": None,
                "useChunk": True if server_options['use_chunk_coords'] else False
            })

    return predictions

def get_blindresult(player_data):
    api_evaluations = {
        'EXCELLENT': 'excellent',
        'HIGHROLL_GOOD': 'good for highroll',
        'HIGHROLL_OKAY': 'okay for highroll',
        'BAD_BUT_IN_RING': 'bad, but in ring',
        'BAD': 'bad',
        'NOT_IN_RING': 'not in any ring'
    }

    evaluation = player_data.get('evaluation')
    if evaluation in api_evaluations:
        player_data['evaluation'] = api_evaluations[evaluation]

    player_data['highrollProbability'] = f"{player_data.get('highrollProbability', 0) * 100:.1f}%"
    return player_data

def get_player_data(sse_fetcher, type):
    data = copy.deepcopy(sse_fetcher.get_data())
    
    if type == 'stronghold':     
        player_data = data.get('predictions', {})
        
        data['predictions'] = get_predictions(data)
        return data
    
    elif type == 'blind':      
        player_data = data.get('blindResult', {})
        
        player_data['xInNether'] = round(player_data.get('xInNether', 0))
        player_data['zInNether'] = round(player_data.get('zInNether', 0))
        player_data['improveDirection'] = radians_to_degrees(player_data.get('improveDirection', 0))
        player_data['improveDistance'] = round(player_data.get('improveDistance', 0))

        data['blindResult'] = get_blindresult(player_data)
        return data

    return data

def get_direction(current_position, target_position, current_angle=None):
    x1, y1 = current_position
    x2, y2 = target_position

    delta_x = x2 - x1
    delta_y = y2 - y1

    target_angle_rad = math.atan2(delta_y, delta_x)
    target_angle_deg = math.degrees(target_angle_rad)

    target_angle_deg = (target_angle_deg + 270) % 360

    if current_angle is None:
        if target_angle_deg > 180:
            target_angle_deg -= 360
        return target_angle_deg

    current_angle = current_angle % 360
    direction = target_angle_deg - current_angle

    direction = (direction + 180) % 360 - 180

    return direction

def get_coords_and_angle(command):
    match = re.search(r'tp @s (-?\d+\.\d+) \d+\.\d+ (-?\d+\.\d+) (-?\d+\.\d+)', command)
    if match:
        x = float(match.group(1))
        z = float(match.group(2))
        angle = float(match.group(3))
        return [x, z, angle]
    else:
        return None

app = Flask(__name__)

app.logger.setLevel(logging.WARNING)

werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.WARNING)

fetchers = {
    'stronghold': EventDataFetcher(STRONGHOLD_SSE_URL),
    'blind': EventDataFetcher(BLIND_SSE_URL),
    'boat': EventDataFetcher(BOAT_SSE_URL)
}

for fetcher in fetchers.values():
    fetcher.start()

server_options = {
    'use_chunk_coords': True,
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
    def get_response_code(player_data, base_code):
        response_codes = {
            'NONE': base_code,
            'MEASURING': base_code + 1,
            'VALID': base_code + 2,
            'ERROR': base_code + 3
        }
        return response_codes.get(player_data)

    for fetcher_name, fetcher in fetchers.items():
        if fetcher.error:
            return jsonify({'error': fetcher.error}), 510

    boat_data = copy.deepcopy(fetchers['boat'].get_data())
    player_data = boat_data.get('boatState', None)

    data = get_player_data(fetchers['stronghold'], 'stronghold')
    if data['predictions']:
        base_code = 201
        response_code = get_response_code(player_data, base_code)
        return jsonify(data), response_code
    elif data.get('eyeThrows'):
        base_code = 206
        response_code = get_response_code(player_data, base_code)
        data['misread'] = True
        return jsonify(data), response_code

    data = get_player_data(fetchers['blind'], 'blind')
    if data['isBlindModeEnabled']:
        base_code = 211
        response_code = get_response_code(player_data, base_code)
        return jsonify(data), response_code

    response_code = get_response_code(player_data, 501)
    if response_code:
        data['angle'] = True if server_options['show_angle'] else None
        return jsonify(data), response_code

    return jsonify(data), 500
