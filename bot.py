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

# ========== СОВЕТЫ ДЛЯ КАТЕГОРИЙ (С ИМЕНЕМ) ==========
ADVICE = {
    "food": [
        "{name}, ну ты ахуела столько на доставку тратить? Готовь дома!",
        "{name}, твой кошелёк плачет. Хватит заказывать роллы каждый день.",
        "{name}, ты что, из ресторана не вылезаешь? Давай поскромнее, зайка.",
        "{name}, готовь дома — это не только дешевле, но и полезнее.",
        "{name}, бери ланч с собой на работу. Экономия ~3000 ₽ в месяц.",
        "{name}, не ходи в магазин голодной. Иначе в корзине окажется всё, кроме хлеба.",
        "{name}, планируй меню на неделю — меньше импульсивных покупок.",
        "{name}, заказывай доставку только по акциям. Полная цена — это грабёж.",
        "{name}, пей воду в кафе, а не сок за 300 ₽.",
        "{name}, устрой челлендж: неделя без доставки. Твоя карта скажет спасибо."
    ],
    "transport": [
        "{name}, давай нахуй меньше на такси езжай! Общественный транспорт — это не стыдно, это умно.",
        "{name}, такси — для богатых. А ты пока копишь на золотое яблочко, помнишь?",
        "{name}, ноги бесплатные. Вспомни про них, пожалуйста.",
        "{name}, каршеринг дешевле такси, если совсем невмоготу.",
        "{name}, проездной на месяц окупится через 2 недели. Математика, малыха.",
        "{name}, автобус/трамвай/троллейбус — твои новые лучшие друзья.",
        "{name}, если ехать 15 минут — может, пешком? И деньги целее, и попа подкачается 🍑",
        "{name}, такси в час пик — это самый дорогой способ простоять в пробке.",
        "{name}, одна поездка на такси = неделя проездного. Подумай об этом.",
        "{name}, твой кошелёк скажет спасибо, если ты пересечёшь на автобус."
    ],
    "cafe": [
        "{name}, кофе дома — это не скучно, это выгодно. Купи красивую кружку.",
        "{name}, устрой «кофейный детокс» на неделю — проверь, сможешь ли ты.",
        "{name}, встречайся с подругами дома, а не в кафе. Уютнее и дешевле.",
        "{name}, бери с собой термокружку — в некоторых заведениях скидка.",
        "{name}, завтракай дома — кафе утром самое дорогое удовольствие.",
        "{name}, ходи в кафе только по скидочным картам или в счастливые часы.",
        "{name}, десерт — зло. Особенно за 400 ₽ за кусочек бисквита.",
        "{name}, вместо кафе — кофе с собой и скамейка в парке.",
        "{name}, на работе часто есть кофеварка — пользуйся ею!",
        "{name}, если невтерпёж, купи хороший кофе домой и радуйся каждое утро."
    ],
    "shopping": [
        "{name}, перед покупкой подожди 24 часа. Через день уже не хочется.",
        "{name}, удали приложения магазинов с телефона — меньше соблазна.",
        "{name}, покупай на распродажах, но только то, что планировала заранее.",
        "{name}, спроси себя: «Мне это нужно или просто хочется?»",
        "{name}, не ходи в торговый центр «просто посмотреть».",
        "{name}, составь капсульный гардероб — меньше вещей, больше комбинаций.",
        "{name}, на Wildberries сначала добавь в корзину, а оплати через день.",
        "{name}, косметику покупай на замену старой, а не потому что красивая баночка.",
        "{name}, сравни цены на маркетплейсах — иногда разница в 1000 ₽.",
        "{name}, вспомни, что у тебя дома уже есть три чёрных платья."
    ],
    "home": [
        "{name}, выключай свет, когда выходишь из комнаты. Да, это реально работает.",
        "{name}, установи счётчики на воду — окупаются за полгода.",
        "{name}, стирай при полной загрузке и при 30° — экономия электричества.",
        "{name}, не кипяти полный чайник, если нужна одна кружка.",
        "{name}, заряжай телефон от ноутбука — так меньше жрёшь розетки.",
        "{name}, утепли окна на зиму — отопление будет эффективнее.",
        "{name}, не держи технику в режиме ожидания — выключай из розетки.",
        "{name}, покупай лампочки LED — они светят ярче и живут дольше.",
        "{name}, почини кран с капающей водой — экономия до 500 ₽ в месяц.",
        "{name}, проветривай комнату быстро, а не держи окно открытым часами."
    ],
    "health": [
        "{name}, не занимайся самолечением — дороже выйдет потом.",
        "{name}, сравнивай цены в разных аптеках через приложения.",
        "{name}, покупай дженерики вместо брендов — то же самое, но дешевле.",
        "{name}, проверяй срок годности — выброшенные лекарства = выброшенные деньги.",
        "{name}, пей витамины курсами, а не круглый год.",
        "{name}, лечи насморк промыванием, а не спреями за 800 ₽.",
        "{name}, купи аптечку и пополняй её постепенно, а не перед болезнью.",
        "{name}, не ведись на рекламу — часто дешёвый аналог работает так же.",
        "{name}, храни лекарства правильно — чтобы не портились.",
        "{name}, профилактика дешевле лечения. Высыпайся и ешь овощи 🥦"
    ],
    "subscriptions": [
        "{name}, раз в месяц проверяй, на что у тебя списываются деньги.",
        "{name}, отпишись от стримингов, которыми не пользуешься.",
        "{name}, дели подписку с подругой — Spotify, Netflix делятся.",
        "{name}, установи лимит на подписки: максимум 3 в месяц.",
        "{name}, используй бесплатные триалы, но ставь напоминалку отменить.",
        "{name}, подумай, нужен ли тебе онлайн-кинотеатр, если ты всё равно смотришь YouTube.",
        "{name}, многие приложения дают скидку при оплате на год сразу.",
        "{name}, VPN часто дорогой — найди бесплатный или пользуйся встроенным в браузер.",
        "{name}, спроси себя: «Я реально пользовалась этим сервисом за последний месяц?»",
        "{name}, без подписок жить можно. Проверено."
    ],
    "gifts": [
        "{name}, подарок — это жест, а не сумма. Не обязательно тратить ползарплаты.",
        "{name}, подари впечатления: билет в кино, мастер-класс, сертификат на массаж.",
        "{name}, сделай подарок своими руками — ценится больше и дешевле.",
        "{name}, договорись с подругами не дарить друг другу дорогие подарки.",
        "{name}, покупай подарки заранее, а не в последний день перед праздником.",
        "{name}, используй кэшбэк и скидочные карты при покупке подарков.",
        "{name}, вместо букета цветов — одно красивое растение в горшке.",
        "{name}, подари совместный ужин дома — дешевле ресторана и душевнее.",
        "{name}, не стесняйся спрашивать, что человек хочет — меньше риска промахнуться.",
        "{name}, самое ценное — это твоё внимание, а не цена подарка."
    ],
    "travel": [
        "{name}, покупай билеты заранее за 2-3 месяца.",
        "{name}, следи за акциями авиакомпаний и подпишись на рассылки.",
        "{name}, лети в будни — дешевле, чем в пятницу или воскресенье.",
        "{name}, бери только ручную кладь — экономия на багаже.",
        "{name}, жильё ищи не в центре, а в 10 минутах на транспорте.",
        "{name}, гугли бесплатные развлечения в городе: парки, музеи в определённые дни.",
        "{name}, ешь там, где местные, а не у туристических достопримечательностей.",
        "{name}, путешествуй в несезон — цены в 2 раза ниже.",
        "{name}, собирай кэшбэк на путешествия с картой.",
        "{name}, копи на поездку по чуть-чуть каждый месяц — так незаметно накопится."
    ],
    "credit": [
        "{name}, зайка, кредиты — это зло. Погаси самый маленький первым — психологически легче.",
        "{name}, не бери новый кредит, чтобы закрыть старый. Это как вырыть яму, чтобы засыпать другую.",
        "{name}, плати больше минимального платежа — иначе будешь должна до пенсии.",
        "{name}, если взяла в долг у подруги — отдай сразу, не тяни. Дружба дороже.",
        "{name}, рефинансирование может снизить ставку. Проверь, может быть выгодно.",
        "{name}, кредитка с грейс-периодом — ок, но только если успеваешь погасить без процентов.",
        "{name}, не бери кредит на импульсивные покупки. Айфон подождать может.",
        "{name}, составь список всех долгов от самого маленького до большого и гаси по очереди.",
        "{name}, если должно несколько человек, плати всем по чуть-чуть — меньше обид.",
        "{name}, кредиты — это как лишний вес: от них трудно избавиться, но можно. Главное — начать.",
        "{name}, перестань брать рассрочку на каждую мелочь. Это всё равно кредит.",
        "{name}, установи автоплатёж, чтобы не забыть про ежемесячный платёж. Штрафы — зло.",
        "{name}, если кредитов много — объедини их в один с меньшей ставкой.",
        "{name}, не бери микрозаймы. Там проценты такие, что лучше у мамы попросить.",
        "{name}, закрыла кредит? Устрой маленький праздник. Ты заслужила 🎉"
    ],
    "other": [
        "{name}, заведи привычку записывать каждую трату — хотя бы на неделю.",
        "{name}, в конце недели посмотри, куда утекло больше всего.",
        "{name}, спроси себя: «Эта покупка сделала меня счастливее?»",
        "{name}, не трать деньги на то, что можно получить бесплатно.",
        "{name}, установи лимит на спонтанные покупки — например, 1000 ₽ в неделю.",
        "{name}, перед крупной покупкой сравни цены в трёх местах.",
        "{name}, не поддавайся на «ограниченное предложение» — это маркетинг.",
        "{name}, кэшбэк — твой друг. Пользуйся картами с кэшбэком.",
        "{name}, откладывай 10% от любого дохода сразу, не думая.",
        "{name}, ты молодец, что следишь за деньгами. Так держать! 🌸"
    ]
}

