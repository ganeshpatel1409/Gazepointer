import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time
import sys

pyautogui.FAILSAFE = False


# MEDIAPIPE SETUP
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


# CAMERA + SCREEN
cap = cv2.VideoCapture(0)

screen_w, screen_h = pyautogui.size()

ret, frame = cap.read()
cam_h, cam_w, _ = frame.shape



# GLOBAL QUIT FUNCTION
def quit_program():
    print("Program stopped")
    cap.release()
    cv2.destroyAllWindows()
    sys.exit()



# GET EYE CENTER
def get_eye_center(frame):

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb
    )

    result = landmarker.detect_for_video(
        mp_image,
        int(time.time() * 1000)
    )

    if result.face_landmarks:

        landmarks = result.face_landmarks[0]

        left_iris = landmarks[468]
        right_iris = landmarks[473]

        center_x = (left_iris.x + right_iris.x) / 2
        center_y = (left_iris.y + right_iris.y) / 2

        return center_x, center_y

    return None



# CALIBRATION
def run_calibration():

    cv2.namedWindow("Calibration", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(
        "Calibration",
        cv2.WND_PROP_FULLSCREEN,
        cv2.WINDOW_FULLSCREEN
    )

    margin_x = int(cam_w * 0.03)
    margin_y = int(cam_h * 0.04)



    
    
    cols = 3
    rows = 3
    xs = np.linspace(margin_x, cam_w - margin_x, cols)
    ys = np.linspace(margin_y, cam_h - margin_y, rows)
    calibration_points = []
    for y in ys:
      for x in xs:
        calibration_points.append((int(x), int(y)))

    calibration_data = []

    for point in calibration_points:

        captured = False

        while not captured:

            ret, frame = cap.read()

            eye = get_eye_center(frame)

            # UI canvas
            ui = np.ones((cam_h, cam_w, 3), dtype=np.uint8) * 255

            # dot
            cv2.circle(ui, point, 8, (0,0,255), -1)

            # text
            text = "Look at dot and press SPACE"
            font = cv2.FONT_HERSHEY_SIMPLEX
            scale = 0.9
            thickness = 2

            (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)

            cv2.putText(
                ui,
                text,
                ((cam_w - tw) // 2, int(cam_h * 0.1)),
                font,
                scale,
                (0,0,0),
                thickness
            )

            cv2.imshow("Calibration", ui)

            key = cv2.waitKey(1) & 0xFF

            if key == 27 or key == ord('q'):
                quit_program()

            if key == 32 and eye is not None:

                calibration_data.append(eye)
                captured = True

    cv2.destroyWindow("Calibration")

    xs = [p[0] for p in calibration_data]
    ys = [p[1] for p in calibration_data]

    return min(xs), max(xs), min(ys), max(ys)



# RUN CALIBRATION
print("Starting calibration...")

min_x, max_x, min_y, max_y = run_calibration()

print("Calibration complete")



# CURSOR SMOOTHING
smooth_x = 0.0
smooth_y = 0.0
alpha = 0.08



# MAIN LOOP0
while True:

    ret, frame = cap.read()

    if not ret:
        break

    eye = get_eye_center(frame)

    if eye is not None:

        center_x, center_y = eye

        norm_x = (center_x - min_x) / (max_x - min_x)
        norm_y = (center_y - min_y) / (max_y - min_y)

        norm_x = 1 - norm_x

        screen_x = int(norm_x * screen_w)
        screen_y = int(norm_y * screen_h)

        # smoothing
        smooth_x = smooth_x + alpha * (screen_x - smooth_x)
        smooth_y = smooth_y + alpha * (screen_y - smooth_y)

        pyautogui.moveTo(int(smooth_x), int(smooth_y))

    key = cv2.waitKey(1) & 0xFF

    if key == 27 or key == ord('q'):
        quit_program()