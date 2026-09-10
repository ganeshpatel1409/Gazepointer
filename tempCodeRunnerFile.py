import cv2
import mediapipe as mp
import numpy as np
import pyautogui

pyautogui.FAILSAFE = False
import time



BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path="face_landmarker.task"),
    running_mode=VisionRunningMode.VIDEO,
    num_faces=1
)

landmarker = FaceLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)

screen_w, screen_h = pyautogui.size()

# ========================
# FULL CAMERA CALIBRATION
# ========================

cv2.namedWindow("Calibration", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("Calibration", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

ret, frame = cap.read()
cam_h, cam_w, _ = frame.shape

calibration_points = [
    (80, 80),                      # top-left
    (cam_w - 80, 80),              # top-right
    (80, cam_h - 80),              # bottom-left
    (cam_w - 80, cam_h - 80)       # bottom-right
]

calibration_data = []

for point in calibration_points:

    captured = False

    while not captured:
        ret, frame = cap.read()
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = landmarker.detect_for_video(mp_image, int(time.time()*1000))

        # Draw calibration dot ON CAMERA FRAME
        cv2.circle(frame, point, 20, (0,0,255), -1)

        cv2.putText(frame,
                    "Look at dot & press SPACE | ESC to quit",
                    (30,50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255,255,255),
                    2)

        cv2.imshow("Calibration", frame)

        if result.face_landmarks:
            landmarks = result.face_landmarks[0]
            left_iris = landmarks[468]
            right_iris = landmarks[473]

            center_x = (left_iris.x + right_iris.x) / 2
            center_y = (left_iris.y + right_iris.y) / 2

        key = cv2.waitKey(1)

        if key == 27:  # ESC
            cap.release()
            cv2.destroyAllWindows()
            exit()

        if key == 32:  # SPACE
            calibration_data.append((center_x, center_y))
            captured = True

cv2.destroyWindow("Calibration")
print("Calibration Complete!")

# Get boundaries
xs = [p[0] for p in calibration_data]
ys = [p[1] for p in calibration_data]

min_x, max_x = min(xs), max(xs)
min_y, max_y = min(ys), max(ys)

print("Calibration Complete!")



while True:
    ret, frame = cap.read()
    if not ret:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = landmarker.detect_for_video(mp_image, int(time.time()*1000))

    if result.face_landmarks:
        landmarks = result.face_landmarks[0]

        left_iris = landmarks[468]
        right_iris = landmarks[473]

        center_x = (left_iris.x + right_iris.x) / 2
        center_y = (left_iris.y + right_iris.y) / 2

        # Normalize
        norm_x = (center_x - min_x) / (max_x - min_x)
        norm_y = (center_y - min_y) / (max_y - min_y)
        norm_x = 1 - norm_x
        

        screen_x = int(norm_x * screen_w)
        screen_y = int(norm_y * screen_h)

        print("Mapped:", screen_x, screen_y)

        pyautogui.moveTo(screen_x, screen_y)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()