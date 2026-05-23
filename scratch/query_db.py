import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "..", "database", "sandbox.db")
db_path = os.path.abspath(db_path)

print(f"Connecting to DB at: {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查询所有模型 metrics 的得分状态
cursor.execute("SELECT date, model_name, score, score_change, score_reason FROM model_metrics ORDER BY date DESC, score DESC")
rows = cursor.fetchall()
print("\n--- Model Metrics Scores ---")
for r in rows:
    print(f"Date: {r[0]} | Model: {r[1]} | Score: {r[2]} | Change: {r[3]} | Reason: {r[4]}")

conn.close()
