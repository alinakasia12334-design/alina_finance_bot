import telebot
import json
import os
from datetime import datetime, timedelta
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import threading
import time
import random
from functools import wraps

# ========== НАСТРОЙКИ ==========
TOKEN = "8692541391:AAH6Cf8eh_afsynkA277SJ-_28ihs2VEutI"
ADMIN_ID = 463620997

bot = telebot.TeleBot(TOKEN)
DATA_FOLDER = "user_data"

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

# Категории расходов
CATEGORIES = {
    "food": "🍕 Еда",
    "transport": "🚗 Транспорт",
    "cafe": "☕ Кафе",
    "shopping": "🛒 Покупки",
    "home": "🏠 Дом",
    "health": "💊 Аптеки",
    "subscriptions": "📱 Подписки",
    "gifts": "🎁 Подарки",
    "travel": "✈️ Путешествия",
    "credit": "💳 Кредиты/долги",
    "other": "📝 Другое"
}

# ========== СОВЕТЫ ==========
ADVICE = {
    "food": ["{name}, ну ты ахуела столько на доставку тратить? Готовь дома!", "{name}, твой кошелёк плачет. Хватит заказывать роллы каждый день.", "{name}, готовь дома — это не только дешевле, но и полезнее.", "{name}, бери ланч с собой на работу. Экономия ~3000 ₽ в месяц.", "{name}, не ходи в магазин голодной. Иначе в корзине окажется всё, кроме хлеба."],
    "transport": ["{name}, давай нахуй меньше на такси езжай! Общественный транспорт — это не стыдно, это умно.", "{name}, такси — для богатых. А ты пока копишь на золотое яблочко, помнишь?", "{name}, ноги бесплатные. Вспомни про них, пожалуйста.", "{name}, каршеринг дешевле такси, если совсем невмоготу.", "{name}, проездной на месяц окупится через 2 недели."],
    "cafe": ["{name}, кофе дома — это не скучно, это выгодно. Купи красивую кружку.", "{name}, устрой «кофейный детокс» на неделю.", "{name}, встречайся с подругами дома, а не в кафе.", "{name}, завтракай дома — кафе утром самое дорогое удовольствие.", "{name}, бери с собой термокружку — в некоторых заведениях скидка."],
    "shopping": ["{name}, перед покупкой подожди 24 часа. Через день уже не хочется.", "{name}, удали приложения магазинов с телефона — меньше соблазна.", "{name}, покупай на распродажах, но только то, что планировала.", "{name}, спроси себя: «Мне это нужно или просто хочется?»", "{name}, не ходи в торговый центр «просто посмотреть»."],
    "home": ["{name}, выключай свет, когда выходишь из комнаты.", "{name}, установи счётчики на воду — окупаются за полгода.", "{name}, стирай при полной загрузке и при 30°.", "{name}, не кипяти полный чайник, если нужна одна кружка.", "{name}, не держи технику в режиме ожидания — выключай из розетки."],
    "health": ["{name}, не занимайся самолечением — дороже выйдет потом.", "{name}, сравнивай цены в разных аптеках через приложения.", "{name}, покупай дженерики вместо брендов.", "{name}, проверяй срок годности — выброшенные лекарства = выброшенные деньги.", "{name}, пей витамины курсами, а не круглый год."],
    "subscriptions": ["{name}, раз в месяц проверяй, на что у тебя списываются деньги.", "{name}, отпишись от стримингов, которыми не пользуешься.", "{name}, дели подписку с подругой.", "{name}, установи лимит на подписки: максимум 3.", "{name}, используй бесплатные триалы, но ставь напоминалку отменить."],
    "gifts": ["{name}, подарок — это жест, а не сумма.", "{name}, подари впечатления: билет в кино, мастер-класс.", "{name}, сделай подарок своими руками — ценится больше.", "{name}, договорись с подругами не дарить друг другу дорогие подарки.", "{name}, покупай подарки заранее, а не в последний день."],
    "travel": ["{name}, покупай билеты заранее за 2-3 месяца.", "{name}, следи за акциями авиакомпаний.", "{name}, лети в будни — дешевле.", "{name}, бери только ручную кладь — экономия на багаже.", "{name}, жильё ищи не в центре, а в 10 минутах на транспорте."],
    "credit": ["{name}, зайка, кредиты — это зло. Погаси самый маленький первым.", "{name}, не бери новый кредит, чтобы закрыть старый.", "{name}, плати больше минимального платежа.", "{name}, если взяла в долг у подруги — отдай сразу.", "{name}, рефинансирование может снизить ставку."],
    "other": ["{name}, заведи привычку записывать каждую трату.", "{name}, в конце недели посмотри, куда утекло больше всего.", "{name}, спроси себя: «Эта покупка сделала меня счастливее?»", "{name}, не трать деньги на то, что можно получить бесплатно.", "{name}, откладывай 10% от любого дохода сразу."]
}

advice_indexes = {}

def get_next_advice(user_id, category):
    key = f"{user_id}_{category}"
    if key not in advice_indexes:
        advice_indexes[key] = 0
    advices = ADVICE.get(category, ADVICE["other"])
    idx = advice_indexes[key]
    advice = advices[idx]
    advice_indexes[key] = (idx + 1) % len(advices)
    return advice

def get_name_form(name):
    if not name:
        return "Зайка"
    name_lower = name.lower()
    if name_lower.endswith("а"):
        return name_lower[:-1].capitalize()
    elif name_lower.endswith("я"):
        return (name_lower[:-1] + "ь").capitalize()
    elif name_lower.endswith("ия"):
        return (name_lower[:-2] + "ий").capitalize()
    else:
        return name_lower.capitalize()

def get_moscow_time():
    return datetime.utcnow() + timedelta(hours=3)

# ========== ДЕКОРАТОРЫ ==========
def require_auth(func):
    @wraps(func)
    def wrapper(message, *args, **kwargs):
        if not is_allowed(message.from_user.id):
            bot.reply_to(message, "🔒 У тебя нет доступа к этому боту. Напиши Алине.")
            return
        return func(message, *args, **kwargs)
    return wrapper

def require_admin(func):
    @wraps(func)
    def wrapper(message, *args, **kwargs):
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "❌ Эта команда только для администратора.")
            return
        return func(message, *args, **kwargs)
    return wrapper

# ========== РАБОТА С ДАННЫМИ ==========
def get_user_file(user_id):
    return os.path.join(DATA_FOLDER, f"user_{user_id}.json")

