import os
import csv
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# 데이터셋 폴더 구조 (Kaggle에서 받은 구조 기준)
# rps_dataset/
#   ├── rock/        *.png
#   ├── paper/       *.png
#   └── scissors/    *.png
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "..", "Rock-Paper-Scissors", "rps_dataset")
LABELS = ["rock", "paper", "scissors"]

# Hand Landmarker 준비
# 경로에 한글(바탕 화면)이 있으면 mediapipe가 파일을 못 열어서, 파이썬으로 읽어서 넘겨줌
with open(os.path.join(BASE_DIR, 'hand_landmarker.task'), 'rb') as f:
    model_data = f.read()
base_options = python.BaseOptions(model_asset_buffer=model_data)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1  # 한 이미지에 손 하나만 있다고 가정
)
landmarker = vision.HandLandmarker.create_from_options(options)

# CSV 헤더 만들기: label, x0,y0,z0, x1,y1,z1, ... x20,y20,z20 (21개 관절 x 3)
header = ["label"]
for i in range(21):
    header += [f"x{i}", f"y{i}", f"z{i}"]

rows = []

for label in LABELS:
    folder = os.path.join(DATASET_DIR, label)
    for filename in os.listdir(folder):
        if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        image_path = os.path.join(folder, filename)
        rgb = np.array(Image.open(image_path).convert("RGB"))
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        result = landmarker.detect(image)

        if not result.hand_landmarks:
            print(f"손 인식 실패: {image_path}")
            continue

        landmarks = result.hand_landmarks[0]  # 첫 번째 손
        row = [label]
        for lm in landmarks:
            row += [lm.x, lm.y, lm.z]

        rows.append(row)

# CSV로 저장
with open(os.path.join(BASE_DIR, "gesture_landmarks.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(rows)

print(f"총 {len(rows)}개 샘플 저장 완료")