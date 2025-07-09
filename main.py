import os
import json
from datetime import datetime
from flask import Flask, request
import telebot

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "123456"))

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

USERS_FILE = "users.json"
TIMER_FILE = "timer.json"
ORGANIZERS_FILE = "organizers.json"

# Загрузка или создание данных
def load_json(filename, default):
    if os.path.exists(filename):
        with open(filename) as f:
            return json.load(f)
    return default

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

users = load_json(USERS_FILE, {})
organizers = load_json(ORGANIZERS_FILE, [ADMIN_ID])
timer_data = load_json(TIMER_FILE, {"timestamp": None})

user_states = {}

# Команды
@bot.message_handler(commands=["start"])
def cmd_start(message):
    uid = message.from_user.id
    name = message.from_user.first_name or "Игрок"
    role = "Вы организатор. Вам доступны админ-команды." if uid in organizers else "Вы игрок."
    bot.send_message(uid, f"👋 Здравствуйте, {name}!\n{role}")

@bot.message_handler(commands=["help"])
def cmd_help(message):
    text = "📖 Команды:\n/start — начать\n/help — помощь\n/info — инфо о конкурсе\n/event — регистрация\n/contact — связь с оргом\n/admin — админ-команды (только для организаторов)"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["info"])
def cmd_info(message):
    if timer_data["timestamp"]:
        event_time = datetime.fromtimestamp(timer_data["timestamp"])
        now = datetime.now()
        delta = event_time - now
        if delta.total_seconds() > 0:
            h = delta.seconds // 3600
            m = (delta.seconds % 3600) // 60
            t = f"⏳ До начала: {delta.days} дн {h} ч {m} мин"
        else:
            t = "🎉 Конкурс уже начался!"
    else:
        t = "⏳ Таймер ещё не установлен."
    text = f"🎮 Конкурс от wokolad\n🌐 Сервер: play.24mine.ru\n📱 Порт: 19133\n🧩 Версия: 0.14.x\n🎁 Приз: донат кейс\n{t}"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["contact"])
def cmd_contact(message):
    bot.send_message(message.chat.id, "📩 Напишите организатору: https://t.me/feedback_for_event_bot")

@bot.message_handler(commands=["event"])
def cmd_event(message):
    user_states[message.chat.id] = {"step": 1, "answers": {}}
    bot.send_message(message.chat.id, "📝 Как тебя зовут?")

# Админ команды
@bot.message_handler(commands=["admin"])
def cmd_admin(message):
    if message.from_user.id not in organizers:
        return
    text = "🛠 Админ-команды:\n/settimer — установить таймер\n/participants — список участников\n/promote ID — выдать права организатора"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["settimer"])
def cmd_settimer(message):
    if message.from_user.id not in organizers:
        return
    bot.send_message(message.chat.id, "🕓 Введи дату и время начала (ГГГГ-ММ-ДД ЧЧ:ММ)")
    user_states[message.chat.id] = {"admin_timer": True}

@bot.message_handler(commands=["participants"])
def cmd_participants(message):
    if message.from_user.id not in organizers:
        return
    if not users:
        bot.send_message(message.chat.id, "😢 Нет участников.")
        return
    msg = "🧾 Участники:\n"
    for uid, data in users.items():
        msg += f"👤 @{data.get('username', 'без username')} (ID: {uid})\n"
        for k, v in data['answers'].items():
            msg += f"• {k}: {v}\n"
        msg += "\n"
    bot.send_message(message.chat.id, msg)

@bot.message_handler(commands=["promote"])
def cmd_promote(message):
    if message.from_user.id not in organizers:
        return
    parts = message.text.split()
    if len(parts) == 2 and parts[1].isdigit():
        new_admin = int(parts[1])
        if new_admin not in organizers:
            organizers.append(new_admin)
            save_json(ORGANIZERS_FILE, organizers)
            bot.send_message(message.chat.id, f"✅ {new_admin} теперь организатор.")
    else:
        bot.send_message(message.chat.id, "❗ Пример: /promote 123456789")

# Ответы пользователя
@bot.message_handler(func=lambda m: m.chat.id in user_states)
def handle_state(msg):
    state = user_states[msg.chat.id]

    if "admin_timer" in state:
        try:
            dt = datetime.strptime(msg.text, "%Y-%m-%d %H:%M")
            timer_data["timestamp"] = int(dt.timestamp())
            save_json(TIMER_FILE, timer_data)
            bot.send_message(msg.chat.id, f"✅ Таймер установлен: {dt}")
        except:
            bot.send_message(msg.chat.id, "❌ Формат неверный. Пример: 2025-07-10 18:30")
        user_states.pop(msg.chat.id)
        return

    step = state["step"]
    if step == 1:
        state["answers"]["Имя"] = msg.text
        bot.send_message(msg.chat.id, "Ты придешь на конкурс? (Да / Нет / Не знаю)")
        state["step"] = 2
    elif step == 2:
        state["answers"]["Придёт"] = msg.text
        bot.send_message(msg.chat.id, "Откуда ты?")
        state["step"] = 3
    elif step == 3:
        state["answers"]["Место"] = msg.text
        users[str(msg.from_user.id)] = {
            "username": msg.from_user.username or "-",
            "answers": state["answers"]
        }
        save_json(USERS_FILE, users)
        bot.send_message(msg.chat.id, "🎉 Спасибо! Ты зарегистрирован.")
        user_states.pop(msg.chat.id)

# Flask (для webhook)
@app.route("/", methods=["GET"])
def index():
    return "Bot is running"

@app.route("/", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.data.decode("utf-8"))
    bot.process_new_updates([update])
    return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
