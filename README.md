# 🤖 AnonBot ULTIMATE

> Telegram-бот анонимных вопросов с Mini App, PostgreSQL, реакциями и анонимным чатом.

![Python](https://img.shields.io/badge/python-3.12-blue)
![aiogram](https://img.shields.io/badge/aiogram-3.15-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![Docker](https://img.shields.io/badge/Docker-ready-green)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Возможности

### Для пользователя
- 💬 Отправить анонимный вопрос (текст / фото / видео / голос / файл / стикер)
- 📩 Получить ответ от владельца
- ❤️🔥😍 Реагировать на ответ
- 💬 Начать анонимный чат с владельцем
- 📊 `/myreactions` — свои реакции

### Для владельца
- 👑 Красивое инлайн-меню
- 📥 Входящие / 📚 Все вопросы с пагинацией
- ✍️ Ответ, 🕒 отложенный ответ
- 🏆 Топ по реакциям
- 📊 Статистика + 📈 график активности
- 📤 CSV-экспорт
- 📢 Рассылка по всем пользователям
- 🤖 Автоответ новым пользователям
- 🌐 RU / EN
- 🌐 Mini App (WebApp) с графиками
- 💬 Анонимный чат с автором вопроса

### Технически
- 🗄️ PostgreSQL 16 + индексы
- 🧠 Redis для FSM (опционально)
- 🔒 Проверка подписи WebApp initData
- 🐳 Docker + docker-compose
- 🔐 Nginx + Let's Encrypt HTTPS
- 💾 Автобэкап БД каждый день в 03:00
- 🩺 Healthcheck-и
- 📝 Логи в консоль + файл

---

## 🚀 Быстрый старт

### Вариант 1: Локально (без Docker)

```bash
# 1. Клонировать
git clone <repo> && cd anonbot

# 2. Виртуальное окружение
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Зависимости
pip install -r requirements.txt

# 4. PostgreSQL локально
sudo -u postgres createdb anonbot
sudo -u postgres psql anonbot < init.sql

# 5. .env
cp .env.example .env
nano .env   # BOT_TOKEN, OWNER_IDS, DATABASE_URL

# 6. Запуск
python run.py              # только бот
python run.py webapp       # только Mini App
python run.py all          # всё вместе