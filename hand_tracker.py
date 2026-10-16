import os
import time

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "hand_landmarker.task")


class HandTracker:
    def __init__(self, model_path=MODEL_PATH, num_hands=2):
        options = vision.HandLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=model_path),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=num_hands,
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)
        self._start = time.monotonic()

    def detect(self, frame_bgr):
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        timestamp_ms = int((time.monotonic() - self._start) * 1000)
        result = self.landmarker.detect_for_video(image, timestamp_ms)
        return split_players(result.hand_landmarks)

    def close(self):
        self.landmarker.close()


def split_players(hand_landmarks):
    players = {"P1": None, "P2": None}
    for landmarks in hand_landmarks:
        points = [(lm.x, lm.y, lm.z) for lm in landmarks]
        side = "P1" if points[0][0] < 0.5 else "P2"
        if players[side] is None:
            players[side] = points
    return players


def draw_players(frame, hands):
    h, w = frame.shape[:2]
    cv2.line(frame, (w // 2, 0), (w // 2, h), (255, 255, 255), 2)
    cv2.putText(frame, "P1", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
    cv2.putText(frame, "P2", (w - 80, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
    for points in hands.values():
        if points is not None:
            for x, y, _ in points:
                cv2.circle(frame, (int(x * w), int(y * h)), 4, (0, 255, 0), -1)


def open_camera(index=0):
    return cv2.VideoCapture(index)
