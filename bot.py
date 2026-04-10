import telebot
from datetime import datetime, timedelta
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import threading
import time
from functools import wraps
from config import TOKEN, ADMIN_ID, SUPPORT_CONTACT, DB_PATH
from phrases import STYLE_MODES, choose_phrase, choose_expense_mix, get_next_advice
from analytics import build_behavior_insights
from storage import Storage, CATEGORIES

bot = telebot.TeleBot(TOKEN)

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
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
storage = Storage(DB_PATH, ADMIN_ID)
storage.ensure_user(ADMIN_ID)

def load_user_data(user_id):
    return storage.load_user_data(user_id)

def save_user_data(user_id, data):
    storage.save_user_data(user_id, data)

def is_admin(user_id):
    return user_id == ADMIN_ID

def get_allowed_users():
    return storage.get_allowed_users()

def is_allowed(user_id):
    return user_id in get_allowed_users()

# ========== ОБНУЛЕНИЕ СТАТИСТИКИ ==========
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
    buttons = [
        "💎 Баланс", "📊 Отчёты", "➕ Доход", "➖ Расход", "🎯 Цели", "📈 Бюджет",
        "📂 Траты", "📋 История", "💭 Хочу купить", "📝 Вишлист",
        "🧾 Подписки", "🧠 Состояние", "🔥 Роаст", "💡 Инсайт", "🕊️ Отменить", "⚙️ Настройки"
    ]
    if is_admin(user_id):
        buttons.append("👥 Пользователи")
    keyboard.add(*buttons)
    return keyboard

def get_back_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_main"))
    return keyboard

def get_category_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    for key, emoji_name in CATEGORIES.items():
        keyboard.add(InlineKeyboardButton(emoji_name, callback_data=f"cat_{key}"))
    keyboard.row(InlineKeyboardButton("❌ Отмена", callback_data="cancel"))
    return keyboard

# ========== ПРИВЕТСТВИЕ ==========
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    name = message.from_user.first_name or "Подруга"
    
    if not is_allowed(user_id):
        bot.reply_to(
            message,
            f"🌸 Привет, {name}!\n\n"
            f"Сейчас бот закрыт по приглашениям 🔒\n\n"
            f"Что делать:\n"
            f"1) Нажми /getid и скопируй свой ID\n"
            f"2) Отправь его в {SUPPORT_CONTACT}\n"
            f"3) После подтверждения снова напиши /start\n\n"
            f"Я тебя жду 💅"
        )
        return

    storage.ensure_user(user_id)
    data = reset_monthly_stats_if_needed(user_id)
    
    if not data.get("transactions"):
        welcome = (
            f"🌸 Привет, {name}!\n\n"
            f"Я — финансовая подруга с характером, создана Алиной.\n"
            f"Я не только считаю деньги, но и помогаю увидеть твои паттерны:\n"
            f"когда ты тратишь из усталости, тревоги или импульса.\n\n"
            f"Старт простой:\n"
            f"1) Нажми ➖ Расход\n"
            f"2) Запиши первую трату\n"
            f"3) Получи разбор и инсайт 💡\n\n"
            f"Погнали, красотка. Начни с первой траты прямо сейчас."
        )
    else:
        welcome = f"С возвращением, {name} 💅 Готова держать бюджет под контролем?"
    
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
        storage.ensure_user(new_user_id)
        bot.reply_to(message, f"✅ Пользователь `{new_user_id}` добавлен", parse_mode='Markdown')
        try:
            bot.send_message(new_user_id, "🎉 Тебе открыли доступ!\nНапиши /start")
        except:
            pass
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['removeuser'])
@require_admin
def remove_user(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Формат: /removeuser 123456789")
            return
        user_id = int(parts[1])
        if storage.user_exists(user_id):
            storage.delete_user(user_id)
            bot.reply_to(message, f"✅ Пользователь `{user_id}` удалён", parse_mode='Markdown')
        else:
            bot.reply_to(message, "ℹ️ Пользователь не найден")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

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
@bot.message_handler(func=lambda m: m.text == "🎯 Цели")
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

# Временное хранилище для состояний диалогов
user_states = {}

# ========== ДОХОД ==========
@bot.message_handler(func=lambda m: m.text == "➕ Доход")
@require_auth
def button_income(message):
    user_states[message.from_user.id] = {"action": "income"}
    bot.reply_to(message, "💰 Сумма и описание:\n\nПример: 5000 зарплата")

# ========== РАСХОД ==========
@bot.message_handler(func=lambda m: m.text == "➖ Расход")
@require_auth
def button_expense(message):
    user_states[message.from_user.id] = {"action": "expense"}
    bot.reply_to(message, "💸 Сумма и описание:\n\nПример: 1200 такси")

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
            bot.reply_to(message, "❌ Сумма должна быть больше 0")
            return
        comment = parts[1] if len(parts) > 1 else ""
        
        if state["action"] == "income":
            keyboard = InlineKeyboardMarkup()
            keyboard.add(
                InlineKeyboardButton("💵 Доллар ($)", callback_data="inc_$"),
                InlineKeyboardButton("₽ Рубль (₽)", callback_data="inc_₽")
            )
            user_states[user_id] = {"action": "income_currency", "amount": amount, "comment": comment}
            bot.reply_to(message, "💱 Выбери валюту:", reply_markup=keyboard)
        
        elif state["action"] == "expense":
            keyboard = InlineKeyboardMarkup()
            keyboard.add(
                InlineKeyboardButton("💵 Доллар ($)", callback_data="exp_$"),
                InlineKeyboardButton("₽ Рубль (₽)", callback_data="exp_₽")
            )
            user_states[user_id] = {"action": "expense_currency", "amount": amount, "comment": comment}
            bot.reply_to(message, "💱 Выбери валюту:", reply_markup=keyboard)
    
    except ValueError:
        bot.reply_to(message, "❌ Введи число. Пример: 5000 зарплата")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("inc_") or call.data.startswith("exp_"))