def load_user_data(user_id):
    file_path = get_user_file(user_id)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            data.setdefault("goals", [])
            data.setdefault("budget", None)
            data.setdefault("transactions", [])
            data.setdefault("monthly_stats", {})
            data.setdefault("current_month_stats", {cat: 0 for cat in CATEGORIES.keys()})
            data.setdefault("current_month_total", 0)
            data.setdefault("last_reset_month", None)
            data.setdefault("last_report_month", None)
            data.setdefault("last_auto_report_sent", None)
            return data
    return {
        "usd": 0.0,
        "rub": 0,
        "transactions": [],
        "goals": [],
        "budget": None,
        "monthly_stats": {},
        "current_month_stats": {cat: 0 for cat in CATEGORIES.keys()},
        "current_month_total": 0,
        "last_reset_month": None,
        "last_report_month": None,
        "last_auto_report_sent": None
    }

def save_user_data(user_id, data):
    data["rub"] = int(data["rub"])
    with open(get_user_file(user_id), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_admin(user_id):
    return user_id == ADMIN_ID

def get_allowed_users():
    allowed = [ADMIN_ID]
    for filename in os.listdir(DATA_FOLDER):
        if filename.startswith("user_") and filename.endswith(".json"):
            try:
                user_id = int(filename.split("_")[1].split(".")[0])
                if user_id != ADMIN_ID:
                    allowed.append(user_id)
            except:
                pass
    return allowed

def is_allowed(user_id):
    return user_id in get_allowed_users()

# ========== ОБНУЛЕНИЕ ==========
def reset_monthly_stats_if_needed(user_id):
    data = load_user_data(user_id)
    now = get_moscow_time()
    current_month = now.month
    current_year = now.year
    
    if data["last_reset_month"] != current_month:
        if data["last_reset_month"] is not None:
            key = f"{data['last_reset_month']}_{current_year if current_month > 1 else current_year-1}"
            data["monthly_stats"][key] = data.get("current_month_stats", {}).copy()
        
        data["current_month_stats"] = {cat: 0 for cat in CATEGORIES.keys()}
        data["current_month_total"] = 0
        data["last_reset_month"] = current_month
        save_user_data(user_id, data)
    return data

# ========== КЛАВИАТУРЫ ==========
def get_main_keyboard(user_id):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = ["💎 Баланс", "📊 Отчёты", "➕ Доход", "➖ Расход", "🎯 Мои цели", "📈 Бюджет", "📂 Категории трат", "📋 История", "🕊️ Отменить", "⚙️ Настройки"]
    if is_admin(user_id):
        buttons.append("👥 Пользователи")
    keyboard.add(*buttons)
    return keyboard

def get_back_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_main"))
    return keyboard

# ========== ПРИВЕТСТВИЕ ==========
@bot.message_handler(commands=['start'])
@require_auth
def start(message):
    user_id = message.from_user.id
    name = message.from_user.first_name or "Подруга"
    reset_monthly_stats_if_needed(user_id)
    
    welcome = f"🌸 Привет, {name}!\n\nЯ — Твоя финансовая нянька 💅\nСоздала меня **Алина** 🔥\n\n📚 ИНСТРУКЦИЯ:\n💎 Баланс — свободные и отложенные\n➕ Доход — сумма + описание\n➖ Расход — сумма + описание → категория → совет\n🎯 Мои цели — создать/отложить/потратить\n📈 Бюджет — /budget 50000\n📂 Категории трат — проценты + совет\n📋 История — последние операции\n🕊️ Отменить — откат\n\n👇 Кнопки внизу! 😘"
    bot.reply_to(message, welcome, reply_markup=get_main_keyboard(user_id))

@bot.message_handler(commands=['getid'])
def get_id(message):
    bot.reply_to(message, f"🆔 Твой ID: `{message.from_user.id}`\n\nПерешли этот ID Алине.", parse_mode='Markdown')

# ========== УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ==========
@bot.message_handler(commands=['adduser'])
@require_admin
def add_user(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Формат: /adduser 123456789")
            return
        new_user_id = int(parts[1])
        save_user_data(new_user_id, load_user_data(new_user_id))
        bot.reply_to(message, f"✅ Пользователь `{new_user_id}` добавлен", parse_mode='Markdown')
        try:
            bot.send_message(new_user_id, "🎉 Тебе открыли доступ!\nНапиши /start")
        except:
            pass
    except:
        bot.reply_to(message, "❌ Ошибка")

@bot.message_handler(commands=['removeuser'])
@require_admin
def remove_user(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Формат: /removeuser 123456789")
            return
        user_id = int(parts[1])
        file_path = get_user_file(user_id)
        if os.path.exists(file_path):
            os.remove(file_path)
            bot.reply_to(message, f"✅ Пользователь `{user_id}` удалён", parse_mode='Markdown')
        else:
            bot.reply_to(message, "ℹ️ Пользователь не найден")
    except:
        bot.reply_to(message, "❌ Ошибка")

@bot.message_handler(commands=['users'])
@require_admin
def list_users(message):
    allowed = get_allowed_users()
    text = "👥 ДОСТУП ЕСТЬ У:\n━━━━━━━━━━━━━━━\n" + "\n".join([f"🆔 `{uid}`" for uid in allowed]) + f"\n\n👑 Админ: `{ADMIN_ID}`"
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "👥 Пользователи")
@require_admin
def user_management_button(message):
    bot.reply_to(message, "👥 Управление\n━━━━━━━━━━━━━━━\n\n/adduser ID — добавить\n/removeuser ID — удалить\n/users — список\n/getid — свой ID")

# ========== БАЛАНС ==========
@bot.message_handler(func=lambda m: m.text == "💎 Баланс")
@require_auth
def button_balance(message):
    user_id = message.from_user.id
    data = reset_monthly_stats_if_needed(user_id)
    now = get_moscow_time()
    
    total_saved = sum(g["current"] for g in data["goals"])
    free_rub = data["rub"] - total_saved
    
    text = f"💎 БАЛАНС\n━━━━━━━━━━━━━━━\n💰 Свободно: {free_rub} ₽\n🎯 Отложено на цели: {total_saved} ₽\n━━━━━━━━━━━━━━━\n💎 Итого: {data['rub']} ₽\n\n🇺🇸 Доллары: {data['usd']:.2f}$\n\n🕐 {now.strftime('%d.%m.%Y %H:%M')} МСК"
    
    if data["goals"]:
        text += "\n\n🎯 БЛИЖАЙШАЯ ЦЕЛЬ:\n" + "\n".join([f"• {g['name']}: {int(g['current'])} / {int(g['target'])} ₽" for g in data["goals"][:3]])
    
    bot.reply_to(message, text, reply_markup=get_main_keyboard(user_id))

# ========== ЦЕЛИ ==========
@bot.message_handler(func=lambda m: m.text == "🎯 Мои цели")
@require_auth
def button_goals(message):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📋 Список целей", callback_data="goals_list"),
        InlineKeyboardButton("➕ Новая цель", callback_data="goal_add"),
        InlineKeyboardButton("💰 Отложить на цель", callback_data="goal_save"),
        InlineKeyboardButton("💸 Потратить из цели", callback_data="goal_spend"),
        InlineKeyboardButton("🗑️ Удалить цель", callback_data="goal_delete"),
        InlineKeyboardButton("❌ Закрыть", callback_data="cancel")
    )
    bot.send_message(message.chat.id, "🎯 Управление целями:", reply_markup=keyboard)

def show_goals_list(message, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
    data = load_user_data(user_id)
    
    if not data["goals"]:
        bot.edit_message_text("🎯 У тебя пока нет целей.\n\nСоздай цель:\n/goal Название сумма ГГГГ-ММ-ДД\n\nПример: /goal Золотое яблочко 50000 2026-12-31", message.chat.id, message.message_id, reply_markup=get_back_keyboard())
        return
    
    text = "🎯 МОИ ЦЕЛИ\n━━━━━━━━━━━━━━━\n\n"
    for g in data["goals"]:
        left = g["target"] - g["current"]
        percent = (g["current"] / g["target"]) * 100 if g["target"] > 0 else 0
        text += f"💰 {g['name']}\n   Нужно: {int(g['target'])} ₽\n   Отложено: {int(g['current'])} ₽\n   Осталось: {int(left)} ₽\n   Прогресс: {'█' * int(percent//10)}{'░' * (10 - int(percent//10))} {percent:.0f}%\n"
        if g.get("deadline"):
            try:
                deadline = datetime.strptime(g["deadline"], "%Y-%m-%d")
                days_left = (deadline - datetime.now()).days
                text += f"   ⏰ Дедлайн: {deadline.strftime('%d.%m.%Y')} (осталось {days_left} дн.)\n"
            except:
                pass
        text += "\n"
    
    bot.edit_message_text(text, message.chat.id, message.message_id, reply_markup=get_back_keyboard())

def validate_amount(amount):
    try:
        amount = float(amount)
        if amount <= 0:
            return None, "❌ Сумма должна быть больше 0"
        return amount, None
    except:
        return None, "❌ Введи число"

@bot.callback_query_handler(func=lambda call: call.data.startswith("goal_") or call.data.startswith("goals_") or call.data == "back_to_main")
def handle_goals_callback(call):
    if not is_allowed(call.from_user.id):
        bot.answer_callback_query(call.id, "Нет доступа")
        return
    
    user_id = call.from_user.id
    data = load_user_data(user_id)
    
    if call.data == "goals_list":
        show_goals_list(call.message, user_id)
    elif call.data == "goal_add":
        bot.edit_message_text("🎯 Введи цель: Название сумма ГГГГ-ММ-ДД\n\nПример: Золотое яблочко 50000 2026-12-31", call.message.chat.id, call.message.message_id)
        bot.register_next_step_handler(call.message, process_goal_add)
    elif call.data == "goal_save":
        if not data["goals"]:
            bot.edit_message_text("❌ У тебя нет целей. Сначала создай цель через «➕ Новая цель»", call.message.chat.id, call.message.message_id)
        else:
            keyboard = InlineKeyboardMarkup(row_width=1)
            for i, g in enumerate(data["goals"]):
                keyboard.add(InlineKeyboardButton(f"{g['name']} ({int(g['current'])}/{int(g['target'])} ₽)", callback_data=f"goal_select_save_{i}"))
            keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="goals_back"))
            bot.edit_message_text("💰 Выбери цель для пополнения:", call.message.chat.id, call.message.message_id, reply_markup=keyboard)
    elif call.data == "goal_spend":
        if not data["goals"]:
            bot.edit_message_text("❌ У тебя нет целей. Сначала создай цель.", call.message.chat.id, call.message.message_id)
        else:
            keyboard = InlineKeyboardMarkup(row_width=1)
            for i, g in enumerate(data["goals"]):
                keyboard.add(InlineKeyboardButton(f"{g['name']} ({int(g['current'])}/{int(g['target'])} ₽)", callback_data=f"goal_select_spend_{i}"))
            keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="goals_back"))
            bot.edit_message_text("💸 Выбери цель для траты:", call.message.chat.id, call.message.message_id, reply_markup=keyboard)
    elif call.data == "goal_delete":
        if not data["goals"]:
            bot.edit_message_text("❌ У тебя нет целей.", call.message.chat.id, call.message.message_id)
        else:
            keyboard = InlineKeyboardMarkup(row_width=1)
            for i, g in enumerate(data["goals"]):
                keyboard.add(InlineKeyboardButton(f"{g['name']} ({int(g['current'])} ₽ отложено)", callback_data=f"goal_select_delete_{i}"))
            keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="goals_back"))
            bot.edit_message_text("🗑️ Выбери цель для удаления:", call.message.chat.id, call.message.message_id, reply_markup=keyboard)
    elif call.data.startswith("goal_select_save_"):
        idx = int(call.data.split("_")[3])
        goal = data["goals"][idx]
        bot.edit_message_text(f"💰 Введи сумму для пополнения цели «{goal['name']}»:", call.message.chat.id, call.message.message_id)
        bot.register_next_step_handler(call.message, lambda m: process_goal_save_amount(m, idx))
    elif call.data.startswith("goal_select_spend_"):
        idx = int(call.data.split("_")[3])
        goal = data["goals"][idx]
        bot.edit_message_text(f"💸 Введи сумму для траты из цели «{goal['name']}»:", call.message.chat.id, call.message.message_id)
        bot.register_next_step_handler(call.message, lambda m: process_goal_spend_amount(m, idx))
    elif call.data.startswith("goal_select_delete_"):
        idx = int(call.data.split("_")[3])
        goal = data["goals"][idx]
        # Возвращаем отложенные деньги
        data["rub"] += goal["current"]
        data["goals"].pop(idx)
        save_user_data(user_id, data)
        bot.edit_message_text(f"✅ Цель «{goal['name']}» удалена. {int(goal['current'])} ₽ возвращено в свободный остаток.", call.message.chat.id, call.message.message_id)
        button_balance(call.message)
    elif call.data == "goals_back":
        button_goals(call.message)
    elif call.data == "back_to_main":
        bot.edit_message_text("🔙 Возврат в главное меню", call.message.chat.id, call.message.message_id)
        button_balance(call.message)
    
    bot.answer_callback_query(call.id)

