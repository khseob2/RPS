"""가위바위보 승패 판정과 판수(3·5·7) 진행을 담당하는 모듈.

손모양 값: "rock" / "paper" / "scissors" / None
라운드 결과 값: "P1" / "P2" / "DRAW" / None
"""

# 왼쪽 손모양이 오른쪽 손모양을 이긴다
BEATS = {
    "rock": "scissors",
    "scissors": "paper",
    "paper": "rock",
}


def judge(p1_hand, p2_hand):
    """두 손모양을 비교해서 라운드 승패를 돌려준다.

    반환: "P1" | "P2" | "DRAW" | None
    """
    if p1_hand == p2_hand:
        return "DRAW"
    if BEATS[p1_hand] == p2_hand:
        return "P1"
    return "P2"


if __name__ == "__main__":
    # 9가지 조합 테스트
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
    ]
    for p1, p2, expected in cases:
        result = judge(p1, p2)
        mark = "OK" if result == expected else "FAIL"
        print(f"[{mark}] {p1:>8} vs {p2:<8} -> {result}")
