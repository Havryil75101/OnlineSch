import telebot
from telebot import types
from config import TG_BOT_TOKEN
from bd import Database

bot = telebot.TeleBot(TG_BOT_TOKEN)
db = Database()

# ===== ХРАНЕНИЕ СООБЩЕНИЙ БОТА =====
bot_messages = {}

# ===== Статические данные =====
DAYS = ["mon","tue","wed","thu","fri","sat","sun"]
DAY_NAMES = {
    "mon":"Понедельник","tue":"Вторник","wed":"Среда",
    "thu":"Четверг","fri":"Пятница","sat":"Суббота","sun":"Воскресенье"
}
DAY_EMOJI = {
    "mon":"📘","tue":"📗","wed":"📙","thu":"📕","fri":"📒","sat":"📓","sun":"📔"
}

# ===== КНОПКА ВНИЗУ =====
def bottom_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton("🧹 Очистить чат"))
    return kb

# ===== Меню классов =====
def classes_menu(page=0, per_page=8):
    kb = types.InlineKeyboardMarkup(row_width=4)
    all_classes = [f"{i}{l}" for i in range(1,11) for l in ["A","B"]]
    start = page * per_page
    for cls in all_classes[start:start+per_page]:
        kb.add(types.InlineKeyboardButton(cls, callback_data=f"class_{cls}"))
    if start + per_page < len(all_classes):
        kb.add(types.InlineKeyboardButton("➡️", callback_data=f"class_next_{page+1}"))
    if page > 0:
        kb.add(types.InlineKeyboardButton("⬅️", callback_data=f"class_prev_{page-1}"))
    return kb

# ===== Меню дней =====
def days_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    for d in DAYS:
        kb.add(types.InlineKeyboardButton(f"{DAY_EMOJI[d]} {DAY_NAMES[d]}", callback_data=f"day_{d}"))
    return kb

# ===== /start =====
@bot.message_handler(commands=['start'])
def start(message):
    msg = bot.send_message(
        message.chat.id,
        "Привет. Я бот который тебе подскажет твое росписание!!!🏫 Выбери класс 👇",
        reply_markup=bottom_menu()
    )
    bot_messages.setdefault(message.chat.id, []).append(msg.message_id)

    msg2 = bot.send_message(
        message.chat.id,
        "Нажми на нужный класс:",
        reply_markup=classes_menu()
    )
    bot_messages[message.chat.id].append(msg2.message_id)

# ===== CALLBACK =====
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    # ===== Выбор класса =====
    if call.data.startswith("class_") and not call.data.startswith("class_next_") and not call.data.startswith("class_prev_"):
        cls = call.data.replace("class_","")
        db.set_user_class(user_id, cls)

        msg = bot.send_message(
            chat_id,
            f"✅ Класс *{cls}* выбран\n📅 Выбери день недели 👇",
            parse_mode="Markdown",
            reply_markup=days_menu()
        )
        bot_messages.setdefault(chat_id, []).append(msg.message_id)

    # ===== Пагинация =====
    elif call.data.startswith("class_next_"):
        page = int(call.data.split("_")[-1])
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=classes_menu(page))

    elif call.data.startswith("class_prev_"):
        page = int(call.data.split("_")[-1])
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=classes_menu(page))

    # ===== Выбор дня =====
    elif call.data.startswith("day_"):
        day = call.data.replace("day_","")
        cls = db.get_user_class(user_id)

        if not cls:
            msg = bot.send_message(chat_id, "❗ Сначала выбери класс")
            bot_messages.setdefault(chat_id, []).append(msg.message_id)
            return

        lessons = db.get_schedule(cls, day)
        text = f"🏫 *{cls}*\n📅 *{DAY_NAMES[day]}*\n\n"

        if lessons:
            for num, lesson in lessons:
                text += f"{num}️⃣ {lesson}\n"
        else:
            text += "❌ Занятий нет"

        msg = bot.send_message(chat_id, text, parse_mode="Markdown")
        bot_messages.setdefault(chat_id, []).append(msg.message_id)

# ===== ОЧИСТКА ЧАТА =====
@bot.message_handler(func=lambda m: m.text == "🧹 Очистить чат")
def clear_chat(message):
    chat_id = message.chat.id

    for msg_id in bot_messages.get(chat_id, []):
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass

    bot_messages[chat_id] = []

    try:
        bot.delete_message(chat_id, message.message_id)
    except:
        pass

# ===== АДМИН =====
@bot.message_handler(commands=['addlesson'])
def add_lesson(message):
    if not db.is_admin(message.from_user.id):
        bot.send_message(message.chat.id,"⛔ Нет прав")
        return

    try:
        _, cls, day, num, lesson = message.text.split(maxsplit=4)
        num = int(num)
        if day not in DAYS:
            raise ValueError
    except:
        bot.send_message(message.chat.id,"❗ /addlesson 5A mon 1 Математика")
        return

    db.add_lesson(cls, day, num, lesson)
    bot.send_message(message.chat.id,"✅ Урок добавлен")

# ===== ЗАПУСК =====
bot.infinity_polling()