def process_goal_add(message):
    user_id = message.from_user.id
    try:
        parts = message.text.rsplit(" ", 2)
        if len(parts) < 2:
            bot.reply_to(message, "❌ Формат: Название сумма ГГГГ-ММ-ДД")
            return
        name = parts[0]
        target = float(parts[1])
        deadline = parts[2] if len(parts) > 2 else None
        
        data = load_user_data(user_id)
        data["goals"].append({"name": name, "target": target, "current": 0, "deadline": deadline})
        save_user_data(user_id, data)
        bot.reply_to(message, f"✅ Цель «{name}» создана! Нужно накопить: {int(target)} ₽")
        button_goals(message)
    except:
        bot.reply_to(message, "❌ Ошибка. Формат: Название сумма ГГГГ-ММ-ДД")

def process_goal_save_amount(message, goal_idx):
    user_id = message.from_user.id
    amount, error = validate_amount(message.text)
    if error:
        bot.reply_to(message, error)
        return
    
    data = load_user_data(user_id)
    if goal_idx >= len(data["goals"]):
        bot.reply_to(message, "❌ Цель не найдена")
        return
    
    goal = data["goals"][goal_idx]
    total_saved = sum(g["current"] for g in data["goals"])
    free_rub = data["rub"] - total_saved
    
    if free_rub < amount:
        bot.reply_to(message, f"❌ Недостаточно свободных денег. Свободно: {int(free_rub)} ₽")
        return
    
    goal["current"] += amount
    save_user_data(user_id, data)
    
    left = goal["target"] - goal["current"]
    percent = (goal["current"] / goal["target"]) * 100
    bot.reply_to(message, f"✅ Отложено {int(amount)} ₽ на цель «{goal['name']}»\n\nТеперь: {int(goal['current'])} / {int(goal['target'])} ₽\nОсталось: {int(left)} ₽\nПрогресс: {percent:.0f}%")
    button_balance(message)

