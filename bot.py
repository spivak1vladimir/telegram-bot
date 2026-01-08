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

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=admin_text
    )

    if is_main:
        user_text = (
            "Регистрация подтверждена.\n"
            "Дистанция: 6 км\n"
            f"Ваш номер: {position}/{MAX_SLOTS}"
        )
    else:
        user_text = (
            "Основные места заняты.\n"
            "Вы добавлены в лист ожидания.\n"
            f"Позиция в очереди: {position - MAX_SLOTS}"
        )

    keyboard = [[InlineKeyboardButton("Отменить участие", callback_data="cancel")]]
    await query.edit_message_text(
        user_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ------------------ ОТМЕНА ------------------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id in data["6km"]:
        data["6km"].remove(user_id)
        save_data()
        await query.edit_message_text("Регистрация отменена.")
        return

    await query.edit_message_text("Вы не были зарегистрированы.")

# ------------------ АДМИНКА ------------------
async def admin_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID:
        return

    users = data["6km"]

    if not users:
        await update.message.reply_text("Список участников пуст.")
        return

    text = "Участники 6 км:\n\n"
    for i, user_id in enumerate(users, start=1):
        text += f"{i}. ID: {user_id}\n"

    await update.message.reply_text(text)

# ------------------ НАПОМИНАНИЕ ------------------
async def send_warning(context: ContextTypes.DEFAULT_TYPE):
    users = data["6km"]

    for user_id in users:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=WARNING_TEXT,
                connect_timeout=10,
                read_timeout=10,
                write_timeout=10
            )
        except Exception as e:
            logger.warning(f"Ошибка отправки пользователю {user_id}: {e}")

# ------------------ ЗАПУСК ------------------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_list))
    app.add_handler(CallbackQueryHandler(register, pattern="reg_6"))
    app.add_handler(CallbackQueryHandler(info, pattern="info"))
    app.add_handler(CallbackQueryHandler(cancel, pattern="cancel"))

    # Напоминание каждый день в 00:30
    app.job_queue.run_daily(
        send_warning,
        time=time(hour=0, minute=30)
    )

    app.run_polling()

if __name__ == "__main__":
    main()
