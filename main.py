import time

import cv2

import ui
from finger_state import classify_hand
from game import Match, judge
from hand_tracker import HandTracker, draw_players, open_camera

BEST_OF = 3                # MVP: 3판 2선승 고정 (판수 선택은 다음 단계)
RESULT_SHOW_SECONDS = 2    # 라운드 결과를 보여 주는 시간(초)


def main():
    tracker = HandTracker()
    cap = open_camera()

    match = Match(BEST_OF)
    state = "GUIDE"            # GUIDE → COUNTDOWN → RESULT → (COUNTDOWN 반복) → OVER
    countdown_start = None
    result_start = None
    last = (None, None, None)  # (p1_hand, p2_hand, result)

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("웹캠 프레임을 읽지 못했습니다.")
                break

            frame = cv2.flip(frame, 1)
            hands = tracker.detect(frame)
            draw_players(frame, hands)

            if state == "GUIDE":
                ui.draw_message(frame, "Press SPACE to start", ui.YELLOW)

            elif state == "COUNTDOWN":
                text = ui.get_countdown_text(countdown_start)
                ui.draw_countdown(frame, text)
                if text is None:
                    # 카운트다운이 끝난 순간의 손모양으로 판정
                    p1_hand = classify_hand(hands["P1"])
                    p2_hand = classify_hand(hands["P2"])
                    result = judge(p1_hand, p2_hand)
                    match.add_round(result)   # None이면 점수·라운드 그대로(재시도)
                    last = (p1_hand, p2_hand, result)
                    state, result_start = "RESULT", time.time()

            elif state == "RESULT":
                ui.draw_round_result(frame, *last)
                if time.time() - result_start >= RESULT_SHOW_SECONDS:
                    if match.is_over:
                        state = "OVER"
                    else:
                        state, countdown_start = "COUNTDOWN", ui.start_countdown()

            elif state == "OVER":
                ui.draw_game_over(frame, match.winner, match.p1_score, match.p2_score)
                h = frame.shape[0]
                cv2.putText(frame, "r: restart / q: quit", (20, h - 30),
                            ui.FONT, 0.8, ui.WHITE, 2)

            if state != "OVER":
                ui.draw_scoreboard(frame, match.p1_score, match.p2_score,
                                   match.round_no, match.best_of)

            key = ui.show_frame(frame)
            if ui.should_quit(key):
                break
            if key == ord(" ") and state == "GUIDE":
                state, countdown_start = "COUNTDOWN", ui.start_countdown()
            elif key == ord("r") and state == "OVER":
                match = Match(BEST_OF)
                state = "GUIDE"
    finally:
        cap.release()
        tracker.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