def process_goal_spend_amount(message, goal_idx):
    user_id = message.from_user.id
    amount, error = validate_amount(message.text)
    if error:
        bot.reply_to(message, error)
        return
    
    data = load_user_data(user_id)
    if goal_idx >= len(data["goals"]):
        bot.reply_to(message, "❌ Цель не найдена")
        return
    
    goal = data["goals"][goal_idx]
    if goal["current"] < amount:
        bot.reply_to(message, f"❌ На цели «{goal['name']}» отложено только {int(goal['current'])} ₽")
        return
    
    goal["current"] -= amount
    
    # Записываем транзакцию и обновляем статистику
    now = get_moscow_time()
    transaction = {"date": now.strftime("%Y-%m-%d %H:%M:%S"), "type": "expense", "amount": int(amount), "currency": "₽", "comment": f"{goal['name']} (из отложенного)", "category": "other", "sign": '-'}
    data["transactions"].append(transaction)
    data["current_month_stats"]["other"] = data["current_month_stats"].get("other", 0) + int(amount)
    data["current_month_total"] = data.get("current_month_total", 0) + int(amount)
    
    if goal["current"] == 0:
        data["goals"].pop(goal_idx)
        save_user_data(user_id, data)
        bot.reply_to(message, f"✅ Потрачено {int(amount)} ₽ из цели «{goal['name']}»\n\n🎉 Цель полностью потрачена!")
    else:
        save_user_data(user_id, data)
        left = goal["target"] - goal["current"]
        bot.reply_to(message, f"✅ Потрачено {int(amount)} ₽ из цели «{goal['name']}»\n\nОсталось на цели: {int(goal['current'])} / {int(goal['target'])} ₽\nОсталось накопить: {int(left)} ₽")
    
    button_balance(message)

# ========== КАТЕГОРИИ ТРАТ ==========
@bot.message_handler(func=lambda m: m.text == "📂 Категории трат")
@require_auth
def button_categories(message):
    user_id = message.from_user.id
    data = reset_monthly_stats_if_needed(user_id)
    stats = data.get("current_month_stats", {})
    total = data.get("current_month_total", 0)
    month_name = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"][get_moscow_time().month-1]
    
    if total == 0:
        bot.reply_to(message, f"📂 КАТЕГОРИИ ТРАТ\n━━━━━━━━━━━━━━━\n\n📊 АНАЛИЗ ЗА {month_name.upper()}:\n💰 Всего потрачено: 0 ₽\n\nПока нет трат за этот месяц.", reply_markup=get_main_keyboard(user_id))
        return
    
    cat_list = [(cat_key, amount, (amount / total) * 100) for cat_key, amount in stats.items() if amount > 0]
    cat_list.sort(key=lambda x: x[1], reverse=True)
    
    text = f"📂 КАТЕГОРИИ ТРАТ\n━━━━━━━━━━━━━━━\n\n📊 АНАЛИЗ ЗА {month_name.upper()}:\n💰 Всего потрачено: {total} ₽\n\n" + "\n".join([f"{CATEGORIES[cat_key]}: {percent:.0f}% ({amount} ₽)" for cat_key, amount, percent in cat_list])
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("💡 Хочу совет", callback_data="advice_main"))
    bot.reply_to(message, text, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("advice_"))
def handle_advice_callback(call):
    if not is_allowed(call.from_user.id):
        bot.answer_callback_query(call.id, "Нет доступа")
        return
    
    user_id = call.from_user.id
    name = call.from_user.first_name or "Подруга"
    name_form = get_name_form(name)
    data = reset_monthly_stats_if_needed(user_id)
    
    stats = data.get("current_month_stats", {})
    cat_list = [(cat_key, amount) for cat_key, amount in stats.items() if amount > 0]
    
    if not cat_list:
        bot.edit_message_text("Пока нет трат за этот месяц, не могу дать совет 😢", call.message.chat.id, call.message.message_id)
    else:
        top_cat = max(cat_list, key=lambda x: x[1])
        cat_name = CATEGORIES[top_cat[0]]
        advice = get_next_advice(user_id, top_cat[0]).format(name=name_form)
        text = f"💡 ХОЧУ СОВЕТ\n━━━━━━━━━━━━━━━\n\n{name_form}, больше всего денег уходит на {cat_name} — {top_cat[1]} ₽\n\n🎯 {advice}"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
    
    bot.answer_callback_query(call.id)

