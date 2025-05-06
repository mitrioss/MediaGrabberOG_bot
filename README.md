# MediaGrabberOG\_bot

**MediaGrabberOG\_bot** — Telegram‑бот для скачивания видео и фото из YouTube, TikTok, Instagram и VK.

## Что должно быть в репозитории

* `main.py` — главный скрипт бота
* `Dockerfile` — для контейнеризации
* `requirements.txt` — зависимости Python
* `.gitignore` — исключения для Git
* `README.md` — документация (этот файл)

---

## Быстрый старт

1. Клонируйте репозиторий:

   ```bash
   git clone https://github.com/<ваш‑юзернейм>/MediaGrabberOG_bot.git
   cd MediaGrabberOG_bot
   ```

2. Создайте файл `.env` в корне с переменными:

   ```ini
   TELEGRAM_TOKEN=ваш_токен
   INSTAGRAM_USERNAME=логин
   INSTAGRAM_PASSWORD=пароль
   ```

3. Соберите Docker‑образ и запустите контейнер:

   ```bash
   docker build -t media-grabber-bot .
   docker run -d --name media_bot --env-file .env media-grabber-bot
   ```

4. Готово! Бот работает и ждёт ссылки.

---

## Локальный запуск без Docker

1. Создайте и активируйте виртуальное окружение:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Установите зависимости:

   ```bash
   pip install -r requirements.txt
   ```

3. Запустите бота:

   ```bash
   python main.py
   ```

---

## Команды бота

* `/start` — приветствие и инструкция
* `/help` — список команд
* Просто отправьте ссылку на медиа — бот скачает и пришлёт фото/видео.

---

## Логи и отладка

Логи выводятся в консоль. Для повышения уровня детализации редактируйте настройки в `logging.basicConfig`.

---

*Автор: вы*