# Хранилище индексов советов
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

# Функция для склонения имени
def get_name_form(name):
    name_lower = name.lower()
    if name_lower.endswith("а"):
        return name_lower[:-1]
    elif name_lower.endswith("я"):
        return name_lower[:-1] + "ь"
    elif name_lower.endswith("ия"):
        return name_lower[:-2] + "ий"
    else:
        return name_lower

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
            if "goals" not in data:
                data["goals"] = []
            if "budget" not in data:
                data["budget"] = None
            if "transactions" not in data:
                data["transactions"] = []
            if "monthly_stats" not in data:
                data["monthly_stats"] = {}
            if "last_reset_month" not in data:
                data["last_reset_month"] = None
            return data
    return {
        "usd": 0.0,
        "rub": 0,
        "transactions": [],
        "savings": [],
        "goals": [],
        "budget": None,
        "monthly_stats": {},
        "last_reset_month": None,
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

# ========== ОБНУЛЕНИЕ СТАТИСТИКИ ==========
def reset_monthly_stats_if_needed(user_id):
    data = load_user_data(user_id)
    now = get_moscow_time()
    current_month = now.month
    current_year = now.year
    
    if data["last_reset_month"] != current_month or data["last_reset_month"] is None:
        # Сохраняем статистику прошлого месяца в историю
        if data["last_reset_month"] is not None:
            key = f"{data['last_reset_month']}_{now.year if now.month > 1 else now.year-1}"
            data["monthly_stats"][key] = data.get("current_month_stats", {})
        
        # Обнуляем текущую статистику
        data["current_month_stats"] = {cat: 0 for cat in CATEGORIES.keys()}
        data["current_month_total"] = 0
        data["last_reset_month"] = current_month
        save_user_data(user_id, data)
    
    return data

# ========== КЛАВИАТУРЫ ==========
def get_main_keyboard(user_id):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("💎 Баланс"),
        KeyboardButton("📊 Отчёты"),
        KeyboardButton("➕ Доход"),
        KeyboardButton("➖ Расход"),
        KeyboardButton("🏦 Отложить"),
        KeyboardButton("🎯 Мои цели"),
        KeyboardButton("📈 Бюджет"),
        KeyboardButton("📂 Категории трат"),
        KeyboardButton("📋 История"),
        KeyboardButton("🕊️ Отменить"),
        KeyboardButton("⚙️ Настройки")
    ]
    if is_admin(user_id):
        buttons.append(KeyboardButton("👥 Пользователи"))
    keyboard.add(*buttons)
    return keyboard

