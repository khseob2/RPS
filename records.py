import csv
import os

records_path = "data/records.csv"

header = ["game_id", "round", "p1_hand", "p2_hand", "result"]

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
