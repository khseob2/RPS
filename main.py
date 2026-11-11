import time

import cv2

import ui
import records
from finger_state import classify_hand
from game import Match, judge
from hand_tracker import HandTracker, draw_hand, open_camera

RESULT_SHOW_SECONDS = 2    # 라운드 결과를 보여 주는 시간(초)


def main():
    records.start_records()
    tracker = HandTracker()
    cap = open_camera()
    ui.enable_mouse()

    state = "GUIDE"            # GUIDE → SELECT → PLAY → OVER  (ui.py 흐름 그대로)
    match = Match(3)
    game_id = 0                # 몇 번째 게임인지 구분하기 위한 변수
    countdown_start = None
    result_info = None         # (p1_hand, p2_hand, result, 보여 주기 시작한 시각, 판정한 라운드 번호)

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("웹캠 프레임을 읽지 못했습니다.")
                break

            frame = cv2.flip(frame, 1)  # 거울처럼 좌우 반전
            hands = tracker.detect(frame)

            # 분할선·라벨은 ui, 손 관절은 hand_tracker가 그린다
            frame = ui.draw_split_screen(frame)
            if hands["P1"] is not None:
                draw_hand(frame, hands["P1"], ui.P1_COLOR)
            if hands["P2"] is not None:
                draw_hand(frame, hands["P2"], ui.P2_COLOR)

            click = ui.get_click()

            if state == "GUIDE":
                frame = ui.draw_guide(frame)
                if ui.is_start_clicked(frame, click):
                    state = "SELECT"

            elif state == "SELECT":
                frame = ui.draw_best_of_select(frame)
                chosen = ui.get_clicked_best_of(frame, click)
                if chosen is not None:
                    game_id += 1
                    match = Match(chosen)
                    state = "PLAY"

            elif state == "PLAY":
                # 결과를 보여 주는 동안에는 방금 판정한 라운드 번호를 그대로 보여 준다
                shown_round = result_info[4] if result_info is not None else match.round_no
                frame = ui.draw_scoreboard(frame, match.p1_score, match.p2_score,
                                           shown_round, match.best_of)
                frame = ui.draw_quit_button(frame)
                if ui.is_quit_clicked(frame, click):  # 중간 종료 → 누적 점수로 승자 결정
                    match.finish()
                    state, countdown_start, result_info = "OVER", None, None

                if countdown_start is not None:
                    text = ui.get_countdown_text(countdown_start)
                    frame = ui.draw_countdown(frame, text)
                    if text is None:
                        # 카운트다운이 끝난 순간의 손모양으로 판정
                        countdown_start = None
                        p1_hand = classify_hand(hands["P1"])
                        p2_hand = classify_hand(hands["P2"])
                        result = judge(p1_hand, p2_hand)
                        judged_round = match.round_no   # add_round()가 번호를 올리기 전에 저장

                        if result is not None:
                            records.append_records(
                                game_id,
                                match.round_no,
                                p1_hand,
                                p2_hand,
                                result
                            )
                        
                        match.add_round(result)   # None이면 점수·라운드 그대로(재시도)
                        result_info = (p1_hand, p2_hand, result, time.time(), judged_round)

                if state == "PLAY" and result_info is not None:
                    frame = ui.draw_round_result(frame, *result_info[:3])
                    if time.time() - result_info[3] >= RESULT_SHOW_SECONDS:
                        result_info = None
                        if match.is_over:
                            state = "OVER"

            elif state == "OVER":
                frame = ui.draw_game_over(frame, match.winner, match.p1_score, match.p2_score)

            key = ui.show_frame(frame)
            if (key == ord(" ") and state == "PLAY"
                    and countdown_start is None and result_info is None):
                countdown_start = ui.start_countdown()
            elif key == ord("r"):
                state, countdown_start, result_info = "SELECT", None, None
            if ui.should_quit(key):
                break

        report = records.generate_report()

        for player in ["P1", "P2"]:
            for line in report[player]:
                print(line)
    finally:
        cap.release()
        tracker.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()