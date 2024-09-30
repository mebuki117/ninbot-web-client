from flask import Flask, Response, render_template, jsonify
import requests, threading, json
from sseclient import SSEClient

import threading
import json
from sseclient import SSEClient

class EventDataFetcher:
    def __init__(self, sse_url):
        self.sse_url = sse_url
        self.data = {}
        self.error = None
        self.thread = threading.Thread(target=self._sse_worker, daemon=True)
    
    def start(self):
        self.thread.start()
    
    def _sse_worker(self):
        try:
                
            client = SSEClient(self.sse_url)
            print('aja')
            for msg in client:
                if msg.event == 'message':
                    self.data = json.loads(msg.data)
            
            self.error = None
        except Exception as e:
            self.error = e.__str__()
            
    def get_data(self):
        return self.data

SSE_URL = 'http://localhost:52533/api/v1/stronghold/events' 

app = Flask(__name__)
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=31621)
