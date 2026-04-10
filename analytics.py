from collections import Counter
import datetime as dt

MARKET_HINTS = ["wb", "wildberries", "ozon", "золотое яблоко"]
COMFORT_CATEGORIES = {"food", "cafe", "transport", "shopping"}
LOW_RESOURCE_MOODS = {"устала", "тревожно", "грустно", "злая"}

def build_behavior_insights(data, categories_map):
    tx = [t for t in data.get("transactions", []) if t.get("sign") == '-' and t.get("currency") == "₽"][-40:]
    if not tx:
        return ["Пока мало данных для аналитики. Добавь 5–10 трат и вернись за инсайтами."]

    insights = []
    total = sum(int(t.get("amount", 0)) for t in tx)
    micro = [t for t in tx if int(t.get("amount", 0)) <= 500]
    if len(micro) >= 6:
        insights.append(f"Микротраты: {len(micro)} шт., суммарно {sum(int(t['amount']) for t in micro)} ₽.")

    marketplace = [t for t in tx if any(w in t.get("comment", "").lower() for w in MARKET_HINTS)]
    if len(marketplace) >= 3:
        insights.append(f"Маркетплейс-паттерн: {len(marketplace)} покупок из {len(tx)} последних.")

    by_hour = Counter(int(t["date"].split()[1].split(":")[0]) for t in tx if " " in t.get("date", ""))
    if by_hour:
        top_hour, hour_count = by_hour.most_common(1)[0]
        if hour_count >= 4:
            insights.append(f"Пик трат в {top_hour:02d}:00 — {hour_count} операций.")

    by_cat = Counter(t.get("category", "other") for t in tx)
    top_cat, top_count = by_cat.most_common(1)[0]
    insights.append(f"Топ-категория: {categories_map.get(top_cat, top_cat)} ({top_count} операций).")

    moods = data.get("moods", [])[-10:]
    low = sum(1 for m in moods if m.get("mood") in LOW_RESOURCE_MOODS)
    comfort = [t for t in tx if t.get("category") in COMFORT_CATEGORIES]
    if low >= 4 and len(comfort) >= 5:
        insights.append("Похоже на паттерн «усталость → покупка комфорта».")

    if len(set(t.get("category", "other") for t in tx[-10:])) >= 6:
        insights.append("Последние траты хаотичны по категориям — признак импульсного режима.")

    month_end = sum(1 for t in tx if int(t["date"].split()[0].split("-")[2]) >= 25)
    if month_end >= 4:
        insights.append("Ближе к концу месяца траты ускоряются — проверь лимиты последних 7 дней.")

    weekend = 0
    for t in tx:
        y, m, d = map(int, t["date"].split()[0].split("-"))
        if dt.date(y, m, d).weekday() >= 5:
            weekend += 1
    if weekend >= 4:
        insights.append("Выходные заметно влияют на расходы — стоит заложить отдельный weekend-лимит.")

    insights.append(f"Сумма последних {len(tx)} расходов: {total} ₽.")
    return insights[:5]