def handle_currency_callback(call):
    user_id = call.from_user.id
    state = user_states.get(user_id, {})
    currency = "₽" if call.data.endswith("₽") else "$"
    data = reset_monthly_stats_if_needed(user_id)
    now = get_moscow_time()
    
    if call.data.startswith("inc_"):
        if currency == "$":
            data["usd"] += state["amount"]
            amount_display = f"{state['amount']:.2f}{currency}"
        else:
            data["rub"] += int(state["amount"])
            amount_display = f"{int(state['amount'])}{currency}"
        
        data["transactions"].append({
            "date": now.strftime("%Y-%m-%d %H:%M:%S"),
            "type": "income",
            "amount": int(state["amount"]) if currency == "₽" else state["amount"],
            "currency": currency,
            "comment": state["comment"],
            "sign": '+'
        })
        save_user_data(user_id, data)
        
        reaction = choose_phrase(data, "income_reaction", get_name_form(call.from_user.first_name or "Подруга"))
        save_user_data(user_id, data)
        
        bot.edit_message_text(
            f"✅ ДОХОД {amount_display} {state['comment']}\n🕐 {now.strftime('%H:%M')} МСК\n\n💬 {reaction}",
            call.message.chat.id,
            call.message.message_id
        )
        button_balance(call.message)
    
    elif call.data.startswith("exp_"):
        if currency == "$":
            bot.edit_message_text("❌ Расход в долларах пока не поддерживается. Используй рубли.", call.message.chat.id, call.message.message_id)
        else:
            user_states[user_id] = {
                "action": "category",
                "amount": state["amount"],
                "comment": state["comment"]
            }
            bot.edit_message_text("📂 Выбери категорию расхода:", call.message.chat.id, call.message.message_id, reply_markup=get_category_keyboard())
    
    user_states.pop(user_id, None)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def handle_category_callback(call):
    if call.data == "cancel":
        bot.edit_message_text("❌ Отменено", call.message.chat.id, call.message.message_id)
        user_states.pop(call.from_user.id, None)
        return
    
    category_key = call.data.split("_")[1]
    if category_key not in CATEGORIES:
        bot.answer_callback_query(call.id, "Ошибка: категория не найдена")
        return
    
    user_id = call.from_user.id
    state = user_states.get(user_id, {})
    amount = state.get("amount")
    comment = state.get("comment", "")
    
    if not amount:
        bot.answer_callback_query(call.id, "Ошибка")
        return
    
    data = reset_monthly_stats_if_needed(user_id)
    now = get_moscow_time()
    
    data["rub"] -= int(amount)
    data["current_month_stats"][category_key] = data["current_month_stats"].get(category_key, 0) + int(amount)
    data["current_month_total"] += int(amount)
    
    transaction = {
        "date": now.strftime("%Y-%m-%d %H:%M:%S"),
        "type": "expense",
        "amount": int(amount),
        "currency": "₽",
        "comment": comment,
        "category": category_key,
        "sign": '-'
    }
    data["transactions"].append(transaction)
    save_user_data(user_id, data)
    
    reaction = choose_expense_mix(data, category_key, get_name_form(call.from_user.first_name or "Подруга"))
    advice = get_next_advice(user_id, category_key).format(name=get_name_form(call.from_user.first_name or "Подруга"))
    insights = build_behavior_insights(data, CATEGORIES)
    insights_text = "💡 ИНСАЙТЫ\n━━━━━━━━━━━━━━━\n" + "\n".join([f"• {x}" for x in insights[:3]])
    
    bot.edit_message_text(
        f"✅ РАСХОД {int(amount)}₽ {comment}\n📂 {CATEGORIES[category_key]}\n🕐 {now.strftime('%H:%M')} МСК\n\n💬 {reaction}\n💡 {advice}\n\n{insights_text}",
        call.message.chat.id,
        call.message.message_id
    )
    
    user_states.pop(user_id, None)
    bot.answer_callback_query(call.id)

