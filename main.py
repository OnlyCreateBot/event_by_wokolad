import os import json from datetime import datetime from flask import Flask, request import telebot

Получение переменных окружения

BOT_TOKEN = os.environ.get("BOT_TOKEN")  # безопаснее, чем писать токен в коде ADMIN_ID = int(os.environ.get("ADMIN_ID", "123456789"))  # по умолчанию 123456789

bot = telebot.TeleBot(BOT_TOKEN) app = Flask(name)

Пути к файлам

USERS_FILE = "users.json" TIMER_FILE = "timer.json" ORGANIZERS_FILE = "organizers.json"

Загрузка данных

if os.path.exists(USERS_FILE): with open(USERS_FILE) as f: users = json.load(f) else: users = {}

if os.path.exists(ORGANIZERS_FILE): with open(ORGANIZERS_FILE) as f: organizers = json.load(f) else: organizers = [ADMIN_ID]

if os.path.exists(TIMER_FILE): with open(TIMER_FILE) as f: timer_data = json.load(f) else: timer_data = {"timestamp": None}

user_states = {}

/start

@bot.message_handler(commands=["start"]) def cmd_start(message): uid = message.from_user.id name = message.from_user.first_name or "Игрок" is_admin = uid in organizers role = "Вы организатор игры. Вам доступны все команды." if is_admin else "Вы игрок." bot.send_message(uid, f"Здравствуйте, {name}!\n{role}")

/help

@bot.message_handler(commands=["help"]) def cmd_help(message): help_text = ( "\U0001F4D6 Команды:\n" "/start – Приветствие\n" "/help – Все команды\n" "/info – Информация о конкурсе\n" "/contact – Связь с организатором\n" "/event – Запись на конкурс" ) if message.from_user.id in organizers: help_text += "\n(Скрытые админ-команды доступны через /admin)" bot.send_message(message.chat.id, help_text)

/info

@bot.message_handler(commands=["info"]) def cmd_info(message): if timer_data["timestamp"]: event_time = datetime.fromtimestamp(timer_data["timestamp"]) now = datetime.now() delta = event_time - now if delta.total_seconds() > 0: days = delta.days hours = delta.seconds // 3600 minutes = (delta.seconds % 3600) // 60 timer_text = f"\u23F3 До начала конкурса: {days} дн {hours} ч {minutes} мин" else: timer_text = "\U0001F389 Конкурс уже начался!" else: timer_text = "\u23F3 До начала конкурса: Скоро"

info = (
    "\U0001F3AE Конкурс от wokolad\n"
    "\U0001F310 Сервер: play.24mine.ru\n"
    "\U0001F4F1 Порт: 19133\n"
    "\U0001F9E9 Версия: Minecraft PE 0.14.x\n"
    "\U0001F381 Приз: Донат кейс\n"
    f"{timer_text}"
)
bot.send_message(message.chat.id, info)

/contact

@bot.message_handler(commands=["contact"]) def cmd_contact(message): bot.send_message(message.chat.id, "\U0001F4E9 Связь с организатором: https://t.me/feedback_for_event_bot")

/event (регистрация)

@bot.message_handler(commands=["event"]) def cmd_event(message): bot.send_message(message.chat.id, "\U0001F4DD Как тебя зовут?") user_states[message.chat.id] = {"step": 1, "answers": {}}

/admin

@bot.message_handler(commands=["admin"]) def cmd_admin(message): if message.from_user.id not in organizers: return text = ( "\U0001F6E0 Админ-команды:\n" "/settimer – Установить дату и время конкурса\n" "/participants – Список всех участников\n" "/promote ID – Повысить до организатора" ) bot.send_message(message.chat.id, text)

/settimer

@bot.message_handler(commands=["settimer"]) def cmd_settimer(message): if message.from_user.id not in organizers: return bot.send_message(message.chat.id, "\U0001F4C5 Введи дату и время (ГГГГ-ММ-ДД ЧЧ:ММ)") user_states[message.chat.id] = {"admin_timer": True}

/participants

@bot.message_handler(commands=["participants"]) def cmd_participants(message): if message.from_user.id not in organizers: return text = "\U0001F4CB Список участников:\n" for uid, data in users.items(): text += f"\n\U0001F464 @{data.get('username', '-')}, ID: {uid}\n" for k, v in data['answers'].items(): text += f"• {k}: {v}\n" bot.send_message(message.chat.id, text or "Участников нет")

/promote

@bot.message_handler(commands=["promote"]) def cmd_promote(message): if message.from_user.id not in organizers: return parts = message.text.split() if len(parts) != 2: bot.send_message(message.chat.id, "❗ Используй: /promote 123456789") return try: new_admin = int(parts[1]) if new_admin not in organizers: organizers.append(new_admin) with open(ORGANIZERS_FILE, "w") as f: json.dump(organizers, f) bot.send_message(message.chat.id, f"✅ Пользователь {new_admin} теперь организатор") else: bot.send_message(message.chat.id, "Уже организатор") except: bot.send_message(message.chat.id, "❌ Ошибка в ID")

Обработка состояний (регистрация и установка таймера)

@bot.message_handler(func=lambda msg: msg.chat.id in user_states) def handle_state(msg): state = user_states[msg.chat.id] if "admin_timer" in state: try: dt = datetime.strptime(msg.text, "%Y-%m-%d %H:%M") timer_data["timestamp"] = int(dt.timestamp()) with open(TIMER_FILE, "w") as f: json.dump(timer_data, f) bot.send_message(msg.chat.id, f"✅ Таймер установлен: {dt}") except: bot.send_message(msg.chat.id, "❌ Неверный формат. Пример: 2025-07-10 18:30") user_states.pop(msg.chat.id) return

step = state.get("step")
if step == 1:
    state["answers"]["Имя"] = msg.text
    bot.send_message(msg.chat.id, "✅ Ты придёшь на конкурс? (Да / Нет / Не знаю)")
    state["step"] = 2
elif step == 2:
    state["answers"]["Придёт"] = msg.text
    bot.send_message(msg.chat.id, "🌍 Откуда ты?")
    state["step"] = 3
elif step == 3:
    state["answers"]["Место"] = msg.text
    users[str(msg.from_user.id)] = {
        "username": msg.from_user.username or "-",
        "answers": state["answers"]
    }
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)
    bot.send_message(msg.chat.id, "🎉 Спасибо, ты зарегистрирован!")
    user_states.pop(msg.chat.id)

Flask endpoints

@app.route("/", methods=["GET"]) def home(): return "Bot is running!"

@app.route("/", methods=["POST"]) def webhook(): update = telebot.types.Update.de_json(request.data.decode("utf-8")) bot.process_new_updates([update]) return "ok", 200

Запуск

if name == "main": app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