def get_reports_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📅 Сегодня", callback_data="report_today"),
        InlineKeyboardButton("📆 За день", callback_data="report_single_day"),
        InlineKeyboardButton("🗓️ За период", callback_data="report_period"),
        InlineKeyboardButton("📊 За месяц", callback_data="report_monthly")
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
        InlineKeyboardButton("➕ Добавить цель", callback_data="goal_add"),
        InlineKeyboardButton("📋 Мои цели", callback_data="goal_list"),
        InlineKeyboardButton("❌ Закрыть", callback_data="cancel")
    )
    return keyboard

def get_advice_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("💡 Другой совет", callback_data="advice_another"),
        InlineKeyboardButton("🔙 Назад", callback_data="advice_back")
    )
    return keyboard

# ========== ИНСТРУКЦИЯ ==========
def get_instructions():
    return (
        "📚 ИНСТРУКЦИЯ\n━━━━━━━━━━━━━━━\n\n"
        "💎 Баланс — свободные, отложенные и доллары\n"
        "➕ Доход — сумма + описание → выбор валюты\n"
        "➖ Расход — сумма + описание → валюта → категория → совет\n"
        "🏦 Отложить — копилка на цели\n"
        "🎯 Мои цели — создать/пополнить цель\n"
        "📈 Бюджет — установить /budget 50000\n"
        "📂 Категории трат — проценты за месяц + совет\n"
        "📋 История — последние 15 операций\n"
        "🕊️ Отменить — откат последней операции\n\n"
        "🆔 /getid — узнать свой ID (для добавления подружек)\n\n"
        "🌸 Создано Алиной"
    )

# ========== ПРИВЕТСТВИЕ ==========
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    name = message.from_user.first_name or "Подруга"
    
    if not is_allowed(user_id):
        bot.reply_to(message,
            f"🌸 Привет, {name}!\n\n"
            "🔒 Доступ закрыт\n\n"
            "Чтобы получить доступ:\n"
            "1. Напиши /getid — узнай свой ID\n"
            "2. Перешли этот ID Алине\n"
            "3. Она добавит тебя\n\n"
            "После добавления напиши /start снова 😘")
        return
    
    reset_monthly_stats_if_needed(user_id)
    
    welcome = (
        f"🌸 Привет, {name}!\n\n"
        "Я — Твоя финансовая нянька с характером 💅\n"
        "Создала меня **Алина** — она, кстати, сама ахуеть это сделала 🔥\n\n"
        f"{get_instructions()}\n\n"
        "👇 Кнопки внизу — просто жми!\n\n"
        "🍀 Погнали, красотка! 😘"
    )
    bot.reply_to(message, welcome, reply_markup=get_main_keyboard(user_id))

@bot.message_handler(commands=['getid'])
def get_id(message):
    user_id = message.from_user.id
    bot.reply_to(message,
        f"🆔 Твой ID: `{user_id}`\n\nПерешли этот ID Алине.",
        parse_mode='Markdown')

# ========== УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ (ТОЛЬКО АДМИН) ==========
@bot.message_handler(commands=['adduser'])
def add_user(message):
    if not is_admin(message.from_user.id):
        return
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Формат: /adduser 123456789")
            return
        new_user_id = int(parts[1])
        
        user_data = load_user_data(new_user_id)
        save_user_data(new_user_id, user_data)
        
        bot.reply_to(message, f"✅ Пользователь `{new_user_id}` добавлен", parse_mode='Markdown')
        try:
            bot.send_message(new_user_id, 
                f"🎉 Тебе открыли доступ!\n\nНапиши /start\n\n{get_instructions()}")
        except:
            pass
    except:
        bot.reply_to(message, "❌ Ошибка")

@bot.message_handler(commands=['removeuser'])
def remove_user(message):
    if not is_admin(message.from_user.id):
        return
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
            bot.reply_to(message, f"ℹ️ Пользователь не найден", parse_mode='Markdown')
    except:
        bot.reply_to(message, "❌ Ошибка")

@bot.message_handler(commands=['users'])
def list_users(message):
    if not is_admin(message.from_user.id):
        return
    allowed = get_allowed_users()
    if not allowed:
        bot.reply_to(message, "👥 Список пуст")
        return
    text = "👥 ДОСТУП ЕСТЬ У:\n━━━━━━━━━━━━━━━\n"
    for uid in allowed:
        text += f"🆔 `{uid}`\n"
    text += f"\n👑 Админ: `{ADMIN_ID}`"
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "👥 Пользователи")
def user_management_button(message):
    if not is_admin(message.from_user.id):
        return
    bot.reply_to(message,
        "👥 Управление\n━━━━━━━━━━━━━━━\n\n"
        "/adduser ID — добавить\n"
        "/removeuser ID — удалить\n"
        "/users — список\n"
        "/getid — свой ID")

# ========== БАЛАНС ==========
@bot.message_handler(func=lambda m: m.text == "💎 Баланс")
def button_balance(message):
    if not is_allowed(message.from_user.id):
        return
    user_id = message.from_user.id
    data = reset_monthly_stats_if_needed(user_id)
    now = get_moscow_time()
    
    total_saved = sum(s["amount"] for s in data["savings"])
    free_rub = data["rub"] - total_saved
    
    text = f"💎 БАЛАНС\n━━━━━━━━━━━━━━━\n"
    text += f"💰 Свободно: {free_rub} ₽\n"
    text += f"🏦 Отложено на цели: {total_saved} ₽\n"
    text += f"━━━━━━━━━━━━━━━\n"
    text += f"💎 Итого: {data['rub']} ₽\n\n"
    text += f"🇺🇸 Доллары: {data['usd']:.2f}$\n\n"
    text += f"🕐 {now.strftime('%d.%m.%Y %H:%M')} МСК"
    
    if data["goals"]:
        text += "\n\n🎯 БЛИЖАЙШАЯ ЦЕЛЬ:\n"
        for g in data["goals"][:3]:
            left = g["target"] - g["current"]
            text += f"• {g['name']}: {g['current']} / {g['target']} ₽ (осталось {left})\n"
    
    bot.reply_to(message, text, reply_markup=get_main_keyboard(user_id))

