import telebot
import json
import os
from datetime import datetime, timedelta
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import threading
import time

# ========== НАСТРОЙКИ ==========
TOKEN = "8692541391:AAH6Cf8eh_afsynkA277SJ-_28ihs2VEutI"
ADMIN_ID = 463620997  # ⚠️ ЗАМЕНИ НА СВОЙ TELEGRAM ID

bot = telebot.TeleBot(TOKEN)
DATA_FILE = "finance.json"

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
    "other": "📝 Другое"
}

CATEGORIES_LIST = list(CATEGORIES.keys())
CATEGORIES_EMOJI = {v: k for k, v in CATEGORIES.items()}

# Московское время (UTC+3)
def get_moscow_time():
    return datetime.utcnow() + timedelta(hours=3)

# ========== РАБОТА С ДАННЫМИ ==========
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "allowed_users" not in data:
                data["allowed_users"] = []
            if "savings" not in data:
                data["savings"] = []  # [{name, amount, date}]
            if "budget" not in data:
                data["budget"] = None  # {amount, month, year}
            if "last_report_month" not in data:
                data["last_report_month"] = None
            if isinstance(data.get("rub"), float):
                data["rub"] = int(data["rub"])
            return data
    return {
        "usd": 0.0,
        "rub": 0,
        "transactions": [],
        "allowed_users": [],
        "savings": [],
        "budget": None,
        "last_report_month": None
    }

def save_data(data):
    data["rub"] = int(data["rub"])
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_admin(user_id):
    return user_id == ADMIN_ID

def is_allowed(user_id):
    data = load_data()
    return user_id == ADMIN_ID or user_id in data.get("allowed_users", [])

# ========== КЛАВИАТУРЫ ==========
def get_admin_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("💎 Баланс"),
        KeyboardButton("📊 Отчёты"),
        KeyboardButton("➕ Доход"),
        KeyboardButton("➖ Расход"),
        KeyboardButton("🏦 Отложить"),
        KeyboardButton("📈 Бюджет"),
        KeyboardButton("📊 График трат"),
        KeyboardButton("📋 История"),
        KeyboardButton("🕊️ Отменить последнее"),
        KeyboardButton("⚙️ Настройки"),
        KeyboardButton("👥 Пользователи")
    ]
    keyboard.add(*buttons)
    return keyboard

def get_user_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("💎 Баланс"),
        KeyboardButton("📊 Отчёты")
    ]
    keyboard.add(*buttons)
    return keyboard

def get_reports_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📅 Сегодня", callback_data="report_today"),
        InlineKeyboardButton("📆 За день", callback_data="report_single_day"),
        InlineKeyboardButton("🗓️ За период", callback_data="report_period")
    )
    return keyboard

def get_currency_keyboard(action_type):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("💵 Доллар ($)", callback_data=f"{action_type}_$"),
        InlineKeyboardButton("₽ Рубль (₽)", callback_data=f"{action_type}_₽")
    )
    keyboard.row(
        InlineKeyboardButton("❌ Отмена", callback_data="cancel")
    )
    return keyboard

def get_category_keyboard(transaction_type):
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = []
    for key, emoji_name in CATEGORIES.items():
        buttons.append(InlineKeyboardButton(emoji_name, callback_data=f"cat_{transaction_type}_{key}"))
    keyboard.add(*buttons)
    keyboard.row(InlineKeyboardButton("❌ Отмена", callback_data="cancel"))
    return keyboard

def get_savings_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("➕ Отложить деньги", callback_data="savings_add"),
        InlineKeyboardButton("➖ Вернуть из отложенных", callback_data="savings_remove"),
        InlineKeyboardButton("💸 Потратить из отложенного", callback_data="savings_spend"),
        InlineKeyboardButton("📋 Список отложенных", callback_data="savings_list"),
        InlineKeyboardButton("❌ Закрыть", callback_data="cancel")
    )
    return keyboard

# ========== КОМАНДА /START ==========
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    if not is_allowed(user_id):
        bot.reply_to(message,
            "🔒 *Доступ закрыт*\n\n"
            "Бот работает по приглашению.\n"
            "Отправьте свой ID администратору через /getid",
            parse_mode='Markdown')
        return

    if is_admin(user_id):
        welcome = (
            "➕ *Привет, хозяйка!* 💅\n\n"
            "Твой финансовый помощник готов.\n"
            "💰 Рубли и доллары — отдельно\n"
            "🏦 Отложенные деньги\n"
            "📊 Графики трат и бюджет\n\n"
            "👇 Кнопки внизу"
        )
        bot.reply_to(message, welcome, parse_mode='Markdown', reply_markup=get_admin_keyboard())
    else:
        welcome = "➕ *Привет!*\n\nТебе открыли доступ.\nТы можешь смотреть баланс и отчёты."
        bot.reply_to(message, welcome, parse_mode='Markdown', reply_markup=get_user_keyboard())

@bot.message_handler(commands=['getid'])
def get_id(message):
    user_id = message.from_user.id
    bot.reply_to(message,
        f"🆔 *Твой ID:* `{user_id}`\n\nПерешли этот ID администратору.",
        parse_mode='Markdown')

