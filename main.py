import os import json from datetime import datetime from flask import Flask, request import telebot from telebot import types

ENV config

BOT_TOKEN = os.environ.get("BOT_TOKEN") ADMIN_ID = int(os.environ.get("ADMIN_ID", "123456")) BACKUP_PASSWORD = "wokolad"

bot = telebot.TeleBot(BOT_TOKEN) app = Flask(name)

Files

USERS_FILE = "users.json" TIMER_FILE = "timer.json" ORGANIZERS_FILE = "organizers.json"

Storage

user_states = {} users = {} organizers = [ADMIN_ID] timer_data = {"timestamp": None}

Utils

def load_json(filename, default): if os.path.exists(filename): with open(filename) as f: return json.load(f) return default

def save_json(filename, data): with open(filename, "w") as f: json.dump(data, f, indent=2)

users = load_json(USERS_FILE, {}) organizers = load_json(ORGANIZERS_FILE, [ADMIN_ID]) timer_data = load_json(TIMER_FILE, {"timestamp": None})

Footer info

FOOTER = "\n\n✨ Конкурс проводится на Minecraft сервере 24Mine\n🌐 IP: play.24mine.ru | 📱 Порт: 19133\n🔹 Версия: 0.14.x\n🥇 Главный приз: Донат-кейс\n👨‍🎓 Организатор: @wokolad"

Command /start

@bot.message_handler(commands=["start"]) def start_cmd(message): uid = message.from_user.id name = message.from_user.first_name or "Игрок" is_admin = uid in organizers text = f"✋ Привет, {name}!

🎓 Это бот для регистрации на конкурс Minecraft 0.14.x от @wokolad.

🌟 Ты можешь: • 🔢 /event — заполнить анкету для участия • 📜 /info — информация о конкурсе • 📢 /contact — связаться с организатором • 🔧 /help — список всех команд" if is_admin: text += "\n• 🛠️ /admin — админ-команды" bot.send_message(uid, text + FOOTER)

@bot.message_handler(commands=["help"]) def help_cmd(message): text = "❓ Все команды: /start — приветствие и инфо /info — информация о конкурсе /event — заполнить анкету /contact — связаться с организатором" if message.from_user.id in organizers: text += "\n\n🛠️ Админ-команды: /settimer — назначить/сбросить время /notify [всем/да/нет] текст — рассылка /promote ID — выдать админку /participants — участники /backup пароль — выгрузка базы" bot.send_message(message.chat.id, text + FOOTER)

@bot.message_handler(commands=["contact"]) def contact_cmd(message): bot.send_message(message.chat.id, "📢 Связь с организатором: https://t.me/feedback_for_event_bot" + FOOTER)

@bot.message_handler(commands=["info"]) def info_cmd(message): if timer_data["timestamp"]: dt = datetime.fromtimestamp(timer_data["timestamp"]) now = datetime.now() delta = dt - now time_text = f"🌇 Начало игры запланировано на {dt.strftime('%Y-%m-%d %H:%M')} ({dt.strftime('%A')})\n⏳ До начала: {delta.days} дн {delta.seconds // 3600} ч {(delta.seconds % 3600) // 60} мин" else: time_text = "⏰ Начало игры ещё не запланировано!" bot.send_message(message.chat.id, f"🎮 Конкурс от @wokolad\n{time_text}\n🎁 Главный приз: Донат-кейс" + FOOTER)

@bot.message_handler(commands=["event"]) def event_cmd(message): user_states[message.chat.id] = {"step": 1, "answers": {}} bot.send_message(message.chat.id, "👤 Какой у вас игровой ник на сервере 24mine? (до 25 символов)")

@bot.message_handler(commands=["admin"]) def admin_cmd(message): if message.from_user.id in organizers: text = "⚖️ Админ-панель: /settimer /notify [всем/да/нет] текст /promote ID /participants /backup пароль" bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["settimer"]) def settimer_cmd(message): if message.from_user.id in organizers: bot.send_message(message.chat.id, "🕒 Введите дату и время (ГГГГ-ММ-ДД ЧЧ:ММ) или 'сброс' для отмены") user_states[message.chat.id] = {"admin_timer": True}

