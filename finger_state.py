
# MediaPipe 손가락 펼침/접힘 상태 판별

# 손가락 상태를 이용한 가위바위보 판정
def classify_rps(states):
    index = states["index"]
    middle = states["middle"]
    ring = states["ring"]
    pinky = states["pinky"]

    if not index and not middle and not ring and not pinky:
        return "rock"

    elif index and middle and not ring and not pinky:
        return "scissors"

    elif index and middle and ring and pinky:
        return "paper"

    else:
        return None

def classify_hand(landmarks):
    if landmarks is None or len(landmarks) < 21:
        return None
    states = detect_finger_states(landmarks)
    return classify_rps(states)

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
            (tip[0] - wrist[0]) ** 2
            + (tip[1] - wrist[1]) ** 2
        )

        pip_dist = (
            (pip[0] - wrist[0]) ** 2
            + (pip[1] - wrist[1]) ** 2
        )

        states[name] = tip_dist > pip_dist

    return states