# ========== ТРАТЫ ==========
@bot.message_handler(func=lambda m: m.text == "📂 Траты")
@require_auth
def button_categories(message):
    user_id = message.from_user.id
    data = reset_monthly_stats_if_needed(user_id)
    stats = data.get("current_month_stats", {})
    total = data.get("current_month_total", 0)
    month_name = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"][get_moscow_time().month-1]
    
    if total == 0:
        bot.reply_to(message, f"📂 ТРАТЫ\n━━━━━━━━━━━━━━━\n\n📊 ЗА {month_name.upper()}:\n💰 Всего потрачено: 0 ₽\n\nПока нет трат за этот месяц.", reply_markup=get_main_keyboard(user_id))
        return
    
    cat_list = [(cat_key, amount, (amount / total) * 100) for cat_key, amount in stats.items() if amount > 0]
    cat_list.sort(key=lambda x: x[1], reverse=True)
    
    text = f"📂 ТРАТЫ\n━━━━━━━━━━━━━━━\n\n📊 ЗА {month_name.upper()}:\n💰 Всего потрачено: {total} ₽\n\n" + "\n".join([f"{CATEGORIES[cat_key]}: {percent:.0f}% ({amount} ₽)" for cat_key, amount, percent in cat_list])
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("💡 Хочу совет", callback_data="advice_main"))
    bot.reply_to(message, text, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "advice_main")
def handle_advice_callback(call):
    if not is_allowed(call.from_user.id):
        bot.answer_callback_query(call.id, "Нет доступа")
        return
    
    user_id = call.from_user.id
    name = get_name_form(call.from_user.first_name or "Подруга")
    data = reset_monthly_stats_if_needed(user_id)
    
    stats = data.get("current_month_stats", {})
    cat_list = [(cat_key, amount) for cat_key, amount in stats.items() if amount > 0]
    
    if not cat_list:
        bot.edit_message_text("Пока нет трат за этот месяц, не могу дать совет 😢", call.message.chat.id, call.message.message_id)
    else:
        top_cat = max(cat_list, key=lambda x: x[1])
        cat_name = CATEGORIES[top_cat[0]]
        advice = get_next_advice(user_id, top_cat[0]).format(name=name)
        text = f"💡 СОВЕТ\n━━━━━━━━━━━━━━━\n\n{name}, больше всего денег уходит на {cat_name} — {top_cat[1]} ₽\n\n{advice}"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
    
    bot.answer_callback_query(call.id)

# ========== ИСТОРИЯ ==========
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

# ========== ОТМЕНА ==========
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
            if last.get("category") and last["currency"] == "₽":
                data["current_month_stats"][last["category"]] = max(0, data["current_month_stats"].get(last["category"], 0) - last["amount"])
                data["current_month_total"] = max(0, data.get("current_month_total", 0) - last["amount"])
    
    save_user_data(user_id, data)
    amount_display = f"{last['amount']:.2f}" if last["currency"] == "$" else f"{int(last['amount'])}"
    bot.reply_to(message, f"↩️ Отменено: {last['sign']}{amount_display}{last['currency']} {last['comment']}")

