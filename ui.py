import cv2
 
WINDOW_NAME = "HandClash"
QUIT_KEYS = (ord("q"), 27)  # q, ESC
 
# 색은 OpenCV 기준 BGR 순서
WHITE = (255, 255, 255)
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
 
 
if __name__ == "__main__":
    # 혼자 실행해서 화면이 뜨는지 확인하는 테스트용 코드
    cap = open_camera()
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)  # 거울처럼 좌우 반전
        frame = draw_split_screen(frame)
        key = show_frame(frame)
        if should_quit(key):
            break
    cap.release()
    cv2.destroyAllWindows()