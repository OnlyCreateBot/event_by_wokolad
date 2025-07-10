import os
import json
import time
import threading
from datetime import datetime
from flask import Flask, request
import telebot
from telebot import types
import requests

# Инициализация
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
RULES_TEXT = os.environ.get("RULES_TEXT", "Правила пока не установлены")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Константы
PRIVILEGES = [
    "Игрок", "Птица", "Вип", "Архитектор", "Астроном", 
    "Анти-Грифер", "Полиция", "Админ", "Хелпер", 
    "Император", "Миллиардер", "Оператор", "Спонсор", "Загадочник"
]

PARTICIPATION_OPTIONS = [
    "Нет", "Да", "Подумаю", "Не знаю", 
    "Если освобожусь, буду участвовать"
]

# Файлы данных
USERS_FILE = "users.json"
TIMER_FILE = "timer.json"
ORGANIZERS_FILE = "organizers.json"
RULES_FILE = "rules.json"

# Загрузка данных
def load_json(filename, default):
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки {filename}: {e}")
    return default

def save_json(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Ошибка сохранения {filename}: {e}")

# Инициализация данных
users = load_json(USERS_FILE, {})
organizers = load_json(ORGANIZERS_FILE, [ADMIN_ID])
timer_data = load_json(TIMER_FILE, {"timestamp": None})
rules_data = load_json(RULES_FILE, {"text": RULES_TEXT})

user_states = {}
notify_selections = {}

# Обновленный футер
def get_footer():
    footer = "\n\n⭐ Конкурс на сервере 24mine (Minecraft PE 0.14.x)"
    
    if timer_data["timestamp"]:
        event_time = datetime.fromtimestamp(timer_data["timestamp"])
        footer += f"\n🕒 Время проведения: {event_time.strftime('%d.%m.%Y %H:%M')}"
    else:
        footer += "\n🕒 Время проведения: не назначено"
        
    footer += "\n🏠 IP: play.24mine.ru"
    footer += "\n🔗 Порт: 19133"
    footer += "\n🏆 Главный приз: Донат-кейс"
    footer += "\n👤 Организатор: Игрок wokolad с привилегией Анти-Грифер"
    
    return footer

# Функция для поддержания активности
def keep_alive():
    while True:
        try:
            # Периодически обращаемся к health-чекеру
            domain = os.environ.get("ZEABUR_DOMAIN")
            if domain:
                requests.get(f"https://{domain}/health", timeout=10)
            time.sleep(300)  # Каждые 5 минут
        except Exception as e:
            print(f"Keep-alive error: {e}")
            time.sleep(60)

# Запуск потока поддержания активности
if os.environ.get("ENV") == "PRODUCTION":
    threading.Thread(target=keep_alive, daemon=True).start()

# Команды
@bot.message_handler(commands=["start"])
def cmd_start(message):
    uid = message.from_user.id
    name = message.from_user.first_name or "Игрок"
    is_admin = uid in organizers
    role = "🚀 Вы организатор. Вам доступны команды администратора." if is_admin else "🏃 Вы участник."
    
    # Очистка состояния
    if uid in user_states:
        user_states.pop(uid)
    
    text = f"👋 Здравствуйте, {name}!\n{role}\n\n"
    text += "💡 Напишите /help чтобы увидеть команды\n"
    text += "📜 Просмотреть правила: /rules"
    
    bot.send_message(uid, text + get_footer())

@bot.message_handler(commands=["help"])
def cmd_help(message):
    text = "📚 Основные команды:\n"
    text += "/start - перезапуск бота\n"
    text += "/help - список команд\n"
    text += "/info - информация о конкурсе\n"
    text += "/rules - правила использования бота\n"
    text += "/event - заполнить анкету\n"
    text += "/edit - изменить анкету\n"
    text += "/delete - удалить анкету\n"
    text += "/contact - связаться с организатором\n"
    
    if message.from_user.id in organizers:
        text += "\n🛠 Админ-команды:\n"
        text += "/settimer - установить время конкурса\n"
        text += "/removetimer - удалить время конкурса\n"
        text += "/participants - список участников\n"
        text += "/promote ID - выдать права организатора\n"
        text += "/removeadmin ID - удалить организатора\n"
        text += "/notify - уведомить по категориям\n"
        text += "/backup ПАРОЛЬ - резервная копия\n"
        text += "/export - экспорт данных в CSV\n"
        text += "/setrules - установить новые правила\n"
        text += "/getrules - показать текущие правила"
    
    bot.send_message(message.chat.id, text + get_footer())

@bot.message_handler(commands=["info"])
def cmd_info(message):
    text = "🎮 Информация о конкурсе:\n\n"
    
    if timer_data["timestamp"]:
        event_time = datetime.fromtimestamp(timer_data["timestamp"])
        now = datetime.now()
        delta = event_time - now
        
        if delta.total_seconds() > 0:
            days = delta.days
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            text += f"⏳ До начала: {days} дней, {hours} часов, {minutes} минут"
        else:
            text += "🚀 Конкурс уже начался!"
    else:
        text += "⏱ Время начала пока не установлено"
    
    text += get_footer()
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["contact"])
def cmd_contact(message):
    bot.send_message(
        message.chat.id, 
        "📨 Связь с организатором: @wokolad\n" + get_footer()
    )

