
# MediaPipe 손가락 펼침/접힘 상태 판별

# 손가락 상태를 이용한 가위바위보 판정
def classify_rps(states):
    index = states["index"]
    middle = states["middle"]
    ring = states["ring"]
    pinky = states["pinky"]

    if not index and not middle and not ring and not pinky:
        return "Rock"

    elif index and middle and not ring and not pinky:
        return "Scissors"

    elif index and middle and ring and pinky:
        return "Paper"

    else:
        return "Unknown"

def detect_finger_states(landmarks):
    # 손가락 끝과 중간 관절 번호
    fingers = {
        "index": (8, 6),
        "middle": (12, 10),
        "ring": (16, 14),
        "pinky": (20, 18)
    }


    states = {}

    # 손목(0번)과의 거리를 기준으로 판별
    wrist = landmarks[0]

    for name, (tip_id, pip_id) in fingers.items():
        tip = landmarks[tip_id]
        pip = landmarks[pip_id]

        tip_dist = (
            (tip.x - wrist.x) ** 2
            + (tip.y - wrist.y) ** 2
        )

        pip_dist = (
            (pip.x - wrist.x) ** 2
            + (pip.y - wrist.y) ** 2
        )

        states[name] = tip_dist > pip_dist

    return states


# 간단한 동작 테스트
if __name__ == "__main__":
    from types import SimpleNamespace

    # 테스트용 가상 랜드마크
    points = [
        SimpleNamespace(x=0.5, y=0.5)
        for _ in range(21)
    ]

    # 검지만 펼친 상태를 가정
    points[8].y = 0.1
    points[6].y = 0.3

    result = detect_finger_states(points)

    for finger, extended in result.items():
        print(f"{finger}: {'펴짐' if extended else '접힘'}")
