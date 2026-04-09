import telebot
from telebot.types import ReplyKeyboardMarkup
import json
import os
from datetime import datetime
import calendar

TOKEN = '8692541391:AAH6Cf8eh_afsynkA277SJ-_28ihs2VEutI'
bot = telebot.TeleBot(TOKEN)

DATA_FILE = 'finance.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'rub': 0, 'usd': 0, 'transactions': [], 'goals': [], 'obligatory': {'квартира': 27000, 'кредит': 10000}}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = ['💰 Баланс', '📊 Отчёт за месяц', '🎯 Мои цели', '➕ Доход (₽)', '➖ Расход (₽)', '💵 Доход ($)', '🇺🇸 Расход ($)', '🏠 Обязательные', '⚙️ Установить остаток']
    kb.add(*buttons)
    return kb

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🌸 Привет! Я твой финансовый помощник.\n\n💰 Рубли и доллары отдельно\n🎯 Цели и отчёты\n👇 Используй кнопки", reply_markup=main_keyboard())

@bot.message_handler(func=lambda m: m.text == '💰 Баланс')
def show_balance(message):
    data = load_data()
    text = f"💰 БАЛАНС:\n\n🇷🇺 Рубли: {data['rub']} ₽\n🇺🇸 Доллары: {data['usd']}$"
    goal = next((g for g in data['goals'] if g['name'] == 'кератин'), None)
    if goal:
        left = goal['target'] - goal['current']
        text += f"\n\n🎯 Кератин: {goal['current']} / {goal['target']} ₽ (осталось {left} ₽)"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == '⚙️ Установить остаток')
def ask_balance(message):
    bot.send_message(message.chat.id, "Введи: рубли доллары\nПример: 5000 20")

@bot.message_handler(func=lambda m: m.text and len(m.text.split()) == 2 and m.text.split()[0].isdigit())
def set_balance(message):
    rub, usd = map(float, message.text.split())
    data = load_data()
    data['rub'] = rub
    data['usd'] = usd
    save_data(data)
    bot.send_message(message.chat.id, f"✅ Остаток: {rub} ₽ и {usd}$")

@bot.message_handler(func=lambda m: m.text in ['➕ Доход (₽)', '➖ Расход (₽)', '💵 Доход ($)', '🇺🇸 Расход ($)'])
def ask_amount(message):
    bot.send_message(message.chat.id, "Введи сумму и комментарий\nПример: 1500 зарплата")
    bot.register_next_step_handler(message, process_transaction, message.text)

def process_transaction(message, action):
    parts = message.text.split(maxsplit=1)
    amount = float(parts[0])
    comment = parts[1] if len(parts) > 1 else ""
    data = load_data()
    if action == '➕ Доход (₽)':
        data['rub'] += amount
    elif action == '➖ Расход (₽)':
        data['rub'] -= amount
    elif action == '💵 Доход ($)':
        data['usd'] += amount
    elif action == '🇺🇸 Расход ($)':
        data['usd'] -= amount
    data['transactions'].append({'date': datetime.now().isoformat(), 'type': action, 'amount': amount, 'comment': comment})
    save_data(data)
    bot.send_message(message.chat.id, f"✅ Добавлено: {amount} {comment}")

@bot.message_handler(func=lambda m: m.text == '📊 Отчёт за месяц')
def monthly_report(message):
    data = load_data()
    now = datetime.now()
    rub_in = sum(t['amount'] for t in data['transactions'] if t['type'] == '➕ Доход (₽)' and datetime.fromisoformat(t['date']).month == now.month)
    rub_out = sum(t['amount'] for t in data['transactions'] if t['type'] == '➖ Расход (₽)' and datetime.fromisoformat(t['date']).month == now.month)
    usd_in = sum(t['amount'] for t in data['transactions'] if t['type'] == '💵 Доход ($)' and datetime.fromisoformat(t['date']).month == now.month)
    usd_out = sum(t['amount'] for t in data['transactions'] if t['type'] == '🇺🇸 Расход ($)' and datetime.fromisoformat(t['date']).month == now.month)
    text = f"📆 {calendar.month_name[now.month]}\n🇷🇺 Доходы: {rub_in} ₽, Расходы: {rub_out} ₽, Итого: +{rub_in - rub_out} ₽\n🇺🇸 Доходы: {usd_in}$, Расходы: {usd_out}$, Итого: +{usd_in - usd_out}$"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == '🎯 Мои цели')
def show_goals(message):
    data = load_data()
    if not data['goals']:
        bot.send_message(message.chat.id, "Нет целей. Добавь: /goal кератин 6500 2026-04-20")
    else:
        text = "🎯 ЦЕЛИ:\n"
        for g in data['goals']:
            text += f"\n{g['name']}: {g['current']} / {g['target']} ₽ (до {g['deadline']})"
        bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['goal'])
def add_goal(message):
    parts = message.text.split()
    if len(parts) < 3:
        bot.send_message(message.chat.id, "❌ /goal название сумма ГГГГ-ММ-ДД\nПример: /goal кератин 6500 2026-04-20")
        return
    data = load_data()
    data['goals'].append({'name': parts[1], 'target': float(parts[2]), 'current': 0, 'deadline': parts[3] if len(parts) > 3 else ''})
    save_data(data)
    bot.send_message(message.chat.id, f"✅ Цель {parts[1]}: {parts[2]} ₽")

@bot.message_handler(commands=['setgoal'])
def set_goal_progress(message):
    parts = message.text.split()
    if len(parts) < 3:
        bot.send_message(message.chat.id, "❌ /setgoal название сумма\nПример: /setgoal кератин 4000")
        return
    data = load_data()
    for g in data['goals']:
        if g['name'] == parts[1]:
            g['current'] = float(parts[2])
    save_data(data)
    bot.send_message(message.chat.id, f"✅ {parts[1]}: {parts[2]} ₽ отложено")

@bot.message_handler(func=lambda m: m.text == '🏠 Обязательные')
def obligatory(message):
    data = load_data()
    text = "🏠 Обязательные расходы:\n"
    for name, amount in data['obligatory'].items():
        text += f"{name}: {amount} ₽\n"
    bot.send_message(message.chat.id, text)

if __name__ == '__main__':
    print("Бот запущен!")
    bot.infinity_polling()
