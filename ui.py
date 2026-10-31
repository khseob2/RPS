import time

import cv2
 
WINDOW_NAME = "HandClash"
QUIT_KEYS = (ord("q"), 27)  # q, ESC
COUNTDOWN_SECONDS = 3       # 3, 2, 1 을 세는 시간(초)
SHOW_SECONDS = 1            # "SHOW!"를 보여 주는 시간(초)
SCOREBOARD_HEIGHT = 90      # 점수판 높이(픽셀)
 
# 색은 OpenCV 기준 BGR 순서
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (0, 220, 255)
P1_COLOR = (255, 160, 60)   # 파랑 계열
P2_COLOR = (80, 80, 255)    # 빨강 계열
FONT = cv2.FONT_HERSHEY_SIMPLEX


# 손모양 이름
HAND_NAMES = {
    "rock": "Rock", "paper": "Paper", "scissors": "Scissors",
}
# 판정 결과: "P1"(P1 승), "P2"(P2 승), "DRAW"(무승부)
RESULT_TEXT = {"P1": "P1 WIN", "P2": "P2 WIN", "DRAW": "DRAW"}
RESULT_COLOR = {"P1": P1_COLOR, "P2": P2_COLOR, "DRAW": YELLOW}

BEST_OF_CHOICES = (3, 5, 7)   # 고를 수 있는 판수
BUTTON_COLOR = (50, 50, 50)    # 버튼 바탕색(진한 회색)

_clicks = []  # 마우스로 클릭한 좌표가 쌓이는 곳 (내부용)


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


