import sqlite3, os

DB = "auto.db"
if not os.path.exists(DB):
    print(f"Файл {DB} не найден. Запусти сначала app.py, чтобы база создалась.")
    raise SystemExit

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

print("=== Пользователи ===")
for u in conn.execute("SELECT id, username, password_hash, created_at FROM users"):
    print(f"#{u['id']} {u['username']} {u['password_hash']}  (создан {u['created_at']})")

print("\n=== Машины ===")
for c in conn.execute("""SELECT c.*, u.username FROM cars c
                         JOIN users u ON u.id = c.user_id
                         ORDER BY c.id"""):
    invested = c["buy_price"] + c["expenses"]
    profit = (c["sell_price"] - invested) if c["sell_price"] else 0
    print(f"#{c['id']} [{c['username']}] {c['name']}: "
          f"вложено {invested:.0f}, продажа {c['sell_price']:.0f}, "
          f"прибыль {profit:+.0f}, {c['status']}")

conn.close()