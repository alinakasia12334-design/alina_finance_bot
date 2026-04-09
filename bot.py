import telebot
import json
import os
from datetime import datetime, timedelta
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import threading
import time
import random

# ========== НАСТРОЙКИ ==========
TOKEN = "8692541391:AAH6Cf8eh_afsynkA277SJ-_28ihs2VEutI"
ADMIN_ID = 463620997  # ⚠️ ЗАМЕНИ НА СВОЙ TELEGRAM ID

bot = telebot.TeleBot(TOKEN)
DATA_FOLDER = "user_data"

# Создаём папку для данных пользователей
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
    "other": "📝 Другое"
}

CATEGORIES_LIST = list(CATEGORIES.keys())
CATEGORIES_EMOJI = {v: k for k, v in CATEGORIES.items()}

# ========== СМЕШНЫЕ ФРАЗЫ ==========
PHRASES = {
    "budget_set": [
        "🎯 *Окей, зайка. Бюджет на месяц — {amount} ₽. Давай без шопинг-истерик, ладно?*",
        "🎯 *{amount} ₽ на месяц. Это дошик или доставка? Решай, малыха.*",
        "🎯 *Бюджет {amount} ₽. Карта плачет, но мы крепкие.*",
        "🎯 *Так, бюджет {amount} ₽. Никаких «ой, я случайно» — я слежу.*",
        "🎯 *Твой лимит — {amount} ₽. Хочешь больше — иди работай или выходи замуж.*",
        "🎯 *{amount} ₽ на 30 дней. Экономь, мать.*",
        "🎯 *Готово. Бюджет {amount} ₽. Если увижу «Яндекс.Маркет» — удалю бота.*",
        "🎯 *Организм готов к лишениям. Бюджет {amount} ₽. Погнали.*",
        "🎯 *{amount} ₽. Никаких «ой, у меня нет денег» в конце месяца, ок?*",
        "🎯 *Бюджет принят. Следующая остановка — психушка от экономии.*"
    ],
    "budget_low": [
        "⚠️ *Малыха бля, ты поскромней живи! Осталось {remaining} ₽, иначе бабки закончатся все.*",
        "⚠️ *Карта в шоке, кошелёк плачет. Осталось {remaining} ₽. Может, перейдём на дошик?*",
        "⚠️ *Так, подруга, ты где деньги деваешь? Остаток — {remaining} ₽. Не жируй.*",
        "⚠️ *Твой бюджет как твои отношения — почти закончился. Осталось {remaining} ₽.*",
        "⚠️ *Внимание! До конца месяца {days} дней, а денег — {remaining} ₽. Зови маму.*",
        "⚠️ *Короче, зайка, осталось {remaining} ₽. На такси уже не хватит, только пешком.*",
        "⚠️ *Если увижу ещё одну доставку — бан. Осталось {remaining} ₽.*",
        "⚠️ *Ты в режиме «выживание». Остаток — {remaining} ₽. Держись.*",
        "⚠️ *Бюджет на грани. Как твои нервы. Осталось {remaining} ₽.*",
        "⚠️ *Эй, малыха! Ты чего? Осталось {remaining} ₽. Хватит на такси до метро и всё.*"
    ],
    "budget_over": [
        "💀 *Бля… Ты превысила бюджет на {overflow} ₽. Короче, завязывай, а то пойдёшь на хлеб и воду.*",
        "💀 *Поздравляю! Ты официально в минусе. На {overflow} ₽. Мама будет ругаться.*",
        "💀 *Ты что, купила золотое яблочко? Превышение — {overflow} ₽. Ай-яй-яй.*",
        "💀 *Банкротство уже близко. Превысила на {overflow} ₽. В следующий раз кредит в бота добавлю.*",
        "💀 *Ты как бюджет России. Превышение {overflow} ₽. Горжусь? Нет.*",
        "💀 *Я всё вижу. Ты потратила на {overflow} ₽ больше. Надеюсь, это было не на марафоны желаний.*",
        "💀 *Слушай, подруга. Превышение {overflow} ₽. Может, тебе к психологу? А не к косметологу.*",
        "💀 *Твоя карта в ужасе. Превышение {overflow} ₽. Я пас.*",
        "💀 *Превысила бюджет на {overflow} ₽. Начинаем голодовку завтра с утра.*",
        "💀 *Ты серьёзно? {overflow} ₽ сверху. Удали приложения с доставкой. Пожалуйста.*"
    ],
    "income": [
        "💰 *Ого! +{amount} ₽. Ты богачка. Не забудь меня покормить 🍕*",
        "💰 *+{amount} ₽ залетели. На такси до метро хватит.*",
        "💰 *Зарплата? Подарок? Продала почку? +{amount} ₽.*",
        "💰 *Ура, денежка! +{amount} ₽. Не протри дыру в кармане.*",
        "💰 *+{amount} ₽. Я прям чувствую себя богатой. Ну, почти.*",
        "💰 *Твой баланс пополнился на {amount} ₽. Магазины уже трясутся.*",
        "💰 *О, смотри-ка, деньги. +{amount} ₽. Надолго ли?*",
        "💰 *+{amount} ₽. Главное — не потратить за 5 минут.*",
        "💰 *Доход +{amount} ₽. Ты сегодня звезда. Ну или просто подработка.*",
        "💰 *Кто-то получил денежку! +{amount} ₽. Тратим с умом? Ахаха, нет.*"
    ],
    "expense": [
        "💸 *–{amount} ₽. Карта плачет, но мы крепкие.*",
        "💸 *{amount} ₽ ушло. Надеюсь, это было не на марафон желаний.*",
        "💸 *Ой, всё. –{amount} ₽. Копи на жизнь, а не на шмотки.*",
        "💸 *Только что ты стала беднее на {amount} ₽. Зато счастливее (наверное).*",
        "💸 *–{amount} ₽. Твой бюджет в нокдауне.*",
        "💸 *Расход {amount} ₽. Если это такси — иди пешком.*",
        "💸 *Ты потратила {amount} ₽. Я не одобряю, но кто я такая.*",
        "💸 *–{amount} ₽. Короче, завязывай.*",
        "💸 *{amount} ₽ улетели в никуда. Как твои нервы.*",
        "💸 *Твоя карта в шоке. Расход {amount} ₽. Мои соболезнования.*"
    ],
    "low_balance": [
        "📉 *Всё, зайка, ты на мели. Осталось {rub} ₽. Может, родителям позвонить?*",
        "📉 *Остаток {rub} ₽. На такси до метро ещё хватит. На дошик — уже нет.*",
        "📉 *Ты бедная, но гордая. Осталось {rub} ₽. Держись.*",
        "📉 *Карта пустая. Кошелёк тоже. Осталось {rub} ₽. Экономь.*",
        "📉 *Твой баланс — {rub} ₽. Как твои отношения. Пусто.*",
        "📉 *Денег почти нет. {rub} ₽. Надеюсь, ты уже поела.*",
        "📉 *Осталось {rub} ₽. Это на хлеб и воду. Или на один клик в Wildberries.*",
        "📉 *Ты на грани финансового дна. {rub} ₽. Я в тебя верю.*",
        "📉 *Остаток {rub} ₽. В следующий раз не покупай золотое яблочко.*",
        "📉 *Бабки кончились. Осталось {rub} ₽. Зови подругу на дошик.*"
    ],
    "saving": [
        "🐷 *Ещё {amount} ₽ в копилку. Скоро станешь нефтяной королевой.*",
        "🐷 *{amount} ₽ отложено. Ты сегодня ответственная. Странно.*",
        "🐷 *Копилка пополняется. +{amount} ₽. На золотое яблочко копим?*",
        "🐷 *Ого, дисциплина! Отложено {amount} ₽. Я в шоке.*",
        "🐷 *+{amount} ₽ в копилку. Скоро купим остров.*",
        "🐷 *Ты серьёзно? Отложила {amount} ₽? Это не ты.*",
        "🐷 *Отложено {amount} ₽. На такси до метро больше не тратим.*",
        "🐷 *Копилка довольна. Ты тоже. +{amount} ₽.*",
        "🐷 *{amount} ₽ ушли в будущее. Горжусь. Пока.*",
        "🐷 *Ты сегодня фея экономии. Отложено {amount} ₽. Не расслабляйся.*"
    ],
    "goal": [
        "🎀 *Ну что, зайка, пиши на что копим. Золотое яблочко? Шмотки? Или может быть ебучие анализы?*",
        "🎀 *Ой, какая цель! {name} на {target} ₽. Ты серьёзно или так, помечтать?*",
        "🎀 *Копим на {name}. Если через месяц 0 на счету — удаляюсь.*",
        "🎀 *{name} — звучит дорого. Но мы девочки смелые. Цель {target} ₽.*",
        "🎀 *Твоя новая цель: {name}. Давай без «ой, я передумала».*",
        "🎀 *Окей, малыха. {name} в прицеле. Нужно {target} ₽. Погнали копить.*",
        "🎀 *Хочешь {name}? Работай или выходи замуж. А пока копим {target} ₽.*",
        "🎀 *{name} — это база. Цель {target} ₽. Я в тебя верю. Карта — нет.*",
        "🎀 *Твоя мечта — {name}. А твой бюджет — {target} ₽. Давай, не подведи.*",
        "🎀 *Копим на {name}. На {target} ₽. Если сорвёшься на шмотки — убью.*"
    ],
    "monthly_report": [
        "📊 *Ща всё расскажу, только чай налью... Держи, твои траты за {month}. Спойлер: на доставку ушло дохера.*",
        "📊 *Ну что, отчёт за {month}. Ты потратила {total} ₽. Гордишься? Я — нет.*",
        "📊 *Держи отчёт. Ты снова всё просрала. Но мы тебя любим.*",
        "📊 *{month} прошёл. Ты богаче? Нет. Счастливее? Тоже нет. Держи цифры.*",
        "📊 *Траты за {month}. Спойлер: на марафоны желаний ушло всё.*",
        "📊 *Твой финансовый дневник за {month}. Не плачь, просто посмотри.*",
        "📊 *Отчёт за {month}. Если увидишь минус — не удивляйся.*",
        "📊 *{month} в цифрах. Ты молодец? Не уверена. Но держи.*",
        "📊 *Держи отчёт. И не говори, что я тебя не предупреждала.*",
        "📊 *Твой финансовый отчёт. Плакать будем вместе или ты одна?*"
    ],
    "undo": [
        "↩️ *Отменила. Твоя ошибка — не твоя проблема. Я здесь, чтобы фиксить.*",
        "↩️ *Ой, передумала? Отменила последнюю операцию.*",
        "↩️ *Готово. Последняя операция в прошлом. Как твои бывшие.*",
        "↩️ *Отмена прошла успешно. Можешь дышать.*",
        "↩️ *Вжух — и нет. Отменила. Давай без драмы.*",
        "↩️ *Отменила. В следующий раз думай, прежде чем тратить.*",
        "↩️ *Готово. Твоя ошибка удалена. Как мои надежды на твою экономию.*",
        "↩️ *Отмена. Ты снова можешь ошибиться, я рядом.*",
        "↩️ *Последняя операция ушла в небытие. Не благодари.*",
        "↩️ *Отменила. Всё, забудь. И не возвращайся к этому.*"
    ],
    "error": [
        "❌ *Эй, малыха, ты чего творишь? Неправильно ввела. Давай по-человечески: сумма описание.*",
        "❌ *Не-не-не. Так не пойдёт. Формат: сумма и описание. Пробуй ещё.*",
        "❌ *Ты где цифры потеряла? Напиши сумму и что это было. Пример: `1200 такси`.*",
        "❌ *Ошибка, зайка. Я тебя люблю, но формат соблюдай: сумма и комментарий.*",
        "❌ *Не поняла тебя. Напиши как я люблю: `5000 зарплата` или `1200 кафе`.*"
    ]
}

