
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import argparse

app = Flask(__name__)
CORS(app)

def execute_mental_health(query):
    return f"Mental health advice for: {query}"

@app.route('/api/execute', methods=['POST'])
def execute():
    data = request.get_json()
    query = data.get('query', '')
    try:
        result = execute_mental_health(query)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run the mental_health agent as a Flask app.")
    parser.add_argument("--port", type=int, default=5031, help="Port to run the Flask app on.")
    args = parser.parse_args()
    app.run(port=args.port)