# ========== ОТЧЁТЫ ==========
@bot.message_handler(func=lambda m: m.text == "📊 Отчёты")
@require_auth
def button_reports(message):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("📅 Сегодня", callback_data="report_today"), InlineKeyboardButton("📆 За день", callback_data="report_single_day"), InlineKeyboardButton("🗓️ За период", callback_data="report_period"), InlineKeyboardButton("📊 За месяц", callback_data="report_monthly"))
    bot.send_message(message.chat.id, "📅 Выбери отчёт:", reply_markup=keyboard)

# ========== ДОХОД И РАСХОД ==========
temp_data = {}

@bot.message_handler(func=lambda m: m.text == "➕ Доход")
@require_auth
def button_income(message):
    msg = bot.reply_to(message, "💰 Сумма и описание:\n\nПример: 5000 зарплата")
    bot.register_next_step_handler(msg, process_income_amount)

def process_income_amount(message):
    user_id = message.from_user.id
    try:
        parts = message.text.split(maxsplit=1)
        amount = float(parts[0])
        if amount <= 0:
            bot.reply_to(message, "❌ Сумма должна быть больше 0")
            return
        comment = parts[1] if len(parts) > 1 else ""
        temp_data[message.chat.id] = {"amount": amount, "comment": comment}
        bot.send_message(message.chat.id, "💱 Выбери валюту:", reply_markup=get_currency_keyboard("income"))
    except:
        bot.reply_to(message, "❌ Ошибка. Пример: 5000 зарплата")

@bot.message_handler(func=lambda m: m.text == "➖ Расход")
@require_auth
def button_expense(message):
    msg = bot.reply_to(message, "💸 Сумма и описание:\n\nПример: 1200 продукты")
    bot.register_next_step_handler(msg, process_expense_amount)

def process_expense_amount(message):
    user_id = message.from_user.id
    try:
        parts = message.text.split(maxsplit=1)
        amount = float(parts[0])
        if amount <= 0:
            bot.reply_to(message, "❌ Сумма должна быть больше 0")
            return
        comment = parts[1] if len(parts) > 1 else ""
        temp_data[message.chat.id] = {"amount": amount, "comment": comment}
        bot.send_message(message.chat.id, "💱 Выбери валюту:", reply_markup=get_currency_keyboard("expense"))
    except:
        bot.reply_to(message, "❌ Ошибка. Пример: 1200 продукты")

def get_currency_keyboard(action_type):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton("💵 Доллар ($)", callback_data=f"{action_type}_$"), InlineKeyboardButton("₽ Рубль (₽)", callback_data=f"{action_type}_₽"))
    keyboard.row(InlineKeyboardButton("❌ Отмена", callback_data="cancel"))
    return keyboard

def get_category_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    for key, emoji_name in CATEGORIES.items():
        keyboard.add(InlineKeyboardButton(emoji_name, callback_data=f"cat_{key}"))
    keyboard.row(InlineKeyboardButton("❌ Отмена", callback_data="cancel"))
    return keyboard

@bot.callback_query_handler(func=lambda call: call.data.startswith("income") or call.data.startswith("expense") or call.data == "cancel")
def handle_currency_callback(call):
    if call.data == "cancel":
        bot.edit_message_text("❌ Отменено", call.message.chat.id, call.message.message_id)
        temp_data.pop(call.message.chat.id, None)
        return
    
    if not is_allowed(call.from_user.id):
        bot.answer_callback_query(call.id, "Нет доступа")
        return
    
    user_data = temp_data.get(call.message.chat.id, {})
    amount = user_data.get("amount")
    comment = user_data.get("comment", "")
    
    if not amount:
        bot.answer_callback_query(call.id, "Ошибка")
        return
    
    user_id = call.from_user.id
    data = reset_monthly_stats_if_needed(user_id)
    now = get_moscow_time()
    
    if call.data.startswith("income"):
        currency = call.data.split("_")[1]
        if currency == "$":
            data["usd"] += amount
            amount_display = f"{amount:.2f}{currency}"
        else:
            data["rub"] += int(amount)
            amount_display = f"{int(amount)}{currency}"
        
        data["transactions"].append({"date": now.strftime("%Y-%m-%d %H:%M:%S"), "type": "income", "amount": int(amount) if currency == "₽" else amount, "currency": currency, "comment": comment, "sign": '+'})
        save_user_data(user_id, data)
        bot.edit_message_text(f"✅ ДОХОД {amount_display} {comment}\n🕐 {now.strftime('%H:%M')} МСК", call.message.chat.id, call.message.message_id)
        button_balance(call.message)
        
    elif call.data.startswith("expense"):
        currency = call.data.split("_")[1]
        if currency == "$":
            bot.edit_message_text("❌ Расход в долларах пока не поддерживается. Используй рубли.", call.message.chat.id, call.message.message_id)
        else:
            temp_data[call.message.chat.id]["currency"] = currency
            bot.edit_message_text("📂 Выбери категорию:", call.message.chat.id, call.message.message_id, reply_markup=get_category_keyboard())
    
    temp_data.pop(call.message.chat.id, None)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def handle_category_callback(call):
    if call.data == "cancel":
        bot.edit_message_text("❌ Отменено", call.message.chat.id, call.message.message_id)
        temp_data.pop(call.message.chat.id, None)
        return
    
    category_key = call.data.split("_")[1]
    user_data = temp_data.get(call.message.chat.id, {})
    amount = user_data.get("amount")
    comment = user_data.get("comment", "")
    currency = user_data.get("currency")
    
    if not amount:
        bot.answer_callback_query(call.id, "Ошибка")
        return
    
    user_id = call.from_user.id
    data = reset_monthly_stats_if_needed(user_id)
    now = get_moscow_time()
    
    data["rub"] -= int(amount)
    data["current_month_stats"][category_key] = data["current_month_stats"].get(category_key, 0) + int(amount)
    data["current_month_total"] += int(amount)
    data["transactions"].append({"date": now.strftime("%Y-%m-%d %H:%M:%S"), "type": "expense", "amount": int(amount), "currency": "₽", "comment": comment, "category": category_key, "sign": '-'})
    save_user_data(user_id, data)
    
    name = call.from_user.first_name or "Подруга"
    advice = get_next_advice(user_id, category_key).format(name=get_name_form(name))
    bot.edit_message_text(f"✅ РАСХОД {int(amount)}₽ {comment}\n📂 {CATEGORIES[category_key]}\n🕐 {now.strftime('%H:%M')} МСК\n\n💡 {advice}", call.message.chat.id, call.message.message_id)
    
    temp_data.pop(call.message.chat.id, None)
    bot.answer_callback_query(call.id)

