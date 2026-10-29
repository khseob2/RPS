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
    with open(records_path, "a", newline="", encoding="uft-8") as file:
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
            result = row["result"].strip.upper()

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
