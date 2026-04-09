import telebot
import json
import os
from datetime import datetime, timedelta
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# ========== НАСТРОЙКИ ==========
TOKEN = "8692541391:AAH6Cf8eh_afsynkA277SJ-_28ihs2VEutI"
ADMIN_ID = 463620997  # ⚠️ ЗАМЕНИ НА СВОЙ ТЕЛЕГРАМ ID

bot = telebot.TeleBot(TOKEN)
DATA_FILE = "finance.json"

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
            if isinstance(data.get("rub"), float):
                data["rub"] = int(data["rub"])
            return data
    return {
        "usd": 0.0,
        "rub": 0,
        "transactions": [],
        "allowed_users": []
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
        KeyboardButton("💎 Мой баланс"),
        KeyboardButton("📊 Отчёты"),
        KeyboardButton("✨ Доход"),
        KeyboardButton("🌸 Расход"),
        KeyboardButton("🕊️ Отменить последнее"),
        KeyboardButton("⚙️ Установить остаток"),
        KeyboardButton("👥 Управление доступом")
    ]
    keyboard.add(*buttons)
    return keyboard

def get_user_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("💎 Мой баланс"),
        KeyboardButton("📊 Отчёты")
    ]
    keyboard.add(*buttons)
    return keyboard

def get_reports_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📅 Сегодня", callback_data="report_today"),
        InlineKeyboardButton("📆 За конкретный день", callback_data="report_single_day"),
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

def get_instructions():
    return (
        "📘 *Доступные действия:*\n\n"
        "💎 *Баланс* — показать текущие рубли и доллары\n"
        "📊 *Отчёты* — выбрать:\n"
        "   • отчёт за сегодня\n"
        "   • за конкретный день\n"
        "   • за период\n\n"
        "✨ *Доход* — добавить доход в рублях или долларах\n"
        "🌸 *Расход* — добавить расход в рублях или долларах\n"
        "🕊️ *Отменить последнее* — откатить последнюю операцию\n"
        "⚙️ *Установить остаток* — задать текущие суммы вручную\n\n"
        "Изменять данные может только администратор."
    )

# ========== СТАРТ ==========
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    if not is_allowed(user_id):
        bot.reply_to(message,
            "🔒 *Доступ закрыт*\n\n"
            "Этот бот работает по приглашению.\n"
            "Напишите администратору и отправьте свой ID через /getid",
            parse_mode='Markdown')
        return

    if is_admin(user_id):
        welcome = (
            "🌸 *Привет, хозяйка!* 💅\n\n"
            "Твой личный финансовый помощник готов.\n"
            "Рубли и доллары — отдельно, отчёты — красивые.\n\n"
            "👇 Меню — под тобой"
        )
        bot.reply_to(message, welcome, parse_mode='Markdown', reply_markup=get_admin_keyboard())
    else:
        welcome = (
            "🌸 *Привет!*\n\n"
            "Тебе открыли доступ к финансовому боту.\n"
            "Ты можешь смотреть баланс и отчёты.\n\n"
            f"{get_instructions()}"
        )
        bot.reply_to(message, welcome, parse_mode='Markdown', reply_markup=get_user_keyboard())

@bot.message_handler(commands=['getid'])
def get_id(message):
    user_id = message.from_user.id
    bot.reply_to(message,
        f"🆔 *Твой Telegram ID:* `{user_id}`\n\n"
        "Перешли этот ID администратору для доступа к боту.",
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
                bot.send_message(new_user_id,
                    "🎉 *Вам открыли доступ к боту!*\n\n"
                    "Напишите /start, чтобы начать.\n\n"
                    f"{get_instructions()}",
                    parse_mode='Markdown')
            except:
                pass
        else:
            bot.reply_to(message, f"ℹ️ Пользователь `{new_user_id}` уже в списке", parse_mode='Markdown')
    except:
        bot.reply_to(message, "❌ Ошибка. Формат: `/adduser 123456789`", parse_mode='Markdown')

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
            bot.reply_to(message, f"ℹ️ Пользователь `{user_id}` не найден", parse_mode='Markdown')
    except:
        bot.reply_to(message, "❌ Ошибка", parse_mode='Markdown')

@bot.message_handler(commands=['users'])
def list_users(message):
    if not is_admin(message.from_user.id):
        return

    data = load_data()
    allowed = data.get("allowed_users", [])

    if not allowed:
        bot.reply_to(message, "👥 *Список пользователей пуст*", parse_mode='Markdown')
        return

    text = "👥 *ДОСТУП ЕСТЬ У:*\n━━━━━━━━━━━━━━━\n"
    for uid in allowed:
        text += f"🆔 `{uid}`\n"
    text += f"\n👑 *Администратор:* `{ADMIN_ID}`"
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "👥 Управление доступом")
def user_management_button(message):
    if not is_admin(message.from_user.id):
        return
    bot.reply_to(message,
        "👥 *Управление пользователями*\n━━━━━━━━━━━━━━━\n\n"
        "📌 Команды:\n"
        "`/adduser 123456789` — добавить\n"
        "`/removeuser 123456789` — удалить\n"
        "`/users` — список\n"
        "`/getid` — узнать свой ID\n\n"
        "👉 Новый пользователь:\n"
        "1. просит /getid\n"
        "2. ты добавляешь ID через /adduser",
        parse_mode='Markdown')