# ========== КАТЕГОРИИ ТРАТ ==========
@bot.message_handler(func=lambda m: m.text == "📂 Категории трат")
def button_categories(message):
    if not is_allowed(message.from_user.id):
        return
    user_id = message.from_user.id
    name = message.from_user.first_name or "Подруга"
    data = reset_monthly_stats_if_needed(user_id)
    
    current_month_stats = data.get("current_month_stats", {})
    total = data.get("current_month_total", 0)
    now = get_moscow_time()
    month_name = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"][now.month-1]
    
    if total == 0:
        text = f"📂 КАТЕГОРИИ ТРАТ\n━━━━━━━━━━━━━━━\n\n📊 АНАЛИЗ ЗА {month_name.upper()}:\n💰 Всего потрачено: 0 ₽\n\nПока нет трат за этот месяц.\nДобавь расход через кнопку ➖ Расход"
        bot.reply_to(message, text, reply_markup=get_main_keyboard(user_id))
        return
    
    # Сортируем категории по сумме
    cat_list = []
    for cat_key, amount in current_month_stats.items():
        if amount > 0:
            percent = (amount / total) * 100
            cat_list.append((cat_key, amount, percent))
    cat_list.sort(key=lambda x: x[1], reverse=True)
    
    text = f"📂 КАТЕГОРИИ ТРАТ\n━━━━━━━━━━━━━━━\n\n📊 АНАЛИЗ ЗА {month_name.upper()}:\n💰 Всего потрачено: {total} ₽\n\n"
    
    for cat_key, amount, percent in cat_list:
        cat_name = CATEGORIES[cat_key]
        text += f"{cat_name}: {percent:.0f}% ({amount} ₽)\n"
    
    # Сохраняем для кнопки "Хочу совет"
    bot.temp_categories = getattr(bot, "temp_categories", {})
    bot.temp_categories[user_id] = {"list": cat_list, "month": now.month, "total": total}
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("💡 Хочу совет", callback_data="advice_main"))
    bot.reply_to(message, text, reply_markup=keyboard)

# ========== ОБРАБОТКА СОВЕТОВ ==========
@bot.callback_query_handler(func=lambda call: call.data.startswith("advice_"))
def handle_advice_callback(call):
    if not is_allowed(call.from_user.id):
        bot.answer_callback_query(call.id, "Нет доступа")
        return
    
    user_id = call.from_user.id
    name = call.from_user.first_name or "Подруга"
    name_form = get_name_form(name)
    
    temp_data = getattr(bot, "temp_categories", {}).get(user_id, {})
    cat_list = temp_data.get("list", [])
    total = temp_data.get("total", 0)
    
    if not cat_list or total == 0:
        bot.edit_message_text("Пока нет трат за этот месяц, не могу дать совет 😢", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "advice_main":
        # Берём самую большую категорию
        top_cat = cat_list[0]
        cat_key = top_cat[0]
        amount = top_cat[1]
        percent = top_cat[2]
        cat_name = CATEGORIES[cat_key]
        
        advice = get_next_advice(user_id, cat_key).format(name=name_form)
        
        text = f"💡 ХОЧУ СОВЕТ\n━━━━━━━━━━━━━━━\n\n{name_form}, я посмотрела твои траты за месяц 👀\n\nБольше всего денег уходит на {cat_name} — {percent:.0f}% ({amount} ₽)\n\n🎯 Мой совет:\n{advice}\n\n━━━━━━━━━━━━━━━\n💡 Другой совет | 🔙 Назад"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("💡 Другой совет", callback_data="advice_next_0"),
            InlineKeyboardButton("🔙 Назад", callback_data="advice_back_to_cats")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard)
        
    elif call.data.startswith("advice_next_"):
        idx = int(call.data.split("_")[2])
        next_idx = (idx + 1) % len(cat_list)
        cat_key = cat_list[next_idx][0]
        amount = cat_list[next_idx][1]
        percent = cat_list[next_idx][2]
        cat_name = CATEGORIES[cat_key]
        
        advice = get_next_advice(user_id, cat_key).format(name=name_form)
        
        text = f"💡 ХОЧУ СОВЕТ\n━━━━━━━━━━━━━━━\n\nВот совет для {cat_name.lower()} ({percent:.0f}%, {amount} ₽):\n\n{advice}\n\n━━━━━━━━━━━━━━━\n💡 Другой совет | 🔙 Назад"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("💡 Другой совет", callback_data=f"advice_next_{next_idx}"),
            InlineKeyboardButton("🔙 Назад", callback_data="advice_back_to_cats")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard)
        
    elif call.data == "advice_back_to_cats":
        button_categories(call.message)
    
    bot.answer_callback_query(call.id)

# ========== ОТЧЁТЫ ==========
@bot.message_handler(func=lambda m: m.text == "📊 Отчёты")
def button_reports(message):
    if not is_allowed(message.from_user.id):
        return
    bot.send_message(message.chat.id, "📅 Выбери отчёт:", reply_markup=get_reports_keyboard())

# ========== ДОХОД ==========
@bot.message_handler(func=lambda m: m.text == "➕ Доход")
def button_income(message):
    if not is_allowed(message.from_user.id):
        return
    msg = bot.reply_to(message, "💰 Сумма и описание:\n\nПример: 5000 зарплата")
    bot.register_next_step_handler(msg, process_income_amount)

def process_income_amount(message):
    user_id = message.from_user.id
    if not is_allowed(user_id):
        return
    try:
        parts = message.text.split()
        amount = float(parts[0])
        comment = " ".join(parts[1:]) if len(parts) > 1 else ""
        if not hasattr(bot, "temp_data"):
            bot.temp_data = {}
        bot.temp_data[message.chat.id] = {"amount": amount, "comment": comment}
        bot.send_message(message.chat.id, "💱 Выбери валюту:", reply_markup=get_currency_keyboard("income"))
    except:
        bot.reply_to(message, "❌ Ошибка. Пример: 5000 зарплата")

