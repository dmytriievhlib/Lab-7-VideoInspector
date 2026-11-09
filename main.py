
import cv2
import csv
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
VIDEO_DIR = BASE_DIR / "videos"
SHOT_DIR = BASE_DIR / "screenshots"
LOG_DIR = BASE_DIR / "logs"

for folder in (VIDEO_DIR, SHOT_DIR, LOG_DIR):
    folder.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "motion_events.csv"

# Параметри виявлення руху
MIN_AREA = 1200
MOTION_COOLDOWN = 3

# Камера
camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("Помилка: не вдалося підключитися до камери.")
    raise SystemExit(1)

camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# Детектор руху
background = cv2.createBackgroundSubtractorMOG2(
    history=300,
    varThreshold=40,
    detectShadows=False
)

recording = False
video_writer = None
last_motion_time = 0
motion_detected = False

# Створення журналу
if not LOG_FILE.exists():
    with open(LOG_FILE, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["Дата і час", "Подія"])

print("VideoInspector запущено.")
print("S - зробити скриншот")
print("R - почати / зупинити запис")
print("Q - вихід")

while True:
    success, frame = camera.read()

    if not success:
        print("Не вдалося отримати кадр.")
        break

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Виявлення руху
    mask = background.apply(frame)

    _, mask = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.dilate(mask, kernel, iterations=2)

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    current_motion = False

    for contour in contours:
        area = cv2.contourArea(contour)

        if area < MIN_AREA:
            continue

        current_motion = True

        x, y, w, h = cv2.boundingRect(contour)

        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            (0, 0, 255),
            2
        )

    # Реєстрація події руху з інтервалом
    current_time = time.time()

    if current_motion and current_time - last_motion_time >= MOTION_COOLDOWN:
        print(f"[{timestamp}] Виявлено рух!")

        with open(LOG_FILE, "a", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, "Виявлено рух"])

        last_motion_time = current_time

    # Інформація у вікні
    status = "MOTION DETECTED" if current_motion else "NO MOTION"

    color = (0, 0, 255) if current_motion else (0, 255, 0)

    cv2.putText(
        frame,
        timestamp,
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2
    )

    cv2.putText(
        frame,
        status,
        (20, 75),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        color,
        2
    )

    if recording:
        cv2.putText(
            frame,
            "REC",
            (20, 115),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

        video_writer.write(frame)

    cv2.imshow("VideoInspector - Video Surveillance", frame)

    key = cv2.waitKey(1) & 0xFF

    # Створення скриншота
    if key == ord("s"):
        filename = datetime.now().strftime("shot_%Y%m%d_%H%M%S.jpg")
        cv2.imwrite(str(SHOT_DIR / filename), frame)
        print(f"Скриншот збережено: {filename}")

    # Керування записом
    elif key == ord("r"):
        if not recording:
            filename = datetime.now().strftime("video_%Y%m%d_%H%M%S.mp4")
            path = str(VIDEO_DIR / filename)

            height, width = frame.shape[:2]
            fps = camera.get(cv2.CAP_PROP_FPS)

            if fps <= 0 or fps > 120:
                fps = 20.0

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")

            video_writer = cv2.VideoWriter(
                path,
                fourcc,
                fps,
                (width, height)
            )

            if not video_writer.isOpened():
                print("Не вдалося створити відеофайл.")
                video_writer = None
                continue

            recording = True
            print(f"Запис розпочато: {filename}")

        else:
            recording = False
            video_writer.release()
            video_writer = None
            print("Запис зупинено.")

    elif key == ord("q"):
        break

# Завершення роботи
if video_writer is not None:
    video_writer.release()

camera.release()
cv2.destroyAllWindows()

print("VideoInspector завершив роботу.")
