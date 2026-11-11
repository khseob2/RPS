import time

import cv2
 
WINDOW_NAME = "HandClash"
QUIT_KEYS = (ord("q"), 27)  # q, ESC
COUNTDOWN_SECONDS = 3       # 3, 2, 1 을 세는 시간(초)
SHOW_SECONDS = 1            # "SHOW!"를 보여 주는 시간(초)
 
SCOREBOARD_HEIGHT = 120     # 점수판 카드 + 아래 여백 높이(720px 화면 기준, 픽셀)
# 색은 OpenCV 기준 BGR 순서 (발표 자료와 같은 색)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
NAVY = (38, 20, 16)          # #101426  카드·버튼 바탕
MUTED = (184, 163, 154)      # #9AA3B8  작은 설명 글자
ACCENT = (197, 215, 37)      # #25D7C5  청록 강조색 (제목, SHOW!, START)
YELLOW = (61, 200, 255)      # #FFC83D  안내·경고 문구
P1_COLOR = (255, 108, 79)    # #4F6CFF  P1 파랑
P2_COLOR = (95, 107, 255)    # #FF6B5F  P2 빨강
FONT = cv2.FONT_HERSHEY_SIMPLEX        # 작은 글자
TITLE_FONT = cv2.FONT_HERSHEY_DUPLEX   # 숫자·제목 (조금 더 매끈한 글꼴)
AA = cv2.LINE_AA                       # 글자·도형 가장자리를 부드럽게


# 손모양 이름
HAND_NAMES = {
    "rock": "Rock", "paper": "Paper", "scissors": "Scissors",
}
# 판정 결과: "P1"(P1 승), "P2"(P2 승), "DRAW"(무승부)
RESULT_TEXT = {"P1": "P1 WIN", "P2": "P2 WIN", "DRAW": "DRAW"}
RESULT_COLOR = {"P1": P1_COLOR, "P2": P2_COLOR, "DRAW": ACCENT}

BEST_OF_CHOICES = (3, 5, 7)   # 고를 수 있는 판수
BUTTON_COLOR = NAVY           # 버튼 바탕색

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
 
 
# ---------------------------------------------------------------------------
# 그리기 도구 (내부용): 둥근 카드, 반투명 패널, 가운데 정렬 글자
# ---------------------------------------------------------------------------

def _ui_scale(frame):
    """화면 높이 720px을 1로 보고 크기를 맞추는 배율. (640x480이면 약 0.67)"""
    return frame.shape[0] / 720


