import telebot
from datetime import datetime, timedelta
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import threading
import time
from functools import wraps

# ========== ТОКЕН ПРЯМО В КОДЕ (БЕЗ .ENV) ==========
TOKEN = "8692541391:AAFxKWsf7cRTq84LgDTwy8CqwbYUwYpdZXE"
ADMIN_ID = 463620997
DB_PATH = "bot_data.sqlite3"
SUPPORT_CONTACT = "@privetetoalina"

# ========== КАТЕГОРИИ ==========
CATEGORIES = {
    "food": "🍕 Еда",
    "transport": "🚗 Транспорт",
    "cafe": "☕ Кафе",
    "shopping": "🛒 Покупки",
    "beauty": "💄 Красота/уход",
    "home": "🏠 Дом",
    "health": "💊 Аптеки",
    "subscriptions": "📱 Подписки",
    "gifts": "🎁 Подарки",
    "travel": "✈️ Путешествия",
    "credit": "💳 Кредиты/долги",
    "dates": "❤️ Мужики/свидания",
    "other": "📝 Другое"
}

# ========== ФРАЗЫ ==========
expense_phrases = {
    "soft": [
        "{name}, ты сегодня себя порадовала — это тоже важно 💖",
        "{name}, главное — чтобы это правда принесло тебе удовольствие",
    ],
    "bold": [
        "{name}, ты сейчас реально это хотела или просто стало скучно?",
        "{name}, это покупка или эмоциональная поддержка за деньги?",
    ],
    "roast": [
        "{name}, ты не тратишь — ты эмоционально реагируешь рублём",
        "{name}, тебе не это нужно было, тебе нужно было выдохнуть",
    ]
}

income_phrases = [
    "{name}, вот это я понимаю 💅 деньги пришли",
    "{name}, давай часть сразу спрячем, пока не потратила",
]

advice_dict = {
    "food": "{name}, не ходи голодной в магазин — это автосписание силы воли.",
    "transport": "{name}, проверь: такси из усталости или реально срочно?",
    "cafe": "{name}, одна кофейня в день — норм, пять — уже утечка.",
    "shopping": "{name}, правило 24 часов спасает от 50% импульсов.",
    "credit": "{name}, закрывай долг по схеме: минимум + чуть сверху.",
    "other": "{name}, сначала заметить паттерн, потом чинить — ты уже на шаг впереди.",
}

advice_idx = {}

def get_advice(user_id, category):
    key = f"{user_id}_{category}"
    if key not in advice_idx:
        advice_idx[key] = 0
    items = advice_dict.get(category, advice_dict["other"])
    idx = advice_idx[key]
    advice_idx[key] = (idx + 1) % len(items) if isinstance(items, list) else 0
    return items.format(name=get_name_form_from_id(user_id)) if "{" in items else items

def get_name_form_from_id(user_id):
    return "Зайка"

def get_name_form(name):
    if not name:
        return "Зайка"
    name_lower = name.lower()
    if name_lower.endswith("а"):
        return name_lower[:-1].capitalize()
    return name_lower.capitalize()

def get_moscow_time():
    return datetime.utcnow() + timedelta(hours=3)