# Московское время
def get_moscow_time():
    return datetime.utcnow() + timedelta(hours=3)

# ========== РАБОТА С ДАННЫМИ ПОЛЬЗОВАТЕЛЯ ==========
def get_user_file(user_id):
    return os.path.join(DATA_FOLDER, f"user_{user_id}.json")

def load_user_data(user_id):
    file_path = get_user_file(user_id)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "savings" not in data:
                data["savings"] = []
            if "budget" not in data:
                data["budget"] = None
            if "transactions" not in data:
                data["transactions"] = []
            if "goals" not in data:
                data["goals"] = []
            return data
    return {
        "usd": 0.0,
        "rub": 0,
        "transactions": [],
        "savings": [],
        "goals": [],
        "budget": None,
        "last_report_month": None
    }

def save_user_data(user_id, data):
    file_path = get_user_file(user_id)
    data["rub"] = int(data["rub"])
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_admin(user_id):
    return user_id == ADMIN_ID

def get_allowed_users():
    # Список разрешённых пользователей (все, у кого есть файл)
    allowed = []
    for filename in os.listdir(DATA_FOLDER):
        if filename.startswith("user_") and filename.endswith(".json"):
            try:
                user_id = int(filename.split("_")[1].split(".")[0])
                allowed.append(user_id)
            except:
                pass
    if ADMIN_ID not in allowed:
        allowed.append(ADMIN_ID)
    return allowed

