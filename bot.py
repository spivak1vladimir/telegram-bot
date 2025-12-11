# --- coding: utf-8 ---
import os
import json
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ------------------ ЛОГИРОВАНИЕ ------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
# --------------------------------------------------

TOKEN = "8222360016:AAHAqa7gsBxpP9mN0d98XB7LNvapjUukNds"
ADMIN_CHAT_ID = 194614510
MAX_SLOTS = 12
DATA_FILE = "registered_users.json"


# ------------------ ХРАНЕНИЕ ПОЛЬЗОВАТЕЛЕЙ ------------------

def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_users(users):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False)


registered_users = load_users()  # список, а не set — важен порядок


# ------------------------ ОБРАБОТКА КОМАНД ------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/start — user_id={update.effective_user.id}")

    text = (
        "Мы выбегаем из заведения *Короче Кофе* на Бауманской.\n"
        "📍 Сбор в *10:00*\n"
        "🏃 Старт в *10:30*\n"
        "📏 Дистанция: *5 км*\n"
        "⏱ Темп: *7:00 мин/км*\n\n"
        "Ты присоединился к субботней пробежке *Spivak Run*.\n\n"
        "Пожалуйста, ознакомься с условиями участия:\n\n"
        "- Ответственность за жизнь и здоровье.\n"
        "- Ответственность за свои вещи.\n"
        "- Согласие на обработку персональных данных.\n"
        "- Согласие на фото/видео съёмку.\n\n"
        "Если согласен — нажми кнопку ниже."
    )

    keyboard = [[
        InlineKeyboardButton("Принимаю и бегу", callback_data="register"),
        InlineKeyboardButton("Отменить", callback_data="cancel")
    ]]

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    user_id = user.id

    logger.info(f"Register attempt — user_id={user_id}")

    # Уже зарегистрирован
    if user_id in registered_users:
        pos = registered_users.index(user_id) + 1

        if pos <= MAX_SLOTS:
            text = f"Ты уже зарегистрирован. Твой номер: {pos}/{MAX_SLOTS}"
        else:
            text = f"Ты в листе ожидания. Твоя позиция: {pos} (после {MAX_SLOTS} основных)"

        await query.edit_message_text(text)
        return

    # Новая регистрация
    registered_users.append(user_id)
    save_users(registered_users)
    position = len(registered_users)

    username_link = f"@{user.username}" if user.username else "(нет username)"
    is_main = position <= MAX_SLOTS

    logger.info(f"User registered — user_id={user_id}, pos={position}")

    # Сообщение админу
    admin_text = (
        "Новый участник пробежки!\n\n"
        f"Имя: {user.first_name}\n"
        f"Username: {username_link}\n"
        f"ID: {user.id}\n"
        f"Статус: {'Основной' if is_main else 'Лист ожидания'}\n"
        f"Позиция: {position}"
    )

    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_text)

    # Сообщение пользователю
    if is_main:
        user_text = f"Ты зарегистрирован! Твой номер: {position}/{MAX_SLOTS}"
    else:
        user_text = (
            "Основные 12 мест уже заняты.\n"
            f"Ты добавлен в лист ожидания.\n"
            f"Твоя позиция: {position} (ты — номер {position - MAX_SLOTS} в очереди)"
        )

    keyboard = [[InlineKeyboardButton("Отменить участие", callback_data="cancel")]]

    await context.bot.send_message(
        chat_id=user_id,
        text=user_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await query.edit_message_text(user_text)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    logger.info(f"Cancel attempt — user_id={user_id}")

    if user_id in registered_users:
        registered_users.remove(user_id)
        save_users(registered_users)

        logger.info(f"User canceled — user_id={user_id}")
        await query.edit_message_text("Ты отменил участие в пробежке.")
    else:
        logger.info(f"Cancel rejected — user not registered (user_id={user_id})")
        await query.edit_message_text("Ты не был зарегистрирован.")


# ---------------------------- ЗАПУСК БОТА ----------------------------

def main():
    logger.info("Bot starting…")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(register, pattern="register"))
    app.add_handler(CallbackQueryHandler(cancel, pattern="cancel"))

    logger.info("Bot running (polling)…")
    print("Бот запущен…")
    app.run_polling()


if __name__ == "__main__":
    main()
