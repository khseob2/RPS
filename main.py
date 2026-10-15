import time

import cv2

from hand_tracker import HandTracker, draw_players, open_camera

WINDOW_NAME = "HandClash"
COUNTDOWN_SECONDS = 3
RESULT_SHOW_SECONDS = 2


def main():
    tracker = HandTracker()
    cap = open_camera()

    state = "GUIDE"
    state_start = time.monotonic()

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("웹캠 프레임을 읽지 못했습니다.")
                break

            frame = cv2.flip(frame, 1)
            hands = tracker.detect(frame)
            draw_players(frame, hands)

            key = cv2.waitKey(1) & 0xFF
            if key == 27:
                break

            elapsed = time.monotonic() - state_start

            if state == "GUIDE":
                pass

            elif state == "SELECT":
                pass

            elif state == "COUNTDOWN":
                if elapsed >= COUNTDOWN_SECONDS:
                    state, state_start = "JUDGE", time.monotonic()

            elif state == "JUDGE":
                state, state_start = "RESULT", time.monotonic()

            elif state == "RESULT":
                if elapsed >= RESULT_SHOW_SECONDS:
                    state, state_start = "COUNTDOWN", time.monotonic()

            elif state == "REPORT":
                pass

            cv2.imshow(WINDOW_NAME, frame)
    finally:
        cap.release()
        tracker.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
