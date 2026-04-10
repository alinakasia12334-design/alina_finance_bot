diff --git a/config.py b/config.py
new file mode 100644
index 0000000000000000000000000000000000000000..973419844864d64be5be4a5a6eedfeeba3d27bae
--- /dev/null
+++ b/config.py
@@ -0,0 +1,26 @@
+import os
+
+
+def _load_dotenv(path=".env"):
+    if not os.path.exists(path):
+        return
+    with open(path, "r", encoding="utf-8") as f:
+        for raw in f:
+            line = raw.strip()
+            if not line or line.startswith("#") or "=" not in line:
+                continue
+            key, value = line.split("=", 1)
+            key = key.strip()
+            value = value.strip().strip('"').strip("'")
+            os.environ.setdefault(key, value)
+
+
+_load_dotenv()
+
+TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
+if not TOKEN:
+    raise RuntimeError("Не задан TELEGRAM_BOT_TOKEN")
+
+ADMIN_ID = int(os.getenv("ADMIN_ID", "463620997"))
+DB_PATH = os.getenv("BOT_DB_PATH", "bot_data.sqlite3")
+SUPPORT_CONTACT = os.getenv("SUPPORT_CONTACT", "@privetetoalina")