# ========== БАЛАНС ==========
@bot.message_handler(func=lambda m: m.text == "💎 Мой баланс")
def button_balance(message):
    if not is_allowed(message.from_user.id):
        return
    data = load_data()
    now = get_moscow_time()
    keyboard = get_admin_keyboard() if is_admin(message.from_user.id) else get_user_keyboard()
    bot.reply_to(message,
        f"💎 *БАЛАНС*\n━━━━━━━━━━━━━━━\n$ {data['usd']:.2f}\n₽ {int(data['rub'])}\n\n🕐 {now.strftime('%d.%m.%Y %H:%M')} МСК",
        parse_mode='Markdown',
        reply_markup=keyboard)

# ========== ОТЧЁТЫ ==========
@bot.message_handler(func=lambda m: m.text == "📊 Отчёты")
def button_reports(message):
    if not is_allowed(message.from_user.id):
        return
    bot.send_message(message.chat.id, "📅 *Тип отчёта:*", parse_mode='Markdown', reply_markup=get_reports_keyboard())

# ========== ДОХОД / РАСХОД ==========
@bot.message_handler(func=lambda m: m.text == "✨ Доход")
def button_income(message):
    if not is_admin(message.from_user.id):
        return
    msg = bot.reply_to(message, "💰 *Сумма и комментарий:*\n\nПример: `5000 зарплата`", parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_income_amount)

@bot.message_handler(func=lambda m: m.text == "🌸 Расход")
def button_expense(message):
    if not is_admin(message.from_user.id):
        return
    msg = bot.reply_to(message, "💸 *Сумма и комментарий:*\n\nПример: `1200 продукты`", parse_mode='Markdown')
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
        bot.temp_data[message.chat.id] = {"amount": amount, "comment": comment}
        bot.send_message(message.chat.id, "💱 *Выбери валюту:*", parse_mode='Markdown', reply_markup=get_currency_keyboard("expense"))
    except:
        bot.reply_to(message, "❌ Ошибка. Формат: `1200 продукты`", parse_mode='Markdown')

# ========== УСТАНОВИТЬ ОСТАТОК ==========
@bot.message_handler(func=lambda m: m.text == "⚙️ Установить остаток")
def button_set_balance(message):
    if not is_admin(message.from_user.id):
        return
    msg = bot.reply_to(message, "📝 *Формат:*\n`$ 1000`\n`₽ 50000`", parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_set_balance)

def process_set_balance(message):
    try:
        parts = message.text.split()
        currency = parts[0]
        amount = float(parts[1])
        data = load_data()

        if currency == "$":
            data["usd"] = amount
            bot.reply_to(message, f"✅ Доллары установлены: {amount:.2f}$")
        elif currency == "₽":
            data["rub"] = int(amount)
            bot.reply_to(message, f"✅ Рубли установлены: {int(amount)}₽")
        else:
            bot.reply_to(message, "❌ Укажи валюту: `$` или `₽`", parse_mode='Markdown')
            return
        save_data(data)
    except:
        bot.reply_to(message, "❌ Формат: `$ 1000` или `₽ 50000`", parse_mode='Markdown')

# ========== ВЫБОР ВАЛЮТЫ ==========
@bot.callback_query_handler(func=lambda call: call.data.startswith("income") or call.data.startswith("expense") or call.data == "cancel")
def handle_currency_callback(call):
    if call.data == "cancel":
        bot.edit_message_text("❌ Отменено", call.message.chat.id, call.message.message_id)
        return

    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Только администратор")
        return

    data = load_data()
    user_data = getattr(bot, "temp_data", {}).get(call.message.chat.id, {})
    amount = user_data.get("amount")
    comment = user_data.get("comment", "")

    if not amount:
        bot.answer_callback_query(call.id, "Ошибка, попробуй снова")
        return

    if call.data.startswith("income"):
        currency = call.data.split("_")[1]
        if currency == "$":
            data["usd"] += amount
            amount_display = f"{amount:.2f}{currency}"
        else:
            data["rub"] += int(amount)
            amount_display = f"{int(amount)}{currency}"
        action = "ДОХОД"
    else:
        currency = call.data.split("_")[1]
        if currency == "$":
            data["usd"] -= amount
            amount_display = f"{amount:.2f}{currency}"
        else:
            data["rub"] -= int(amount)
            amount_display = f"{int(amount)}{currency}"
        action = "РАСХОД"

    now = get_moscow_time()
    transaction = {
        "date": now.strftime("%Y-%m-%d %H:%M:%S"),
        "type": action.lower(),
        "amount": int(amount) if currency == "₽" else amount,
        "currency": currency,
        "comment": comment,
        "sign": '+' if action == "ДОХОД" else '-'
    }
    data["transactions"].append(transaction)
    save_data(data)

    bot.edit_message_text(
        f"✅ {action} {amount_display} {comment}\n🕐 {now.strftime('%H:%M')} МСК",
        call.message.chat.id,
        call.message.message_id
    )
    bot.send_message(call.message.chat.id, f"💰 Баланс: $ {data['usd']:.2f} | ₽ {int(data['rub'])}")

    if hasattr(bot, "temp_data") and call.message.chat.id in bot.temp_data:
        del bot.temp_data[call.message.chat.id]

    bot.answer_callback_query(call.id)

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
    bot.reply_to(message, f"✅ Отменено: {last['sign']}{amount_display}{last['currency']} {last['comment']}\n💰 Остаток: $ {data['usd']:.2f} | ₽ {int(data['rub'])}")

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
        bot.send_message(chat_id, "❌ Ошибка. Пример даты: `1.04`", parse_mode='Markdown')

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

# ========== ЗАПУСК ==========
print("🌸 Бот Алины запущен")
print(f"👑 Админ: {ADMIN_ID}")
print("💰 Рубли и доллары")
print("🕐 Московское время")
bot.infinity_polling()
