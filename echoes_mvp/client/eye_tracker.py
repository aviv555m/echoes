
import cv2
import mediapipe as mp
import threading
import socketio

sio = socketio.Client()
sio.connect('http://localhost:5001')

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5)
cap = cv2.VideoCapture(0)

def track_eyes():
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(frame_rgb)

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                left_eye = [face_landmarks.landmark[i] for i in range(33, 42)]
                right_eye = [face_landmarks.landmark[i] for i in range(133, 142)]

                left_eye_pos = [(lmk.x, lmk.y) for lmk in left_eye]
                right_eye_pos = [(lmk.x, lmk.y) for lmk in right_eye]

                sio.emit('eye_data', {'left_eye': left_eye_pos, 'right_eye': right_eye_pos})

                for (x, y) in left_eye + right_eye:
                    h, w, _ = frame.shape
                    cv2.circle(frame, (int(x * w), int(y * h)), 2, (0, 255, 0), -1)

        cv2.imshow("Eye Tracker", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def start_eye_tracker():
    thread = threading.Thread(target=track_eyes)
    thread.daemon = True
    thread.start()
