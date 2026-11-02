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
        self.stopped = False

    def add_round(self, result):
        """judge() 결과를 받아 점수와 라운드를 갱신한다.

        None이면 아무것도 바꾸지 않는다(같은 라운드를 다시 한다).
        DRAW면 점수는 그대로 두고 다음 라운드로 넘어간다.
        게임이 이미 끝났으면 무시한다.
        """
        if result is None or self.is_over:
            return
        if result == "P1":
            self.p1_score += 1
        elif result == "P2":
            self.p2_score += 1
        self.round_no += 1

    @property
    def winner(self):
        """승자("P1"/"P2"/"DRAW"). 아직 안 끝났으면 None.

        선승하면 그 플레이어, 중간에 finish()로 끝내면 누적 점수로 정한다.
        """
        need = wins_needed(self.best_of)
        if self.p1_score >= need:
            return "P1"
        if self.p2_score >= need:
            return "P2"
        if self.stopped:
            if self.p1_score > self.p2_score:
                return "P1"
            if self.p2_score > self.p1_score:
                return "P2"
            return "DRAW"
        return None

    @property
    def is_over(self):
        """게임이 끝났는지 여부."""
        return self.winner is not None

    def finish(self):
        """게임 종료 버튼을 눌렀을 때 호출한다. 누적 점수로 정한 승자를 돌려준다."""
        self.stopped = True
        return self.winner


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

    print()
    m = Match(3)
    for r in ["P1", None, "DRAW", "P2", "P1"]:
        m.add_round(r)
        print(f"{str(r):>4} -> 점수 {m.p1_score}:{m.p2_score}, Round {m.round_no}, 종료 {m.is_over}")
    print(f"승자: {m.winner}")
    m.add_round("P2")
    print(f"종료 후 P2 입력 -> 점수 {m.p1_score}:{m.p2_score} (변화 없어야 함)")

    print()
    for results in (["P1", "P2", "P1"], ["P2"], ["P1", "P2"], []):
        m = Match(7)
        for r in results:
            m.add_round(r)
        print(f"7판 중간 종료 {m.p1_score}:{m.p2_score} -> {m.finish()}, 종료 {m.is_over}")
