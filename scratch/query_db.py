import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "..", "database", "sandbox.db")
db_path = os.path.abspath(db_path)

print(f"Connecting to DB at: {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查询 2026-05-22 的所有模型 metrics 路径
cursor.execute("SELECT date, model_name, photo_path FROM model_metrics WHERE date = '2026-05-22'")
rows = cursor.fetchall()
print("\n--- 2026-05-22 Metrics ---")
for r in rows:
    print(f"Date: {r[0]} | Model: {r[1]} | Path: {r[2]}")

conn.close()