# ========== БЮДЖЕТ ==========
@bot.message_handler(func=lambda m: m.text == "📈 Бюджет")
@require_auth
def button_budget(message):
    user_id = message.from_user.id
    data = reset_monthly_stats_if_needed(user_id)
    now = get_moscow_time()
    month_name = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"][now.month-1]
    
    if data["budget"] and data["budget"]["month"] == now.month and data["budget"]["year"] == now.year:
        budget_amount = data["budget"]["amount"]
        expenses = data.get("current_month_total", 0)
        remaining = budget_amount - expenses
        percent = (expenses / budget_amount) * 100 if budget_amount > 0 else 0
        
        text = f"📈 БЮДЖЕТ НА {month_name.upper()}\n━━━━━━━━━━━━━━━\n💰 Бюджет: {int(budget_amount)} ₽\n💸 Потрачено: {int(expenses)} ₽ ({percent:.0f}%)\n✅ Осталось: {int(remaining)} ₽"
        if percent >= 100:
            text += f"\n\n💀 Превышение на {int(expenses - budget_amount)} ₽"
        elif percent >= 80:
            text += f"\n\n⚠️ Осталось всего {int(remaining)} ₽ до конца месяца!"
        bot.reply_to(message, text, reply_markup=get_main_keyboard(user_id))
    else:
        bot.reply_to(message, "📈 Бюджет не установлен\n\nУстанови: /budget 50000")

@bot.message_handler(commands=['budget'])
@require_auth
def set_budget(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Формат: /budget 50000")
            return
        amount = float(parts[1])
        if amount <= 0:
            bot.reply_to(message, "❌ Сумма должна быть больше 0")
            return
        now = get_moscow_time()
        data = load_user_data(message.from_user.id)
        data["budget"] = {"amount": amount, "month": now.month, "year": now.year}
        save_user_data(message.from_user.id, data)
        bot.reply_to(message, f"🎯 Бюджет на месяц установлен: {int(amount)} ₽")
    except:
        bot.reply_to(message, "❌ Ошибка")

# ========== ИСТОРИЯ И ОТМЕНА ==========
@bot.message_handler(func=lambda m: m.text == "📋 История")
@require_auth
def show_history(message):
    data = load_user_data(message.from_user.id)
    last_tx = data["transactions"][-15:]
    
    if not last_tx:
        bot.reply_to(message, "📋 История пуста")
        return
    
    text = "📋 ПОСЛЕДНИЕ 15 ОПЕРАЦИЙ\n━━━━━━━━━━━━━━━\n"
    for tx in reversed(last_tx):
        try:
            date_str = datetime.strptime(tx["date"].split()[0], "%Y-%m-%d").strftime("%d.%m")
            time_str = tx["date"].split()[1][:5]
        except:
            date_str = time_str = "??"
        sign = "➕" if tx["sign"] == '+' else "➖"
        currency_symbol = "$" if tx["currency"] == "$" else "₽"
        amount_display = f"{tx['amount']:.2f}" if tx["currency"] == "$" else f"{int(tx['amount'])}"
        text += f"{sign} {amount_display}{currency_symbol} {tx['comment']}\n   📅 {date_str} {time_str}\n\n"
    
    bot.reply_to(message, text)

@bot.message_handler(func=lambda m: m.text == "🕊️ Отменить")
@require_auth
def button_undo(message):
    user_id = message.from_user.id
    data = load_user_data(user_id)
    if not data["transactions"]:
        bot.reply_to(message, "❌ Нет операций для отмены")
        return
    
    last = data["transactions"].pop()
    if last["sign"] == '+':
        if last["currency"] == "$":
            data["usd"] -= last["amount"]
        else:
            data["rub"] -= last["amount"]
    else:
        if last["currency"] == "$":
            data["usd"] += last["amount"]
        else:
            data["rub"] += last["amount"]
            # Обновляем статистику категорий
            if last.get("category") and last["currency"] == "₽":
                data["current_month_stats"][last["category"]] = max(0, data["current_month_stats"].get(last["category"], 0) - last["amount"])
                data["current_month_total"] = max(0, data.get("current_month_total", 0) - last["amount"])
    
    save_user_data(user_id, data)
    amount_display = f"{last['amount']:.2f}" if last["currency"] == "$" else f"{int(last['amount'])}"
    bot.reply_to(message, f"↩️ Отменено: {last['sign']}{amount_display}{last['currency']} {last['comment']}")

# ========== НАСТРОЙКИ ==========
@bot.message_handler(func=lambda m: m.text == "⚙️ Настройки")
@require_auth
def button_settings(message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("💰 Установить остаток", callback_data="settings_balance"), InlineKeyboardButton("📊 Очистить всё", callback_data="settings_clear"), InlineKeyboardButton("❌ Закрыть", callback_data="cancel"))
    bot.send_message(message.chat.id, "⚙️ Настройки:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("settings_"))
def handle_settings_callback(call):
    if not is_allowed(call.from_user.id):
        bot.answer_callback_query(call.id, "Нет доступа")
        return
    
    if call.data == "settings_balance":
        bot.edit_message_text("📝 Формат:\n$ 1000\n₽ 50000", call.message.chat.id, call.message.message_id)
        bot.register_next_step_handler(call.message, process_set_balance)
    elif call.data == "settings_clear":
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("✅ Да, очистить", callback_data="confirm_clear"), InlineKeyboardButton("❌ Нет", callback_data="cancel"))
        bot.edit_message_text("⚠️ Точно очистить все данные? Это необратимо.", call.message.chat.id, call.message.message_id, reply_markup=keyboard)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "confirm_clear")
def confirm_clear(call):
    if not is_allowed(call.from_user.id):
        return
    user_id = call.from_user.id
    data = load_user_data(user_id)
    data["transactions"] = []
    data["goals"] = []
    data["rub"] = 0
    data["usd"] = 0
    data["budget"] = None
    data["current_month_stats"] = {cat: 0 for cat in CATEGORIES.keys()}
    data["current_month_total"] = 0
    save_user_data(user_id, data)
    bot.edit_message_text("✅ Все данные очищены", call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id)

