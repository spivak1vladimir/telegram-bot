# --- coding: utf-8 ---
import os
import json
import logging
from datetime import time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ------------------ НАСТРОЙКИ ------------------
TOKEN = "8222360016:AAHAqa7gsBxpP9mN0d98XB7LNvapjUukNds"
ADMIN_CHAT_ID = 194614510
MAX_SLOTS = 12
DATA_FILE = "registered_users.json"

ROUTE_LINK = "https://yandex.ru/maps/-/CLXsMV-x"

RUN_DATE = "8 января"
RUN_TIME = "10:30"

WARNING_TEXT = (
    "Напоминание о пробежке.\n\n"
    f"Дата: {RUN_DATE}\n"
    f"Старт: {RUN_TIME}\n"
    "Место старта:\n"
    "Ул. Старокирочный переулок, 16/2с1\n\n"
    f"Маршрут:\n{ROUTE_LINK}"
)

# ------------------ ЛОГИ ------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ------------------ ХРАНЕНИЕ ------------------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"6km": []}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

# ------------------ START ------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Пробежка от КАРОЧЕ КОФЕ\n\n"
        "Место старта:\n"
        "Ул. Старокирочный переулок, 16/2с1\n\n"
        f"Дата: {RUN_DATE}\n"
        "Сбор: 10:00\n"
        f"Старт: {RUN_TIME}\n\n"
        "Дистанция:\n"
        "6 км — темп 7:30–7:00\n\n"
        f"Маршрут:\n{ROUTE_LINK}"
    )

    keyboard = [
        [InlineKeyboardButton("Зарегистрироваться (6 км)", callback_data="reg_6")],
        [InlineKeyboardButton("Информация о забеге", callback_data="info")]
    ]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ------------------ ИНФОРМАЦИЯ ------------------
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = (
        "Условия участия:\n"
        "Ответственность за жизнь и здоровье\n"
        "Ответственность за личные вещи\n"
        "Согласие на обработку данных\n"
        "Согласие на фото и видео съемку\n\n"
        f"Маршрут:\n{ROUTE_LINK}"
    )

    await query.edit_message_text(text)

# ------------------ РЕГИСТРАЦИЯ ------------------
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    users = data["6km"]

    if user.id in users:
        position = users.index(user.id) + 1
        await query.edit_message_text(
            f"Вы уже зарегистрированы.\nВаша позиция: {position}"
        )
        return

    users.append(user.id)
    save_data()

    position = len(users)
    is_main = position <= MAX_SLOTS
    status = "Основной состав" if is_main else "Лист ожидания"

    admin_text = (
        "Новый игрок!\n\n"
        f"Имя: {user.first_name}\n"
        f"Фамилия: {user.last_name or 'не указана'}\n"
        f"Username: @{user.username if user.username else 'нет'}\n"
        f"ID: {user.id}\n"
        f"Язык: {user.language_code}\n"
        f"Бот: {'Да' if user.is_bot else 'Нет'}\n"
        f"Статус: {status}\n"
        f"Позиция: {position}"
    )