def is_allowed(user_id):
    return user_id in get_allowed_users()

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
        KeyboardButton("🕊️ Отменить"),
        KeyboardButton("⚙️ Настройки"),
        KeyboardButton("👥 Пользователи")
    ]
    keyboard.add(*buttons)
    return keyboard

def get_user_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("💎 Баланс"),
        KeyboardButton("📊 Отчёты"),
        KeyboardButton("📊 График трат"),
        KeyboardButton("📋 История")
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
        InlineKeyboardButton("➕ Отложить", callback_data="savings_add"),
        InlineKeyboardButton("➖ Вернуть", callback_data="savings_remove"),
        InlineKeyboardButton("💸 Потратить", callback_data="savings_spend"),
        InlineKeyboardButton("📋 Список", callback_data="savings_list"),
        InlineKeyboardButton("❌ Закрыть", callback_data="cancel")
    )
    return keyboard

def get_goals_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🎯 Добавить цель", callback_data="goal_add"),
        InlineKeyboardButton("📋 Мои цели", callback_data="goal_list"),
        InlineKeyboardButton("❌ Закрыть", callback_data="cancel")
    )
    return keyboard

# ========== ПРИВЕТСТВИЕ ==========
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    name = message.from_user.first_name or "Подруга"
    
    # Добавляем пользователя в разрешённые, если его нет
    if user_id not in get_allowed_users():
        # Автоматически добавляем нового пользователя (для админа)
        if user_id == ADMIN_ID:
            pass  # админ уже есть
        else:
            # Обычный пользователь не может сам добавиться
            bot.reply_to(message,
                "🔒 *Доступ закрыт*\n\n"
                "Этот бот работает по приглашению.\n"
                "Напиши Алине, она добавит тебя командой /adduser",
                parse_mode='Markdown')
            return
    
    if is_admin(user_id):
        welcome = (
            f"🌸 *Привет, {name}!*\n\n"
            "Я — **Твоя финансовая нянька с характером** 💅\n"
            "Создала меня **Алина** — она, кстати, сама ахуеть это сделала 🔥\n\n"
            "Я буду помогать тебе не проедать всё до копейки, откладывать на золотое яблочко и вовремя говорить: *«Малыха, ты поскромней живи»*.\n\n"
            "### 📚 Что я умею:\n\n"
            "- 💰 **Доходы** — когда тебе кто-то закинул денег\n"
            "- 💸 **Расходы** — когда ты снова купила свечку за 2000 ₽\n"
            "- 🏦 **Отложить** — копим на мечту\n"
            "- 📈 **Бюджет** — ставим лимит, чтобы ты не ушла в минус\n"
            "- 📊 **График трат** — чтобы увидеть, куда улетела зарплата\n"
            "- 📋 **История** — список твоих грехов\n\n"
            "### 🎀 Как со мной общаться?\n\n"
            "Внизу есть **кнопки** — просто жми на них.\n\n"
            "### 👯‍♀️ Для подружек\n\n"
            "Ты можешь **дать доступ** подружкам через /adduser — у каждой будет **свой личный кабинет**.\n\n"
            "---\n"
            "🍀 *Погнали, красотка? Жми на кнопку и не стесняйся своих трат!* 😘"
        )
        bot.reply_to(message, welcome, parse_mode='Markdown', reply_markup=get_admin_keyboard())
    else:
        welcome = (
            f"🌸 *Привет, {name}!*\n\n"
            "Я — **Твоя финансовая нянька** 💅\n"
            "Создала меня **Алина** 🔥\n\n"
            "Ты можешь смотреть баланс, отчёты и графики.\n"
            "А доходы, расходы и бюджет настраивает администратор.\n\n"
            "👇 Кнопки внизу"
        )
        bot.reply_to(message, welcome, parse_mode='Markdown', reply_markup=get_user_keyboard())