@bot.message_handler(commands=["rules"])
def cmd_rules(message):
    bot.send_message(
        message.chat.id, 
        f"📜 Правила использования бота и конкурса:\n\n{rules_data['text']}" + get_footer()
    )

@bot.message_handler(commands=["setrules"])
def cmd_set_rules(message):
    if message.from_user.id not in organizers:
        return
        
    text = message.text.replace("/setrules", "").strip()
    if not text:
        bot.send_message(message.chat.id, "❌ Укажите текст правил после команды")
        return
        
    rules_data["text"] = text
    save_json(RULES_FILE, rules_data)
    bot.send_message(message.chat.id, "✅ Правила успешно обновлены!" + get_footer())

@bot.message_handler(commands=["getrules"])
def cmd_get_rules(message):
    if message.from_user.id not in organizers:
        return
        
    bot.send_message(
        message.chat.id, 
        f"📜 Текущие правила:\n\n{rules_data['text']}" + get_footer()
    )

@bot.message_handler(commands=["event", "edit"])
def cmd_event(message):
    uid = str(message.from_user.id)
    chat_id = message.chat.id
    
    # Для команды edit проверяем существование анкеты
    if "edit" in message.text and uid not in users:
        bot.send_message(chat_id, "❌ У вас нет анкеты для редактирования")
        return
    
    # Начинаем процесс заполнения анкеты
    user_states[chat_id] = {"step": 1, "answers": {}}
    bot.send_message(chat_id, "🆔 Ваш игровой никнейм на сервере 24mine 0.14.x?")

@bot.message_handler(commands=["delete"])
def cmd_delete(message):
    uid = str(message.from_user.id)
    if uid in users:
        users.pop(uid)
        save_json(USERS_FILE, users)
        
        # Очищаем состояние
        if message.chat.id in user_states:
            user_states.pop(message.chat.id)
            
        bot.send_message(message.chat.id, "✅ Ваша анкета удалена." + get_footer())
    else:
        bot.send_message(message.chat.id, "❌ У вас нет анкеты." + get_footer())

# Админ-команды
@bot.message_handler(commands=["settimer"])
def cmd_settimer(message):
    if message.from_user.id in organizers:
        bot.send_message(message.chat.id, "⏰ Введите дату и время (ГГГГ-ММ-ДД ЧЧ:ММ):")
        user_states[message.chat.id] = {"admin_timer": True}

@bot.message_handler(commands=["removetimer"])
def cmd_removetimer(message):
    if message.from_user.id in organizers:
        timer_data["timestamp"] = None
        save_json(TIMER_FILE, timer_data)
        bot.send_message(message.chat.id, "✅ Таймер конкурса удален." + get_footer())

