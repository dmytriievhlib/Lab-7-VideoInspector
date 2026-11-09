# VideoInspector

VideoInspector — програмна система відеоспостереження на Python.

## Можливості

- Отримання відео з вебкамери.
- Перегляд відео в реальному часі.
- Створення скриншотів.
- Запис відео у форматі MP4.
- Виявлення руху за допомогою OpenCV.
- Реєстрація подій руху у CSV-файлі.
- Вебінтерфейс для перегляду відеопотоку.
- Авторизація користувача за паролем.
- Доступ до системи через локальну мережу.

## Технології

- Python
- OpenCV
- Flask
- HTML
- CSV
- HTTP

## Структура проєкту

```text
VideoInspector/
├── main.py
├── server.py
├── generate_cert.py
├── requirements.txt
├── README.md
├── .gitignore
├── logs/
│   └── motion_events.csv
├── screenshots/
└── videos/