# ========== РАСХОД ==========
@bot.message_handler(func=lambda m: m.text == "➖ Расход")
def button_expense(message):
    if not is_allowed(message.from_user.id):
        return
    msg = bot.reply_to(message, "💸 Сумма и описание:\n\nПример: 1200 продукты")
    bot.register_next_step_handler(msg, process_expense_amount)

def process_expense_amount(message):
    user_id = message.from_user.id
    if not is_allowed(user_id):
        return
    try:
        parts = message.text.split()
        amount = float(parts[0])
        comment = " ".join(parts[1:]) if len(parts) > 1 else ""
        if not hasattr(bot, "temp_data"):
            bot.temp_data = {}
        bot.temp_data[message.chat.id] = {"amount": amount, "comment": comment, "need_category": True}
        bot.send_message(message.chat.id, "💱 Выбери валюту:", reply_markup=get_currency_keyboard("expense"))
    except:
        bot.reply_to(message, "❌ Ошибка. Пример: 1200 продукты")

# ========== ОТЛОЖЕННЫЕ ==========
@bot.message_handler(func=lambda m: m.text == "🏦 Отложить")
def button_savings(message):
    if not is_allowed(message.from_user.id):
        return
    bot.send_message(message.chat.id, "🏦 Управление отложенными:", reply_markup=get_savings_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("savings_"))
def handle_savings_callback(call):
    if not is_allowed(call.from_user.id):
        bot.answer_callback_query(call.id, "Нет доступа")
        return
    
    if call.data == "savings_add":
        bot.edit_message_text("💰 Сумма и цель:\n\nПример: 10000 новый телефон", call.message.chat.id, call.message.message_id)
        bot.register_next_step_handler(call.message, process_savings_add)
    elif call.data == "savings_remove":
        bot.edit_message_text("💰 Сумма и цель (вернуть):\n\nПример: 2000 отпуск", call.message.chat.id, call.message.message_id)
        bot.register_next_step_handler(call.message, process_savings_remove)
    elif call.data == "savings_spend":
        bot.edit_message_text("💸 Сумма и цель (потратить):\n\nПример: 3000 новый телефон", call.message.chat.id, call.message.message_id)
        bot.register_next_step_handler(call.message, process_savings_spend)
    elif call.data == "savings_list":
        show_savings_list(call.message)
    bot.answer_callback_query(call.id)

def process_savings_add(message):
    user_id = message.from_user.id
    if not is_allowed(user_id):
        return
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
        
        bot.reply_to(message, f"✅ Отложено {int(amount)} ₽ на «{name}»")
        button_balance(message)
    except:
        bot.reply_to(message, "❌ Ошибка. Формат: 10000 новый телефон")

def process_savings_remove(message):
    user_id = message.from_user.id
    if not is_allowed(user_id):
        return
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
        bot.reply_to(message, "❌ Ошибка. Формат: 2000 отпуск")

def process_savings_spend(message):
    user_id = message.from_user.id
    if not is_allowed(user_id):
        return
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
                    
                    bot.reply_to(message, f"✅ Потрачено {int(amount)} ₽ из отложенного на «{name}»")
                    button_balance(message)
                    return
                else:
                    bot.reply_to(message, f"❌ В «{s['name']}» отложено только {int(s['amount'])} ₽")
                    return
        bot.reply_to(message, f"❌ Цель «{name}» не найдена")
    except:
        bot.reply_to(message, "❌ Ошибка. Формат: 3000 новый телефон")

def show_savings_list(message):
    user_id = message.from_user.id
    if not is_allowed(user_id):
        return
    data = load_user_data(user_id)
    if not data["savings"]:
        bot.reply_to(message, "🏦 Нет отложенных денег")
        return
    text = "🏦 ОТЛОЖЕННЫЕ ЦЕЛИ:\n━━━━━━━━━━━━━━━\n"
    for s in data["savings"]:
        text += f"• {s['name']}: {int(s['amount'])} ₽\n"
    bot.reply_to(message, text)

# ========== ЦЕЛИ ==========
@bot.message_handler(func=lambda m: m.text == "🎯 Мои цели")
def button_goals(message):
    if not is_allowed(message.from_user.id):
        return
    bot.send_message(message.chat.id, "🎯 Управление целями:", reply_markup=get_goals_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("goal_"))
def handle_goals_callback(call):
    if not is_allowed(call.from_user.id):
        bot.answer_callback_query(call.id, "Нет доступа")
        return
    
    if call.data == "goal_add":
        bot.edit_message_text("🎯 Название цели и сумма:\n\nПример: Золотое яблочко 50000", call.message.chat.id, call.message.message_id)
        bot.register_next_step_handler(call.message, process_goal_add)
    elif call.data == "goal_list":
        show_goals_list(call.message)
    bot.answer_callback_query(call.id)

def process_goal_add(message):
    user_id = message.from_user.id
    if not is_allowed(user_id):
        return
    try:
        parts = message.text.rsplit(" ", 1)
        if len(parts) < 2:
            bot.reply_to(message, "❌ Формат: Название 50000")
            return
        name = parts[0]
        target = float(parts[1])
        
        data = load_user_data(user_id)
        data["goals"].append({
            "name": name,
            "target": target,
            "current": 0
        })
        save_user_data(user_id, data)
        
        bot.reply_to(message, f"✅ Цель «{name}» создана! Нужно накопить: {int(target)} ₽")
    except:
        bot.reply_to(message, "❌ Ошибка. Формат: Золотое яблочко 50000")