@bot.message_handler(commands=["participants"])
def cmd_participants(message):
    if message.from_user.id not in organizers:
        return
        
    if not users:
        bot.send_message(message.chat.id, "😢 Нет участников." + get_footer())
        return
        
    # Форматируем вывод
    result = ["📋 Участники:\n"]
    
    for i, (uid, data) in enumerate(users.items(), 1):
        result.append(f"\n👤 Участник #{i}:")
        result.append(f"└ @{data.get('username', 'без username')}")
        
        for q, a in data['answers'].items():
            result.append(f"   • {q}: {a}")
    
    full_text = "\n".join(result)
    
    # Разбиваем на части если превышен лимит
    if len(full_text) > 4000:
        parts = []
        while full_text:
            if len(full_text) > 4000:
                part = full_text[:4000]
                last_newline = part.rfind('\n')
                if last_newline != -1:
                    part = full_text[:last_newline]
                    full_text = full_text[last_newline+1:]
                else:
                    full_text = full_text[4000:]
                parts.append(part)
            else:
                parts.append(full_text)
                full_text = ""
        
        for part in parts:
            bot.send_message(message.chat.id, part)
    else:
        bot.send_message(message.chat.id, full_text + get_footer())

@bot.message_handler(commands=["promote"])
def cmd_promote(message):
    if message.from_user.id in organizers:
        parts = message.text.split()
        if len(parts) == 2 and parts[1].isdigit():
            uid = int(parts[1])
            if uid not in organizers:
                organizers.append(uid)
                save_json(ORGANIZERS_FILE, organizers)
                bot.send_message(message.chat.id, f"✅ {uid} теперь организатор." + get_footer())

@bot.message_handler(commands=["removeadmin"])
def cmd_removeadmin(message):
    if message.from_user.id in organizers:
        parts = message.text.split()
        if len(parts) == 2 and parts[1].isdigit():
            uid = int(parts[1])
            if uid in organizers and uid != ADMIN_ID:
                organizers.remove(uid)
                save_json(ORGANIZERS_FILE, organizers)
                bot.send_message(message.chat.id, f"✅ {uid} больше не организатор." + get_footer())

# Улучшенная система рассылки
@bot.message_handler(commands=["notify"])
def cmd_notify(message):
    if message.from_user.id not in organizers:
        return
        
    # Создаем инлайн-клавиатуру для выбора категорий
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Категории по статусу
    markup.add(
        types.InlineKeyboardButton("Все участники", callback_data="notify_all"),
        types.InlineKeyboardButton("Заинтересованные", callback_data="notify_interested"),
        types.InlineKeyboardButton("Незаинтересованные", callback_data="notify_uninterested"),
        types.InlineKeyboardButton("Не заполнили анкету", callback_data="notify_noform")
    )
    
    # Категории по привилегиям
    markup.row(types.InlineKeyboardButton("Выбрать привилегии", callback_data="select_privileges"))
    
    bot.send_message(
        message.chat.id, 
        "📨 Выберите категорию для рассылки:",
        reply_markup=markup
    )

