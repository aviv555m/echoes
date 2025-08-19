
from eye_tracker import start_eye_tracker
from speech_monitor import start_speech_monitor
import time

if __name__ == "__main__":
    start_eye_tracker()
    start_speech_monitor()
    
    print("Eye tracker and speech monitor running in background...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
