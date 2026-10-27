import time

import cv2
 
WINDOW_NAME = "HandClash"
QUIT_KEYS = (ord("q"), 27)  # q, ESC
COUNTDOWN_SECONDS = 3       # 3, 2, 1 을 세는 시간(초)
SHOW_SECONDS = 1            # "SHOW!"를 보여 주는 시간(초)
 
# 색은 OpenCV 기준 BGR 순서
WHITE = (255, 255, 255)
YELLOW = (0, 220, 255)
P1_COLOR = (255, 160, 60)   # 파랑 계열
P2_COLOR = (80, 80, 255)    # 빨강 계열
FONT = cv2.FONT_HERSHEY_SIMPLEX
 
 
def open_camera(index=0):
    """웹캠을 열어 VideoCapture 객체를 돌려준다. 못 열면 RuntimeError."""
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        raise RuntimeError("Cannot open webcam")
    return cap
 
 
def show_frame(frame):
    """프레임을 창에 그리고, 눌린 키 값을 돌려준다(안 눌렸으면 255)."""
    cv2.imshow(WINDOW_NAME, frame)
    return cv2.waitKey(1) & 0xFF
 
 
def should_quit(key):
    """종료 키(q, ESC)가 눌렸는지 확인한다."""
    return key in QUIT_KEYS
 
 
def get_center_x(frame):
    """화면 가운데 x좌표. 손목 x가 이 값보다 작으면 P1, 크면 P2로 나눈다."""
    return frame.shape[1] // 2
 
 
def draw_split_screen(frame):
    """가운데 세로선과 P1/P2 라벨을 그린다. 같은 frame에 그려서 돌려준다."""
    h, w = frame.shape[:2]
    center_x = get_center_x(frame)
 
    cv2.line(frame, (center_x, 0), (center_x, h), WHITE, 2)
    cv2.putText(frame, "P1", (20, 40), FONT, 1.2, P1_COLOR, 3)
    cv2.putText(frame, "P2", (center_x + 20, 40), FONT, 1.2, P2_COLOR, 3)
    return frame


def start_countdown():
    """카운트다운을 시작한 시각을 돌려준다. 나중에 get_countdown_text에 넘긴다."""
    return time.time()


def get_countdown_text(start_time, now=None):
    """시작 시각 기준으로 지금 보여 줄 글자를 돌려준다.

    3초 동안 "3" → "2" → "1", 그다음 1초 동안 "SHOW!", 끝나면 None.
    (영상이 멈추지 않도록 sleep 대신 경과 시간으로 계산한다.)
    """
    if now is None:
        now = time.time()
    elapsed = now - start_time

    if elapsed < COUNTDOWN_SECONDS:
        return str(COUNTDOWN_SECONDS - int(elapsed))
    if elapsed < COUNTDOWN_SECONDS + SHOW_SECONDS:
        return "SHOW!"
    return None


def draw_countdown(frame, text):
    """카운트다운 글자를 화면 정중앙에 크게 그린다. text가 None이면 아무것도 안 그린다."""
    if text is None:
        return frame

    h, w = frame.shape[:2]
    scale = 5.0 if text.isdigit() else 3.0
    color = WHITE if text.isdigit() else YELLOW
    thickness = 10

    (text_w, text_h), _ = cv2.getTextSize(text, FONT, scale, thickness)
    x = (w - text_w) // 2
    y = (h + text_h) // 2
    cv2.putText(frame, text, (x, y), FONT, scale, color, thickness)
    return frame
 
 
if __name__ == "__main__":
    # 혼자 실행해서 화면이 뜨는지 확인하는 테스트용 코드
    cap = open_camera()
    countdown_start = None
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)  # 거울처럼 좌우 반전
        frame = draw_split_screen(frame)

        if countdown_start is not None:
            text = get_countdown_text(countdown_start)
            frame = draw_countdown(frame, text)
            if text is None:
                countdown_start = None

        key = show_frame(frame)
        if key == ord(" "):
            countdown_start = start_countdown()
        if should_quit(key):
            break
    cap.release()
    cv2.destroyAllWindows()