def show_goals_list(message):
    user_id = message.from_user.id
    if not is_allowed(user_id):
        return
    data = load_user_data(user_id)
    if not data["goals"]:
        bot.reply_to(message, "🎯 У тебя пока нет целей.\nДобавь через «➕ Добавить цель»")
        return
    
    text = "🎯 ТВОИ ЦЕЛИ\n━━━━━━━━━━━━━━━\n\n"
    for g in data["goals"]:
        left = g["target"] - g["current"]
        percent = (g["current"] / g["target"]) * 100 if g["target"] > 0 else 0
        text += f"💰 {g['name']}\n"
        text += f"   Нужно: {int(g['target'])} ₽\n"
        text += f"   Отложено: {int(g['current'])} ₽\n"
        text += f"   Осталось: {int(left)} ₽\n"
        text += f"   Прогресс: {'█' * int(percent//10)}{'░' * (10 - int(percent//10))} {percent:.0f}%\n\n"
    
    bot.reply_to(message, text)

# ========== БЮДЖЕТ ==========
@bot.message_handler(func=lambda m: m.text == "📈 Бюджет")
def button_budget(message):
    if not is_allowed(message.from_user.id):
        return
    user_id = message.from_user.id
    data = reset_monthly_stats_if_needed(user_id)
    now = get_moscow_time()
    month_name = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"][now.month-1]
    
    if data["budget"] and data["budget"]["month"] == now.month and data["budget"]["year"] == now.year:
        budget_amount = data["budget"]["amount"]
        expenses = data.get("current_month_total", 0)
        remaining = budget_amount - expenses
        percent = (expenses / budget_amount) * 100 if budget_amount > 0 else 0
        
        text = f"📈 БЮДЖЕТ НА {month_name.upper()}\n━━━━━━━━━━━━━━━\n"
        text += f"💰 Бюджет: {int(budget_amount)} ₽\n"
        text += f"💸 Потрачено: {int(expenses)} ₽ ({percent:.0f}%)\n"
        text += f"✅ Осталось: {int(remaining)} ₽\n"
        
        if percent >= 100:
            text += f"\n💀 Бля… Ты превысила бюджет на {int(expenses - budget_amount)} ₽"
        elif percent >= 80:
            text += f"\n⚠️ Осталось всего {int(remaining)} ₽ до конца месяца!"
        
        bot.reply_to(message, text, reply_markup=get_main_keyboard(user_id))
    else:
        bot.reply_to(message, 
            "📈 Бюджет не установлен\n\nУстанови: /budget 50000")

@bot.message_handler(commands=['budget'])
def set_budget(message):
    if not is_allowed(message.from_user.id):
        return
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Формат: /budget 50000")
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
        
        bot.reply_to(message, f"🎯 Окей, зайка. Бюджет на месяц — {int(amount)} ₽")
    except:
        bot.reply_to(message, "❌ Ошибка")

# ========== ИСТОРИЯ ==========
@bot.message_handler(func=lambda m: m.text == "📋 История")
def show_history(message):
    if not is_allowed(message.from_user.id):
        return
    user_id = message.from_user.id
    data = load_user_data(user_id)
    last_tx = data["transactions"][-15:]
    
    if not last_tx:
        bot.reply_to(message, "📋 История пуста")
        return
    
    text = "📋 ПОСЛЕДНИЕ 15 ОПЕРАЦИЙ\n━━━━━━━━━━━━━━━\n"
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
    
    bot.reply_to(message, text)

# ========== ОТМЕНИТЬ ==========
@bot.message_handler(func=lambda m: m.text == "🕊️ Отменить")
def button_undo(message):
    if not is_allowed(message.from_user.id):
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
    bot.reply_to(message, f"↩️ Отменено: {last['sign']}{amount_display}{last['currency']} {last['comment']}")

# ========== НАСТРОЙКИ ==========
@bot.message_handler(func=lambda m: m.text == "⚙️ Настройки")
def button_settings(message):
    if not is_allowed(message.from_user.id):
        return
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("💰 Установить остаток", callback_data="settings_balance"))
    keyboard.add(InlineKeyboardButton("📊 Очистить всё", callback_data="settings_clear"))
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
        bot.edit_message_text("⚠️ Точно очистить все данные?\nЭто действие необратимо.", call.message.chat.id, call.message.message_id)
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("✅ Да, очистить", callback_data="confirm_clear"))
        keyboard.add(InlineKeyboardButton("❌ Нет", callback_data="cancel"))
        bot.send_message(call.message.chat.id, "Подтверждение:", reply_markup=keyboard)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "confirm_clear")
def confirm_clear(call):
    if not is_allowed(call.from_user.id):
        return
    user_id = call.from_user.id
    data = load_user_data(user_id)
    data["transactions"] = []
    data["savings"] = []
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
    if not is_allowed(user_id):
        return
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
            bot.reply_to(message, "❌ Укажи валюту: $ или ₽")
            return
        save_user_data(user_id, data)
        button_balance(message)
    except:
        bot.reply_to(message, "❌ Формат: $ 1000 или ₽ 50000")

# ========== ОБРАБОТКА ВАЛЮТ И КАТЕГОРИЙ ==========
@bot.callback_query_handler(func=lambda call: call.data.startswith("income") or call.data.startswith("expense") or call.data == "cancel")
def handle_currency_callback(call):
    if call.data == "cancel":
        bot.edit_message_text("❌ Отменено", call.message.chat.id, call.message.message_id)
        if hasattr(bot, "temp_data") and call.message.chat.id in bot.temp_data:
            del bot.temp_data[call.message.chat.id]
        return
    
    if not is_allowed(call.from_user.id):
        bot.answer_callback_query(call.id, "Нет доступа")
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
    now = get_moscow_time()
    
    if call.data.startswith("income"):
        currency = call.data.split("_")[1]
        if currency == "$":
            data["usd"] += amount
            amount_display = f"{amount:.2f}{currency}"
        else:
            data["rub"] += int(amount)
            amount_display = f"{int(amount)}{currency}"
        
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
            bot.edit_message_text("📂 Выбери категорию:", call.message.chat.id, call.message.message_id, reply_markup=get_category_keyboard("expense"))
        else:
            if currency == "$":
                data["usd"] -= amount
                amount_display = f"{amount:.2f}{currency}"
            else:
                data["rub"] -= int(amount)
                amount_display = f"{int(amount)}{currency}"
            
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
    category_key = parts[2]
    
    user_data = getattr(bot, "temp_data", {}).get(call.message.chat.id, {})
    amount = user_data.get("amount")
    comment = user_data.get("comment", "")
    currency = user_data.get("currency")
    
    if not amount:
        bot.answer_callback_query(call.id, "Ошибка")
        return
    
    user_id = call.from_user.id
    data = reset_monthly_stats_if_needed(user_id)
    now = get_moscow_time()
    
    if currency == "$":
        data["usd"] -= amount
        amount_display = f"{amount:.2f}{currency}"
    else:
        data["rub"] -= int(amount)
        amount_display = f"{int(amount)}{currency}"
        
        # Обновляем статистику по категориям
        if category_key in data["current_month_stats"]:
            data["current_month_stats"][category_key] += int(amount)
        else:
            data["current_month_stats"][category_key] = int(amount)
        data["current_month_total"] = data.get("current_month_total", 0) + int(amount)
    
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
    
    # Показываем совет
    name = call.from_user.first_name or "Подруга"
    name_form = get_name_form(name)
    advice = get_next_advice(user_id, category_key).format(name=name_form)
    
    bot.edit_message_text(
        f"✅ РАСХОД {amount_display} {comment}\n📂 {category_name}\n🕐 {now.strftime('%H:%M')} МСК\n\n💡 {advice}",
        call.message.chat.id,
        call.message.message_id
    )
    
    if hasattr(bot, "temp_data") and call.message.chat.id in bot.temp_data:
        del bot.temp_data[call.message.chat.id]
    
    bot.answer_callback_query(call.id)

