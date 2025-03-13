from flask import Flask, request, jsonify, Response
import json
import threading
import time

app = Flask(__name__)

models = ["model1", "model2", "model3"]

@app.route('/v1/models', methods=['GET'])
def list_models():
    return jsonify(models)

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    data = request.get_json()
    model = data.get('model')
    messages = data.get('messages')
    stream = data.get('stream', False)

    if stream:
        return Response(stream_response(model, messages), content_type='text/event-stream')
    else:
        return jsonify(non_stream_response(model, messages))

def stream_response(model, messages):
    for i in range(5):
        yield f"data: {json.dumps({'model': model, 'messages': messages, 'chunk': i})}\n\n"
        time.sleep(1)

def non_stream_response(model, messages):
    return {'model': model, 'messages': messages, 'response': 'This is a non-streaming response'}

if __name__ == '__main__':
    app.run(port=5000)