# ========== ЖИВЫЕ ФУНКЦИИ ==========
@bot.message_handler(func=lambda m: m.text == "💭 Хочу купить")
@require_auth
def anti_impulse(message):
    user_states[message.from_user.id] = {"action": "want_buy"}
    bot.reply_to(message, "💭 Что хочешь купить и за сколько?\nПример: Наушники 7990")

def process_anti_impulse(message):
    try:
        parts = message.text.rsplit(" ", 1)
        item = parts[0]
        price = int(float(parts[1]))
        data = load_user_data(message.from_user.id)
        free_money = data["rub"] - sum(g["current"] for g in data.get("goals", []))
        share = (price / free_money * 100) if free_money > 0 else 999
        mood = data.get("moods", [])[-1]["mood"] if data.get("moods") else "неизвестно"
        verdict = "Похоже на эмоциональную покупку." if share > 25 or mood in ["устала", "грустно", "тревожно", "злая"] else "Покупка выглядит адекватно бюджету."
        
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton("⏳ Подумать 24 часа", callback_data="buy_wait"),
            InlineKeyboardButton("✅ Купить всё равно", callback_data="buy_confirm"),
            InlineKeyboardButton("❌ Отмена", callback_data="cancel")
        )
        
        phrase = choose_phrase(data, "want_buy", get_name_form(message.from_user.first_name or "Подруга"))
        
        text = (
            f"🧠 АНТИИМПУЛЬС\n━━━━━━━━━━━━━━━\n"
            f"Покупка: {item}\nЦена: {price} ₽\n\n"
            f"Свободно: {int(free_money)} ₽\n"
            f"Доля от свободных: {share:.1f}%\n"
            f"Текущее состояние: {mood}\n\n"
            f"Вердикт: {verdict}\n\n"
            f"💬 {phrase}"
        )
        save_user_data(message.from_user.id, data)
        bot.reply_to(message, text, reply_markup=keyboard)
    except:
        bot.reply_to(message, "❌ Формат: Наушники 7990")

@bot.callback_query_handler(func=lambda call: call.data in ["buy_wait", "buy_confirm"])
def anti_impulse_callback(call):
    if call.data == "buy_wait":
        bot.edit_message_text("⏳ Окей, ставим правило 24 часов. Если завтра всё ещё надо — это уже осознаннее.", call.message.chat.id, call.message.message_id)
    else:
        bot.edit_message_text("✅ Принято. Покупай осознанно и зафиксируй расход после покупки.", call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: m.text == "📝 Вишлист")
@require_auth
def wishlist_menu(message):
    msg = bot.reply_to(message, "📝 ВИШЛИСТ\n━━━━━━━━━━━━━━━\n\n+ Название цена — добавить\nlist — показать\nbuy 1 — отметить купленным")
    bot.register_next_step_handler(msg, process_wishlist)

def process_wishlist(message):
    data = load_user_data(message.from_user.id)
    text = message.text.strip()
    
    if text.lower() == "list":
        items = data.get("wishlist", [])
        if not items:
            bot.reply_to(message, "Вишлист пуст.")
            return
        out = "\n".join([f"{i+1}. {w['name']} — {w['price']} ₽" for i, w in enumerate(items)])
        bot.reply_to(message, "📝 ТВОЙ ВИШЛИСТ\n━━━━━━━━━━━━━━━\n" + out)
        return
    
    if text.lower().startswith("buy "):
        idx = int(text.split()[1]) - 1
        if 0 <= idx < len(data["wishlist"]):
            item = data["wishlist"].pop(idx)
            save_user_data(message.from_user.id, data)
            bot.reply_to(message, f"✅ «{item['name']}» отмечено как купленное.")
        else:
            bot.reply_to(message, "❌ Нет такого пункта.")
        return
    
    try:
        name, price = text.rsplit(" ", 1)
        data["wishlist"].append({"name": name, "price": int(float(price)), "added_at": get_moscow_time().strftime("%Y-%m-%d")})
        save_user_data(message.from_user.id, data)
        bot.reply_to(message, f"✅ Добавила в вишлист: {name} — {int(float(price))} ₽")
    except:
        bot.reply_to(message, "❌ Формат: Название 1990")

