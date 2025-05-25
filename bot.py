import logging
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Настройки
TOKEN = "7302146730:AAH1leQBmTGUFSWoy8JnJX6EsgJESXJ9EYU"  # Замените на реальный токен!
DB_NAME = "diary.db"

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация БД
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            user_id INTEGER,
            date TEXT,
            message TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Команда /start
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    update.message.reply_text(
        f"📖 Привет, {user.first_name}! Я твой личный дневник.\n"
        "Доступные команды:\n"
        "/new_entry [текст] - добавить запись\n"
        "/date_search [дд.мм.гггг] - найти записи\n"
        "/profile - статистика"
    )

# Команда /new_entry
def new_entry(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    text = ' '.join(context.args)  # Объединяем аргументы в текст

    if not text:
        update.message.reply_text("❌ Напишите текст записи: /new_entry [текст]")
        return

    date = datetime.now().strftime("%d.%m.%Y")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO entries VALUES (?, ?, ?)", (user_id, date, text))
    conn.commit()
    conn.close()

    update.message.reply_text(f"✅ Запись за {date} сохранена!")

# Команда /date_search
def date_search(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if not context.args:
        update.message.reply_text("❌ Укажите дату: /date_search дд.мм.гггг")
        return

    date = context.args[0]
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT message FROM entries WHERE user_id=? AND date=?", (user_id, date))
    entries = cursor.fetchall()
    conn.close()

    if entries:
        response = f"📅 {date}:\n" + "\n".join([entry[0] for entry in entries])
    else:
        response = "Записей не найдено."
    update.message.reply_text(response)

# Команда /profile
def profile(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Первая запись
    cursor.execute("SELECT date FROM entries WHERE user_id=? ORDER BY date ASC LIMIT 1", (user_id,))
    first_date = cursor.fetchone()
    first_date = first_date[0] if first_date else "Нет записей"

    # Общее количество
    cursor.execute("SELECT COUNT(*) FROM entries WHERE user_id=?", (user_id,))
    total = cursor.fetchone()[0]

    conn.close()
    update.message.reply_text(
        f"👤 Ваш профиль:\n"
        f"📅 Первая запись: {first_date}\n"
        f"🔢 Всего записей: {total}"
    )

# Обработка ошибок
def error(update: Update, context: CallbackContext):
    logger.warning(f'Ошибка: {context.error}')

# Главная функция
def main():
    init_db()
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("new_entry", new_entry, pass_args=True))
    dp.add_handler(CommandHandler("date_search", date_search, pass_args=True))
    dp.add_handler(CommandHandler("profile", profile))
    dp.add_error_handler(error)

    # Запуск бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()