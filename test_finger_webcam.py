
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from pathlib import Path

# 기존 함수가 저장된 파일 이름에 맞게 수정
from finger_state import detect_finger_states, classify_rps# 모델 파일 경로
MODEL_PATH = Path(__file__).parent / "hand_landmarker.task"

# MediaPipe 손 인식기 설정
options = vision.HandLandmarkerOptions(
    base_options=python.BaseOptions(
        model_asset_path=str(MODEL_PATH)
    ),
    running_mode=vision.RunningMode.IMAGE,
    num_hands=1
)

cap = cv2.VideoCapture(0)

with vision.HandLandmarker.create_from_options(options) as landmarker:
    while cap.isOpened():
        success, frame = cap.read()

        if not success:
            print("웹캠을 읽을 수 없습니다.")
            break

        # MediaPipe 이미지로 변환
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        # 손 랜드마크 추출
        result = landmarker.detect(mp_image)

        if result.hand_landmarks:
            landmarks = result.hand_landmarks[0]

            # 기존 손가락 상태 판별 함수 호출
            states = detect_finger_states(landmarks)
            gesture = classify_rps(states)

            print(f"손가락 상태: {states} | 판정: {gesture}")
            
            # 손가락 끝 위치 표시
            h, w = frame.shape[:2]
            for idx in [8, 12, 16, 20]:
                point = landmarks[idx]
                x = int(point.x * w)
                y = int(point.y * h)
                cv2.circle(frame, (x, y), 6, (0, 255, 0), -1)

        cv2.imshow("Finger State Test", frame)

        # q를 누르면 종료
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()
