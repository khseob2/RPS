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
    - 한쪽이라도 None이거나 정해진 값이 아니면 None을 돌려준다.
      이때는 점수를 올리지 않고 같은 라운드를 다시 한다.
    - 결과는 ui.draw_round_result()와 records에 그대로 넘긴다.
    """
    if p1_hand not in BEATS or p2_hand not in BEATS:
        return None
    if p1_hand == p2_hand:
        return "DRAW"
    if BEATS[p1_hand] == p2_hand:
        return "P1"
    return "P2"


def wins_needed(best_of):
    """판수(3·5·7)에서 이기는 데 필요한 승수를 돌려준다."""
    return best_of // 2 + 1


class Match:
    """판수(3·5·7)를 정해서 진행하는 한 게임."""

    def __init__(self, best_of=3):
        if best_of not in (3, 5, 7):
            raise ValueError(f"판수는 3, 5, 7 중 하나여야 합니다: {best_of!r}")
        self.best_of = best_of
        self.p1_score = 0
        self.p2_score = 0
        self.round_no = 1


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
        ("Rock", "scissors", None),
        ("rock", "", None),
    ]
    for p1, p2, expected in cases:
        result = judge(p1, p2)
        mark = "OK" if result == expected else "FAIL"
        print(f"[{mark}] {str(p1):>8} vs {str(p2):<8} -> {result}")

    print()
    for n in (3, 5, 7):
        m = Match(n)
        print(f"{n}판 -> {wins_needed(n)}선승, 점수 {m.p1_score}:{m.p2_score}, Round {m.round_no}")
    try:
        Match(4)
    except ValueError as e:
        print(f"[OK] Match(4) -> {e}")
