
import speech_recognition as sr
import threading
import socketio

sio = socketio.Client()
sio.connect('http://localhost:5001')

BAD_WORDS = ['badword1', 'badword2']

def monitor_speech():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)

    while True:
        try:
            with mic as source:
                audio = recognizer.listen(source)
                text = recognizer.recognize_google(audio).lower()
                for word in BAD_WORDS:
                    if word in text:
                        sio.emit('speech_event', {'word': word})
                        print(f"Detected bad word: {word}")
        except Exception:
            pass

def start_speech_monitor():
    thread = threading.Thread(target=monitor_speech)
    thread.daemon = True
    thread.start()