@bot.message_handler(func=lambda m: m.text == "🧾 Подписки")
@require_auth
def subscriptions_menu(message):
    msg = bot.reply_to(message, "🧾 ПОДПИСКИ\n━━━━━━━━━━━━━━━\n\n+ Название сумма период(месяц/год) день_месяца\nlist — показать\nrm 1 — удалить")
    bot.register_next_step_handler(msg, process_subscriptions)

def process_subscriptions(message):
    data = load_user_data(message.from_user.id)
    text = message.text.strip()
    
    if text.lower() == "list":
        subs = data.get("subscriptions", [])
        if not subs:
            bot.reply_to(message, "Подписок нет.")
            return
        monthly_total = 0
        lines = []
        for i, s in enumerate(subs):
            period = s.get("period", "месяц")
            m_amount = s["amount"] if period == "месяц" else s["amount"] / 12
            monthly_total += m_amount
            lines.append(f"{i+1}. {s['name']} — {s['amount']} ₽ / {period} ({s['day']} число)")
        out = "\n".join(lines)
        bot.reply_to(message, f"🧾 ПОДПИСКИ\n━━━━━━━━━━━━━━━\n{out}\n\nИтого в месяц: {int(monthly_total)} ₽")
        return
    
    if text.lower().startswith("rm "):
        idx = int(text.split()[1]) - 1
        if 0 <= idx < len(data["subscriptions"]):
            s = data["subscriptions"].pop(idx)
            save_user_data(message.from_user.id, data)
            bot.reply_to(message, f"✅ Удалила подписку: {s['name']}")
        else:
            bot.reply_to(message, "❌ Нет такой подписки.")
        return
    
    try:
        name, amount, period, day = text.rsplit(" ", 3)
        period = period.lower()
        if period not in ["месяц", "год"]:
            bot.reply_to(message, "❌ Период: месяц или год")
            return
        data["subscriptions"].append({"name": name, "amount": int(float(amount)), "period": period, "day": int(day)})
        save_user_data(message.from_user.id, data)
        bot.reply_to(message, f"✅ Подписка добавлена: {name}, {int(float(amount))} ₽ / {period}, {int(day)} числа")
    except:
        bot.reply_to(message, "❌ Формат: Spotify 499 месяц 12")

@bot.message_handler(func=lambda m: m.text == "🧠 Состояние")
@require_auth
def mood_state(message):
    keyboard = InlineKeyboardMarkup(row_width=2)
    for mood in ["устала", "грустно", "злая", "тревожно", "нормально", "энергия"]:
        keyboard.add(InlineKeyboardButton(mood, callback_data=f"mood_{mood}"))
    bot.reply_to(message, "🧠 Как ты сейчас?", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("mood_"))
def mood_callback(call):
    if not is_allowed(call.from_user.id):
        return
    mood = call.data.split("_", 1)[1]
    data = load_user_data(call.from_user.id)
    if "moods" not in data:
        data["moods"] = []
    data["moods"].append({"date": get_moscow_time().strftime("%Y-%m-%d %H:%M"), "mood": mood})
    data["moods"] = data["moods"][-100:]
    save_user_data(call.from_user.id, data)
    bot.edit_message_text(f"Записала состояние: {mood}.", call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: m.text == "🔥 Роаст")