def _put_centered(frame, text, center_x, y, scale, color, thickness):
    """center_x를 가운데로 해서 글자를 그린다. (내부용)"""
    (text_w, _), _ = cv2.getTextSize(text, FONT, scale, thickness)
    cv2.putText(frame, text, (center_x - text_w // 2, y), FONT, scale, color, thickness)


def draw_scoreboard(frame, p1_score, p2_score, round_no, best_of=3):
    """화면 아래에 점수판을 그린다.

    p1_score, p2_score: 지금까지 이긴 판 수
    round_no: 지금 몇 번째 판인지 (1부터)
    best_of: 판수 (3, 5, 7). 이기려면 best_of // 2 + 1 승이 필요하다.
    """
    h, w = frame.shape[:2]
    top = h - SCOREBOARD_HEIGHT
    wins_needed = best_of // 2 + 1

    # 반투명 검은 띠 (뒤의 영상이 비쳐 보이게)
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, top), (w, h), BLACK, -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    center_x = get_center_x(frame)
    # 윗줄: 라운드와 필요 승수
    info = f"Round {round_no}  (First to {wins_needed})"
    _put_centered(frame, info, center_x, top + 30, 0.8, WHITE, 2)
    # 아랫줄: 점수  P1 1 : 0 P2
    _put_centered(frame, f"{p1_score}", center_x - 60, top + 75, 1.6, P1_COLOR, 4)
    _put_centered(frame, ":", center_x, top + 70, 1.4, WHITE, 3)
    _put_centered(frame, f"{p2_score}", center_x + 60, top + 75, 1.6, P2_COLOR, 4)
    cv2.putText(frame, "P1", (20, top + 70), FONT, 1.0, P1_COLOR, 3)
    cv2.putText(frame, "P2", (w - 70, top + 70), FONT, 1.0, P2_COLOR, 3)
    return frame


def get_hand_name(hand):
    """손모양 값("rock" / "paper" / "scissors")을 화면에 그릴 글자로 바꾼다. 없으면 "-", 모르는 값이면 "?"."""
    if hand is None:
        return "-"
    return HAND_NAMES.get(str(hand).strip().lower(), "?")


def draw_message(frame, text, color=WHITE, scale=1.5):
    """화면 정중앙에 안내 문구를 그린다. (예: "Show both hands!")"""
    h, w = frame.shape[:2]
    _put_centered(frame, text, w // 2, h // 2, scale, color, 3)
    return frame


def draw_round_result(frame, p1_hand, p2_hand, result):
    """한 판의 결과를 화면 가운데에 그린다.

    p1_hand, p2_hand: "rock" / "paper" / "scissors" (소문자), 손이 없으면 None
    result: "P1", "P2", "DRAW"  (None이면 결과 없음 → 안내 문구만 그린다)
    각 플레이어 영역 가운데에 손모양, 화면 정중앙에 승패를 크게 보여 준다.
    """
    if result not in RESULT_TEXT:
        return draw_message(frame, "Show both hands!", YELLOW)

    h, w = frame.shape[:2]
    center_x = get_center_x(frame)
    mid_y = h // 2

    # 글자가 잘 보이도록 반투명 검은 띠
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, mid_y - 120), (w, mid_y + 110), BLACK, -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    _put_centered(frame, get_hand_name(p1_hand), center_x // 2, mid_y - 40, 1.6, P1_COLOR, 4)
    _put_centered(frame, get_hand_name(p2_hand), center_x + center_x // 2, mid_y - 40, 1.6, P2_COLOR, 4)
    _put_centered(frame, RESULT_TEXT[result], center_x, mid_y + 70, 2.8, RESULT_COLOR[result], 8)
    return frame


def _on_mouse(event, x, y, flags, param):
    """마우스 왼쪽 버튼을 누르면 그 좌표를 기록한다. (내부용, OpenCV가 대신 불러 준다)"""
    if event == cv2.EVENT_LBUTTONDOWN:
        _clicks.append((x, y))


def enable_mouse():
    """창을 만들고 마우스 클릭을 받기 시작한다. 반복문 시작 전에 한 번만 부른다."""
    cv2.namedWindow(WINDOW_NAME)
    cv2.setMouseCallback(WINDOW_NAME, _on_mouse)


def get_click():
    """마지막으로 클릭한 좌표 (x, y)를 돌려준다. 클릭이 없었으면 None.

    한 번 읽으면 지워지므로, 한 프레임에 한 번만 불러서 변수에 담아 쓴다.
    """
    if not _clicks:
        return None
    click = _clicks[-1]
    _clicks.clear()
    return click


def make_button(label, x, y, w, h):
    """버튼 하나를 만든다. (x, y)는 왼쪽 위 꼭짓점, w·h는 너비·높이."""
    return {"label": label, "rect": (x, y, x + w, y + h)}


def is_clicked(button, click):
    """클릭 좌표가 버튼 사각형 안에 있으면 True. click이 None이면 False."""
    if click is None:
        return False
    x, y = click
    x1, y1, x2, y2 = button["rect"]
    return x1 <= x <= x2 and y1 <= y <= y2


def draw_button(frame, button, color=WHITE):
    """버튼을 그린다: 회색 바탕 + 색 테두리 + 가운데 글자."""
    x1, y1, x2, y2 = button["rect"]
    cv2.rectangle(frame, (x1, y1), (x2, y2), BUTTON_COLOR, -1)
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)

    scale = (y2 - y1) / 50   # 버튼 높이에 맞춰 글자 크기를 정한다
    thickness = max(2, int(scale * 2))
    (text_w, text_h), _ = cv2.getTextSize(button["label"], FONT, scale, thickness)
    text_x = (x1 + x2 - text_w) // 2
    text_y = (y1 + y2 + text_h) // 2
    cv2.putText(frame, button["label"], (text_x, text_y), FONT, scale, color, thickness)
    return frame


def get_best_of_buttons(frame):
    """판수 선택 버튼 3개(3, 5, 7)를 화면 가운데에 가로로 놓은 버튼 리스트."""
    h, w = frame.shape[:2]
    size = min(w, h) // 5      # 정사각형 버튼 한 변
    gap = size // 3
    left = (w - (size * 3 + gap * 2)) // 2
    top = h // 2 - size // 2
    return [make_button(str(n), left + i * (size + gap), top, size, size)
            for i, n in enumerate(BEST_OF_CHOICES)]


def draw_best_of_select(frame):
    """판수 선택 화면: 위에 안내 문구, 가운데 3 / 5 / 7 버튼, 아래에 설명."""
    h, w = frame.shape[:2]
    buttons = get_best_of_buttons(frame)
    top = buttons[0]["rect"][1]
    bottom = buttons[0]["rect"][3]

    # 글자와 버튼이 잘 보이도록 반투명 검은 띠
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, top - 70), (w, bottom + 70), BLACK, -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    _put_centered(frame, "Click to choose rounds", w // 2, top - 30, 1.0, WHITE, 2)
    for button in buttons:
        draw_button(frame, button, YELLOW)
    _put_centered(frame, "Best of 3 / 5 / 7", w // 2, bottom + 45, 0.8, WHITE, 2)
    return frame


def get_clicked_best_of(frame, click):
    """판수 버튼을 눌렀으면 그 판수(3, 5, 7)를, 아니면 None을 돌려준다."""
    for best_of, button in zip(BEST_OF_CHOICES, get_best_of_buttons(frame)):
        if is_clicked(button, click):
            return best_of
    return None


if __name__ == "__main__":
    # 혼자 실행해서 화면이 뜨는지 확인하는 테스트용 코드 (나중에는 game.py/main.py가 이 역할을 한다)
    #   판수 버튼 클릭 → SPACE: 한 판 시작 → 누가 먼저 필요 승수에 닿으면 게임 끝
    #   r: 판수 선택으로 돌아가기 / q: 종료
    import random

    def demo_judge(a, b):
        """테스트용 판정. 실제 판정은 game.py가 한다."""
        if a == b:
            return "DRAW"
        return "P1" if (a, b) in (("rock", "scissors"), ("scissors", "paper"), ("paper", "rock")) else "P2"

    RESULT_SHOW_SECONDS = 2

    cap = open_camera()
    enable_mouse()
    state = "SELECT"            # SELECT → PLAY → OVER
    best_of = 3
    countdown_start = None
    result_info = None          # (p1_hand, p2_hand, result, 보여 주기 시작한 시각)
    p1_score, p2_score, round_no = 0, 0, 1
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)  # 거울처럼 좌우 반전
        frame = draw_split_screen(frame)
        click = get_click()

        if state == "SELECT":
            frame = draw_best_of_select(frame)
            chosen = get_clicked_best_of(frame, click)
            if chosen is not None:
                best_of, state = chosen, "PLAY"
                p1_score, p2_score, round_no = 0, 0, 1

        elif state == "PLAY":
            frame = draw_scoreboard(frame, p1_score, p2_score, round_no, best_of)
            if countdown_start is not None:
                text = get_countdown_text(countdown_start)
                frame = draw_countdown(frame, text)
                if text is None:  # 카운트다운 끝 → 판정
                    countdown_start = None
                    a, b = random.choice(["rock", "paper", "scissors"]), random.choice(["rock", "paper", "scissors"])
                    res = demo_judge(a, b)
                    p1_score += res == "P1"
                    p2_score += res == "P2"
                    result_info = (a, b, res, time.time())

            if result_info is not None:
                frame = draw_round_result(frame, *result_info[:3])
                if time.time() - result_info[3] >= RESULT_SHOW_SECONDS:
                    result_info = None
                    round_no += 1
                    if max(p1_score, p2_score) >= best_of // 2 + 1:
                        state = "OVER"

        elif state == "OVER":
            frame = draw_scoreboard(frame, p1_score, p2_score, round_no - 1, best_of)
            winner = "P1" if p1_score > p2_score else "P2"
            frame = draw_message(frame, f"{winner} WINS!  (r: restart)", RESULT_COLOR[winner])

        key = show_frame(frame)
        if key == ord(" ") and state == "PLAY" and countdown_start is None and result_info is None:
            countdown_start = start_countdown() 
        elif key == ord("r"):
            state, countdown_start, result_info = "SELECT", None, None
        if should_quit(key):
            break
    cap.release()
    cv2.destroyAllWindows()