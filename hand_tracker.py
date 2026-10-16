import os
import time
import urllib.request

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "hand_landmarker.task")
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
)

WRIST = 0
THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP = 1, 2, 3, 4
INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP = 5, 6, 7, 8
MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP = 9, 10, 11, 12
RING_MCP, RING_PIP, RING_DIP, RING_TIP = 13, 14, 15, 16
PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP = 17, 18, 19, 20

HAND_CONNECTIONS = [(c.start, c.end) for c in vision.HandLandmarksConnections.HAND_CONNECTIONS]

PLAYER_COLORS = {"P1": (255, 128, 0), "P2": (0, 0, 255)}


def ensure_model(path=MODEL_PATH):
    if os.path.exists(path):
        return path
    print("hand_landmarker.task 모델을 내려받는 중...")
    tmp_path = path + ".part"
    urllib.request.urlretrieve(MODEL_URL, tmp_path)
    os.replace(tmp_path, path)
    print("모델 다운로드 완료")
    return path


class HandTracker:
    def __init__(self, model_path=MODEL_PATH, num_hands=2, min_confidence=0.5):
        ensure_model(model_path)
        with open(model_path, "rb") as f:
            model_data = f.read()

        options = vision.HandLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_buffer=model_data),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=num_hands,
            min_hand_detection_confidence=min_confidence,
            min_hand_presence_confidence=min_confidence,
            min_tracking_confidence=min_confidence,
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)
        self._start = time.monotonic()
        self._last_ts = -1

    def _timestamp_ms(self):
        ts = int((time.monotonic() - self._start) * 1000)
        if ts <= self._last_ts:
            ts = self._last_ts + 1
        self._last_ts = ts
        return ts

    def detect(self, frame_bgr):
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self.landmarker.detect_for_video(image, self._timestamp_ms())
        return split_players(result.hand_landmarks)

    def close(self):
        self.landmarker.close()


def split_players(hand_landmarks):
    players = {"P1": None, "P2": None}
    for landmarks in hand_landmarks:
        points = [(lm.x, lm.y, lm.z) for lm in landmarks]
        wrist_x = points[WRIST][0]
        side = "P1" if wrist_x < 0.5 else "P2"

        current = players[side]
        if current is None or abs(wrist_x - 0.5) > abs(current[WRIST][0] - 0.5):
            players[side] = points
    return players


def to_pixel(point, width, height):
    return int(point[0] * width), int(point[1] * height)


def draw_hand(frame, points, color):
    h, w = frame.shape[:2]
    for a, b in HAND_CONNECTIONS:
        cv2.line(frame, to_pixel(points[a], w, h), to_pixel(points[b], w, h), color, 2)
    for p in points:
        cv2.circle(frame, to_pixel(p, w, h), 4, color, -1)


def draw_players(frame, hands):
    h, w = frame.shape[:2]
    cv2.line(frame, (w // 2, 0), (w // 2, h), (255, 255, 255), 2)
    cv2.putText(frame, "P1", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, PLAYER_COLORS["P1"], 3)
    cv2.putText(frame, "P2", (w - 80, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, PLAYER_COLORS["P2"], 3)
    for name, points in hands.items():
        if points is not None:
            draw_hand(frame, points, PLAYER_COLORS[name])


def open_camera(index=0, width=1280, height=720):
    if os.name == "nt":
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        raise RuntimeError(f"웹캠({index})을 열 수 없습니다. 연결 상태를 확인해 주세요.")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    return cap


if __name__ == "__main__":
    tracker = HandTracker()
    cap = open_camera()
    last_print = 0.0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("웹캠 프레임을 읽지 못했습니다.")
                break

            frame = cv2.flip(frame, 1)
            hands = tracker.detect(frame)

            if time.monotonic() - last_print >= 0.5:
                last_print = time.monotonic()
                for name in ("P1", "P2"):
                    points = hands[name]
                    if points is None:
                        print(f"{name}: None")
                    else:
                        x, y, _ = points[WRIST]
                        print(f"{name}: 관절 {len(points)}개, 손목 ({x:.2f}, {y:.2f})")
                print("-" * 30)

            draw_players(frame, hands)
            cv2.imshow("hand_tracker test", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break
    finally:
        cap.release()
        tracker.close()
        cv2.destroyAllWindows()
