import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
import threading
import time
import os
from flask import Flask, request, jsonify, render_template

import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='google.protobuf.symbol_database')


class FocusDetector:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(min_detection_confidence=0.5)

        self.left_eye_indices = [
            33, 7, 7, 163, 163, 144, 144, 145, 145, 153, 153, 154, 154, 155, 155, 133, 33,
            246, 246, 161, 161, 160, 160, 159, 159, 158, 158, 157, 157, 173, 173, 133,

        ]
        self.right_eye_indices = [
            263, 249, 249, 390, 390, 373, 373, 374, 374, 380, 380, 381, 381, 382, 382, 362,
            263, 466, 466, 388, 388, 387, 387, 386, 386, 385, 385, 384, 384, 398, 398, 362,
        ]

    def get_eye_landmarks(self, landmarks, eye_indices):
        return [(landmarks[idx].x, landmarks[idx].y) for idx in eye_indices]

    def calculate_gaze_direction(self, left_eye, right_eye):
        left_center = np.mean(left_eye, axis=0)
        right_center = np.mean(right_eye, axis=0)
        eye_center = np.mean([left_center, right_center], axis=0)

        if eye_center[0] < 0.4:
            return "Right"
        elif eye_center[0] > 0.6:
            return "Left"
        else:
            return "Center"

    def detect_focus(self, image):
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(image_rgb)
        face_results = self.face_detection.process(image_rgb)

        num_faces = len(face_results.detections) if face_results.detections else 0

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                left_eye = self.get_eye_landmarks(face_landmarks.landmark, self.left_eye_indices)
                right_eye = self.get_eye_landmarks(face_landmarks.landmark, self.right_eye_indices)

                gaze_direction = self.calculate_gaze_direction(left_eye, right_eye)
                return gaze_direction, num_faces

        return None, num_faces


app = Flask(__name__)
focus_detector = FocusDetector()

df_columns = ['Time', 'Gaze Direction', 'Number of Faces', 'Total Violation']
df_data = pd.DataFrame(columns=df_columns)
total_violation = 0
df_lock = threading.Lock()

camera_enabled = True


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/process_frame', methods=['POST'])
def process_frame():
    global camera_enabled

    if not camera_enabled:
        return jsonify({"error": "Camera is disabled. Submit the exam to enable camera again."}), 400

    try:
        file = request.files['file']
    except KeyError as e:
        return jsonify({"error": "No file part in request"}), 400

    img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)

    # Pengecekan status kamera sebelum memproses gambar
    if camera_enabled:
        gaze_direction, num_faces = focus_detector.detect_focus(img)

    current_time = time.strftime('%Y-%m-%d %H:%M:%S')
    global total_violation

    # Hitung violation
    violation = 0
    if gaze_direction != "Center" or num_faces > 1:
        violation = 1

    total_violation += violation

    with df_lock:
        new_row = {
            'Time': current_time,
            'Gaze Direction': gaze_direction,
            'Number of Faces': num_faces,
            'Total Violation': total_violation
        }
        df_data.loc[len(df_data)] = new_row

    return jsonify({
        'gaze_direction': gaze_direction,
        'num_faces': num_faces
    })


@app.route('/submit_exam', methods=['POST'])
def submit_exam():
    global camera_enabled

    data = request.json
    if 'answers' not in data:
        return jsonify({"error": "No 'answers' key in JSON data"}), 400

    df = pd.DataFrame(data['answers'])
    exam_answers_file = 'exam_answers.xlsx'
    try:
        df.to_excel(exam_answers_file, index=False)
    except PermissionError as e:
        return jsonify({"error": f"Failed to save exam answers: {e}"}), 500

    # Simpan gaze tracking data hanya saat submit exam
    gaze_tracking_file = 'gaze_tracking_data.xlsx'
    with df_lock:
        try:
            if os.path.exists(gaze_tracking_file):
                df_existing = pd.read_excel(gaze_tracking_file)
                df_data_combined = pd.concat([df_existing, df_data], ignore_index=True)
                df_data_combined.to_excel(gaze_tracking_file, index=False)
            else:
                df_data.to_excel(gaze_tracking_file, index=False)
        except PermissionError as e:
            return jsonify({"error": f"Failed to save gaze tracking data: {e}"}), 500

    # Matikan kamera setelah submit exam
    camera_enabled = False

    return jsonify({"message": "Exam submitted successfully! Camera disabled."}), 200


if __name__ == '__main__':
    app.run(debug=True)