# ========== УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ==========
@bot.message_handler(commands=['adduser'])
def add_user(message):
    if not is_admin(message.from_user.id):
        return
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Формат: `/adduser 123456789`", parse_mode='Markdown')
            return
        new_user_id = int(parts[1])
        data = load_data()
        if new_user_id not in data["allowed_users"] and new_user_id != ADMIN_ID:
            data["allowed_users"].append(new_user_id)
            save_data(data)
            bot.reply_to(message, f"✅ Пользователь `{new_user_id}` добавлен", parse_mode='Markdown')
            try:
                bot.send_message(new_user_id, "🎉 *Вам открыли доступ!*\n\nНапишите /start", parse_mode='Markdown')
            except:
                pass
        else:
            bot.reply_to(message, f"ℹ️ Уже в списке", parse_mode='Markdown')
    except:
        bot.reply_to(message, "❌ Ошибка", parse_mode='Markdown')

@bot.message_handler(commands=['removeuser'])
def remove_user(message):
    if not is_admin(message.from_user.id):
        return
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Формат: `/removeuser 123456789`", parse_mode='Markdown')
            return
        user_id = int(parts[1])
        data = load_data()
        if user_id in data["allowed_users"]:
            data["allowed_users"].remove(user_id)
            save_data(data)
            bot.reply_to(message, f"✅ Пользователь `{user_id}` удалён", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"ℹ️ Не найден", parse_mode='Markdown')
    except:
        bot.reply_to(message, "❌ Ошибка", parse_mode='Markdown')

@bot.message_handler(commands=['users'])
def list_users(message):
    if not is_admin(message.from_user.id):
        return
    data = load_data()
    allowed = data.get("allowed_users", [])
    if not allowed:
        bot.reply_to(message, "👥 *Список пуст*", parse_mode='Markdown')
        return
    text = "👥 *ДОСТУП ЕСТЬ У:*\n━━━━━━━━━━━━━━━\n"
    for uid in allowed:
        text += f"🆔 `{uid}`\n"
    text += f"\n👑 *Админ:* `{ADMIN_ID}`"
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "👥 Пользователи")
def user_management_button(message):
    if not is_admin(message.from_user.id):
        return
    bot.reply_to(message,
        "👥 *Управление*\n━━━━━━━━━━━━━━━\n\n"
        "`/adduser ID` — добавить\n"
        "`/removeuser ID` — удалить\n"
        "`/users` — список\n"
        "`/getid` — свой ID",
        parse_mode='Markdown')

# ========== БАЛАНС ==========
@bot.message_handler(func=lambda m: m.text == "💎 Баланс")
def button_balance(message):
    if not is_allowed(message.from_user.id):
        return
    data = load_data()
    now = get_moscow_time()
    
    total_saved = sum(s["amount"] for s in data["savings"])
    free_rub = data["rub"] - total_saved
    
    text = f"💎 *БАЛАНС*\n━━━━━━━━━━━━━━━\n"
    text += f"💰 Свободно: {free_rub} ₽\n"
    text += f"🏦 Отложено: {total_saved} ₽\n"
    text += f"━━━━━━━━━━━━━━━\n"
    text += f"💎 Итого: {data['rub']} ₽\n\n"
    text += f"🇺🇸 Доллары: {data['usd']:.2f}$\n\n"
    text += f"🕐 {now.strftime('%d.%m.%Y %H:%M')} МСК"
    
    if data["savings"]:
        text += "\n\n🏦 *Отложенные цели:*\n"
        for s in data["savings"]:
            text += f"• {s['name']}: {s['amount']} ₽\n"
    
    keyboard = get_admin_keyboard() if is_admin(message.from_user.id) else get_user_keyboard()
    bot.reply_to(message, text, parse_mode='Markdown', reply_markup=keyboard)

# ========== ОТЧЁТЫ ==========
@bot.message_handler(func=lambda m: m.text == "📊 Отчёты")
def button_reports(message):
    if not is_allowed(message.from_user.id):
        return
    bot.send_message(message.chat.id, "📅 *Выбери отчёт:*", parse_mode='Markdown', reply_markup=get_reports_keyboard())

# ========== ДОХОД / РАСХОД ==========
@bot.message_handler(func=lambda m: m.text == "➕ Доход")
def button_income(message):
    if not is_admin(message.from_user.id):
        return
    msg = bot.reply_to(message, "💰 *Сумма и описание:*\n\nПример: `5000 зарплата`", parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_income_amount)

@bot.message_handler(func=lambda m: m.text == "➖ Расход")
def button_expense(message):
    if not is_admin(message.from_user.id):
        return
    msg = bot.reply_to(message, "💸 *Сумма и описание:*\n\nПример: `1200 продукты`", parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_expense_amount)

def process_income_amount(message):
    try:
        parts = message.text.split()
        amount = float(parts[0])
        comment = " ".join(parts[1:]) if len(parts) > 1 else ""
        if not hasattr(bot, "temp_data"):
            bot.temp_data = {}
        bot.temp_data[message.chat.id] = {"amount": amount, "comment": comment}
        bot.send_message(message.chat.id, "💱 *Выбери валюту:*", parse_mode='Markdown', reply_markup=get_currency_keyboard("income"))
    except:
        bot.reply_to(message, "❌ Ошибка. Формат: `5000 зарплата`", parse_mode='Markdown')