# ========== ОТЧЁТЫ (СЕГОДНЯ, ДЕНЬ, ПЕРИОД, МЕСЯЦ) ==========
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
        bot.send_message(chat_id, f"📅 ЗА {today_name}\n━━━━━━━━━━━━━━━\n\nЗа сегодня операций нет")
        return
    
    report = f"📅 ЗА {today_name}\n━━━━━━━━━━━━━━━\n\n📋 ОПЕРАЦИИ:\n"
    for tx in today_tx:
        time = tx["date"].split()[1][:5]
        sign = "➕" if tx["sign"] == '+' else "➖"
        if tx["currency"] == "$":
            report += f"{sign} {tx['amount']:.2f}{tx['currency']} {tx['comment']} ({time})\n"
        else:
            report += f"{sign} {int(tx['amount'])}{tx['currency']} {tx['comment']} ({time})\n"
    
    report += f"\n📈 ДОХОДЫ:"
    if income_usd: report += f"\n  {income_usd:.2f}$"
    if income_rub: report += f"\n  {income_rub}₽"
    if not income_usd and not income_rub: report += " —"
    
    report += f"\n\n📉 РАСХОДЫ:"
    if expense_usd: report += f"\n  {expense_usd:.2f}$"
    if expense_rub: report += f"\n  {expense_rub}₽"
    if not expense_usd and not expense_rub: report += " —"
    
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
            bot.send_message(chat_id, f"📆 ЗА {display_date}\n━━━━━━━━━━━━━━━\n\nОпераций нет")
            return
        
        report = f"📆 ЗА {display_date}\n━━━━━━━━━━━━━━━\n\n📋 ОПЕРАЦИИ:\n"
        for tx in day_tx:
            time = tx["date"].split()[1][:5]
            sign = "➕" if tx["sign"] == '+' else "➖"
            if tx["currency"] == "$":
                report += f"{sign} {tx['amount']:.2f}{tx['currency']} {tx['comment']} ({time})\n"
            else:
                report += f"{sign} {int(tx['amount'])}{tx['currency']} {tx['comment']} ({time})\n"
        
        report += f"\n📈 ДОХОДЫ:"
        if income_usd: report += f"\n  {income_usd:.2f}$"
        if income_rub: report += f"\n  {income_rub}₽"
        if not income_usd and not income_rub: report += " —"
        
        report += f"\n\n📉 РАСХОДЫ:"
        if expense_usd: report += f"\n  {expense_usd:.2f}$"
        if expense_rub: report += f"\n  {expense_rub}₽"
        if not expense_usd and not expense_rub: report += " —"
        
        bot.send_message(chat_id, report)
    except:
        bot.send_message(chat_id, "❌ Ошибка. Пример: 1.04")

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
            bot.send_message(chat_id, f"📅 ЗА ПЕРИОД\n{start_date_str} — {end_date_str}\n━━━━━━━━━━━━━━━\n\nОпераций нет")
            return
        
        report = f"📅 ЗА ПЕРИОД\n{start_date_str} — {end_date_str}\n━━━━━━━━━━━━━━━\n\n📋 ОПЕРАЦИИ:\n"
        for tx in period_tx:
            tx_date = tx["date"].split()[0][5:]
            time = tx["date"].split()[1][:5]
            sign = "➕" if tx["sign"] == '+' else "➖"
            if tx["currency"] == "$":
                report += f"{sign} {tx['amount']:.2f}{tx['currency']} {tx['comment']}\n   📅 {tx_date} {time}\n\n"
            else:
                report += f"{sign} {int(tx['amount'])}{tx['currency']} {tx['comment']}\n   📅 {tx_date} {time}\n\n"
        
        report += "━━━━━━━━━━━━━━━\n"
        report += "📈 ВСЕГО ДОХОДЫ:\n"
        if income_usd: report += f"  $ {income_usd:.2f}\n"
        if income_rub: report += f"  ₽ {income_rub}\n"
        if not income_usd and not income_rub: report += "  —\n"
        
        report += "\n📉 ВСЕГО РАСХОДЫ:\n"
        if expense_usd: report += f"  $ {expense_usd:.2f}\n"
        if expense_rub: report += f"  ₽ {expense_rub}\n"
        if not expense_usd and not expense_rub: report += "  —\n"
        
        bot.send_message(chat_id, report)
    except:
        bot.send_message(chat_id, "❌ Ошибка периода")

