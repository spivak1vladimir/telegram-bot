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
            return set(json.load(f))
    return set()


def save_users(users):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(list(users), f, ensure_ascii=False)


registered_users = load_users()


# ------------------------ ОБРАБОТКА КОМАНД ------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/start — user_id={update.effective_user.id}")

    text = (
        "Ты присоединился к субботней пробежке Spivak Run.\n"
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

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    user_id = user.id

    logger.info(f"Register attempt — user_id={user_id}")

    # Мест нет
    if len(registered_users) >= MAX_SLOTS:
        logger.info("Registration denied — no slots left")
        await query.edit_message_text("Все 12 мест уже заняты.")
        return

    # Уже зарегистрирован
    if user_id in registered_users:
        pos = list(registered_users).index(user_id) + 1
        logger.info(f"User already registered — pos={pos}")
        await query.edit_message_text(f"Ты уже зарегистрирован. Твой номер: {pos}/12")
        return

    # Новая регистрация
    registered_users.add(user_id)
    save_users(registered_users)
    position = len(registered_users)

    username_link = f"@{user.username}" if user.username else "(нет username)"

    logger.info(f"User registered — user_id={user_id}, pos={position}")

    # Уведомление админу (ссылка на профиль)
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=(
            "Новый участник субботней пробежки!\n\n"
            f"Имя: {user.first_name}\n"
            f"Username: {username_link}\n"
            f"ID: {user.id}\n"
            f"Позиция: {position}/12"
        )
    )

    # Сообщение пользователю + кнопка отмены
    keyboard = [[InlineKeyboardButton("Отменить участие", callback_data="cancel")]]
    await context.bot.send_message(
        chat_id=user_id,
        text=f"Ты зарегистрирован. Твой номер: {position}/12",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await query.edit_message_text(f"Готово. Твой номер: {position}/12")


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
