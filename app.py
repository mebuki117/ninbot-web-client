from flask import Flask, Response, render_template, jsonify
import requests, threading, json
from sseclient import SSEClient

app = Flask(__name__)

sse_url = 'http://localhost:52533/api/v1/stronghold/events' 
data = {}
def sse_worker():
    global data
    client = SSEClient(sse_url)
    for msg in client:
        data = json.loads(msg.data)

threading.Thread(target=sse_worker, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/events')
def proxy_events():
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=31621)
