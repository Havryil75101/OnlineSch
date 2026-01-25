import telebot
import time
import json
from telebot import types
from config import TG_BOT_TOKEN

bot = telebot.TeleBot(TG_BOT_TOKEN)

ADMIN_ID = 5578984865


def load_schedule():
    with open("schedule.json", "r", encoding="utf-8") as f:
        return json.load(f)


schedule = load_schedule()


def inline_menu():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("📘 Понедельник", callback_data="mon"),
        types.InlineKeyboardButton("📗 Вторник", callback_data="tue"),
        types.InlineKeyboardButton("📙 Среда", callback_data="wed"),
        types.InlineKeyboardButton("📕 Четверг", callback_data="thu"),
        types.InlineKeyboardButton("📒 Пятница", callback_data="fri"),
        types.InlineKeyboardButton("📓 Суббота", callback_data="sat"),
        types.InlineKeyboardButton("📔 Воскресенье", callback_data="sun")
    )
    return keyboard


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_chat_action(message.chat.id, 'typing')
    time.sleep(1)
    bot.send_message(message.chat.id, "👋 Выбери день недели 👇", reply_markup=inline_menu())


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    lessons = schedule.get(call.data, [])
    day_names = {
        "mon": "📘 Понедельник",
        "tue": "📗 Вторник",
        "wed": "📙 Среда",
        "thu": "📕 Четверг",
        "fri": "📒 Пятница",
        "sat": "📓 Суббота",
        "sun": "📔 Воскресенье"
    }

    if not lessons:
        text = f"{day_names[call.data]}\n\n❌ Занятий нет"
    else:
        text = f"{day_names[call.data]}\n\n" + "\n".join(lessons)

    bot.send_message(call.message.chat.id, text)


@bot.message_handler(commands=['reload'])
def reload_json(message):
    global schedule

    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ У тебя нет прав")
        return

    try:
        schedule = load_schedule()
        bot.send_message(message.chat.id, "✅ Расписание успешно обновлено")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка загрузки:\n{e}")


bot.infinity_polling()
