
from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('eye_data')
def handle_eye_data(data):
    print("Received eye data:", data)

@socketio.on('speech_event')
def handle_speech_event(data):
    print("Received speech event:", data)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001)
