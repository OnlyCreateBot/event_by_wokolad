import os import json from datetime import datetime from flask import Flask, request import telebot from telebot import types

BOT_TOKEN = os.environ.get("BOT_TOKEN") ADMIN_ID = int(os.environ.get("ADMIN_ID", "123456")) ADMIN_PASSWORD = "wokolad"

bot = telebot.TeleBot(BOT_TOKEN) app = Flask(name)

USERS_FILE = "users.json" TIMER_FILE = "timer.json" ORGANIZERS_FILE = "organizers.json"

Загрузка/сохранение JSON

def load_json(filename, default): if os.path.exists(filename): with open(filename, encoding="utf-8") as f: return json.load(f) return default

def save_json(filename, data): with open(filename, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False)

users = load_json(USERS_FILE, {}) organizers = load_json(ORGANIZERS_FILE, [ADMIN_ID]) timer_data = load_json(TIMER_FILE, {"timestamp": None})

user_states = {}

FOOTER = ("\n\n⭐ Конкурс проводится на сервере 24mine (Minecraft PE 0.14.x)" "\n🏠 IP: play.24mine.ru, 🔗 Порт: 19133" "\n🏆 Главный приз: Донат-кейс" "\n🔸 Организатор: @wokolad")

@bot.message_handler(commands=["start"]) def cmd_start(message): uid = message.from_user.id name = message.from_user.first_name or "Игрок" is_admin = uid in organizers role = "🚀 Вы организатор. Вам доступны команды администратора." if is_admin else "🏋️ Вы участник." bot.send_message(uid, f"👋 Здравствуйте, {name}!\n{role}\n\n✉️ Напишите /help чтобы увидеть команды.{FOOTER}")

@bot.message_handler(commands=["help"]) def cmd_help(message): text = "📖 Команды:\n" text += "/start — перезапуск бота\n" text += "/help — список команд\n" text += "/info — подробная информация о конкурсе\n" text += "/event — заполнить анкету для участия\n" text += "/edit — изменить анкету\n" text += "/delete — удалить анкету\n" text += "/contact — связаться с организатором\n" if message.from_user.id in organizers: text += "\n🔧 Админ-команды:\n" text += "/settimer — установить время начала конкурса\n" text += "/removetimer — удалить время конкурса\n" text += "/participants — список участников\n" text += "/promote ID — выдать права организатора\n" text += "/removeadmin ID — удалить организатора\n" text += "/notify_all ТЕКСТ — уведомить всех\n" text += "/notify_interested ТЕКСТ — уведомить заинтересованных\n" text += "/notify_uninterested ТЕКСТ — уведомить незаинтересованных\n" text += "/backup wokolad — сохранить резервную копию пользователей" bot.send_message(message.chat.id, text + FOOTER)

@bot.message_handler(commands=["info"]) def cmd_info(message): if timer_data["timestamp"]: event_time = datetime.fromtimestamp(timer_data["timestamp"]) now = datetime.now() delta = event_time - now if delta.total_seconds() > 0: t = f"🕒 Начало запланировано на {event_time.strftime('%Y-%m-%d %H:%M')}\n⏳ Осталось: {delta.days} дн {(delta.seconds // 3600)} ч" else: t = "🎉 Конкурс уже начался!" else: t = "❓ Начало игры ещё не запланировано." bot.send_message(message.chat.id, f"🎮 Конкурс от @wokolad\n\n{t}{FOOTER}")

@bot.message_handler(commands=["contact"]) def cmd_contact(message): bot.send_message(message.chat.id, "📨 Связаться с организатором: @wokolad" + FOOTER)

@bot.message_handler(commands=["event", "edit"]) def cmd_event(message): user_states[message.chat.id] = {"step": 1, "answers": {}} bot.send_message(message.chat.id, "📝 Какой у вас игровой никнейм на сервере 24mine?")

@bot.message_handler(commands=["delete"]) def cmd_delete(message): if str(message.from_user.id) in users: users.pop(str(message.from_user.id)) save_json(USERS_FILE, users) bot.send_message(message.chat.id, "✅ Ваша анкета удалена.") else: bot.send_message(message.chat.id, "❓ У вас нет анкеты.")

@bot.message_handler(commands=["settimer"]) def cmd_settimer(message): if message.from_user.id in organizers: bot.send_message(message.chat.id, "🕓 Введите дату и время (ГГГГ-ММ-ДД ЧЧ:ММ):") user_states[message.chat.id] = {"admin_timer": True}

@bot.message_handler(commands=["removetimer"]) def cmd_removetimer(message): if message.from_user.id in organizers: timer_data["timestamp"] = None save_json(TIMER_FILE, timer_data) bot.send_message(message.chat.id, "❌ Время конкурса удалено.")