# Обработчик инлайн-кнопок для рассылки
@bot.callback_query_handler(func=lambda call: call.data.startswith('notify_') or call.data == 'select_privileges')
def handle_notify_selection(call):
    if call.data == 'select_privileges':
        # Создаем меню выбора привилегий
        markup = types.InlineKeyboardMarkup(row_width=3)
        
        for privilege in PRIVILEGES:
            markup.add(types.InlineKeyboardButton(
                privilege, 
                callback_data=f"priv_{privilege}"
            ))
            
        markup.row(types.InlineKeyboardButton("Начать рассылку", callback_data="start_notify"))
        
        bot.edit_message_text(
            "🔍 Выберите привилегии:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    elif call.data.startswith('priv_'):
        # Обработка выбора привилегий
        privilege = call.data[5:]
        selected = call.message.json.get('reply_markup', {}).get('inline_keyboard', [])
        
        # Переключаем выбор
        new_keyboard = []
        for row in selected:
            new_row = []
            for btn in row:
                if btn['callback_data'] == call.data:
                    text = f"✅ {btn['text']}" if not btn['text'].startswith('✅') else btn['text'][2:]
                    new_row.append(types.InlineKeyboardButton(text, callback_data=btn['callback_data']))
                else:
                    new_row.append(btn)
            new_keyboard.append(new_row)
        
        markup = types.InlineKeyboardMarkup(new_keyboard)
        markup.row(types.InlineKeyboardButton("Начать рассылку", callback_data="start_notify"))
        
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    elif call.data == 'start_notify':
        # Получаем выбранные привилегии
        selected_privileges = []
        for row in call.message.reply_markup.keyboard:
            for btn in row:
                if btn.text.startswith('✅'):
                    selected_privileges.append(btn.text[2:])
        
        if not selected_privileges:
            bot.answer_callback_query(call.id, "❌ Выберите хотя бы одну привилегию")
            return
            
        # Сохраняем выбор
        user_states[call.message.chat.id] = {
            "notify_type": "privileges",
            "privileges": selected_privileges
        }
        
        bot.send_message(call.message.chat.id, "✉️ Введите текст сообщения для рассылки:")
    else:
        # Стандартные категории
        user_states[call.message.chat.id] = {"notify_type": call.data.split('_')[1]}
        bot.send_message(call.message.chat.id, "✉️ Введите текст сообщения для рассылки:")

# Обработчик анкеты
@bot.message_handler(func=lambda m: m.chat.id in user_states)
def handle_state(msg):
    state = user_states[msg.chat.id]
    uid = str(msg.from_user.id)
    
    # Обработка установки таймера
    if "admin_timer" in state:
        try:
            dt = datetime.strptime(msg.text, "%Y-%m-%d %H:%M")
            timer_data["timestamp"] = int(dt.timestamp())
            save_json(TIMER_FILE, timer_data)
            bot.send_message(msg.chat.id, "✅ Время установлено." + get_footer())
        except:
            bot.send_message(msg.chat.id, "❌ Неверный формат. Пример: 2025-07-12 18:00")
        user_states.pop(msg.chat.id)
        return
        
    # Обработка рассылки
    if "notify_type" in state:
        text = msg.text + get_footer()
        count = 0
        
        # Рассылка по категориям
        if state["notify_type"] == "all":
            for user_id in users:
                try:
                    bot.send_message(int(user_id), text)
                    count += 1
                except Exception as e:
                    print(f"Ошибка рассылки для {user_id}: {e}")
                    
        elif state["notify_type"] == "interested":
            for user_id, data in users.items():
                answer = data["answers"].get("Будете участвовать на конкурсе?", "").lower()
                if answer in ["да", "подумаю"]:
                    try:
                        bot.send_message(int(user_id), text)
                        count += 1
                    except:
                        pass
                        
        elif state["notify_type"] == "uninterested":
            for user_id, data in users.items():
                answer = data["answers"].get("Будете участвовать на конкурсе?", "").lower()
                if answer == "нет":
                    try:
                        bot.send_message(int(user_id), text)
                        count += 1
                    except:
                        pass
                        
        elif state["notify_type"] == "noform":
            # Для пользователей без анкеты нужен отдельный список
            # В этой реализации не реализовано
            pass
            
        elif state["notify_type"] == "privileges":
            for user_id, data in users.items():
                privilege = data["answers"].get("Ваша привилегия на сервере 24mine 0.14.x?", "")
                if privilege in state["privileges"]:
                    try:
                        bot.send_message(int(user_id), text)
                        count += 1
                    except:
                        pass
        
        bot.send_message(msg.chat.id, f"✅ Рассылка завершена. Отправлено: {count}" + get_footer())
        user_states.pop(msg.chat.id)
        return
        
    # Обработка анкеты
    step = state["step"]
    answers = state["answers"]
    
    if step == 1:  # Никнейм
        answers["Ваш игровой никнейм на сервере 24mine 0.14.x?"] = msg.text.strip()[:25]
        state["step"] = 2
        
        # Клавиатура для привилегий
        markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
        markup.add(*PRIVILEGES)
        
        bot.send_message(msg.chat.id, "👑 Ваша привилегия на сервере 24mine 0.14.x?", reply_markup=markup)
        
    elif step == 2:  # Привилегия
        if msg.text not in PRIVILEGES:
            bot.send_message(msg.chat.id, "❌ Выберите привилегию из предложенных кнопок")
            return
            
        answers["Ваша привилегия на сервере 24mine 0.14.x?"] = msg.text
        state["step"] = 3
        
        # Кнопки для участия
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        markup.add(*PARTICIPATION_OPTIONS)
        
        bot.send_message(msg.chat.id, "🎯 Будете участвовать на конкурсе?", reply_markup=markup)
        
    elif step == 3:  # Участие
        answers["Будете участвовать на конкурсе?"] = msg.text
        state["step"] = 4
        bot.send_message(
            msg.chat.id, 
            "🌍 С какого вы региона? (напишите страну)",
            reply_markup=types.ReplyKeyboardRemove()
        )
        
    elif step == 4:  # Регион
        answers["Ваш регион (страна)"] = msg.text.strip()
        
        # Сохраняем анкету
        users[uid] = {
            "username": msg.from_user.username or f"id_{uid}",
            "answers": answers,
            "timestamp": datetime.now().isoformat()
        }
        save_json(USERS_FILE, users)
        
        # Формируем итоговую анкету
        text = "📝 Ваша анкета:\n"
        for q, a in answers.items():
            text += f"• {q}: {a}\n"
        
        bot.send_message(msg.chat.id, text + get_footer())
        user_states.pop(msg.chat.id, None)

# Экспорт данных
@bot.message_handler(commands=["export"])
def cmd_export(message):
    if message.from_user.id not in organizers:
        return
        
    # Создаем CSV файл
    csv_data = "ID;Username;Никнейм;Привилегия;Участие;Регион;Дата регистрации\n"
    
    for uid, data in users.items():
        answers = data["answers"]
        csv_data += f"{uid};{data['username']};"
        csv_data += f"{answers.get('Ваш игровой никнейм на сервере 24mine 0.14.x?', '')};"
        csv_data += f"{answers.get('Ваша привилегия на сервере 24mine 0.14.x?', '')};"
        csv_data += f"{answers.get('Будете участвовать на конкурсе?', '')};"
        csv_data += f"{answers.get('Ваш регион (страна)', '')};"
        csv_data += f"{data.get('timestamp', '')}\n"
    
    with open("participants.csv", "w", encoding="utf-8") as f:
        f.write(csv_data)
    
    with open("participants.csv", "rb") as f:
        bot.send_document(message.chat.id, f, caption="📊 Экспорт участников")

# Резервное копирование
@bot.message_handler(commands=["backup"])
def cmd_backup(message):
    if message.from_user.id not in organizers:
        return
        
    parts = message.text.split()
    if len(parts) < 2 or parts[1] != ADMIN_PASSWORD:
        bot.send_message(message.chat.id, "❌ Неверный пароль")
        return
        
    try:
        # Создаем резервную копию всех данных
        backup_data = {
            "users": users,
            "organizers": organizers,
            "timer": timer_data,
            "rules": rules_data,
            "timestamp": datetime.now().isoformat()
        }
        
        with open("backup.json", "w", encoding="utf-8") as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
        with open("backup.json", "rb") as f:
            bot.send_document(message.chat.id, f, caption="✅ Резервная копия данных")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка создания резервной копии: {str(e)}")

# Health check для мониторинга
@app.route('/health')
def health_check():
    return "OK", 200

# Веб-сервер
@app.route("/", methods=["GET"])
def index():
    return "Bot is running"

@app.route("/", methods=["POST"])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "ok", 200
    return "Bad Request", 400

# Установка вебхука при запуске
def setup_webhook():
    if not BOT_TOKEN:
        print("BOT_TOKEN не установлен!")
        return
        
    try:
        domain = os.environ.get("ZEABUR_DOMAIN")
        if not domain:
            print("ZEABUR_DOMAIN не установлен! Вебхук не настроен")
            return
            
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
        payload = {
            "url": f"https://{domain}/"
        }
        response = requests.post(url, json=payload)
        print(f"Настройка вебхука: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Ошибка настройки вебхука: {e}")

if __name__ == "__main__":
    # Настройка вебхука при запуске в продакшене
    if os.environ.get("ENV") == "PRODUCTION":
        setup_webhook()
        
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