@require_auth
def roast_report(message):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🔥 Роаст дня", callback_data="roast_day"),
        InlineKeyboardButton("🔥 Роаст недели", callback_data="roast_week"),
        InlineKeyboardButton("🔥 Роаст месяца", callback_data="roast_month")
    )
    bot.reply_to(message, "Выбери формат роаста:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("roast_"))
def roast_callback(call):
    if not is_allowed(call.from_user.id):
        return
    data = load_user_data(call.from_user.id)
    now = get_moscow_time()
    
    if call.data == "roast_day":
        tx = [t for t in data.get("transactions", []) if t.get("date", "").startswith(now.strftime("%Y-%m-%d")) and t.get("sign") == '-']
        title = "🔥 РОАСТ ДНЯ"
    elif call.data == "roast_week":
        start = now - timedelta(days=7)
        tx = [t for t in data.get("transactions", []) if t.get("sign") == '-' and datetime.strptime(t["date"].split()[0], "%Y-%m-%d") >= start]
        title = "🔥 РОАСТ НЕДЕЛИ"
    else:
        tx = [t for t in data.get("transactions", []) if t.get("sign") == '-' and t.get("date", "")[:7] == now.strftime("%Y-%m")]
        title = "🔥 РОАСТ МЕСЯЦА"
    
    phrase = choose_phrase(data, "roast", get_name_form(call.from_user.first_name or "Подруга"))
    total = sum(t["amount"] for t in tx) if tx else 0
    summary = f"Расходов в периоде: {len(tx)}, сумма: {total} ₽" if tx else "Расходов в этом периоде пока нет"
    
    bot.edit_message_text(f"{title}\n━━━━━━━━━━━━━━━\n{summary}\n\n{phrase}", call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: m.text == "💡 Инсайт")
@require_auth
def insight_report(message):
    data = load_user_data(message.from_user.id)
    insights = build_behavior_insights(data, CATEGORIES)
    phrase = choose_phrase(data, "insight", get_name_form(message.from_user.first_name or "Подруга"))
    bot.reply_to(message, f"💡 ИНСАЙТЫ\n━━━━━━━━━━━━━━━\n" + "\n".join([f"• {x}" for x in insights]) + f"\n\n💬 {phrase}")

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
        bot.reply_to(message, "❌ Ошибка. Формат: /budget 50000")

# ========== ОТЧЁТЫ ==========
@bot.message_handler(func=lambda m: m.text == "📊 Отчёты")
@require_auth
def button_reports(message):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📅 Сегодня", callback_data="report_today"),
        InlineKeyboardButton("📆 За день", callback_data="report_single_day"),
        InlineKeyboardButton("📉 За неделю", callback_data="report_week"),
        InlineKeyboardButton("🗓️ За период", callback_data="report_period"),
        InlineKeyboardButton("📊 За месяц", callback_data="report_monthly")
    )
    bot.send_message(message.chat.id, "📅 Выбери отчёт:", reply_markup=keyboard)

def send_week_report(chat_id, user_id):
    data = load_user_data(user_id)
    now = get_moscow_time()
    start = now - timedelta(days=7)
    week_tx = [tx for tx in data["transactions"] if datetime.strptime(tx["date"].split()[0], "%Y-%m-%d") >= start]
    if not week_tx:
        bot.send_message(chat_id, "📉 ЗА НЕДЕЛЮ\n━━━━━━━━━━━━━━━\nОпераций нет")
        return
    income = sum(tx["amount"] for tx in week_tx if tx["sign"] == '+' and tx["currency"] == "₽")
    expense = sum(tx["amount"] for tx in week_tx if tx["sign"] == '-' and tx["currency"] == "₽")
    bot.send_message(chat_id, f"📉 ЗА НЕДЕЛЮ\n━━━━━━━━━━━━━━━\nДоходы: {int(income)} ₽\nРасходы: {int(expense)} ₽\nБаланс недели: {int(income-expense)} ₽")

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
    
    report_lines = []
    for tx in today_tx:
        amount_display = f"{tx['amount']:.2f}" if tx["currency"] == "$" else f"{int(tx['amount'])}"
        report_lines.append(f"{'➕' if tx['sign'] == '+' else '➖'} {amount_display}{tx['currency']} {tx['comment']} ({tx['date'].split()[1][:5]})")
    report = f"📅 ЗА {today_name}\n━━━━━━━━━━━━━━━\n\n📋 ОПЕРАЦИИ:\n" + "\n".join(report_lines)
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
        
        report_lines = []
        for tx in day_tx:
            amount_display = f"{tx['amount']:.2f}" if tx["currency"] == "$" else f"{int(tx['amount'])}"
            report_lines.append(f"{'➕' if tx['sign'] == '+' else '➖'} {amount_display}{tx['currency']} {tx['comment']} ({tx['date'].split()[1][:5]})")
        report = f"📆 ЗА {display_date}\n━━━━━━━━━━━━━━━\n\n📋 ОПЕРАЦИИ:\n" + "\n".join(report_lines)
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
        
        report_lines = []
        for tx in period_tx:
            amount_display = f"{tx['amount']:.2f}" if tx["currency"] == "$" else f"{int(tx['amount'])}"
            report_lines.append(f"{'➕' if tx['sign'] == '+' else '➖'} {amount_display}{tx['currency']} {tx['comment']}\n   📅 {tx['date'].split()[0][5:]} {tx['date'].split()[1][:5]}")
        report = f"📅 ЗА ПЕРИОД\n{start_date_str} — {end_date_str}\n━━━━━━━━━━━━━━━\n\n📋 ОПЕРАЦИИ:\n" + "\n".join(report_lines)
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
        advice = get_next_advice(user_id, cat_list[0][0]).format(name="Зайка")
        text += f"\n\n💡 {advice}"
    
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
    elif call.data == "report_week":
        bot.edit_message_text("📉 Загружаю неделю...", call.message.chat.id, call.message.message_id)
        send_week_report(call.message.chat.id, user_id)
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