@bot.message_handler(commands=['getid'])
def get_id(message):
    user_id = message.from_user.id
    bot.reply_to(message,
        f"🆔 *Твой ID:* `{user_id}`\n\nПерешли этот ID Алине.",
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
        
        # Создаём файл для нового пользователя
        user_data = load_user_data(new_user_id)
        save_user_data(new_user_id, user_data)
        
        bot.reply_to(message, f"✅ Пользователь `{new_user_id}` добавлен", parse_mode='Markdown')
        try:
            bot.send_message(new_user_id, 
                "🎉 *Тебе открыли доступ к финансовому боту!*\n\n"
                "Напиши /start, чтобы начать.",
                parse_mode='Markdown')
        except:
            pass
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
        
        file_path = get_user_file(user_id)
        if os.path.exists(file_path):
            os.remove(file_path)
            bot.reply_to(message, f"✅ Пользователь `{user_id}` удалён", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"ℹ️ Пользователь `{user_id}` не найден", parse_mode='Markdown')
    except:
        bot.reply_to(message, "❌ Ошибка", parse_mode='Markdown')

@bot.message_handler(commands=['users'])
def list_users(message):
    if not is_admin(message.from_user.id):
        return
    allowed = get_allowed_users()
    if not allowed:
        bot.reply_to(message, "👥 *Список пользователей пуст*", parse_mode='Markdown')
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
    user_id = message.from_user.id
    data = load_user_data(user_id)
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
    
    # Проверка на маленький остаток
    if free_rub < 1000 and free_rub > 0:
        phrase = random.choice(PHRASES["low_balance"]).format(rub=free_rub)
        text += f"\n\n{phrase}"
    
    keyboard = get_admin_keyboard() if is_admin(user_id) else get_user_keyboard()
    bot.reply_to(message, text, parse_mode='Markdown', reply_markup=keyboard)

# ========== ОТЧЁТЫ ==========
@bot.message_handler(func=lambda m: m.text == "📊 Отчёты")
def button_reports(message):
    if not is_allowed(message.from_user.id):
        return
    bot.send_message(message.chat.id, "📅 *Выбери отчёт:*", parse_mode='Markdown', reply_markup=get_reports_keyboard())

# ========== ДОХОД ==========
@bot.message_handler(func=lambda m: m.text == "➕ Доход")
def button_income(message):
    if not is_admin(message.from_user.id):
        return
    msg = bot.reply_to(message, "💰 *Сумма и описание:*\n\nПример: `5000 зарплата`", parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_income_amount)

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
        phrase = random.choice(PHRASES["error"])
        bot.reply_to(message, phrase, parse_mode='Markdown')

# ========== РАСХОД ==========
@bot.message_handler(func=lambda m: m.text == "➖ Расход")
def button_expense(message):
    if not is_admin(message.from_user.id):
        return
    msg = bot.reply_to(message, "💸 *Сумма и описание:*\n\nПример: `1200 продукты`", parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_expense_amount)

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
        phrase = random.choice(PHRASES["error"])
        bot.reply_to(message, phrase, parse_mode='Markdown')

# ========== ОТЛОЖЕННЫЕ ==========
@bot.message_handler(func=lambda m: m.text == "🏦 Отложить")
def button_savings(message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(message.chat.id, "🏦 *Управление отложенными:*", parse_mode='Markdown', reply_markup=get_savings_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("savings_"))
def handle_savings_callback(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Только администратор")
        return
    
    if call.data == "savings_add":
        bot.edit_message_text("💰 *Сумма и цель:*\n\nПример: `10000 новый телефон`", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        bot.register_next_step_handler(call.message, process_savings_add)
    elif call.data == "savings_remove":
        bot.edit_message_text("💰 *Сумма и цель (вернуть):*\n\nПример: `2000 отпуск`", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        bot.register_next_step_handler(call.message, process_savings_remove)
    elif call.data == "savings_spend":
        bot.edit_message_text("💸 *Сумма и цель (потратить):*\n\nПример: `3000 новый телефон`", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        bot.register_next_step_handler(call.message, process_savings_spend)
    elif call.data == "savings_list":
        show_savings_list(call.message)
    bot.answer_callback_query(call.id)

def process_savings_add(message):
    user_id = message.from_user.id
    try:
        parts = message.text.split()
        amount = float(parts[0])
        name = " ".join(parts[1:]) if len(parts) > 1 else "без названия"
        data = load_user_data(user_id)
        
        total_saved = sum(s["amount"] for s in data["savings"])
        if data["rub"] - total_saved < amount:
            bot.reply_to(message, f"❌ Недостаточно свободных денег. Свободно: {data['rub'] - total_saved} ₽")
            return
        
        data["savings"].append({
            "name": name,
            "amount": amount,
            "date": get_moscow_time().isoformat()
        })
        save_user_data(user_id, data)
        
        phrase = random.choice(PHRASES["saving"]).format(amount=int(amount))
        bot.reply_to(message, f"{phrase}\n\n💰 На «{name}»")
        button_balance(message)
    except:
        bot.reply_to(message, "❌ Ошибка. Формат: `10000 новый телефон`", parse_mode='Markdown')

def process_savings_remove(message):
    user_id = message.from_user.id
    try:
        parts = message.text.split()
        amount = float(parts[0])
        name = " ".join(parts[1:]) if len(parts) > 1 else ""
        data = load_user_data(user_id)
        
        for s in data["savings"]:
            if name.lower() in s["name"].lower():
                if s["amount"] >= amount:
                    s["amount"] -= amount
                    if s["amount"] == 0:
                        data["savings"].remove(s)
                    save_user_data(user_id, data)
                    bot.reply_to(message, f"✅ Возвращено {int(amount)} ₽ из «{s['name']}»")
                    button_balance(message)
                    return
                else:
                    bot.reply_to(message, f"❌ В «{s['name']}» отложено только {int(s['amount'])} ₽")
                    return
        bot.reply_to(message, f"❌ Цель «{name}» не найдена")
    except:
        bot.reply_to(message, "❌ Ошибка. Формат: `2000 отпуск`", parse_mode='Markdown')

def process_savings_spend(message):
    user_id = message.from_user.id
    try:
        parts = message.text.split()
        amount = float(parts[0])
        name = " ".join(parts[1:]) if len(parts) > 1 else ""
        data = load_user_data(user_id)
        
        for s in data["savings"]:
            if name.lower() in s["name"].lower():
                if s["amount"] >= amount:
                    s["amount"] -= amount
                    if s["amount"] == 0:
                        data["savings"].remove(s)
                    
                    now = get_moscow_time()
                    transaction = {
                        "date": now.strftime("%Y-%m-%d %H:%M:%S"),
                        "type": "expense",
                        "amount": int(amount),
                        "currency": "₽",
                        "comment": f"{name} (из отложенного)",
                        "category": "other",
                        "sign": '-'
                    }
                    data["transactions"].append(transaction)
                    save_user_data(user_id, data)
                    
                    phrase = random.choice(PHRASES["expense"]).format(amount=int(amount))
                    bot.reply_to(message, f"{phrase}\n\n💸 Из отложенного на «{name}»")
                    button_balance(message)
                    return
                else:
                    bot.reply_to(message, f"❌ В «{s['name']}» отложено только {int(s['amount'])} ₽")
                    return
        bot.reply_to(message, f"❌ Цель «{name}» не найдена")
    except:
        bot.reply_to(message, "❌ Ошибка. Формат: `3000 новый телефон`", parse_mode='Markdown')

def show_savings_list(message):
    user_id = message.from_user.id
    data = load_user_data(user_id)
    if not data["savings"]:
        bot.reply_to(message, "🏦 *Нет отложенных денег*", parse_mode='Markdown')
        return
    text = "🏦 *ОТЛОЖЕННЫЕ ЦЕЛИ:*\n━━━━━━━━━━━━━━━\n"
    for s in data["savings"]:
        text += f"• {s['name']}: {int(s['amount'])} ₽\n"
    bot.reply_to(message, text, parse_mode='Markdown')

# ========== БЮДЖЕТ ==========
@bot.message_handler(func=lambda m: m.text == "📈 Бюджет")
def button_budget(message):
    if not is_admin(message.from_user.id):
        return
    user_id = message.from_user.id
    data = load_user_data(user_id)
    now = get_moscow_time()
    current_month = now.month
    current_year = now.year
    month_name = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"][current_month-1]
    
    if data["budget"] and data["budget"]["month"] == current_month and data["budget"]["year"] == current_year:
        budget_amount = data["budget"]["amount"]
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
        
        text = f"📈 *БЮДЖЕТ НА {month_name.upper()}*\n━━━━━━━━━━━━━━━\n"
        text += f"💰 Бюджет: {int(budget_amount)} ₽\n"
        text += f"💸 Потрачено: {int(expenses)} ₽ ({percent:.0f}%)\n"
        text += f"✅ Осталось: {int(remaining)} ₽\n"
        
        if percent >= 100:
            phrase = random.choice(PHRASES["budget_over"]).format(overflow=int(expenses - budget_amount))
            text += f"\n{phrase}"
        elif percent >= 80:
            days_left = (datetime(current_year, current_month, 1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            days_left = (days_left - now).days + 1
            phrase = random.choice(PHRASES["budget_low"]).format(remaining=int(remaining), days=days_left)
            text += f"\n{phrase}"
        
        bot.reply_to(message, text, parse_mode='Markdown')
    else:
        bot.reply_to(message, 
            "📈 *Бюджет не установлен*\n\n"
            "Установи бюджет на месяц:\n"
            "`/budget 50000`",
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
        user_id = message.from_user.id
        data = load_user_data(user_id)
        data["budget"] = {
            "amount": amount,
            "month": now.month,
            "year": now.year
        }
        save_user_data(user_id, data)
        
        phrase = random.choice(PHRASES["budget_set"]).format(amount=int(amount))
        bot.reply_to(message, phrase, parse_mode='Markdown')
    except:
        bot.reply_to(message, "❌ Ошибка. Формат: `/budget 50000`", parse_mode='Markdown')

# ========== ГРАФИК ТРАТ ==========
@bot.message_handler(func=lambda m: m.text == "📊 График трат")
def button_spending_chart(message):
    if not is_allowed(message.from_user.id):
        return
    
    user_id = message.from_user.id
    data = load_user_data(user_id)
    now = get_moscow_time()
    current_month = now.month
    current_year = now.year
    month_name = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"][current_month-1]
    
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
        bot.reply_to(message, f"📊 *За {month_name} расходов нет*", parse_mode='Markdown')
        return
    
    sorted_cats = sorted(category_expenses.items(), key=lambda x: x[1], reverse=True)
    max_amount = max(cat[1] for cat in sorted_cats if cat[1] > 0)
    max_bars = 20
    
    text = f"📊 *ГРАФИК ТРАТ ЗА {month_name.upper()}*\n━━━━━━━━━━━━━━━\n"
    text += f"💰 Всего потрачено: {int(total_expenses)} ₽\n\n"
    
    for cat_key, amount in sorted_cats:
        if amount == 0:
            continue
        percent = amount / max_amount if max_amount > 0 else 0
        bars = int(percent * max_bars)
        bar_str = "▪" * bars if bars > 0 else "▫"
        cat_name = CATEGORIES[cat_key]
        text += f"{cat_name}: {bar_str} {int(amount)} ₽\n"
    
    bot.reply_to(message, text, parse_mode='Markdown')

# ========== ИСТОРИЯ ==========
@bot.message_handler(func=lambda m: m.text == "📋 История")
def show_history(message):
    if not is_allowed(message.from_user.id):
        return
    user_id = message.from_user.id
    data = load_user_data(user_id)
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

# ========== ОТМЕНИТЬ ==========
@bot.message_handler(func=lambda m: m.text == "🕊️ Отменить")
def button_undo(message):
    if not is_admin(message.from_user.id):
        return
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
    save_user_data(user_id, data)
    
    amount_display = f"{last['amount']:.2f}" if last["currency"] == "$" else f"{int(last['amount'])}"
    phrase = random.choice(PHRASES["undo"])
    bot.reply_to(message, f"{phrase}\n\n↩️ Отменено: {last['sign']}{amount_display}{last['currency']} {last['comment']}")

# ========== НАСТРОЙКИ ==========
@bot.message_handler(func=lambda m: m.text == "⚙️ Настройки")
def button_settings(message):
    if not is_admin(message.from_user.id):
        return
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("💰 Установить остаток", callback_data="settings_balance"))
    keyboard.add(InlineKeyboardButton("📊 Очистить всё", callback_data="settings_clear"))
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
    user_id = call.from_user.id
    data = load_user_data(user_id)
    data["transactions"] = []
    data["savings"] = []
    data["rub"] = 0
    data["usd"] = 0
    data["budget"] = None
    save_user_data(user_id, data)
    bot.edit_message_text("✅ *Все данные очищены*", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
    bot.answer_callback_query(call.id)

def process_set_balance(message):
    user_id = message.from_user.id
    try:
        parts = message.text.split()
        currency = parts[0]
        amount = float(parts[1])
        data = load_user_data(user_id)
        if currency == "$":
            data["usd"] = amount
            bot.reply_to(message, f"✅ Доллары: {amount:.2f}$")
        elif currency == "₽":
            data["rub"] = int(amount)
            bot.reply_to(message, f"✅ Рубли: {int(amount)}₽")
        else:
            bot.reply_to(message, "❌ Укажи валюту: `$` или `₽`", parse_mode='Markdown')
            return
        save_user_data(user_id, data)
        button_balance(message)
    except:
        bot.reply_to(message, "❌ Формат: `$ 1000` или `₽ 50000`", parse_mode='Markdown')

# ========== ОБРАБОТКА ВАЛЮТ И КАТЕГОРИЙ ==========
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
    
    user_id = call.from_user.id
    data = load_user_data(user_id)
    
    if call.data.startswith("income"):
        currency = call.data.split("_")[1]
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
        save_user_data(user_id, data)
        
        phrase = random.choice(PHRASES["income"]).format(amount=int(amount) if currency == "₽" else amount)
        bot.edit_message_text(
            f"{phrase}\n🕐 {now.strftime('%H:%M')} МСК",
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
            save_user_data(user_id, data)
            
            phrase = random.choice(PHRASES["expense"]).format(amount=int(amount) if currency == "₽" else amount)
            bot.edit_message_text(
                f"{phrase}\n🕐 {now.strftime('%H:%M')} МСК",
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
    
    user_id = call.from_user.id
    data = load_user_data(user_id)
    
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
    save_user_data(user_id, data)
    
    category_name = CATEGORIES[category_key]
    phrase = random.choice(PHRASES["expense"]).format(amount=int(amount) if currency == "₽" else amount)
    bot.edit_message_text(
        f"{phrase}\n📂 {category_name}\n🕐 {now.strftime('%H:%M')} МСК",
        call.message.chat.id,
        call.message.message_id
    )
    button_balance(call.message)
    
    if hasattr(bot, "temp_data") and call.message.chat.id in bot.temp_data:
        del bot.temp_data[call.message.chat.id]
    
    bot.answer_callback_query(call.id)

# ========== ОТЧЁТЫ ==========
def send_today_report(chat_id, user_id):
    data = load_user_data(user_id)
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
            bot.send_message(chat_id, "❌ Формат: `1.04` или `01.04`", parse_mode='Markdown')
            return
        
        day, month = day.zfill(2), month.zfill(2)
        date_str = f"{year}-{month}-{day}"
        display_date = f"{day}.{month}.{year}"
        data = load_user_data(user_id)
        
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

def send_period_report(chat_id, user_id, start_date_str, end_date_str):
    try:
        start_day, start_month = start_date_str.split('.')
        end_day, end_month = end_date_str.split('.')
        year = datetime.now().year
        
        start_date = datetime(year, int(start_month), int(start_day))
        end_date = datetime(year, int(end_month), int(end_day))
        
        data = load_user_data(user_id)
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
        bot.edit_message_text("📆 *Введи дату:*\n`1.04` или `01.04`", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        bot.waiting_for_day = getattr(bot, "waiting_for_day", {})
        bot.waiting_for_day[call.message.chat.id] = user_id
    elif call.data == "report_period":
        bot.edit_message_text("🗓️ *Начало периода:* `1.04`", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        bot.waiting_for_period = getattr(bot, "waiting_for_period", {})
        bot.waiting_for_period[call.message.chat.id] = {"step": "start", "user_id": user_id}
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: hasattr(bot, "waiting_for_day") and m.chat.id in bot.waiting_for_day)
def handle_day_input(message):
    if not is_allowed(message.from_user.id):
        return
    user_id = bot.waiting_for_day[message.chat.id]
    date_input = message.text.strip()
    del bot.waiting_for_day[message.chat.id]
    send_single_day_report(message.chat.id, user_id, date_input)

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
            user_id = state["user_id"]
            del bot.waiting_for_period[message.chat.id]
            send_period_report(message.chat.id, user_id, start_date, date_input)
    except:
        bot.reply_to(message, "❌ Формат: `1.04`", parse_mode='Markdown')
        if state["step"] == "start":
            del bot.waiting_for_period[message.chat.id]

# ========== АВТОМАТИЧЕСКИЙ ОТЧЁТ ==========
def check_monthly_report():
    while True:
        try:
            now = get_moscow_time()
            for user_id in get_allowed_users():
                data = load_user_data(user_id)
                if data["last_report_month"] != now.month:
                    if data["last_report_month"] is not None:
                        send_monthly_report_to_user(user_id, now.month - 1 if now.month > 1 else 12, now.year if now.month > 1 else now.year - 1)
                    data["last_report_month"] = now.month
                    save_user_data(user_id, data)
            time.sleep(3600)
        except:
            time.sleep(3600)

def send_monthly_report_to_user(user_id, month, year):
    data = load_user_data(user_id)
    
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
    
    month_name = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"][month-1]
    total = rub_in - rub_out
    
    phrase = random.choice(PHRASES["monthly_report"]).format(month=month_name, total=int(rub_out))
    
    text = f"{phrase}\n\n"
    text += f"🇷🇺 Рубли:\n   Доходы: {rub_in} ₽\n   Расходы: {rub_out} ₽\n   ➕ Итого: +{rub_in - rub_out} ₽\n\n"
    text += f"🇺🇸 Доллары:\n   Доходы: {usd_in:.2f}$\n   Расходы: {usd_out:.2f}$\n   ➕ Итого: +{usd_in - usd_out:.2f}$"
    
    try:
        bot.send_message(user_id, text, parse_mode='Markdown')
    except:
        pass

# ========== ЗАПУСК ==========
def start_monthly_checker():
    thread = threading.Thread(target=check_monthly_report, daemon=True)
    thread.start()

print("🌸 Бот Алины запущен")
print(f"👑 Админ: {ADMIN_ID}")
print("💰 Мультипользовательский режим")
print("🎲 Рандомные фразы")
print("🕐 Московское время")

start_monthly_checker()
bot.infinity_polling()
