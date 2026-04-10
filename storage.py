import json
import sqlite3
from typing import Dict

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

DEFAULT_DATA = {
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
    "last_auto_report_sent": None,
    "mode": "bold",
    "wishlist": [],
    "subscriptions": [],
    "moods": [],
    "recent_phrases": []
}

class Storage:
    def __init__(self, db_path: str, admin_id: int):
        self.db_path = db_path
        self.admin_id = admin_id
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    data TEXT NOT NULL
                )
            """)

    def _normalize(self, data: Dict):
        result = DEFAULT_DATA.copy()
        result.update(data or {})
        if not result.get("current_month_stats"):
            result["current_month_stats"] = {cat: 0 for cat in CATEGORIES.keys()}
        for k in ["transactions", "goals", "wishlist", "subscriptions", "moods", "recent_phrases"]:
            result[k] = result.get(k, []) or []
        result["monthly_stats"] = result.get("monthly_stats", {}) or {}
        result["rub"] = int(result.get("rub", 0))
        return result

    def load_user_data(self, user_id: int) -> Dict:
        with self._connect() as conn:
            row = conn.execute("SELECT data FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if row:
                return self._normalize(json.loads(row[0]))
        return self._normalize({})

    def save_user_data(self, user_id: int, data: Dict):
        normalized = self._normalize(data)
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO users(user_id, data) VALUES(?, ?) ON CONFLICT(user_id) DO UPDATE SET data=excluded.data",
                (user_id, json.dumps(normalized, ensure_ascii=False))
            )

    def delete_user(self, user_id: int):
        with self._connect() as conn:
            conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))

    def user_exists(self, user_id: int) -> bool:
        with self._connect() as conn:
            row = conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return row is not None

    def get_allowed_users(self):
        with self._connect() as conn:
            ids = [r[0] for r in conn.execute("SELECT user_id FROM users").fetchall()]
        if self.admin_id not in ids:
            ids.append(self.admin_id)
        return sorted(set(ids))

    def ensure_user(self, user_id: int):
        if not self.user_exists(user_id):
            self.save_user_data(user_id, self._normalize({}))