@bot.message_handler(commands=["promote"]) def promote_cmd(message): if message.from_user.id in organizers: parts = message.text.split() if len(parts) == 2 and parts[1].isdigit(): new_admin = int(parts[1]) if new_admin not in organizers: organizers.append(new_admin) save_json(ORGANIZERS_FILE, organizers) bot.send_message(message.chat.id, f"✅ {new_admin} теперь организатор.")

@bot.message_handler(commands=["participants"]) def participants_cmd(message): if message.from_user.id in organizers: if not users: bot.send_message(message.chat.id, "😟 Участников нет.") return msg = "📄 Участники:\n" for uid, data in users.items(): msg += f"\n👤 @{data.get('username', '-')[:25]} (ID: {uid})" for k, v in data['answers'].items(): msg += f"\n• {k}: {v}" msg += "\n" bot.send_message(message.chat.id, msg)

@bot.message_handler(commands=["backup"]) def backup_cmd(message): if message.from_user.id in organizers: parts = message.text.split() if len(parts) == 2 and parts[1] == BACKUP_PASSWORD: with open(USERS_FILE) as f: content = f.read() bot.send_document(message.chat.id, ("users.json", content)) else: bot.send_message(message.chat.id, "❌ Неверный пароль")

@bot.message_handler(commands=["notify"]) def notify_cmd(message): if message.from_user.id in organizers: parts = message.text.split(" ", 2) if len(parts) < 3: return bot.send_message(message.chat.id, "❓ Пример: /notify да Привет") target, text = parts[1], parts[2] for uid, data in users.items(): answer = data["answers"].get("Будет участвовать", "").lower() if (target == "да" and "да" in answer) or (target == "нет" and "нет" in answer) or target == "всем": try: bot.send_message(int(uid), text + FOOTER) except: pass

Input handler

@bot.message_handler(func=lambda msg: msg.chat.id in user_states) def handle_state(msg): state = user_states[msg.chat.id]

if "admin_timer" in state:
    if msg.text.lower() == "сброс":
        timer_data["timestamp"] = None
        save_json(TIMER_FILE, timer_data)
        bot.send_message(msg.chat.id, "✅ Таймер сброшен")
    else:
        try:
            dt = datetime.strptime(msg.text, "%Y-%m-%d %H:%M")
            timer_data["timestamp"] = int(dt.timestamp())
            save_json(TIMER_FILE, timer_data)
            bot.send_message(msg.chat.id, f"✅ Таймер установлен на {dt}")
        except:
            bot.send_message(msg.chat.id, "❌ Неверный формат. Пример: 2025-07-10 18:30")
    user_states.pop(msg.chat.id)
    return

step = state.get("step")
if step == 1:
    if len(msg.text) > 25:
        return bot.send_message(msg.chat.id, "❌ Ник не должен превышать 25 символов")
    state["answers"]["Игровой ник"] = msg.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Да, хочу зарегистрироваться", "Нет", "Подумаю")
    bot.send_message(msg.chat.id, "📝 Вы хотите зарегистрироваться на конкурс?", reply_markup=markup)
    state["step"] = 2
elif step == 2:
    state["answers"]["Регистрация"] = msg.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Буду участвовать", "Не буду", "Подумаю", "Смотря во сколько")
    bot.send_message(msg.chat.id, "❓ Вы будете участвовать в конкурсе?", reply_markup=markup)
    state["step"] = 3
elif step == 3:
    state["answers"]["Будет участвовать"] = msg.text
    bot.send_message(msg.chat.id, "🌍 С какого региона вы будете участвовать? (Напишите страну)", reply_markup=types.ReplyKeyboardRemove())
    state["step"] = 4
elif step == 4:
    state["answers"]["Регион"] = msg.text
    users[str(msg.from_user.id)] = {
        "username": msg.from_user.username or "-",
        "answers": state["answers"]
    }
    save_json(USERS_FILE, users)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("✅ Подтвердить", "❌ Отмена", "✏️ Изменить анкету")
    bot.send_message(msg.chat.id, "🚀 Ваша анкета сохранена. Что дальше?", reply_markup=markup)
    user_states.pop(msg.chat.id)

Flask webhook

@app.route("/", methods=["GET"]) def index(): return "Bot is running"

@app.route("/", methods=["POST"]) def webhook(): update = telebot.types.Update.de_json(request.data.decode("utf-8")) bot.process_new_updates([update]) return "ok", 200

if name == "main": port = int(os.environ.get("PORT", 8080)) app.run(host="0.0.0.0", port=port)