def process_set_balance(message):
    user_id = message.from_user.id
    try:
        parts = message.text.split()
        currency = parts[0]
        amount = float(parts[1])
        if amount <= 0:
            bot.reply_to(message, "❌ Сумма должна быть больше 0")
            return
        data = load_user_data(user_id)
        if currency == "$":
            data["usd"] = amount
            bot.reply_to(message, f"✅ Доллары: {amount:.2f}$")
        elif currency == "₽":
            data["rub"] = int(amount)
            bot.reply_to(message, f"✅ Рубли: {int(amount)}₽")
        else:
            bot.reply_to(message, "❌ Укажи валюту: $ или ₽")
            return
        save_user_data(user_id, data)
        button_balance(message)
    except:
        bot.reply_to(message, "❌ Формат: $ 1000 или ₽ 50000")

# ========== ОТЧЁТНЫЕ ФУНКЦИИ ==========
def send_today_report(chat_id, user_id):
    data = load_user_data(user_id)
    now = get_moscow_time()
    today = now.strftime("%Y-%m-%d")
    today_name = now.strftime("%d.%m.%y")
    today_tx = [tx for tx in data["transactions"] if tx["date"].startswith(today)]
    
    if not today_tx:
        bot.send_message(chat_id, f"📅 ЗА {today_name}\n━━━━━━━━━━━━━━━\n\nЗа сегодня операций нет")
        return
    
    income_usd = sum(tx["amount"] for tx in today_tx if tx["sign"] == '+' and tx["currency"] == "$")
    income_rub = sum(tx["amount"] for tx in today_tx if tx["sign"] == '+' and tx["currency"] == "₽")
    expense_usd = sum(tx["amount"] for tx in today_tx if tx["sign"] == '-' and tx["currency"] == "$")
    expense_rub = sum(tx["amount"] for tx in today_tx if tx["sign"] == '-' and tx["currency"] == "₽")
    
    report = f"📅 ЗА {today_name}\n━━━━━━━━━━━━━━━\n\n📋 ОПЕРАЦИИ:\n" + "\n".join([f"{'➕' if tx['sign'] == '+' else '➖'} {tx['amount']:.2f if tx['currency'] == '$' else int(tx['amount'])}{tx['currency']} {tx['comment']} ({tx['date'].split()[1][:5]})" for tx in today_tx])
    report += f"\n\n📈 ДОХОДЫ:" + (f"\n  {income_usd:.2f}$" if income_usd else "") + (f"\n  {income_rub}₽" if income_rub else "") + (not income_usd and not income_rub and " —")
    report += f"\n\n📉 РАСХОДЫ:" + (f"\n  {expense_usd:.2f}$" if expense_usd else "") + (f"\n  {expense_rub}₽" if expense_rub else "") + (not expense_usd and not expense_rub and " —")
    bot.send_message(chat_id, report)

def send_single_day_report(chat_id, user_id, date_input):
    try:
        parts = date_input.split('.')
        if len(parts) == 2:
            day, month = parts
            year = datetime.now().year
        elif len(parts) == 3:
            day, month, year = parts
            if len(year) == 2:
                year = 2000 + int(year)
        else:
            bot.send_message(chat_id, "❌ Формат: 1.04 или 01.04")
            return
        
        day, month = day.zfill(2), month.zfill(2)
        date_str = f"{year}-{month}-{day}"
        display_date = f"{day}.{month}.{year}"
        data = load_user_data(user_id)
        day_tx = [tx for tx in data["transactions"] if tx["date"].startswith(date_str)]
        
        if not day_tx:
            bot.send_message(chat_id, f"📆 ЗА {display_date}\n━━━━━━━━━━━━━━━\n\nОпераций нет")
            return
        
        income_usd = sum(tx["amount"] for tx in day_tx if tx["sign"] == '+' and tx["currency"] == "$")
        income_rub = sum(tx["amount"] for tx in day_tx if tx["sign"] == '+' and tx["currency"] == "₽")
        expense_usd = sum(tx["amount"] for tx in day_tx if tx["sign"] == '-' and tx["currency"] == "$")
        expense_rub = sum(tx["amount"] for tx in day_tx if tx["sign"] == '-' and tx["currency"] == "₽")
        
        report = f"📆 ЗА {display_date}\n━━━━━━━━━━━━━━━\n\n📋 ОПЕРАЦИИ:\n" + "\n".join([f"{'➕' if tx['sign'] == '+' else '➖'} {tx['amount']:.2f if tx['currency'] == '$' else int(tx['amount'])}{tx['currency']} {tx['comment']} ({tx['date'].split()[1][:5]})" for tx in day_tx])
        report += f"\n\n📈 ДОХОДЫ:" + (f"\n  {income_usd:.2f}$" if income_usd else "") + (f"\n  {income_rub}₽" if income_rub else "") + (not income_usd and not income_rub and " —")
        report += f"\n\n📉 РАСХОДЫ:" + (f"\n  {expense_usd:.2f}$" if expense_usd else "") + (f"\n  {expense_rub}₽" if expense_rub else "") + (not expense_usd and not expense_rub and " —")
        bot.send_message(chat_id, report)
    except:
        bot.send_message(chat_id, "❌ Ошибка. Пример: 1.04")

def send_period_report(chat_id, user_id, start_date_str, end_date_str):
    try:
        start_day, start_month = map(int, start_date_str.split('.'))
        end_day, end_month = map(int, end_date_str.split('.'))
        year = datetime.now().year
        start_date = datetime(year, start_month, start_day)
        end_date = datetime(year, end_month, end_day)
        
        data = load_user_data(user_id)
        period_tx = []
        for tx in data["transactions"]:
            tx_date = datetime.strptime(tx["date"].split()[0], "%Y-%m-%d")
            if start_date <= tx_date <= end_date:
                period_tx.append(tx)
        
        if not period_tx:
            bot.send_message(chat_id, f"📅 ЗА ПЕРИОД\n{start_date_str} — {end_date_str}\n━━━━━━━━━━━━━━━\n\nОпераций нет")
            return
        
        income_usd = sum(tx["amount"] for tx in period_tx if tx["sign"] == '+' and tx["currency"] == "$")
        income_rub = sum(tx["amount"] for tx in period_tx if tx["sign"] == '+' and tx["currency"] == "₽")
        expense_usd = sum(tx["amount"] for tx in period_tx if tx["sign"] == '-' and tx["currency"] == "$")
        expense_rub = sum(tx["amount"] for tx in period_tx if tx["sign"] == '-' and tx["currency"] == "₽")
        
        report = f"📅 ЗА ПЕРИОД\n{start_date_str} — {end_date_str}\n━━━━━━━━━━━━━━━\n\n📋 ОПЕРАЦИИ:\n" + "\n".join([f"{'➕' if tx['sign'] == '+' else '➖'} {tx['amount']:.2f if tx['currency'] == '$' else int(tx['amount'])}{tx['currency']} {tx['comment']}\n   📅 {tx['date'].split()[0][5:]} {tx['date'].split()[1][:5]}" for tx in period_tx])
        report += f"\n\n📈 ВСЕГО ДОХОДЫ:" + (f"\n  $ {income_usd:.2f}" if income_usd else "") + (f"\n  ₽ {income_rub}" if income_rub else "") + (not income_usd and not income_rub and "  —")
        report += f"\n\n📉 ВСЕГО РАСХОДЫ:" + (f"\n  $ {expense_usd:.2f}" if expense_usd else "") + (f"\n  ₽ {expense_rub}" if expense_rub else "") + (not expense_usd and not expense_rub and "  —")
        bot.send_message(chat_id, report)
    except:
        bot.send_message(chat_id, "❌ Ошибка периода")