def process_expense_amount(message):
    try:
        parts = message.text.split()
        amount = float(parts[0])
        comment = " ".join(parts[1:]) if len(parts) > 1 else ""
        if not hasattr(bot, "temp_data"):
            bot.temp_data = {}
        bot.temp_data[message.chat.id] = {"amount": amount, "comment": comment, "need_category": True}
        bot.send_message(message.chat.id, "💱 *Выбери валюту:*", parse_mode='Markdown', reply_markup=get_currency_keyboard("expense"))
    except:
        bot.reply_to(message, "❌ Ошибка. Формат: `1200 продукты`", parse_mode='Markdown')

# ========== ОТЛОЖЕННЫЕ ДЕНЬГИ ==========
@bot.message_handler(func=lambda m: m.text == "🏦 Отложить")
def button_savings(message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(message.chat.id, "🏦 *Управление отложенными деньгами:*", parse_mode='Markdown', reply_markup=get_savings_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("savings_"))
def handle_savings_callback(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Только администратор")
        return
    
    if call.data == "savings_add":
        bot.edit_message_text("💰 *Сумма и цель:*\n\nПример: `10000 новый телефон`", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        bot.register_next_step_handler(call.message, process_savings_add)
    elif call.data == "savings_remove":
        bot.edit_message_text("💰 *Сумма и цель (снять с отложенного):*\n\nПример: `2000 отпуск`", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        bot.register_next_step_handler(call.message, process_savings_remove)
    elif call.data == "savings_spend":
        bot.edit_message_text("💸 *Сумма и цель (потратить из отложенного):*\n\nПример: `3000 новый телефон`", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        bot.register_next_step_handler(call.message, process_savings_spend)
    elif call.data == "savings_list":
        show_savings_list(call.message)
    bot.answer_callback_query(call.id)

def process_savings_add(message):
    try:
        parts = message.text.split()
        amount = float(parts[0])
        name = " ".join(parts[1:]) if len(parts) > 1 else "без названия"
        data = load_data()
        
        total_saved = sum(s["amount"] for s in data["savings"])
        if data["rub"] - total_saved < amount:
            bot.reply_to(message, f"❌ Недостаточно свободных денег. Свободно: {data['rub'] - total_saved} ₽")
            return
        
        data["savings"].append({
            "name": name,
            "amount": amount,
            "date": get_moscow_time().isoformat()
        })
        save_data(data)
        bot.reply_to(message, f"✅ Отложено: {amount} ₽ на «{name}»")
        button_balance(message)
    except:
        bot.reply_to(message, "❌ Ошибка. Формат: `10000 новый телефон`", parse_mode='Markdown')

def process_savings_remove(message):
    try:
        parts = message.text.split()
        amount = float(parts[0])
        name = " ".join(parts[1:]) if len(parts) > 1 else ""
        data = load_data()
        
        for s in data["savings"]:
            if name.lower() in s["name"].lower():
                if s["amount"] >= amount:
                    s["amount"] -= amount
                    if s["amount"] == 0:
                        data["savings"].remove(s)
                    save_data(data)
                    bot.reply_to(message, f"✅ Возвращено из отложенных: {amount} ₽ из «{s['name']}»")
                    button_balance(message)
                    return
                else:
                    bot.reply_to(message, f"❌ В «{s['name']}» отложено только {s['amount']} ₽")
                    return
        bot.reply_to(message, f"❌ Цель «{name}» не найдена")
    except:
        bot.reply_to(message, "❌ Ошибка. Формат: `2000 отпуск`", parse_mode='Markdown')

def process_savings_spend(message):
    try:
        parts = message.text.split()
        amount = float(parts[0])
        name = " ".join(parts[1:]) if len(parts) > 1 else ""
        data = load_data()
        
        for s in data["savings"]:
            if name.lower() in s["name"].lower():
                if s["amount"] >= amount:
                    s["amount"] -= amount
                    if s["amount"] == 0:
                        data["savings"].remove(s)
                    
                    # Добавляем транзакцию расхода из отложенного
                    now = get_moscow_time()
                    transaction = {
                        "date": now.strftime("%Y-%m-%d %H:%M:%S"),
                        "type": "expense_saved",
                        "amount": int(amount),
                        "currency": "₽",
                        "comment": f"{name} (из отложенного)",
                        "sign": '-'
                    }
                    data["transactions"].append(transaction)
                    save_data(data)
                    bot.reply_to(message, f"✅ Потрачено из отложенного: {amount} ₽ на «{name}»")
                    button_balance(message)
                    return
                else:
                    bot.reply_to(message, f"❌ В «{s['name']}» отложено только {s['amount']} ₽")
                    return
        bot.reply_to(message, f"❌ Цель «{name}» не найдена")
    except:
        bot.reply_to(message, "❌ Ошибка. Формат: `3000 новый телефон`", parse_mode='Markdown')

def show_savings_list(message):
    data = load_data()
    if not data["savings"]:
        bot.reply_to(message, "🏦 *Нет отложенных денег*", parse_mode='Markdown')
        return
    text = "🏦 *ОТЛОЖЕННЫЕ ЦЕЛИ:*\n━━━━━━━━━━━━━━━\n"
    for s in data["savings"]:
        text += f"• {s['name']}: {s['amount']} ₽\n"
    bot.reply_to(message, text, parse_mode='Markdown')

# ========== БЮДЖЕТ ==========
@bot.message_handler(func=lambda m: m.text == "📈 Бюджет")
def button_budget(message):
    if not is_admin(message.from_user.id):
        return
    data = load_data()
    now = get_moscow_time()
    current_month = now.month
    current_year = now.year
    
    if data["budget"] and data["budget"]["month"] == current_month and data["budget"]["year"] == current_year:
        budget_amount = data["budget"]["amount"]
        # Считаем расходы за месяц
        expenses = 0
        for t in data["transactions"]:
            try:
                t_date = datetime.strptime(t["date"].split()[0], "%Y-%m-%d")
                if t_date.month == current_month and t_date.year == current_year and t["type"] == "expense" and t["currency"] == "₽":
                    expenses += t["amount"]
            except:
                pass
        remaining = budget_amount - expenses
        percent = (expenses / budget_amount) * 100 if budget_amount > 0 else 0
        
        text = f"📈 *БЮДЖЕТ НА {now.strftime('%B')}*\n━━━━━━━━━━━━━━━\n"
        text += f"💰 Бюджет: {budget_amount} ₽\n"
        text += f"💸 Потрачено: {expenses} ₽ ({percent:.0f}%)\n"
        text += f"✅ Осталось: {remaining} ₽\n"
        
        if percent >= 90:
            text += "\n⚠️ *Внимание! Бюджет почти исчерпан!*"
        elif percent >= 70:
            text += "\n⚠️ Бюджет заканчивается, будь аккуратнее."
        
        bot.reply_to(message, text, parse_mode='Markdown')
    else:
        bot.reply_to(message, 
            "📈 *Бюджет не установлен*\n\n"
            "Установи бюджет на месяц:\n"
            "`/budget 50000`\n\n"
            "Пример: `/budget 50000`",
            parse_mode='Markdown')

@bot.message_handler(commands=['budget'])
def set_budget(message):
    if not is_admin(message.from_user.id):
        return
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Формат: `/budget 50000`", parse_mode='Markdown')
            return
        amount = float(parts[1])
        now = get_moscow_time()
        data = load_data()
        data["budget"] = {
            "amount": amount,
            "month": now.month,
            "year": now.year
        }
        save_data(data)
        bot.reply_to(message, f"✅ Бюджет на {now.strftime('%B')} установлен: {amount} ₽")
    except:
        bot.reply_to(message, "❌ Ошибка. Формат: `/budget 50000`", parse_mode='Markdown')

# ========== ГРАФИК ТРАТ ==========
@bot.message_handler(func=lambda m: m.text == "📊 График трат")
def button_spending_chart(message):
    if not is_admin(message.from_user.id):
        return
    
    data = load_data()
    now = get_moscow_time()
    current_month = now.month
    current_year = now.year
    
    # Считаем расходы по категориям за месяц
    category_expenses = {cat: 0 for cat in CATEGORIES.keys()}
    total_expenses = 0
    
    for t in data["transactions"]:
        try:
            t_date = datetime.strptime(t["date"].split()[0], "%Y-%m-%d")
            if t_date.month == current_month and t_date.year == current_year and t["type"] == "expense" and t["currency"] == "₽":
                cat = t.get("category", "other")
                if cat in category_expenses:
                    category_expenses[cat] += t["amount"]
                    total_expenses += t["amount"]
        except:
            pass
    
    if total_expenses == 0:
        bot.reply_to(message, f"📊 *За {now.strftime('%B')} расходов нет*", parse_mode='Markdown')
        return
    
    # Сортируем по сумме
    sorted_cats = sorted(category_expenses.items(), key=lambda x: x[1], reverse=True)
    
    # Максимальная сумма для масштаба (50 символов максимум)
    max_amount = max(cat[1] for cat in sorted_cats if cat[1] > 0)
    max_bars = 30
    
    text = f"📊 *ГРАФИК ТРАТ ЗА {now.strftime('%B')}*\n━━━━━━━━━━━━━━━\n"
    text += f"💰 Всего потрачено: {total_expenses} ₽\n\n"
    
    for cat_key, amount in sorted_cats:
        if amount == 0:
            continue
        percent = amount / max_amount if max_amount > 0 else 0
        bars = int(percent * max_bars)
        bar_str = "█" * bars if bars > 0 else "▏"
        cat_name = CATEGORIES[cat_key]
        text += f"{cat_name}: {bar_str} {amount} ₽\n"
    
    bot.reply_to(message, text, parse_mode='Markdown')

# ========== ИСТОРИЯ ==========
@bot.message_handler(func=lambda m: m.text == "📋 История")
def show_history(message):
    if not is_allowed(message.from_user.id):
        return
    data = load_data()
    last_tx = data["transactions"][-15:]
    
    if not last_tx:
        bot.reply_to(message, "📋 *История пуста*", parse_mode='Markdown')
        return
    
    text = "📋 *ПОСЛЕДНИЕ 15 ОПЕРАЦИЙ*\n━━━━━━━━━━━━━━━\n"
    for tx in reversed(last_tx):
        try:
            date_obj = datetime.strptime(tx["date"].split()[0], "%Y-%m-%d")
            date_str = date_obj.strftime("%d.%m")
            time_str = tx["date"].split()[1][:5]
        except:
            date_str = "??"
            time_str = "??:??"
        
        sign = "➕" if tx["sign"] == '+' else "➖"
        currency_symbol = "$" if tx["currency"] == "$" else "₽"
        amount_display = f"{tx['amount']:.2f}" if tx["currency"] == "$" else f"{int(tx['amount'])}"
        
        text += f"{sign} {amount_display}{currency_symbol} {tx['comment']}\n   📅 {date_str} {time_str}\n\n"
    
    bot.reply_to(message, text, parse_mode='Markdown')

# ========== ОТМЕНИТЬ ПОСЛЕДНЕЕ ==========
@bot.message_handler(func=lambda m: m.text == "🕊️ Отменить последнее")
def button_undo(message):
    if not is_admin(message.from_user.id):
        return
    data = load_data()
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
    save_data(data)
    amount_display = f"{last['amount']:.2f}" if last["currency"] == "$" else f"{int(last['amount'])}"
    bot.reply_to(message, f"✅ Отменено: {last['sign']}{amount_display}{last['currency']} {last['comment']}")

# ========== УСТАНОВИТЬ ОСТАТОК ==========
@bot.message_handler(func=lambda m: m.text == "⚙️ Настройки")
def button_settings(message):
    if not is_admin(message.from_user.id):
        return
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("💰 Установить остаток", callback_data="settings_balance"))
    keyboard.add(InlineKeyboardButton("📊 Очистить все данные", callback_data="settings_clear"))
    keyboard.add(InlineKeyboardButton("❌ Закрыть", callback_data="cancel"))
    bot.send_message(message.chat.id, "⚙️ *Настройки:*", parse_mode='Markdown', reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("settings_"))
def handle_settings_callback(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Только администратор")
        return
    
    if call.data == "settings_balance":
        bot.edit_message_text("📝 *Формат:*\n`$ 1000`\n`₽ 50000`", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        bot.register_next_step_handler(call.message, process_set_balance)
    elif call.data == "settings_clear":
        bot.edit_message_text("⚠️ *Точно очистить все данные?*\nЭто действие необратимо.", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("✅ Да, очистить", callback_data="confirm_clear"))
        keyboard.add(InlineKeyboardButton("❌ Нет", callback_data="cancel"))
        bot.send_message(call.message.chat.id, "Подтверждение:", reply_markup=keyboard)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "confirm_clear")
def confirm_clear(call):
    if not is_admin(call.from_user.id):
        return
    data = load_data()
    data["transactions"] = []
    data["savings"] = []
    data["rub"] = 0
    data["usd"] = 0
    data["budget"] = None
    save_data(data)
    bot.edit_message_text("✅ *Все данные очищены*", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
    bot.answer_callback_query(call.id)

def process_set_balance(message):
    try:
        parts = message.text.split()
        currency = parts[0]
        amount = float(parts[1])
        data = load_data()
        if currency == "$":
            data["usd"] = amount
            bot.reply_to(message, f"✅ Доллары: {amount:.2f}$")
        elif currency == "₽":
            data["rub"] = int(amount)
            bot.reply_to(message, f"✅ Рубли: {int(amount)}₽")
        else:
            bot.reply_to(message, "❌ Укажи валюту: `$` или `₽`", parse_mode='Markdown')
            return
        save_data(data)
        button_balance(message)
    except:
        bot.reply_to(message, "❌ Формат: `$ 1000` или `₽ 50000`", parse_mode='Markdown')

# ========== ОБРАБОТКА ВЫБОРА ВАЛЮТЫ И КАТЕГОРИЙ ==========
@bot.callback_query_handler(func=lambda call: call.data.startswith("income") or call.data.startswith("expense") or call.data == "cancel")
def handle_currency_callback(call):
    if call.data == "cancel":
        bot.edit_message_text("❌ Отменено", call.message.chat.id, call.message.message_id)
        if hasattr(bot, "temp_data") and call.message.chat.id in bot.temp_data:
            del bot.temp_data[call.message.chat.id]
        return
    
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Только администратор")
        return
    
    user_data = getattr(bot, "temp_data", {}).get(call.message.chat.id, {})
    amount = user_data.get("amount")
    comment = user_data.get("comment", "")
    need_category = user_data.get("need_category", False)
    
    if not amount:
        bot.answer_callback_query(call.id, "Ошибка")
        return
    
    if call.data.startswith("income"):
        currency = call.data.split("_")[1]
        data = load_data()
        if currency == "$":
            data["usd"] += amount
            amount_display = f"{amount:.2f}{currency}"
        else:
            data["rub"] += int(amount)
            amount_display = f"{int(amount)}{currency}"
        
        now = get_moscow_time()
        transaction = {
            "date": now.strftime("%Y-%m-%d %H:%M:%S"),
            "type": "income",
            "amount": int(amount) if currency == "₽" else amount,
            "currency": currency,
            "comment": comment,
            "sign": '+'
        }
        data["transactions"].append(transaction)
        save_data(data)
        
        bot.edit_message_text(
            f"✅ ДОХОД {amount_display} {comment}\n🕐 {now.strftime('%H:%M')} МСК",
            call.message.chat.id,
            call.message.message_id
        )
        button_balance(call.message)
        
    elif call.data.startswith("expense"):
        currency = call.data.split("_")[1]
        if need_category:
            bot.temp_data[call.message.chat.id]["currency"] = currency
            bot.temp_data[call.message.chat.id]["amount_display"] = amount
            bot.edit_message_text("📂 *Выбери категорию расхода:*", call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=get_category_keyboard("expense"))
        else:
            data = load_data()
            if currency == "$":
                data["usd"] -= amount
                amount_display = f"{amount:.2f}{currency}"
            else:
                data["rub"] -= int(amount)
                amount_display = f"{int(amount)}{currency}"
            
            now = get_moscow_time()
            transaction = {
                "date": now.strftime("%Y-%m-%d %H:%M:%S"),
                "type": "expense",
                "amount": int(amount) if currency == "₽" else amount,
                "currency": currency,
                "comment": comment,
                "category": "other",
                "sign": '-'
            }
            data["transactions"].append(transaction)
            save_data(data)
            
            bot.edit_message_text(
                f"✅ РАСХОД {amount_display} {comment}\n🕐 {now.strftime('%H:%M')} МСК",
                call.message.chat.id,
                call.message.message_id
            )
            button_balance(call.message)
    
    if hasattr(bot, "temp_data") and call.message.chat.id in bot.temp_data and not need_category:
        del bot.temp_data[call.message.chat.id]
    
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def handle_category_callback(call):
    if call.data == "cancel":
        bot.edit_message_text("❌ Отменено", call.message.chat.id, call.message.message_id)
        if hasattr(bot, "temp_data") and call.message.chat.id in bot.temp_data:
            del bot.temp_data[call.message.chat.id]
        return
    
    parts = call.data.split("_")
    transaction_type = parts[1]
    category_key = parts[2]
    
    user_data = getattr(bot, "temp_data", {}).get(call.message.chat.id, {})
    amount = user_data.get("amount")
    comment = user_data.get("comment", "")
    currency = user_data.get("currency")
    
    if not amount:
        bot.answer_callback_query(call.id, "Ошибка")
        return
    
    data = load_data()
    if currency == "$":
        data["usd"] -= amount
        amount_display = f"{amount:.2f}{currency}"
    else:
        data["rub"] -= int(amount)
        amount_display = f"{int(amount)}{currency}"
    
    now = get_moscow_time()
    transaction = {
        "date": now.strftime("%Y-%m-%d %H:%M:%S"),
        "type": "expense",
        "amount": int(amount) if currency == "₽" else amount,
        "currency": currency,
        "comment": comment,
        "category": category_key,
        "sign": '-'
    }
    data["transactions"].append(transaction)
    save_data(data)
    
    category_name = CATEGORIES[category_key]
    bot.edit_message_text(
        f"✅ РАСХОД {amount_display} {comment}\n📂 {category_name}\n🕐 {now.strftime('%H:%M')} МСК",
        call.message.chat.id,
        call.message.message_id
    )
    button_balance(call.message)
    
    if hasattr(bot, "temp_data") and call.message.chat.id in bot.temp_data:
        del bot.temp_data[call.message.chat.id]
    
    bot.answer_callback_query(call.id)

# ========== ОТЧЁТЫ: СЕГОДНЯ / ДЕНЬ / ПЕРИОД ==========
def send_today_report(chat_id):
    data = load_data()
    now = get_moscow_time()
    today = now.strftime("%Y-%m-%d")
    today_name = now.strftime("%d.%m.%y")
    
    income_usd = expense_usd = 0.0
    income_rub = expense_rub = 0
    today_tx = []
    
    for tx in data["transactions"]:
        if tx["date"].startswith(today):
            today_tx.append(tx)
            if tx["sign"] == '+':
                if tx["currency"] == "$":
                    income_usd += tx["amount"]
                else:
                    income_rub += tx["amount"]
            else:
                if tx["currency"] == "$":
                    expense_usd += tx["amount"]
                else:
                    expense_rub += tx["amount"]
    
    if not today_tx:
        bot.send_message(chat_id, f"📅 *ЗА {today_name}*\n━━━━━━━━━━━━━━━\n\nЗа сегодня операций нет", parse_mode='Markdown')
        return
    
    report = f"📅 *ЗА {today_name}*\n━━━━━━━━━━━━━━━\n\n📋 *ОПЕРАЦИИ:*\n"
    for tx in today_tx:
        time = tx["date"].split()[1][:5]
        sign = "➕" if tx["sign"] == '+' else "➖"
        if tx["currency"] == "$":
            report += f"{sign} {tx['amount']:.2f}{tx['currency']} {tx['comment']} ({time})\n"
        else:
            report += f"{sign} {int(tx['amount'])}{tx['currency']} {tx['comment']} ({time})\n"
    
    report += f"\n📈 *ДОХОДЫ:*"
    if income_usd: report += f"\n  {income_usd:.2f}$"
    if income_rub: report += f"\n  {income_rub}₽"
    if not income_usd and not income_rub: report += " —"
    
    report += f"\n\n📉 *РАСХОДЫ:*"
    if expense_usd: report += f"\n  {expense_usd:.2f}$"
    if expense_rub: report += f"\n  {expense_rub}₽"
    if not expense_usd and not expense_rub: report += " —"
    
    bot.send_message(chat_id, report, parse_mode='Markdown')

def send_single_day_report(chat_id, date_input):
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
            bot.send_message(chat_id, "❌ Формат: `1.04` или `01.04`", parse_mode='Markdown')
            return
        
        day, month = day.zfill(2), month.zfill(2)
        date_str = f"{year}-{month}-{day}"
        display_date = f"{day}.{month}.{year}"
        data = load_data()
        
        income_usd = expense_usd = 0.0
        income_rub = expense_rub = 0
        day_tx = []
        
        for tx in data["transactions"]:
            if tx["date"].startswith(date_str):
                day_tx.append(tx)
                if tx["sign"] == '+':
                    if tx["currency"] == "$":
                        income_usd += tx["amount"]
                    else:
                        income_rub += tx["amount"]
                else:
                    if tx["currency"] == "$":
                        expense_usd += tx["amount"]
                    else:
                        expense_rub += tx["amount"]
        
        if not day_tx:
            bot.send_message(chat_id, f"📆 *ЗА {display_date}*\n━━━━━━━━━━━━━━━\n\nОпераций нет", parse_mode='Markdown')
            return
        
        report = f"📆 *ЗА {display_date}*\n━━━━━━━━━━━━━━━\n\n📋 *ОПЕРАЦИИ:*\n"
        for tx in day_tx:
            time = tx["date"].split()[1][:5]
            sign = "➕" if tx["sign"] == '+' else "➖"
            if tx["currency"] == "$":
                report += f"{sign} {tx['amount']:.2f}{tx['currency']} {tx['comment']} ({time})\n"
            else:
                report += f"{sign} {int(tx['amount'])}{tx['currency']} {tx['comment']} ({time})\n"
        
        report += f"\n📈 *ДОХОДЫ:*"
        if income_usd: report += f"\n  {income_usd:.2f}$"
        if income_rub: report += f"\n  {income_rub}₽"
        if not income_usd and not income_rub: report += " —"
        
        report += f"\n\n📉 *РАСХОДЫ:*"
        if expense_usd: report += f"\n  {expense_usd:.2f}$"
        if expense_rub: report += f"\n  {expense_rub}₽"
        if not expense_usd and not expense_rub: report += " —"
        
        bot.send_message(chat_id, report, parse_mode='Markdown')
    except:
        bot.send_message(chat_id, "❌ Ошибка. Пример: `1.04`", parse_mode='Markdown')

def send_period_report(chat_id, start_date_str, end_date_str):
    try:
        start_day, start_month = start_date_str.split('.')
        end_day, end_month = end_date_str.split('.')
        year = datetime.now().year
        
        start_date = datetime(year, int(start_month), int(start_day))
        end_date = datetime(year, int(end_month), int(end_day))
        
        data = load_data()
        income_usd = expense_usd = 0.0
        income_rub = expense_rub = 0
        period_tx = []
        
        for tx in data["transactions"]:
            tx_date = datetime.strptime(tx["date"].split()[0], "%Y-%m-%d")
            if start_date <= tx_date <= end_date:
                period_tx.append(tx)
                if tx["sign"] == '+':
                    if tx["currency"] == "$":
                        income_usd += tx["amount"]
                    else:
                        income_rub += tx["amount"]
                else:
                    if tx["currency"] == "$":
                        expense_usd += tx["amount"]
                    else:
                        expense_rub += tx["amount"]
        
        if not period_tx:
            bot.send_message(chat_id, f"📅 *ЗА ПЕРИОД*\n{start_date_str} — {end_date_str}\n━━━━━━━━━━━━━━━\n\nОпераций нет", parse_mode='Markdown')
            return
        
        report = f"📅 *ЗА ПЕРИОД*\n{start_date_str} — {end_date_str}\n━━━━━━━━━━━━━━━\n\n📋 *ОПЕРАЦИИ:*\n"
        for tx in period_tx:
            tx_date = tx["date"].split()[0][5:]
            time = tx["date"].split()[1][:5]
            sign = "➕" if tx["sign"] == '+' else "➖"
            if tx["currency"] == "$":
                report += f"{sign} {tx['amount']:.2f}{tx['currency']} {tx['comment']}\n   📅 {tx_date} {time}\n\n"
            else:
                report += f"{sign} {int(tx['amount'])}{tx['currency']} {tx['comment']}\n   📅 {tx_date} {time}\n\n"
        
        report += "━━━━━━━━━━━━━━━\n"
        report += "📈 *ВСЕГО ДОХОДЫ:*\n"
        if income_usd: report += f"  $ {income_usd:.2f}\n"
        if income_rub: report += f"  ₽ {income_rub}\n"
        if not income_usd and not income_rub: report += "  —\n"
        
        report += "\n📉 *ВСЕГО РАСХОДЫ:*\n"
        if expense_usd: report += f"  $ {expense_usd:.2f}\n"
        if expense_rub: report += f"  ₽ {expense_rub}\n"
        if not expense_usd and not expense_rub: report += "  —\n"
        
        bot.send_message(chat_id, report, parse_mode='Markdown')
    except:
        bot.send_message(chat_id, "❌ Ошибка периода", parse_mode='Markdown')

# ========== КОЛБЭКИ ОТЧЁТОВ ==========
@bot.callback_query_handler(func=lambda call: call.data.startswith("report_"))
def handle_report_callback(call):
    if not is_allowed(call.from_user.id):
        bot.answer_callback_query(call.id, "Нет доступа")
        return
    
    if call.data == "report_today":
        bot.edit_message_text("📅 Загружаю...", call.message.chat.id, call.message.message_id)
        send_today_report(call.message.chat.id)
    elif call.data == "report_single_day":
        bot.edit_message_text("📆 *Введи дату:*\n`1.04` или `01.04`", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        bot.waiting_for_day = getattr(bot, "waiting_for_day", {})
        bot.waiting_for_day[call.message.chat.id] = True
    elif call.data == "report_period":
        bot.edit_message_text("🗓️ *Начало периода:* `1.04`", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        bot.waiting_for_period = getattr(bot, "waiting_for_period", {})
        bot.waiting_for_period[call.message.chat.id] = {"step": "start"}
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: hasattr(bot, "waiting_for_day") and m.chat.id in bot.waiting_for_day)
def handle_day_input(message):
    if not is_allowed(message.from_user.id):
        return
    date_input = message.text.strip()
    del bot.waiting_for_day[message.chat.id]
    send_single_day_report(message.chat.id, date_input)

@bot.message_handler(func=lambda m: hasattr(bot, "waiting_for_period") and m.chat.id in bot.waiting_for_period)
def handle_period_input(message):
    if not is_allowed(message.from_user.id):
        return
    state = bot.waiting_for_period[message.chat.id]
    date_input = message.text.strip()
    try:
        day, month = date_input.split('.')
        int(day), int(month)
        if state["step"] == "start":
            state["start_date"] = date_input
            state["step"] = "end"
            bot.reply_to(message, f"✅ Начало: {date_input}\n📅 *Конец:*", parse_mode='Markdown')
        elif state["step"] == "end":
            start_date = state["start_date"]
            del bot.waiting_for_period[message.chat.id]
            send_period_report(message.chat.id, start_date, date_input)
    except:
        bot.reply_to(message, "❌ Формат: `1.04`", parse_mode='Markdown')
        if state["step"] == "start":
            del bot.waiting_for_period[message.chat.id]

# ========== АВТОМАТИЧЕСКИЙ ЕЖЕМЕСЯЧНЫЙ ОТЧЁТ ==========
def check_monthly_report():
    while True:
        try:
            now = get_moscow_time()
            data = load_data()
            
            # Проверяем, нужно ли отправить отчёт за прошлый месяц
            if data["last_report_month"] != now.month:
                # Отправляем отчёт за прошлый месяц
                if data["last_report_month"] is not None:
                    send_monthly_report_to_admin(now.month - 1 if now.month > 1 else 12, now.year if now.month > 1 else now.year - 1)
                data["last_report_month"] = now.month
                save_data(data)
            
            time.sleep(3600)  # Проверяем раз в час
        except:
            time.sleep(3600)

def send_monthly_report_to_admin(month, year):
    data = load_data()
    
    rub_in = 0
    rub_out = 0
    usd_in = 0
    usd_out = 0
    
    for t in data["transactions"]:
        try:
            t_date = datetime.strptime(t["date"].split()[0], "%Y-%m-%d")
            if t_date.month == month and t_date.year == year:
                if t["type"] == "income" and t["currency"] == "₽":
                    rub_in += t["amount"]
                elif t["type"] == "expense" and t["currency"] == "₽":
                    rub_out += t["amount"]
                elif t["type"] == "income" and t["currency"] == "$":
                    usd_in += t["amount"]
                elif t["type"] == "expense" and t["currency"] == "$":
                    usd_out += t["amount"]
        except:
            pass
    
    month_name = ["январь", "февраль", "март", "апрель", "май", "июнь", "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"][month-1]
    
    text = f"📊 *ЕЖЕМЕСЯЧНЫЙ ОТЧЁТ ЗА {month_name} {year}*\n━━━━━━━━━━━━━━━\n\n"
    text += f"🇷🇺 Рубли:\n   Доходы: {rub_in} ₽\n   Расходы: {rub_out} ₽\n   ➕ Итого: +{rub_in - rub_out} ₽\n\n"
    text += f"🇺🇸 Доллары:\n   Доходы: {usd_in:.2f}$\n   Расходы: {usd_out:.2f}$\n   ➕ Итого: +{usd_in - usd_out:.2f}$"
    
    try:
        bot.send_message(ADMIN_ID, text, parse_mode='Markdown')
    except:
        pass

# ========== ЗАПУСК ==========
def start_monthly_checker():
    thread = threading.Thread(target=check_monthly_report, daemon=True)
    thread.start()

print("🌸 Бот Алины запущен")
print(f"👑 Админ: {ADMIN_ID}")
print("💰 Рубли и доллары")
print("🏦 Отложенные деньги")
print("📊 Графики и бюджет")
print("🕐 Московское время")

start_monthly_checker()
bot.infinity_polling()
