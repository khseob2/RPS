"""가위바위보 승패 판정과 판수(3·5·7) 진행을 담당하는 모듈.

손모양 값: "rock" / "paper" / "scissors" / None
라운드 결과 값: "P1" / "P2" / "DRAW" / None
"""

BEATS = {
    "rock": "scissors",
    "scissors": "paper",
    "paper": "rock",
}


def judge(p1_hand, p2_hand):
    """두 손모양을 비교해서 라운드 승패를 돌려준다.

    반환: "P1" | "P2" | "DRAW" | None
    - 한쪽이라도 None(손 없음/판별 불가)이면 None을 돌려준다.
      이때는 점수를 올리지 않고 같은 라운드를 다시 한다.
    - 결과는 ui.draw_round_result()와 records에 그대로 넘긴다.
    """
    if p1_hand is None or p2_hand is None:
        return None
    if p1_hand == p2_hand:
        return "DRAW"
    if BEATS[p1_hand] == p2_hand:
        return "P1"
    return "P2"


if __name__ == "__main__":
    cases = [
        ("rock", "rock", "DRAW"),
        ("rock", "scissors", "P1"),
        ("rock", "paper", "P2"),
        ("scissors", "rock", "P2"),
        ("scissors", "scissors", "DRAW"),
        ("scissors", "paper", "P1"),
        ("paper", "rock", "P1"),
        ("paper", "scissors", "P2"),
        ("paper", "paper", "DRAW"),
        (None, "rock", None),
        ("paper", None, None),
        (None, None, None),
    ]
    for p1, p2, expected in cases:
        result = judge(p1, p2)
        mark = "OK" if result == expected else "FAIL"
        print(f"[{mark}] {str(p1):>8} vs {str(p2):<8} -> {result}")
