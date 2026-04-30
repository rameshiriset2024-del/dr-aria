import os
import json
import urllib.request
import urllib.error
from flask import Flask, request, jsonify, send_from_directory, Response

app = Flask(__name__, static_folder='static')

# API key from Render environment variable
ANTHROPIC_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

# ── Health check ──
@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'hasKey': bool(ANTHROPIC_KEY),
        'message': 'Dr. Aria server is running'
    })

# ── Serve main app ──
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# ── Proxy to Anthropic ──
@app.route('/api', methods=['POST', 'OPTIONS'])
def api_proxy():
    if request.method == 'OPTIONS':
        return Response('', status=204, headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        })

    if not ANTHROPIC_KEY:
        return jsonify({
            'error': {
                'message': 'ANTHROPIC_API_KEY not set in Render environment variables.',
                'type': 'configuration_error'
            }
        }), 500

    try:
        body = request.get_data()
        req = urllib.request.Request(
            'https://api.anthropic.com/v1/messages',
            data=body,
            headers={
                'Content-Type': 'application/json',
                'x-api-key': ANTHROPIC_KEY,
                'anthropic-version': '2023-06-01',
            },
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = resp.read()
            return Response(result, status=200, headers={
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            })

    except urllib.error.HTTPError as e:
        error_body = e.read()
        return Response(error_body, status=e.code, headers={
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        })
    except Exception as e:
        return jsonify({
            'error': {'message': str(e), 'type': 'server_error'}
        }), 502

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7777))
    app.run(host='0.0.0.0', port=port, debug=False)
