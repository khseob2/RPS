import csv
import os

records_path = "data/records.csv"

header = ["game_id", "round", "p1_hand", "p2_hand", "result"]

WIN_RULES = { "rock" : "scissors", 
             "scissors" : "paper", 
             "paper" : "rock"}

HANDS = ["rock", "paper", "scissors"]

def start_records(): 
    """게임 시작 시 csv 파일을 초기화하고, 헤더를 작성하는 함수"""
    os.makedirs(os.path.dirname(records_path), exist_ok=True)

    with open(records_path, "w", newline="", encoding="utf-8")as file:
        writer=csv.writer(file)
        writer.writerow(header)

def append_records(game_id, round, p1_hand, p2_hand, result):
    """결과를 csv파일에 추가하고 바로 저장하는 함수"""
    with open(records_path, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([game_id, round, p1_hand, p2_hand, result])
        file.flush()
        os.fsync(file.fileno())

def calculate_hand_stats():
    """CSV 기록을 읽어 플레이어 별 손모양 통계를 반환하는 함수"""

    stats = { "P1" : {},
              "P2" : {} }

    for player in stats:
        for hand in HANDS:
            stats[player][hand] = {
                "count" : 0,
                "wins" : 0,
                "win_rate" : "횟수 없음"
            }

    with open(records_path, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            p1_hand = row["p1_hand"].strip().lower()
            p2_hand = row["p2_hand"].strip().lower()
            result = row["result"].strip().upper()

            if p1_hand in HANDS:
                stats["P1"][p1_hand]["count"] += 1

            if p2_hand in HANDS:
                stats["P2"][p2_hand]["count"] += 1

            if result == "P1" and p1_hand in HANDS:
                stats["P1"][p1_hand]["wins"] += 1

            elif result == "P2" and p2_hand in HANDS:
                stats["P2"][p2_hand]["wins"] += 1

    for player in stats:
        for hand in HANDS:
            count = stats[player][hand]["count"]
            wins = stats[player][hand]["wins"]

            if count > 0:
                stats[player][hand]["win_rate"] = round(
                    wins / count * 100, 2
                )

    return stats

def generate_report():
    """게임 기록을 바탕으로 플레이어별 통계 문장을 생성하는 함수"""

    stats = calculate_hand_stats()

    total_games = {"P1": 0, "P2": 0}
    total_wins = {"P1": 0, "P2": 0}

    with open(records_path, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            result = row["result"].strip().upper()

            total_games["P1"] += 1
            total_games["P2"] += 1

            if result == "P1":
                total_wins["P1"] += 1
            elif result == "P2":
                total_wins["P2"] += 1

    report = {}

    for player in ("P1", "P2"):
        lines = [
            f"[{player}] Total {total_games[player]} games / "
            f"{total_wins[player]} wins"
        ]

        for hand in HANDS:
            hand_stats = stats[player][hand]
            count = hand_stats["count"]
            wins = hand_stats["wins"]
            win_rate = hand_stats["win_rate"]

            hand_name = hand.capitalize()

            if count == 0:
                line = f"{hand_name}: No plays"
            else:
                line = (
                    f"{hand_name}: {count} played / "
                    f"{wins} wins / Win rate: {win_rate}%"
                )

            lines.append(line)

        report[player] = lines

    return report