# ========== НАСТРОЙКИ ==========
@bot.message_handler(func=lambda m: m.text == "⚙️ Настройки")
@require_auth
def button_settings(message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("💰 Установить остаток", callback_data="settings_balance"),
        InlineKeyboardButton("📊 Очистить всё", callback_data="settings_clear")
    )
    keyboard.add(InlineKeyboardButton("🎭 Режим общения", callback_data="settings_mode"))
    keyboard.add(InlineKeyboardButton("❓ Как пользоваться", callback_data="settings_help"))
    keyboard.add(InlineKeyboardButton("❌ Закрыть", callback_data="cancel"))
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
    elif call.data == "settings_mode":
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton("🌸 Мягкий", callback_data="setmode_soft"),
            InlineKeyboardButton("😈 Дерзкий", callback_data="setmode_bold"),
            InlineKeyboardButton("🔥 Разнос", callback_data="setmode_roast")
        )
        bot.edit_message_text("Выбери режим общения:", call.message.chat.id, call.message.message_id, reply_markup=keyboard)
    elif call.data == "settings_help":
        bot.edit_message_text(
            "💡 КАК ПОЛЬЗОВАТЬСЯ\n━━━━━━━━━━━━━━━\n"
            "1) Добавляй расходы и доходы каждый день\n"
            "2) Раз в неделю смотри отчёт и роаст\n"
            "3) Используй «Хочу купить» перед импульсной покупкой\n"
            "4) Отмечай состояние, чтобы увидеть связь эмоций и трат",
            call.message.chat.id,
            call.message.message_id
        )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("setmode_"))
def set_mode_callback(call):
    if not is_allowed(call.from_user.id):
        return
    mode = call.data.split("_", 1)[1]
    if mode not in STYLE_MODES:
        bot.answer_callback_query(call.id, "Неизвестный режим")
        return
    data = load_user_data(call.from_user.id)
    data["mode"] = mode
    save_user_data(call.from_user.id, data)
    bot.edit_message_text(f"✅ Режим: {STYLE_MODES[mode]}", call.message.chat.id, call.message.message_id)
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

# ========== АВТОМАТИЧЕСКИЙ ОТЧЁТ ==========
def check_monthly_reset_and_report():
    while True:
        try:
            now = get_moscow_time()
            for user_id in get_allowed_users():
                data = load_user_data(user_id)
                last_auto = data.get("last_auto_report_sent")
                
                if last_auto != now.month and now.day == 1 and now.hour == 9:
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
                
                # Напоминания по подпискам
                for sub in data.get("subscriptions", []):
                    if int(sub.get("day", 1)) == now.day and now.hour == 10:
                        try:
                            bot.send_message(user_id, f"🧾 Сегодня спишется подписка: {sub['name']} — {sub['amount']} ₽")
                        except:
                            pass
            
            time.sleep(3600)
        except:
            time.sleep(3600)

# ========== ЗАПУСК ==========
def start_background_checker():
    thread = threading.Thread(target=check_monthly_reset_and_report, daemon=True)
    thread.start()

print("🌸 Бот Алины запущен")
print(f"👑 Админ: {ADMIN_ID}")
print("✅ Все функции работают")
print("🕐 Московское время")

start_background_checker()
bot.infinity_polling()
