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
SSE_STRONGHOLD_URL = f'http://localhost:52533/api/v{API_VERSION}/stronghold/events'
SSE_BLIND_URL = f'http://localhost:52533/api/v{API_VERSION}/blind/events'
SSE_BOAT_URL = f'http://localhost:52533/api/v{API_VERSION}/boat/events'
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

def get_angle_to(x1, z1, x2, z2):
    angleDegrees = math.degrees(math.atan2(z1 - z2, x1 - x2))
    angleDegrees -= 90
    if (angleDegrees > 180):
        angleDegrees -= 360
    elif (angleDegrees <= -180):
        angleDegrees += 360

    return round(angleDegrees * 10) / 10.0

import copy

def process_predictions(data, player_position, use_chunk_coords):
    px = player_position.get('xInOverworld', 0)
    pz = player_position.get('zInOverworld', 0)

    predictions = []

    command = pyperclip.paste()
    match = re.match(r'^/execute in ([^ ]+) run tp @s [-+]?[0-9]*\.?[0-9]+ [-+]?[0-9]*\.?[0-9]+ [-+]?[0-9]*\.?[0-9]+ [-+]?[0-9]*\.?[0-9]+ [-+]?[0-9]*\.?[0-9]+$', command)
    
    if match:
        dimension = match.group(1)
        coordinates_and_angle = extract_coordinates_and_angle(command)

        if coordinates_and_angle and all(item is not None for item in coordinates_and_angle):
            current_position = (coordinates_and_angle[0], coordinates_and_angle[1])
            current_angle = coordinates_and_angle[2]

            for pred in data['predictions']:
                chunkX = pred['chunkX']
                chunkZ = pred['chunkZ']
                target_position = ((chunkX * 16) + 4, (chunkZ * 16) + 4)

                angle_change = round(calculate_angle_change(current_position, target_position, current_angle), 2)

                if dimension == "minecraft:the_nether":
                    overworld_distance = round(pred['overworldDistance'] / 8)
                else:
                    overworld_distance = pred['overworldDistance']

                print(f"chunkX: {chunkX}, chunkZ: {chunkZ}")

                predictions.append({
                    "certainty": pred['certainty'],
                    "x": chunkX if use_chunk_coords else (chunkX * 16 + 4),
                    "z": chunkZ if use_chunk_coords else (chunkZ * 16 + 4),
                    "netherX": chunkX * 2,
                    "netherZ": chunkZ * 2,
                    "overworldDistance": overworld_distance,
                    "angle": get_angle_to(chunkX * 16, chunkZ * 16, px, pz) if server_options['show_angle'] else None,
                    "angleChange": angle_change
                })
        else:
            print("Invalid coordinates or angle extracted.")
    else:
        for pred in data['predictions']:
            chunkX = pred['chunkX']
            chunkZ = pred['chunkZ']

            predictions.append({
                "certainty": pred['certainty'],
                "x": chunkX if use_chunk_coords else (chunkX * 16 + 4),
                "z": chunkZ if use_chunk_coords else (chunkZ * 16 + 4),
                "netherX": chunkX * 2,
                "netherZ": chunkZ * 2,
                "overworldDistance": pred['overworldDistance'],
                "angle": '---' if server_options['show_angle'] else None,
                "angleChange": None
            })

    return predictions

def process_blind(player_data):
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

def process_player_data(sse_fetcher, type):
    data = copy.deepcopy(sse_fetcher.get_data())
    
    if type == 'stronghold':     
        player_data = data.get('predictions', {})
        use_chunk_coords = server_options.get('use_chunk_coords', False)
        player_position = data['playerPosition']
        
        data['predictions'] = process_predictions(data, player_position, use_chunk_coords)

        return data
    
    elif type == 'blind':      
        player_data = data.get('blindResult', {})
        
        player_data['xInNether'] = round(player_data.get('xInNether', 0))
        player_data['zInNether'] = round(player_data.get('zInNether', 0))

        data['blindResult'] = process_blind(player_data)
        return data

    return data

def calculate_angle_change(current_position, target_position, current_angle):
    x1, y1 = current_position
    x2, y2 = target_position

    delta_x = x2 - x1
    delta_y = y2 - y1

    target_angle_rad = math.atan2(delta_y, delta_x)
    target_angle_deg = math.degrees(target_angle_rad)

    target_angle_deg = (target_angle_deg + 270) % 360

    current_angle = current_angle % 360

    angle_change = target_angle_deg - current_angle

    angle_change = (angle_change + 180) % 360 - 180

    return angle_change

def extract_coordinates_and_angle(command):
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

sse_stronghold_fetcher = EventDataFetcher(SSE_STRONGHOLD_URL)
sse_blind_fetcher = EventDataFetcher(SSE_BLIND_URL)
sse_boat_fetcher = EventDataFetcher(SSE_BOAT_URL)
sse_stronghold_fetcher.start()
sse_blind_fetcher.start()
sse_boat_fetcher.start()

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
    def get_response_code(player_data, base_code):
        response_codes = {
            'NONE': base_code,
            'MEASURING': base_code + 1,
            'VALID': base_code + 2,
            'ERROR': base_code + 3
        }
        return response_codes.get(player_data)

    for fetcher in [sse_stronghold_fetcher, sse_blind_fetcher, sse_boat_fetcher]:
        if fetcher.error:
            return jsonify({'error': fetcher.error}), 510

    boat_data = copy.deepcopy(sse_boat_fetcher.get_data())
    player_data = boat_data.get('boatState', None)

    data = process_player_data(sse_stronghold_fetcher, 'stronghold')
    if data['predictions']:
        base_code = 201
        response_code = get_response_code(player_data, base_code)
        return jsonify(data), response_code
    elif data.get('eyeThrows'):
        base_code = 206
        response_code = get_response_code(player_data, base_code)
        data['misread'] = True
        return jsonify(data), response_code

    data = process_player_data(sse_blind_fetcher, 'blind')
    if data['isBlindModeEnabled']:
        base_code = 211
        response_code = get_response_code(player_data, base_code)
        return jsonify(data), response_code

    response_code = get_response_code(player_data, 501)
    if response_code:
        data['angle'] = True if server_options['show_angle'] else None
        return jsonify(data), response_code

    return jsonify(data), 500