def send_monthly_report(chat_id, user_id):
    data = load_user_data(user_id)
    now = get_moscow_time()
    current_month = now.month
    current_year = now.year
    month_name = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"][current_month-1]
    
    total = data.get("current_month_total", 0)
    stats = data.get("current_month_stats", {})
    
    if total == 0:
        bot.send_message(chat_id, f"📊 ЗА {month_name.upper()}\n━━━━━━━━━━━━━━━\n\nЗа этот месяц пока нет расходов")
        return
    
    # Сортируем категории
    cat_list = []
    for cat_key, amount in stats.items():
        if amount > 0:
            percent = (amount / total) * 100
            cat_list.append((cat_key, amount, percent))
    cat_list.sort(key=lambda x: x[1], reverse=True)
    
    text = f"📊 ОТЧЁТ ЗА {month_name.upper()}\n━━━━━━━━━━━━━━━\n\n💰 Всего потрачено: {total} ₽\n\n🔝 ТОП-3 КАТЕГОРИИ:\n"
    for i, (cat_key, amount, percent) in enumerate(cat_list[:3]):
        cat_name = CATEGORIES[cat_key]
        text += f"{i+1}. {cat_name} — {amount} ₽ ({percent:.0f}%)\n"
    
    if len(cat_list) > 3:
        text += f"\n📉 ОСТАЛЬНЫЕ:\n"
        for cat_key, amount, percent in cat_list[3:]:
            cat_name = CATEGORIES[cat_key]
            text += f"• {cat_name} — {percent:.0f}% ({amount} ₽)\n"
    
    # Добавляем совет по самой большой категории
    if cat_list:
        top_cat = cat_list[0]
        name = "Подруга"
        name_form = get_name_form(name)
        advice = get_next_advice(user_id, top_cat[0]).format(name=name_form)
        text += f"\n💡 СОВЕТ МЕСЯЦА:\n{advice}"
    
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
        bot.waiting_for_day = getattr(bot, "waiting_for_day", {})
        bot.waiting_for_day[call.message.chat.id] = user_id
    elif call.data == "report_period":
        bot.edit_message_text("🗓️ Начало периода: 1.04", call.message.chat.id, call.message.message_id)
        bot.waiting_for_period = getattr(bot, "waiting_for_period", {})
        bot.waiting_for_period[call.message.chat.id] = {"step": "start", "user_id": user_id}
    elif call.data == "report_monthly":
        bot.edit_message_text("📊 Загружаю...", call.message.chat.id, call.message.message_id)
        send_monthly_report(call.message.chat.id, user_id)
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
            bot.reply_to(message, f"✅ Начало: {date_input}\n📅 Конец:")
        elif state["step"] == "end":
            start_date = state["start_date"]
            user_id = state["user_id"]
            del bot.waiting_for_period[message.chat.id]
            send_period_report(message.chat.id, user_id, start_date, date_input)
    except:
        bot.reply_to(message, "❌ Формат: 1.04")
        if state["step"] == "start":
            del bot.waiting_for_period[message.chat.id]

# ========== АВТОМАТИЧЕСКИЙ ОТЧЁТ 1-ГО ЧИСЛА ==========
def check_monthly_reset_and_report():
    while True:
        try:
            now = get_moscow_time()
            # Проверяем, нужно ли обнулить статистику
            for user_id in get_allowed_users():
                data = load_user_data(user_id)
                
                # Обнуление статистики 1-го числа
                if data["last_reset_month"] != now.month:
                    if data["last_reset_month"] is not None:
                        # Отправляем отчёт за прошлый месяц
                        send_monthly_report_to_user(user_id, data["last_reset_month"], now.year if now.month > 1 else now.year - 1, data)
                    reset_monthly_stats_if_needed(user_id)
                
                # Отправляем отчёт за прошлый месяц 1-го числа
                if data["last_report_month"] != now.month and now.day == 1:
                    if data["last_report_month"] is not None and data["last_report_month"] != now.month:
                        send_monthly_report_to_user(user_id, data["last_report_month"], now.year if now.month > 1 else now.year - 1, data)
                    data["last_report_month"] = now.month
                    save_user_data(user_id, data)
            
            time.sleep(3600)
        except:
            time.sleep(3600)

def send_monthly_report_to_user(user_id, month, year, data=None):
    if data is None:
        data = load_user_data(user_id)
    
    month_name = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"][month-1]
    
    # Берём статистику за тот месяц
    stats_key = f"{month}_{year}"
    stats = data.get("monthly_stats", {}).get(stats_key, {})
    total = sum(stats.values())
    
    if total == 0:
        text = f"📊 АВТООТЧЁТ ЗА {month_name.upper()}\n━━━━━━━━━━━━━━━\n\nЗа этот месяц расходов не было. Молодец! 🌸"
    else:
        cat_list = []
        for cat_key, amount in stats.items():
            percent = (amount / total) * 100
            cat_list.append((cat_key, amount, percent))
        cat_list.sort(key=lambda x: x[1], reverse=True)
        
        text = f"📊 АВТООТЧЁТ ЗА {month_name.upper()}\n━━━━━━━━━━━━━━━\n\n💰 Всего потрачено: {total} ₽\n\n🔝 ТОП-3 КАТЕГОРИИ:\n"
        for i, (cat_key, amount, percent) in enumerate(cat_list[:3]):
            cat_name = CATEGORIES[cat_key]
            text += f"{i+1}. {cat_name} — {amount} ₽ ({percent:.0f}%)\n"
        
        if cat_list:
            top_cat = cat_list[0]
            name = "Зайка"
            advice = get_next_advice(user_id, top_cat[0]).format(name=name)
            text += f"\n💡 СОВЕТ МЕСЯЦА:\n{advice}"
    
    text += "\n\n🌸 Новый месяц — новые возможности! Желаю тебе тратить с умом 💅"
    
    try:
        bot.send_message(user_id, text)
    except:
        pass

# ========== ЗАПУСК ==========
def start_background_checker():
    thread = threading.Thread(target=check_monthly_reset_and_report, daemon=True)
    thread.start()

print("🌸 Бот Алины запущен")
print(f"👑 Админ: {ADMIN_ID}")
print("💰 Мультипользовательский режим")
print("🎯 Цели + отложенные")
print("💡 Советы с именами")
print("📊 Обнуление статистики каждый месяц")
print("🕐 Московское время")

start_background_checker()
bot.infinity_polling()
