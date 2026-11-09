
import cv2
import time
import os
import secrets
import threading

from functools import wraps
from flask import (
    Flask, Response, request, redirect,
    url_for, session, render_template_string
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Налаштування безпеки
secret_key = os.environ.get("VIDEOINSPECTOR_SECRET")
user_password = os.environ.get("VIDEOINSPECTOR_PASSWORD")

if not secret_key or not user_password:
    raise RuntimeError(
        "Спочатку задай VIDEOINSPECTOR_SECRET і VIDEOINSPECTOR_PASSWORD."
    )

app.secret_key = secret_key
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False  # Увімкнути True після переходу на HTTPS
)

PASSWORD_HASH = generate_password_hash(user_password)

# Камера
camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("Помилка: не вдалося підключитися до камери.")
    raise SystemExit(1)

camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

frame_lock = threading.Lock()
latest_frame = None
running = True


def capture_frames():
    global latest_frame, running

    while running:
        success, frame = camera.read()

        if success:
            with frame_lock:
                latest_frame = frame.copy()
        else:
            time.sleep(0.05)


def generate_frames():
    while running:
        with frame_lock:
            frame = latest_frame.copy() if latest_frame is not None else None

        if frame is None:
            time.sleep(0.05)
            continue

        success, buffer = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 80]
        )

        if not success:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + buffer.tobytes()
            + b"\r\n"
        )

        time.sleep(0.03)


def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login"))
        return function(*args, **kwargs)

    return wrapper


LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Вхід — VideoInspector</title>
<style>
body {
    background: #17202b;
    color: white;
    font-family: Arial;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 90vh;
}
.box {
    background: #263545;
    padding: 30px;
    border-radius: 12px;
    width: 320px;
    text-align: center;
}
input, button {
    box-sizing: border-box;
    width: 100%;
    padding: 12px;
    margin-top: 12px;
    border-radius: 6px;
    border: none;
}
button {
    background: #39d98a;
    cursor: pointer;
    font-weight: bold;
}
.error { color: #ff7777; }
</style>
</head>
<body>
<div class="box">
    <h1>VideoInspector</h1>
    <p>Авторизація користувача</p>
    {% if error %}<p class="error">{{ error }}</p>{% endif %}
    <form method="POST">
        <input type="password" name="password"
               placeholder="Введіть пароль" required autofocus>
        <button type="submit">Увійти</button>
    </form>
</div>
</body>
</html>
"""


VIDEO_PAGE = """
<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VideoInspector</title>
<style>
body {
    margin: 0;
    padding: 30px;
    background: #17202b;
    color: white;
    font-family: Arial, sans-serif;
    text-align: center;
}
h1 { color: #39d98a; }
.video-box {
    max-width: 1000px;
    margin: 25px auto;
    padding: 12px;
    background: #263545;
    border-radius: 12px;
}
img {
    width: 100%;
    display: block;
    border-radius: 8px;
}
button {
    padding: 12px 24px;
    background: #39d98a;
    border: none;
    border-radius: 6px;
    cursor: pointer;
}
</style>
</head>
<body>
    <h1>VideoInspector</h1>
    <p>Мережеве відеоспостереження</p>

    <div class="video-box">
        <img src="/video_feed" alt="Відео з камери">
    </div>

    <p style="color:#39d98a">● Авторизований доступ</p>

    <form method="POST" action="/logout">
        <button type="submit">Вийти із системи</button>
    </form>
</body>
</html>
"""


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password", "")

        if check_password_hash(PASSWORD_HASH, password):
            session.clear()
            session["authenticated"] = True
            return redirect(url_for("index"))

        return render_template_string(
            LOGIN_PAGE,
            error="Неправильний пароль."
        ), 401

    return render_template_string(LOGIN_PAGE, error=None)


@app.route("/")
@login_required
def index():
    return render_template_string(VIDEO_PAGE)


@app.route("/video_feed")
@login_required
def video_feed():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-store"}
    )


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    capture_thread = threading.Thread(
        target=capture_frames,
        daemon=True
    )
    capture_thread.start()

    print("VideoInspector Server запущено.")
    print("Адрес: http://127.0.0.1:5000")
    print("Для завершення натисни Ctrl+C.")

    try:
        app.config["SESSION_COOKIE_SECURE"] = False
        app.run(
            host="0.0.0.0",
            port=5000,
            threaded=True,
            use_reloader=False
        )
    finally:
        running = False
        camera.release()
        print("Камеру звільнено.")
