import cv2
import json
import numpy as np


line_points = []
poly_points = []
mode = "LINE"

video_path = r"D:\Multi-camera process\input\count-in.mp4"
cap = cv2.VideoCapture(video_path)

ret, frame = cap.read()
if not ret:
    print("Lỗi: Không thể đọc video!")
    exit()

DISPLAY_W = 1280
DISPLAY_H = 720
def resize(f): return cv2.resize(f, (DISPLAY_W, DISPLAY_H))
clone = resize(frame)

def mouse_callback(event, x, y, flags, param):
    global line_points, poly_points
    if event == cv2.EVENT_LBUTTONDOWN:
        if mode == "LINE":
            if len(line_points) < 2:
                line_points.append([x, y])
            else:
                print("Đường thẳng chỉ cần 2 điểm. Nhấn 'C' để vẽ lại hoặc 'P' để vẽ đa giác.")
        else:
            poly_points.append([x, y])
            
    if event == cv2.EVENT_RBUTTONDOWN:
        if mode == "LINE" and line_points: line_points.pop()
        if mode == "POLYGON" and poly_points: poly_points.pop()

def export():
    print("\n" + "="*50)
    print(" COPY CÁC DÒNG DƯỚI ĐÂY VÀO SETTING.PY ")
    print("="*50)
    
    # Format cho Line
    if len(line_points) == 2:
        l = [line_points[0][0], line_points[0][1], line_points[1][0], line_points[1][1]]
        print(f"COUNTING_LINE = {l}")
    else:
        print("COUNTING_LINE = [] # (Chưa chọn đủ 2 điểm)")
        
    # Format cho Polygon
    print(f"ZONE_POLYGON = {poly_points}")
    print("="*50 + "\n")

cv2.namedWindow("Tool Toa Do", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Tool Toa Do", DISPLAY_W, DISPLAY_H)
cv2.setMouseCallback("Tool Toa Do", mouse_callback)

print("HƯỚNG DẪN:")
print("- Nhấn 'L' để vẽ Đường thẳng (Chọn 2 điểm).")
print("- Nhấn 'P' để vẽ Đa giác (Chọn nhiều điểm).")
print("- Nhấn 'S' để xuất tọa độ ra màn hình Terminal.")
print("- Nhấn 'C' để xóa dữ liệu của chế độ hiện tại.")

while True:
    display = clone.copy()
    
    # Hiển thị hướng dẫn và chế độ hiện tại
    color_mode = (255, 0, 0) if mode == "LINE" else (0, 0, 255)
    cv2.putText(display, f"MODE: {mode} (L or P)", (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, color_mode, 2)

    # Vẽ Đường thẳng (Màu Xanh)
    for p in line_points:
        cv2.circle(display, tuple(p), 5, (255, 0, 0), -1)
    if len(line_points) == 2:
        cv2.line(display, tuple(line_points[0]), tuple(line_points[1]), (255, 0, 0), 2)

    # Vẽ Đa giác (Màu Đỏ)
    for p in poly_points:
        cv2.circle(display, tuple(p), 5, (0, 0, 255), -1)
    if len(poly_points) > 1:
        cv2.polylines(display, [np.array(poly_points, np.int32)], True, (0, 0, 255), 2)

    cv2.imshow("Tool Toa Do", display)
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('l'): mode = "LINE"
    if key == ord('p'): mode = "POLYGON"
    if key == ord('s'): export()
    if key == ord('c'):
        if mode == "LINE": line_points = []
        else: poly_points = []
    if key == 27: break

cap.release()
cv2.destroyAllWindows()