def _rounded_rect(img, x1, y1, x2, y2, r, color, thickness=-1):
    """모서리가 둥근 사각형을 그린다. thickness=-1이면 속을 채운다."""
    r = max(0, min(r, (x2 - x1) // 2, (y2 - y1) // 2))
    if thickness < 0:
        cv2.rectangle(img, (x1 + r, y1), (x2 - r, y2), color, -1)
        cv2.rectangle(img, (x1, y1 + r), (x2, y2 - r), color, -1)
        for cx, cy in ((x1 + r, y1 + r), (x2 - r, y1 + r), (x1 + r, y2 - r), (x2 - r, y2 - r)):
            cv2.circle(img, (cx, cy), r, color, -1, AA)
    else:
        cv2.line(img, (x1 + r, y1), (x2 - r, y1), color, thickness, AA)
        cv2.line(img, (x1 + r, y2), (x2 - r, y2), color, thickness, AA)
        cv2.line(img, (x1, y1 + r), (x1, y2 - r), color, thickness, AA)
        cv2.line(img, (x2, y1 + r), (x2, y2 - r), color, thickness, AA)
        cv2.ellipse(img, (x1 + r, y1 + r), (r, r), 180, 0, 90, color, thickness, AA)
        cv2.ellipse(img, (x2 - r, y1 + r), (r, r), 270, 0, 90, color, thickness, AA)
        cv2.ellipse(img, (x1 + r, y2 - r), (r, r), 90, 0, 90, color, thickness, AA)
        cv2.ellipse(img, (x2 - r, y2 - r), (r, r), 0, 0, 90, color, thickness, AA)


def _panel(frame, x1, y1, x2, y2, color=NAVY, alpha=0.8, r=18, border=None, border_thickness=2):
    """반투명한 둥근 카드를 그린다. 뒤의 영상이 살짝 비쳐 보인다."""
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
    if x2 <= x1 or y2 <= y1:
        return frame
    roi = frame[y1:y2, x1:x2]
    overlay = roi.copy()
    _rounded_rect(overlay, 0, 0, x2 - x1 - 1, y2 - y1 - 1, r, color, -1)
    cv2.addWeighted(overlay, alpha, roi, 1 - alpha, 0, roi)
    if border is not None:
        _rounded_rect(frame, x1, y1, x2 - 1, y2 - 1, r, border, border_thickness)
    return frame


def _dim(frame, alpha=0.6, color=NAVY):
    """화면 전체를 어둡게 덮는다. 안내·선택·최종 결과 화면 뒤에 깐다."""
    overlay = frame.copy()
    overlay[:] = color
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    return frame


def _text_size(text, scale, thickness, font=TITLE_FONT):
    (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
    return tw, th


def _text(frame, text, center_x, y, scale, color, thickness, font=TITLE_FONT, shadow=False):
    """center_x를 가운데로, y를 글자 아랫줄로 해서 글자를 그린다. shadow=True면 아래에 그림자."""
    tw, _ = _text_size(text, scale, thickness, font)
    x = center_x - tw // 2
    if shadow:
        offset = max(1, int(scale * 2))
        cv2.putText(frame, text, (x + offset, y + offset), font, scale, BLACK, thickness + 1, AA)
    cv2.putText(frame, text, (x, y), font, scale, color, thickness, AA)


def _text_mid(frame, text, center_x, center_y, scale, color, thickness, font=TITLE_FONT, shadow=False):
    """글자의 세로 가운데가 center_y에 오도록 그린다."""
    _, th = _text_size(text, scale, thickness, font)
    _text(frame, text, center_x, center_y + th // 2, scale, color, thickness, font, shadow)


def _put_centered(frame, text, center_x, y, scale, color, thickness):
    """center_x를 가운데로 해서 글자를 그린다. (예전 함수 이름 그대로 남겨 둠, 내부용)"""
    _text(frame, text, center_x, y, scale, color, thickness, FONT)


def _pill(frame, text, center_x, center_y, scale, text_color, fill, alpha=0.85, pad_x=18, pad_y=10,
          border=None, font=TITLE_FONT, thickness=1):
    """글자 둘레에 알약 모양 배지를 그린다. 배지의 (x1, y1, x2, y2)를 돌려준다."""
    tw, th = _text_size(text, scale, thickness, font)
    x1, x2 = center_x - tw // 2 - pad_x, center_x + tw // 2 + pad_x
    y1, y2 = center_y - th // 2 - pad_y, center_y + th // 2 + pad_y
    _panel(frame, x1, y1, x2, y2, fill, alpha, (y2 - y1) // 2, border)
    _text_mid(frame, text, center_x, center_y, scale, text_color, thickness, font)
    return x1, y1, x2, y2


def _key_hint(frame, parts, center_x, center_y, s):
    """[SPACE] 같은 키 모양 상자와 설명 글자를 한 줄로 그린다.

    parts: [("SPACE", True), (" to start", False)]처럼 (글자, 키 상자 여부) 목록
    """
    scale = 0.7 * s
    gap = int(10 * s)
    pad = int(8 * s)
    widths = []
    for text, is_key in parts:
        tw, _ = _text_size(text.strip(), scale, 1, FONT)
        widths.append(tw + (pad * 2 if is_key else 0))
    total = sum(widths) + gap * (len(parts) - 1)
    x = center_x - total // 2
    _, th = _text_size("A", scale, 1, FONT)
    for (text, is_key), width in zip(parts, widths):
        if is_key:
            _rounded_rect(frame, x, center_y - th // 2 - pad, x + width, center_y + th // 2 + pad,
                          int(6 * s), WHITE, 1)
            _text_mid(frame, text.strip(), x + width // 2, center_y, scale, WHITE, 1, FONT)
        else:
            _text_mid(frame, text.strip(), x + width // 2, center_y, scale, MUTED, 1, FONT)
        x += width + gap


# ---------------------------------------------------------------------------
# 화면 그리기
# ---------------------------------------------------------------------------

def draw_split_screen(frame):
    """가운데 반투명 세로선과 P1/P2 배지를 그린다. 같은 frame에 그려서 돌려준다."""
    h, w = frame.shape[:2]
    s = _ui_scale(frame)
    center_x = get_center_x(frame)

    # 가운데 세로선: 짧은 선을 반복한 반투명 점선 (영상을 덜 가리게)
    dash, gap = int(18 * s), int(12 * s)
    x1, x2 = center_x - 3, center_x + 4
    roi = frame[:, x1:x2]
    overlay = roi.copy()
    for y in range(0, h, dash + gap):
        cv2.line(overlay, (3, y), (3, min(h, y + dash)), WHITE, max(1, int(2 * s)), AA)
    cv2.addWeighted(overlay, 0.55, roi, 0.45, 0, roi)

    margin = int(22 * s)
    _pill(frame, "P1", margin + int(34 * s), margin + int(20 * s), 0.8 * s, WHITE, P1_COLOR, 0.9,
          int(20 * s), int(10 * s), thickness=2)
    _pill(frame, "P2", center_x + margin + int(34 * s), margin + int(20 * s), 0.8 * s, WHITE, P2_COLOR, 0.9,
          int(20 * s), int(10 * s), thickness=2)
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
    """카운트다운을 화면 정중앙에 그린다. 숫자는 동그란 원 안에, SHOW!는 청록 글자만. None이면 안 그린다."""
    if text is None:
        return frame

    h, w = frame.shape[:2]
    s = _ui_scale(frame)
    cx, cy = w // 2, h // 2

    if text.isdigit():
        radius = int(115 * s)
        overlay = frame.copy()
        cv2.circle(overlay, (cx, cy), radius, NAVY, -1, AA)
        cv2.addWeighted(overlay, 0.88, frame, 0.12, 0, frame)
        cv2.circle(frame, (cx, cy), radius, ACCENT, max(2, int(6 * s)), AA)
        _text_mid(frame, text, cx, cy, 4.2 * s, WHITE, max(2, int(9 * s)))
    else:
        # 바탕 상자 없이 글자만: 영상 위에서도 보이도록 그림자를 깐다
        _text_mid(frame, text, cx, cy, 3.4 * s, ACCENT, max(3, int(8 * s)), shadow=True)
    return frame


def draw_scoreboard(frame, p1_score, p2_score, round_no, best_of=3):
    """화면 아래 가운데에 떠 있는 점수판 카드를 그린다.

    p1_score, p2_score: 지금까지 이긴 판 수
    round_no: 지금 몇 번째 판인지 (1부터)
    best_of: 판수 (3, 5, 7). 이기려면 best_of // 2 + 1 승이 필요하다.
    """
    h, w = frame.shape[:2]
    s = _ui_scale(frame)
    wins_needed = best_of // 2 + 1
    center_x = get_center_x(frame)

    card_w, card_h = int(520 * s), int(96 * s)
    x1, x2 = center_x - card_w // 2, center_x + card_w // 2
    y2 = h - int(18 * s)
    y1 = y2 - card_h
    mid_y = (y1 + y2) // 2
    _panel(frame, x1, y1, x2, y2, NAVY, 0.92, int(22 * s))

    # 가운데: 라운드 번호와 필요 승수
    _text(frame, f"ROUND {round_no}", center_x, mid_y + int(2 * s), 0.8 * s, WHITE, max(1, int(2 * s)))
    _text(frame, f"First to {wins_needed}", center_x, mid_y + int(30 * s), 0.55 * s, MUTED, 1, FONT)

    # 가운데와 양쪽을 나누는 얇은 선
    for x in (center_x - int(95 * s), center_x + int(95 * s)):
        cv2.line(frame, (x, y1 + int(18 * s)), (x, y2 - int(18 * s)), MUTED, 1, AA)

    # 양쪽: 위에 플레이어 이름(작게), 아래에 점수(크게)
    for label, score, color, sign in (("P1", p1_score, P1_COLOR, -1), ("P2", p2_score, P2_COLOR, 1)):
        side_x = center_x + sign * int(176 * s)
        _text(frame, label, side_x, y1 + int(28 * s), 0.55 * s, color, max(1, int(2 * s)), FONT)
        _text_mid(frame, str(score), side_x, mid_y + int(14 * s), 1.5 * s, color, max(2, int(4 * s)))
    return frame


def get_hand_name(hand):
    """손모양 값("rock" / "paper" / "scissors")을 화면에 그릴 글자로 바꾼다. 없으면 "-", 모르는 값이면 "?"."""
    if hand is None:
        return "-"
    return HAND_NAMES.get(str(hand).strip().lower(), "?")


def draw_message(frame, text, color=YELLOW, scale=1.5):
    """화면 정중앙에 안내 문구를 글자만 그린다. (예: "Show both hands!")

    바탕 상자 없이, 영상 위에서도 보이도록 그림자를 깐다.
    """
    h, w = frame.shape[:2]
    s = _ui_scale(frame)
    font_scale = scale * 0.9 * s
    thickness = max(2, int(4 * s))
    _text_mid(frame, text, w // 2, h // 2, font_scale, color, thickness, shadow=True)
    return frame


def draw_round_result(frame, p1_hand, p2_hand, result):
    """한 판의 결과를 화면 가운데 카드에 그린다.

    p1_hand, p2_hand: "rock" / "paper" / "scissors" (소문자), 손이 없으면 None
    result: "P1", "P2", "DRAW"  (None이면 결과 없음 → 안내 문구만 그린다)
    카드 위쪽에 두 사람의 손모양, 아래쪽에 승패를 크게 보여 준다.
    """
    if result not in RESULT_TEXT:
        return draw_message(frame, "Show both hands!", YELLOW)

    h, w = frame.shape[:2]
    s = _ui_scale(frame)
    center_x = get_center_x(frame)
    mid_y = h // 2 - int(20 * s)
    color = RESULT_COLOR[result]

    card_w, card_h = int(640 * s), int(250 * s)
    x1, y1 = center_x - card_w // 2, mid_y - card_h // 2
    x2, y2 = x1 + card_w, y1 + card_h
    _panel(frame, x1, y1, x2, y2, NAVY, 0.92, int(26 * s), color, max(2, int(3 * s)))

    # 윗줄: P1 손모양  vs  P2 손모양
    row_y = y1 + int(70 * s)
    _text_mid(frame, get_hand_name(p1_hand), center_x - int(165 * s), row_y, 1.1 * s, P1_COLOR, max(2, int(2 * s)))
    _text_mid(frame, "vs", center_x, row_y, 0.7 * s, MUTED, 1, FONT)
    _text_mid(frame, get_hand_name(p2_hand), center_x + int(165 * s), row_y, 1.1 * s, P2_COLOR, max(2, int(2 * s)))

    # 아랫줄: 승패 크게
    _text_mid(frame, RESULT_TEXT[result], center_x, y2 - int(78 * s), 2.3 * s, color, max(3, int(6 * s)))
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


def draw_button(frame, button, color=WHITE, filled=False):
    """둥근 버튼을 그린다.

    filled=False: 어두운 반투명 바탕 + 색 테두리 + 흰 글자 (판수 버튼, QUIT)
    filled=True : 색으로 꽉 채운 바탕 + 남색 글자 (START처럼 제일 중요한 버튼)
    """
    x1, y1, x2, y2 = button["rect"]
    s = max(0.5, (y2 - y1) / 60)
    radius = min((y2 - y1) // 2, int(18 * s))
    if filled:
        _panel(frame, x1, y1, x2, y2, color, 0.95, radius)
        text_color = NAVY
    else:
        _panel(frame, x1, y1, x2, y2, BUTTON_COLOR, 0.85, radius, color, max(2, int(2 * s)))
        text_color = WHITE

    scale = (y2 - y1) / 62   # 버튼 높이에 맞춰 글자 크기를 정한다
    thickness = max(1, int(scale * 2))
    _text_mid(frame, button["label"], (x1 + x2) // 2, (y1 + y2) // 2, scale, text_color, thickness)
    return frame


def get_best_of_buttons(frame):
    """판수 선택 버튼 3개(3, 5, 7)를 화면 가운데에 가로로 놓은 버튼 리스트."""
    h, w = frame.shape[:2]
    size = min(w, h) // 4      # 정사각형 버튼 한 변
    gap = size // 4
    left = (w - (size * 3 + gap * 2)) // 2
    top = h // 2 - size // 2
    return [make_button(str(n), left + i * (size + gap), top, size, size)
            for i, n in enumerate(BEST_OF_CHOICES)]


def draw_best_of_select(frame):
    """판수 선택 화면: 제목, 3 / 5 / 7 카드 버튼(아래에 필요 승수), 안내 문구."""
    h, w = frame.shape[:2]
    s = _ui_scale(frame)
    _dim(frame, 0.55)
    buttons = get_best_of_buttons(frame)
    top = buttons[0]["rect"][1]
    bottom = buttons[0]["rect"][3]

    _text(frame, "Choose rounds", w // 2, top - int(60 * s), 1.2 * s, WHITE, max(2, int(2 * s)), shadow=True)
    for best_of, button in zip(BEST_OF_CHOICES, buttons):
        x1, y1, x2, y2 = button["rect"]
        _panel(frame, x1, y1, x2, y2, NAVY, 0.85, int(24 * s), ACCENT, max(2, int(3 * s)))
        _text_mid(frame, str(best_of), (x1 + x2) // 2, y1 + int((y2 - y1) * 0.42), 2.6 * s, WHITE,
                  max(2, int(5 * s)))
        _text(frame, f"First to {best_of // 2 + 1}", (x1 + x2) // 2, y2 - int(24 * s), 0.6 * s, ACCENT,
              1, FONT)
    _text(frame, "Click a card to start", w // 2, bottom + int(55 * s), 0.7 * s, MUTED, 1, FONT)
    return frame


def get_clicked_best_of(frame, click):
    """판수 버튼을 눌렀으면 그 판수(3, 5, 7)를, 아니면 None을 돌려준다."""
    for best_of, button in zip(BEST_OF_CHOICES, get_best_of_buttons(frame)):
        if is_clicked(button, click):
            return best_of
    return None


def get_quit_button(frame):
    """게임 종료(QUIT) 버튼: 화면 오른쪽 위."""
    h, w = frame.shape[:2]
    s = _ui_scale(frame)
    button_w, button_h = int(120 * s), int(48 * s)
    margin = int(22 * s)
    return make_button("QUIT", w - button_w - margin, margin, button_w, button_h)


def draw_quit_button(frame):
    """게임 종료 버튼을 그린다."""
    return draw_button(frame, get_quit_button(frame), P2_COLOR)


def is_quit_clicked(frame, click):
    """게임 종료 버튼을 눌렀으면 True."""
    return is_clicked(get_quit_button(frame), click)


def draw_game_over(frame, winner, p1_score, p2_score):
    """게임이 끝났을 때 최종 결과 카드를 그린다. 아래에 r(다시)·q(종료) 키 안내도 그린다.

    winner: "P1", "P2", "DRAW" (누가 이겼는지는 game.py가 정해서 넘겨준다)
    p1_score, p2_score: 최종 점수
    """
    h, w = frame.shape[:2]
    s = _ui_scale(frame)
    center_x = get_center_x(frame)
    mid_y = h // 2
    color = RESULT_COLOR.get(winner, WHITE)
    _dim(frame, 0.55)

    card_w, card_h = int(560 * s), int(330 * s)
    x1, y1 = center_x - card_w // 2, mid_y - card_h // 2
    _panel(frame, x1, y1, x1 + card_w, y1 + card_h, NAVY, 0.9, int(28 * s), color, max(2, int(3 * s)))

    title = "DRAW" if winner == "DRAW" else f"{winner} WINS!"
    _text(frame, "GAME OVER", center_x, y1 + int(62 * s), 0.75 * s, MUTED, max(1, int(2 * s)))
    _text_mid(frame, title, center_x, y1 + int(135 * s), 2.0 * s, color, max(3, int(5 * s)))

    score_y = y1 + int(225 * s)
    _text_mid(frame, str(p1_score), center_x - int(70 * s), score_y, 1.8 * s, P1_COLOR, max(2, int(4 * s)))
    _text_mid(frame, ":", center_x, score_y, 1.5 * s, MUTED, max(2, int(3 * s)))
    _text_mid(frame, str(p2_score), center_x + int(70 * s), score_y, 1.8 * s, P2_COLOR, max(2, int(4 * s)))

    _key_hint(frame, [("R", True), ("play again", False), ("Q", True), ("quit", False)],
              center_x, y1 + card_h - int(36 * s), s)
    return frame


GUIDE_LINES = [
    "P1 stands on the LEFT, P2 on the RIGHT",
    "Click 3 / 5 / 7 to choose rounds",
    "Press SPACE, then show your hand at SHOW!",
    "Click QUIT to end the game anytime",
]


def get_start_button(frame):
    """안내 화면의 START 버튼: 화면 아래쪽 가운데."""
    h, w = frame.shape[:2]
    button_w, button_h = w // 4, h // 10
    return make_button("START", (w - button_w) // 2, int(h * 0.76), button_w, button_h)


def draw_guide(frame):
    """게임 시작 전 안내 화면: 제목, 번호 붙은 사용법 4줄, START 버튼."""
    h, w = frame.shape[:2]
    s = _ui_scale(frame)
    center_x = w // 2
    _dim(frame, 0.72)

    _text(frame, "HandClash", center_x, int(h * 0.20), 2.4 * s, ACCENT, max(3, int(6 * s)), shadow=True)
    _text(frame, "Webcam Rock-Paper-Scissors for two", center_x, int(h * 0.27), 0.7 * s, MUTED, 1, FONT)

    # 사용법: 왼쪽 정렬된 블록을 화면 가운데에 놓는다
    scale = 0.85 * s
    widest = max(_text_size(line, scale, max(1, int(2 * s)), FONT)[0] for line in GUIDE_LINES)
    num_r = int(16 * s)
    block_w = num_r * 2 + int(18 * s) + widest
    left = center_x - block_w // 2
    for i, line in enumerate(GUIDE_LINES):
        y = int(h * 0.38) + i * int(h * 0.08)
        cv2.circle(frame, (left + num_r, y), num_r, ACCENT, -1, AA)
        _text_mid(frame, str(i + 1), left + num_r, y, 0.6 * s, NAVY, max(1, int(2 * s)))
        tw, _ = _text_size(line, scale, max(1, int(2 * s)), FONT)
        _text_mid(frame, line, left + num_r * 2 + int(18 * s) + tw // 2, y, scale, WHITE, max(1, int(2 * s)), FONT)

    draw_button(frame, get_start_button(frame), ACCENT, filled=True)
    return frame


def is_start_clicked(frame, click):
    """START 버튼을 눌렀으면 True."""
    return is_clicked(get_start_button(frame), click)


if __name__ == "__main__":
    # 혼자 실행해서 화면이 뜨는지 확인하는 테스트용 코드 (나중에는 game.py/main.py가 이 역할을 한다)
    #   START 클릭 → 판수 버튼 클릭 → SPACE: 한 판 시작 → 누가 먼저 필요 승수에 닿거나 QUIT 버튼을 누르면 게임 끝
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
    state = "GUIDE"             # GUIDE → SELECT → PLAY → OVER
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

        if state == "GUIDE":
            frame = draw_guide(frame)
            if is_start_clicked(frame, click):
                state = "SELECT"

        elif state == "SELECT":
            frame = draw_best_of_select(frame)
            chosen = get_clicked_best_of(frame, click)
            if chosen is not None:
                best_of, state = chosen, "PLAY"
                p1_score, p2_score, round_no = 0, 0, 1

        elif state == "PLAY":
            frame = draw_scoreboard(frame, p1_score, p2_score, round_no, best_of)
            frame = draw_quit_button(frame)
            if is_quit_clicked(frame, click):  # 중간 종료 → 지금까지의 점수로 끝
                state, countdown_start, result_info = "OVER", None, None
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

            if state == "PLAY" and result_info is not None:
                frame = draw_round_result(frame, *result_info[:3])
                if time.time() - result_info[3] >= RESULT_SHOW_SECONDS:
                    result_info = None
                    round_no += 1
                    if max(p1_score, p2_score) >= best_of // 2 + 1:
                        state = "OVER"

        elif state == "OVER":
            # 테스트용 승자 판별 (실제로는 game.py가 정한다). 동점이면 DRAW
            if p1_score == p2_score:
                winner = "DRAW"
            else:
                winner = "P1" if p1_score > p2_score else "P2"
            frame = draw_game_over(frame, winner, p1_score, p2_score)

        key = show_frame(frame)
        if key == ord(" ") and state == "PLAY" and countdown_start is None and result_info is None:
            countdown_start = start_countdown() 
        elif key == ord("r"):
            state, countdown_start, result_info = "SELECT", None, None
        if should_quit(key):
            break
    cap.release()
    cv2.destroyAllWindows()