# ========== РАБОТА С ДАННЫМИ (SQLite) ==========
import sqlite3
import json

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            data TEXT NOT NULL
        )
    """)
    return conn

def load_user_data(user_id):
    conn = get_db()
    row = conn.execute("SELECT data FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return {
        "usd": 0.0, "rub": 0, "transactions": [], "goals": [],
        "budget": None, "mode": "bold",
        "current_month_stats": {cat: 0 for cat in CATEGORIES},
        "current_month_total": 0, "last_reset_month": None,
        "wishlist": [], "subscriptions": [], "moods": []
    }

def save_user_data(user_id, data):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO users(user_id, data) VALUES(?, ?)",
                 (user_id, json.dumps(data, ensure_ascii=False)))
    conn.commit()
    conn.close()

def get_allowed_users():
    conn = get_db()
    rows = conn.execute("SELECT user_id FROM users").fetchall()
    conn.close()
    users = [ADMIN_ID] + [r[0] for r in rows]
    return list(set(users))

def is_allowed(user_id):
    return user_id in get_allowed_users()

def is_admin(user_id):
    return user_id == ADMIN_ID

def ensure_user(user_id):
    if not is_allowed(user_id):
        save_user_data(user_id, load_user_data(user_id))

def reset_monthly_stats_if_needed(user_id):
    data = load_user_data(user_id)
    now = get_moscow_time()
    if data["last_reset_month"] != now.month:
        if data["last_reset_month"] is not None:
            key = f"{data['last_reset_month']}_{now.year}"
            data.setdefault("monthly_stats", {})[key] = data.get("current_month_stats", {}).copy()
        data["current_month_stats"] = {cat: 0 for cat in CATEGORIES}
        data["current_month_total"] = 0
        data["last_reset_month"] = now.month
        save_user_data(user_id, data)
    return data

# ========== КЛАВИАТУРЫ ==========
def get_main_keyboard(user_id):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        "💎 Баланс", "📊 Отчёты", "➕ Доход", "➖ Расход", "🎯 Цели",
        "📈 Бюджет", "📂 Траты", "📋 История", "💭 Хочу купить",
        "📝 Вишлист", "🧾 Подписки", "🧠 Состояние", "🔥 Роаст",
        "💡 Инсайт", "🕊️ Отменить", "⚙️ Настройки"
    ]
    if is_admin(user_id):
        buttons.append("👥 Пользователи")
    kb.add(*buttons)
    return kb

def get_category_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    for key, emoji in CATEGORIES.items():
        kb.add(InlineKeyboardButton(emoji, callback_data=f"cat_{key}"))
    kb.row(InlineKeyboardButton("❌ Отмена", callback_data="cancel"))
    return kb

# ========== БОТ ==========
bot = telebot.TeleBot(TOKEN)
user_states = {}

def require_auth(func):
    @wraps(func)
    def wrapper(message, *args, **kwargs):
        if not is_allowed(message.from_user.id):
            bot.reply_to(message, "🔒 У тебя нет доступа. Напиши Алине.")
            return
        return func(message, *args, **kwargs)
    return wrapper

def require_admin(func):
    @wraps(func)
    def wrapper(message, *args, **kwargs):
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "❌ Только для админа.")
            return
        return func(message, *args, **kwargs)
    return wrapper

# ========== СТАРТ ==========
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    name = message.from_user.first_name or "Подруга"
    
    if not is_allowed(user_id):
        bot.reply_to(message, f"🌸 Привет, {name}!\n\n🔒 Доступ закрыт.\nНапиши /getid и отправь ID Алине.")
        return
    
    ensure_user(user_id)
    reset_monthly_stats_if_needed(user_id)
    
    bot.reply_to(message,
        f"🌸 Привет, {name}!\n\nЯ — твоя финансовая подруга с характером 💅\n\n"
        f"👇 Кнопки внизу:\n"
        f"➕ Доход — добавь деньги\n"
        f"➖ Расход — запиши трату\n"
        f"💎 Баланс — посмотри сколько осталось\n"
        f"🎯 Цели — копилка\n"
        f"🔥 Роаст — получи порцию правды\n\n"
        f"Погнали, красотка! 😘",
        reply_markup=get_main_keyboard(user_id))

@bot.message_handler(commands=['getid'])
def get_id(message):
    bot.reply_to(message, f"🆔 Твой ID: `{message.from_user.id}`", parse_mode='Markdown')

# ========== ПОЛЬЗОВАТЕЛИ (только админ) ==========
@bot.message_handler(commands=['adduser'])
@require_admin
def add_user(message):
    try:
        uid = int(message.text.split()[1])
        ensure_user(uid)
        bot.reply_to(message, f"✅ Пользователь {uid} добавлен")
        bot.send_message(uid, "🎉 Тебе открыли доступ! Напиши /start")
    except:
        bot.reply_to(message, "❌ /adduser 123456789")

@bot.message_handler(commands=['removeuser'])
@require_admin
def remove_user(message):
    try:
        uid = int(message.text.split()[1])
        conn = get_db()
        conn.execute("DELETE FROM users WHERE user_id = ?", (uid,))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ Пользователь {uid} удалён")
    except:
        bot.reply_to(message, "❌ /removeuser 123456789")

@bot.message_handler(func=lambda m: m.text == "👥 Пользователи")
@require_admin
def users_menu(message):
    bot.reply_to(message, "👥 Команды:\n/adduser ID\n/removeuser ID\n/users")

@bot.message_handler(commands=['users'])
@require_admin
def users_list(message):
    users = get_allowed_users()
    bot.reply_to(message, "👥 Пользователи: " + ", ".join(map(str, users)))

# ========== БАЛАНС ==========
@bot.message_handler(func=lambda m: m.text == "💎 Баланс")
@require_auth
def balance(message):
    user_id = message.from_user.id
    data = reset_monthly_stats_if_needed(user_id)
    saved = sum(g["current"] for g in data["goals"])
    free = data["rub"] - saved
    text = (f"💎 БАЛАНС\n━━━━━━━━━━\n"
            f"💰 Свободно: {free} ₽\n"
            f"🎯 Отложено: {saved} ₽\n"
            f"💎 Итого: {data['rub']} ₽\n"
            f"🇺🇸 Доллары: {data['usd']:.2f}$")
    bot.reply_to(message, text, reply_markup=get_main_keyboard(user_id))

# ========== ДОХОД ==========
@bot.message_handler(func=lambda m: m.text == "➕ Доход")
@require_auth
def income_start(message):
    user_states[message.from_user.id] = {"action": "income"}
    bot.reply_to(message, "💰 Сумма и описание:\nПример: 5000 зарплата")

# ========== РАСХОД ==========
@bot.message_handler(func=lambda m: m.text == "➖ Расход")
@require_auth
def expense_start(message):
    user_states[message.from_user.id] = {"action": "expense"}
    bot.reply_to(message, "💸 Сумма и описание:\nПример: 1200 такси")

@bot.message_handler(func=lambda m: m.text and m.text[0].isdigit())
def handle_amount(message):
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    if not state:
        return
    try:
        parts = message.text.split(maxsplit=1)
        amount = float(parts[0])
        if amount <= 0:
            bot.reply_to(message, "❌ Сумма > 0")
            return
        comment = parts[1] if len(parts) > 1 else ""
        
        if state["action"] == "income":
            data = load_user_data(user_id)
            data["rub"] += int(amount)
            data["transactions"].append({
                "date": get_moscow_time().isoformat(),
                "type": "income", "amount": int(amount),
                "currency": "₽", "comment": comment, "sign": "+"
            })
            save_user_data(user_id, data)
            phrase = income_phrases[0].format(name=message.from_user.first_name or "Зайка")
            bot.reply_to(message, f"✅ ДОХОД {int(amount)}₽ {comment}\n\n💬 {phrase}")
            balance(message)
            
        elif state["action"] == "expense":
            user_states[user_id] = {"action": "expense_currency", "amount": amount, "comment": comment}
            bot.reply_to(message, "💱 Выбери валюту:", reply_markup=get_currency_keyboard())
        user_states.pop(user_id, None)
    except:
        bot.reply_to(message, "❌ Пример: 5000 зарплата")

def get_currency_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("₽ Рубль", callback_data="currency_rub"))
    kb.add(InlineKeyboardButton("❌ Отмена", callback_data="cancel"))
    return kb

@bot.callback_query_handler(func=lambda call: call.data == "currency_rub")
def currency_rub_callback(call):
    user_id = call.from_user.id
    state = user_states.get(user_id, {})
    if not state:
        return
    user_states[user_id] = {
        "action": "expense_category",
        "amount": state["amount"],
        "comment": state["comment"]
    }
    bot.edit_message_text("📂 Выбери категорию:", call.message.chat.id, call.message.message_id, reply_markup=get_category_keyboard())
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def category_callback(call):
    user_id = call.from_user.id
    state = user_states.get(user_id, {})
    category = call.data.split("_")[1]
    amount = state.get("amount")
    comment = state.get("comment", "")
    
    data = reset_monthly_stats_if_needed(user_id)
    data["rub"] -= int(amount)
    data["current_month_stats"][category] = data["current_month_stats"].get(category, 0) + int(amount)
    data["current_month_total"] += int(amount)
    data["transactions"].append({
        "date": get_moscow_time().isoformat(),
        "type": "expense", "amount": int(amount),
        "currency": "₽", "comment": comment, "category": category, "sign": "-"
    })
    save_user_data(user_id, data)
    
    name = call.from_user.first_name or "Зайка"
    name_form = get_name_form(name)
    mode = data.get("mode", "bold")
    phrases = expense_phrases.get(mode, expense_phrases["bold"])
    reaction = phrases[0].format(name=name_form)
    advice = advice_dict.get(category, advice_dict["other"]).format(name=name_form)
    
    bot.edit_message_text(
        f"✅ РАСХОД {int(amount)}₽ {comment}\n📂 {CATEGORIES[category]}\n\n💬 {reaction}\n💡 {advice}",
        call.message.chat.id, call.message.message_id
    )
    user_states.pop(user_id, None)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def cancel_callback(call):
    bot.edit_message_text("❌ Отменено", call.message.chat.id, call.message.message_id)
    user_states.pop(call.from_user.id, None)
    bot.answer_callback_query(call.id)

# ========== ИСТОРИЯ ==========
@bot.message_handler(func=lambda m: m.text == "📋 История")
@require_auth
def history(message):
    data = load_user_data(message.from_user.id)
    tx = data["transactions"][-15:][::-1]
    if not tx:
        bot.reply_to(message, "📋 История пуста")
        return
    text = "📋 ПОСЛЕДНИЕ 15\n━━━━━━━━━━\n"
    for t in tx:
        sign = "➕" if t["sign"] == "+" else "➖"
        text += f"{sign} {t['amount']}₽ {t['comment']}\n"
    bot.reply_to(message, text)

# ========== ОТМЕНА ==========
@bot.message_handler(func=lambda m: m.text == "🕊️ Отменить")
@require_auth
def undo(message):
    user_id = message.from_user.id
    data = load_user_data(user_id)
    if not data["transactions"]:
        bot.reply_to(message, "❌ Нет операций")
        return
    last = data["transactions"].pop()
    if last["sign"] == "+":
        data["rub"] -= last["amount"]
    else:
        data["rub"] += last["amount"]
        if last.get("category"):
            data["current_month_stats"][last["category"]] = max(0, data["current_month_stats"].get(last["category"], 0) - last["amount"])
            data["current_month_total"] = max(0, data["current_month_total"] - last["amount"])
    save_user_data(user_id, data)
    bot.reply_to(message, f"↩️ Отменено: {last['comment']}")

# ========== ТРАТЫ ==========
@bot.message_handler(func=lambda m: m.text == "📂 Траты")
@require_auth
def categories_stats(message):
    user_id = message.from_user.id
    data = reset_monthly_stats_if_needed(user_id)
    total = data["current_month_total"]
    if total == 0:
        bot.reply_to(message, "📂 За месяц пока нет трат")
        return
    stats = [(k, a, (a/total)*100) for k, a in data["current_month_stats"].items() if a > 0]
    stats.sort(key=lambda x: x[1], reverse=True)
    text = f"📂 ТРАТЫ ЗА МЕСЯЦ\n💰 Всего: {total} ₽\n\n"
    for cat, amount, percent in stats[:5]:
        text += f"{CATEGORIES[cat]}: {percent:.0f}% ({amount} ₽)\n"
    bot.reply_to(message, text)

# ========== БЮДЖЕТ ==========
@bot.message_handler(func=lambda m: m.text == "📈 Бюджет")
@require_auth
def show_budget(message):
    user_id = message.from_user.id
    data = load_user_data(user_id)
    b = data.get("budget")
    if b:
        spent = data["current_month_total"]
        left = b["amount"] - spent
        text = f"📈 БЮДЖЕТ\n💰 {int(b['amount'])} ₽\n💸 Потрачено: {spent} ₽\n✅ Осталось: {left} ₽"
        bot.reply_to(message, text)
    else:
        bot.reply_to(message, "📈 Бюджет не установлен\n/budget 50000")

@bot.message_handler(commands=['budget'])
@require_auth
def set_budget(message):
    try:
        amount = float(message.text.split()[1])
        data = load_user_data(message.from_user.id)
        data["budget"] = {"amount": amount, "month": get_moscow_time().month, "year": get_moscow_time().year}
        save_user_data(message.from_user.id, data)
        bot.reply_to(message, f"✅ Бюджет: {int(amount)} ₽")
    except:
        bot.reply_to(message, "❌ /budget 50000")

# ========== ЦЕЛИ ==========
@bot.message_handler(func=lambda m: m.text == "🎯 Цели")
@require_auth
def goals_menu(message):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("📋 Список", callback_data="goals_list"),
        InlineKeyboardButton("➕ Новая цель", callback_data="goal_add"),
        InlineKeyboardButton("💰 Отложить", callback_data="goal_save"),
        InlineKeyboardButton("💸 Потратить", callback_data="goal_spend")
    )
    bot.send_message(message.chat.id, "🎯 Цели:", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "goals_list")
def goals_list(call):
    data = load_user_data(call.from_user.id)
    if not data["goals"]:
        bot.edit_message_text("🎯 Нет целей. Создай: /goal Название сумма", call.message.chat.id, call.message.message_id)
        return
    text = "🎯 МОИ ЦЕЛИ\n\n"
    for g in data["goals"]:
        p = (g["current"] / g["target"]) * 100 if g["target"] else 0
        text += f"💰 {g['name']}\n   {int(g['current'])}/{int(g['target'])} ₽ ({p:.0f}%)\n\n"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "goal_add")
def goal_add(call):
    bot.edit_message_text("🎯 Введи: Название сумма\nПример: Золотое яблочко 50000", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(call.message, process_goal_add)

def process_goal_add(message):
    try:
        name, target = message.text.rsplit(" ", 1)
        data = load_user_data(message.from_user.id)
        data["goals"].append({"name": name, "target": float(target), "current": 0})
        save_user_data(message.from_user.id, data)
        bot.reply_to(message, f"✅ Цель «{name}»: {int(float(target))} ₽")
    except:
        bot.reply_to(message, "❌ Формат: Название 50000")

@bot.callback_query_handler(func=lambda call: call.data == "goal_save")
def goal_save(call):
    data = load_user_data(call.from_user.id)
    if not data["goals"]:
        bot.edit_message_text("❌ Нет целей", call.message.chat.id, call.message.message_id)
        return
    kb = InlineKeyboardMarkup(row_width=1)
    for i, g in enumerate(data["goals"]):
        kb.add(InlineKeyboardButton(f"{g['name']}", callback_data=f"save_goal_{i}"))
    bot.edit_message_text("💰 Выбери цель:", call.message.chat.id, call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("save_goal_"))
def save_goal_amount(call):
    idx = int(call.data.split("_")[2])
    user_states[call.from_user.id] = {"action": "save_goal", "idx": idx}
    bot.edit_message_text("💰 Введи сумму:", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(call.message, process_save_goal)

def process_save_goal(message):
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    try:
        amount = float(message.text)
        data = load_user_data(user_id)
        goal = data["goals"][state["idx"]]
        saved_total = sum(g["current"] for g in data["goals"])
        free = data["rub"] - saved_total
        if free < amount:
            bot.reply_to(message, f"❌ Не хватает. Свободно: {free} ₽")
            return
        goal["current"] += amount
        save_user_data(user_id, data)
        bot.reply_to(message, f"✅ +{int(amount)} ₽ на «{goal['name']}»")
        balance(message)
    except:
        bot.reply_to(message, "❌ Введи число")
    user_states.pop(user_id, None)

@bot.callback_query_handler(func=lambda call: call.data == "goal_spend")
def goal_spend(call):
    data = load_user_data(call.from_user.id)
    if not data["goals"]:
        bot.edit_message_text("❌ Нет целей", call.message.chat.id, call.message.message_id)
        return
    kb = InlineKeyboardMarkup(row_width=1)
    for i, g in enumerate(data["goals"]):
        kb.add(InlineKeyboardButton(f"{g['name']}", callback_data=f"spend_goal_{i}"))
    bot.edit_message_text("💸 Выбери цель:", call.message.chat.id, call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("spend_goal_"))
def spend_goal_amount(call):
    idx = int(call.data.split("_")[2])
    user_states[call.from_user.id] = {"action": "spend_goal", "idx": idx}
    bot.edit_message_text("💸 Введи сумму:", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(call.message, process_spend_goal)

def process_spend_goal(message):
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    try:
        amount = float(message.text)
        data = load_user_data(user_id)
        goal = data["goals"][state["idx"]]
        if goal["current"] < amount:
            bot.reply_to(message, f"❌ Отложено только {int(goal['current'])} ₽")
            return
        goal["current"] -= amount
        if goal["current"] == 0:
            data["goals"].pop(state["idx"])
        save_user_data(user_id, data)
        bot.reply_to(message, f"✅ -{int(amount)} ₽ из «{goal['name']}»")
        balance(message)
    except:
        bot.reply_to(message, "❌ Введи число")
    user_states.pop(user_id, None)

@bot.message_handler(commands=['goal'])
@require_auth
def goal_cmd(message):
    try:
        _, name, target = message.text.split()
        data = load_user_data(message.from_user.id)
        data["goals"].append({"name": name, "target": float(target), "current": 0})
        save_user_data(message.from_user.id, data)
        bot.reply_to(message, f"✅ Цель «{name}»: {int(float(target))} ₽")
    except:
        bot.reply_to(message, "❌ /goal Название 50000")

# ========== ВИШЛИСТ ==========
@bot.message_handler(func=lambda m: m.text == "📝 Вишлист")
@require_auth
def wishlist_start(message):
    bot.reply_to(message, "📝 ВИШЛИСТ\n\n+ Название цена — добавить\nlist — показать")

@bot.message_handler(func=lambda m: m.text == "💭 Хочу купить")
@require_auth
def anti_impulse(message):
    bot.reply_to(message, "💭 Что хочешь купить и за сколько?\nПример: Наушники 7990")

# ========== ПОДПИСКИ ==========
@bot.message_handler(func=lambda m: m.text == "🧾 Подписки")
@require_auth
def subscriptions_start(message):
    bot.reply_to(message, "🧾 ПОДПИСКИ\n\n+ Название сумма — добавить\nlist — показать")

# ========== СОСТОЯНИЕ ==========
@bot.message_handler(func=lambda m: m.text == "🧠 Состояние")
@require_auth
def mood_start(message):
    kb = InlineKeyboardMarkup(row_width=2)
    for mood in ["устала", "грустно", "злая", "тревожно", "нормально", "энергия"]:
        kb.add(InlineKeyboardButton(mood, callback_data=f"mood_{mood}"))
    bot.reply_to(message, "🧠 Как ты сейчас?", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("mood_"))
def mood_callback(call):
    mood = call.data.split("_")[1]
    data = load_user_data(call.from_user.id)
    data.setdefault("moods", []).append({"date": get_moscow_time().isoformat(), "mood": mood})
    save_user_data(call.from_user.id, data)
    bot.edit_message_text(f"✅ Записала: {mood}", call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id)

# ========== РОАСТ ==========
@bot.message_handler(func=lambda m: m.text == "🔥 Роаст")
@require_auth
def roast_start(message):
    data = load_user_data(message.from_user.id)
    mode = data.get("mode", "bold")
    phrases = expense_phrases.get(mode, expense_phrases["bold"])
    name = message.from_user.first_name or "Зайка"
    bot.reply_to(message, f"🔥 {phrases[0].format(name=get_name_form(name))}")

# ========== ИНСАЙТ ==========
@bot.message_handler(func=lambda m: m.text == "💡 Инсайт")
@require_auth
def insight_start(message):
    data = load_user_data(message.from_user.id)
    total = data["current_month_total"]
    if total == 0:
        bot.reply_to(message, "💡 Пока мало данных. Добавь траты!")
        return
    stats = [(k, a) for k, a in data["current_month_stats"].items() if a > 0]
    if stats:
        top = max(stats, key=lambda x: x[1])
        name = message.from_user.first_name or "Зайка"
        bot.reply_to(message, f"💡 Больше всего ты тратишь на {CATEGORIES[top[0]]} — {top[1]} ₽. {advice_dict.get(top[0], advice_dict['other']).format(name=get_name_form(name))}")

# ========== ОТЧЁТЫ ==========
@bot.message_handler(func=lambda m: m.text == "📊 Отчёты")
@require_auth
def reports_menu(message):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("📅 Сегодня", callback_data="report_today"),
        InlineKeyboardButton("📆 За месяц", callback_data="report_month")
    )
    bot.send_message(message.chat.id, "📊 Отчёты:", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("report_"))
def report_callback(call):
    user_id = call.from_user.id
    data = load_user_data(user_id)
    if call.data == "report_today":
        today = get_moscow_time().strftime("%Y-%m-%d")
        tx = [t for t in data["transactions"] if t["date"].startswith(today)]
        if not tx:
            bot.edit_message_text("📅 За сегодня операций нет", call.message.chat.id, call.message.message_id)
        else:
            inc = sum(t["amount"] for t in tx if t["sign"] == "+")
            exp = sum(t["amount"] for t in tx if t["sign"] == "-")
            bot.edit_message_text(f"📅 СЕГОДНЯ\n💰 Доходы: {inc} ₽\n💸 Расходы: {exp} ₽", call.message.chat.id, call.message.message_id)
    elif call.data == "report_month":
        total = data["current_month_total"]
        bot.edit_message_text(f"📆 ЗА МЕСЯЦ\n💰 Всего потрачено: {total} ₽", call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id)

# ========== НАСТРОЙКИ ==========
@bot.message_handler(func=lambda m: m.text == "⚙️ Настройки")
@require_auth
def settings_menu(message):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("💰 Остаток", callback_data="set_balance"),
        InlineKeyboardButton("🎭 Режим", callback_data="set_mode"),
        InlineKeyboardButton("🗑️ Очистить всё", callback_data="clear_all")
    )
    bot.send_message(message.chat.id, "⚙️ Настройки:", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "set_balance")
def set_balance_start(call):
    bot.edit_message_text("💰 Введи: рубли доллары\nПример: 10000 50", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(call.message, process_set_balance)

def process_set_balance(message):
    try:
        rub, usd = map(float, message.text.split())
        data = load_user_data(message.from_user.id)
        data["rub"] = int(rub)
        data["usd"] = usd
        save_user_data(message.from_user.id, data)
        bot.reply_to(message, f"✅ {int(rub)} ₽, {usd:.2f}$")
        balance(message)
    except:
        bot.reply_to(message, "❌ Пример: 10000 50")

@bot.callback_query_handler(func=lambda call: call.data == "set_mode")
def set_mode_start(call):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🌸 Мягкий", callback_data="mode_soft"),
        InlineKeyboardButton("😈 Дерзкий", callback_data="mode_bold"),
        InlineKeyboardButton("🔥 Разнос", callback_data="mode_roast")
    )
    bot.edit_message_text("🎭 Выбери режим:", call.message.chat.id, call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("mode_"))
def set_mode_callback(call):
    mode = call.data.split("_")[1]
    data = load_user_data(call.from_user.id)
    data["mode"] = mode
    save_user_data(call.from_user.id, data)
    bot.edit_message_text(f"✅ Режим: {mode}", call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "clear_all")
def clear_start(call):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ ДА", callback_data="confirm_clear"), InlineKeyboardButton("❌ НЕТ", callback_data="cancel"))
    bot.edit_message_text("⚠️ Очистить всё? Необратимо.", call.message.chat.id, call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "confirm_clear")
def confirm_clear(call):
    data = load_user_data(call.from_user.id)
    data["transactions"] = []
    data["goals"] = []
    data["rub"] = 0
    data["usd"] = 0
    data["budget"] = None
    data["current_month_stats"] = {cat: 0 for cat in CATEGORIES}
    data["current_month_total"] = 0
    save_user_data(call.from_user.id, data)
    bot.edit_message_text("✅ Всё очищено", call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id)

# ========== ЗАПУСК ==========
print("🌸 Бот Алины запущен!")
print(f"👑 Админ: {ADMIN_ID}")
print("🕐 Московское время")

bot.infinity_polling()