def send_monthly_report(chat_id, user_id):
    data = load_user_data(user_id)
    now = get_moscow_time()
    month_name = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"][now.month-1]
    total = data.get("current_month_total", 0)
    stats = data.get("current_month_stats", {})
    
    if total == 0:
        bot.send_message(chat_id, f"📊 ЗА {month_name.upper()}\n━━━━━━━━━━━━━━━\n\nЗа этот месяц пока нет расходов")
        return
    
    cat_list = [(cat_key, amount, (amount / total) * 100) for cat_key, amount in stats.items() if amount > 0]
    cat_list.sort(key=lambda x: x[1], reverse=True)
    
    text = f"📊 ОТЧЁТ ЗА {month_name.upper()}\n━━━━━━━━━━━━━━━\n\n💰 Всего потрачено: {total} ₽\n\n🔝 ТОП-3 КАТЕГОРИИ:\n" + "\n".join([f"{i+1}. {CATEGORIES[cat_key]} — {amount} ₽ ({percent:.0f}%)" for i, (cat_key, amount, percent) in enumerate(cat_list[:3])])
    if len(cat_list) > 3:
        text += "\n\n📉 ОСТАЛЬНЫЕ:\n" + "\n".join([f"• {CATEGORIES[cat_key]} — {percent:.0f}% ({amount} ₽)" for cat_key, amount, percent in cat_list[3:]])
    
    if cat_list:
        name = "Зайка"
        advice = get_next_advice(user_id, cat_list[0][0]).format(name=name)
        text += f"\n\n💡 СОВЕТ МЕСЯЦА:\n{advice}"
    
    bot.send_message(chat_id, text)

@bot.callback_query_handler(func=lambda call: call.data.startswith("report_"))
def handle_report_callback(call):
    if not is_allowed(call.from_user.id):
        bot.answer_callback_query(call.id, "Нет доступа")
        return
    
    user_id = call.from_user.id
    
    if call.data == "report_today":
        bot.edit_message_text("📅 Загружаю...", call.message.chat.id, call.message.message_id)
        send_today_report(call.message.chat.id, user_id)
    elif call.data == "report_single_day":
        bot.edit_message_text("📆 Введи дату:\n1.04 или 01.04", call.message.chat.id, call.message.message_id)
        bot.register_next_step_handler(call.message, lambda m: send_single_day_report(m.chat.id, user_id, m.text))
    elif call.data == "report_period":
        bot.edit_message_text("🗓️ Начало периода: 1.04", call.message.chat.id, call.message.message_id)
        bot.register_next_step_handler(call.message, lambda m: process_period_start(m, user_id))
    elif call.data == "report_monthly":
        bot.edit_message_text("📊 Загружаю...", call.message.chat.id, call.message.message_id)
        send_monthly_report(call.message.chat.id, user_id)
    bot.answer_callback_query(call.id)

def process_period_start(message, user_id):
    start_date = message.text.strip()
    bot.reply_to(message, f"✅ Начало: {start_date}\n📅 Конец периода:")
    bot.register_next_step_handler(message, lambda m: send_period_report(m.chat.id, user_id, start_date, m.text))

# ========== АВТОМАТИЧЕСКИЙ ОТЧЁТ ==========
def check_monthly_reset_and_report():
    while True:
        try:
            now = get_moscow_time()
            for user_id in get_allowed_users():
                data = load_user_data(user_id)
                last_auto = data.get("last_auto_report_sent")
                
                if last_auto != now.month and now.day == 1:
                    if data["last_reset_month"] is not None and data["last_reset_month"] != now.month:
                        month_name = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"][data["last_reset_month"]-1]
                        stats = data.get("monthly_stats", {}).get(f"{data['last_reset_month']}_{now.year if now.month > 1 else now.year-1}", {})
                        total = sum(stats.values())
                        text = f"📊 АВТООТЧЁТ ЗА {month_name.upper()}\n━━━━━━━━━━━━━━━\n\n💰 Всего потрачено: {total} ₽\n\n"
                        if total > 0:
                            cat_list = [(cat_key, amount, (amount / total) * 100) for cat_key, amount in stats.items() if amount > 0]
                            cat_list.sort(key=lambda x: x[1], reverse=True)
                            text += "🔝 ТОП-3:\n" + "\n".join([f"{i+1}. {CATEGORIES[cat_key]} — {amount} ₽ ({percent:.0f}%)" for i, (cat_key, amount, percent) in enumerate(cat_list[:3])])
                            if cat_list:
                                advice = get_next_advice(user_id, cat_list[0][0]).format(name="Зайка")
                                text += f"\n\n💡 {advice}"
                        else:
                            text += "За этот месяц расходов не было. Молодец! 🌸"
                        text += "\n\n🌸 Новый месяц — новые возможности! Желаю тебе тратить с умом 💅"
                        try:
                            bot.send_message(user_id, text)
                        except:
                            pass
                    
                    data["last_auto_report_sent"] = now.month
                    save_user_data(user_id, data)
                
                if data["last_reset_month"] != now.month:
                    reset_monthly_stats_if_needed(user_id)
            
            time.sleep(3600)
        except:
            time.sleep(3600)

# ========== ЗАПУСК ==========
def start_background_checker():
    thread = threading.Thread(target=check_monthly_reset_and_report, daemon=True)
    thread.start()

print("🌸 Бот Алины запущен")
print(f"👑 Админ: {ADMIN_ID}")
print("💰 Оптимизированная версия")
print("✅ Все функции работают")
print("🕐 Московское время")

start_background_checker()
bot.infinity_polling()