@bot.message_handler(commands=["participants"]) def cmd_participants(message): if message.from_user.id in organizers: if not users: bot.send_message(message.chat.id, "😢 Нет участников.") return text = "📄 Участники:\n" for uid, data in users.items(): text += f"@{data.get('username', 'без username')} (ID: {uid})\n" for k, v in data['answers'].items(): text += f"• {k}: {v}\n" text += "\n" bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["promote"]) def cmd_promote(message): if message.from_user.id in organizers: parts = message.text.split() if len(parts) == 2 and parts[1].isdigit(): uid = int(parts[1]) if uid not in organizers: organizers.append(uid) save_json(ORGANIZERS_FILE, organizers) bot.send_message(message.chat.id, f"✅ {uid} теперь организатор.")

@bot.message_handler(commands=["removeadmin"]) def cmd_removeadmin(message): if message.from_user.id in organizers: parts = message.text.split() if len(parts) == 2 and parts[1].isdigit(): uid = int(parts[1]) if uid in organizers and uid != ADMIN_ID: organizers.remove(uid) save_json(ORGANIZERS_FILE, organizers) bot.send_message(message.chat.id, f"✅ {uid} больше не организатор.")

@bot.message_handler(commands=["notify_all", "notify_interested", "notify_uninterested"]) def cmd_notify(message): if message.from_user.id not in organizers: return parts = message.text.split(maxsplit=1) if len(parts) < 2: bot.send_message(message.chat.id, "❓ Укажите сообщение.") return cmd = message.text.split()[0][1:] text = parts[1] + FOOTER for uid, data in users.items(): interested = data["answers"].get("Вы хотите зарегистрироваться на конкурс?", "").lower() if cmd == "notify_all": bot.send_message(int(uid), text) elif cmd == "notify_interested" and interested in ["да", "подумаю"]: bot.send_message(int(uid), text) elif cmd == "notify_uninterested" and interested not in ["да", "подумаю"]: bot.send_message(int(uid), text)

@bot.message_handler(commands=["backup"]) def cmd_backup(message): if message.text.strip() == f"/backup {ADMIN_PASSWORD}": with open("backup.json", "w", encoding="utf-8") as f: json.dump(users, f, indent=2, ensure_ascii=False) bot.send_message(message.chat.id, "✅ Резервная копия сохранена.")

@bot.message_handler(func=lambda m: m.chat.id in user_states) def handle_state(msg): uid = str(msg.from_user.id) state = user_states[msg.chat.id]

if "admin_timer" in state:
    try:
        dt = datetime.strptime(msg.text, "%Y-%m-%d %H:%M")
        timer_data["timestamp"] = int(dt.timestamp())
        save_json(TIMER_FILE, timer_data)
        bot.send_message(msg.chat.id, "✅ Время установлено.")
    except:
        bot.send_message(msg.chat.id, "❌ Неверный формат. Пример: 2025-07-12 18:00")
    user_states.pop(msg.chat.id)
    return

step = state.get("step")
answers = state["answers"]

if step == 1:
    answers["Ник в Minecraft"] = msg.text.strip()[:25]
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("Да", "Нет", "Подумаю")
    bot.send_message(msg.chat.id, "❓ Вы хотите зарегистрироваться на конкурс?", reply_markup=markup)
    state["step"] = 2
elif step == 2:
    answers["Вы хотите зарегистрироваться на конкурс?"] = msg.text
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("Да", "Нет", "Подумаю", "Смотря в какое время, если буду свободен приду")
    bot.send_message(msg.chat.id, "❓ Вы будете участвовать в конкурсе?", reply_markup=markup)
    state["step"] = 3
elif step == 3:
    answers["Вы будете участвовать в конкурсе?"] = msg.text
    bot.send_message(msg.chat.id, "🌍 С какого региона вы будете участвовать? (Напишите в какой стране вы живёте)", reply_markup=types.ReplyKeyboardRemove())
    state["step"] = 4
elif step == 4:
    answers["Регион (страна)"] = msg.text.strip()
    users[uid] = {
        "username": msg.from_user.username or f"id_{uid}",
        "answers": answers
    }
    save_json(USERS_FILE, users)
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("Подтвердить", "Изменить анкету", "Отмена")
    text = "📄 Ваша анкета:\n"
    for k, v in answers.items():
        text += f"• {k}: {v}\n"
    bot.send_message(msg.chat.id, text, reply_markup=markup)
    user_states.pop(msg.chat.id)

@app.route("/", methods=["GET"]) def index(): return "Bot is running"

@app.route("/", methods=["POST"]) def webhook(): update = telebot.types.Update.de_json(request.data.decode("utf-8")) bot.process_new_updates([update]) return "ok", 200

if name == "main": port = int(os.environ.get("PORT", 8080)) app.run(host="0.0.0.0", port=port)
