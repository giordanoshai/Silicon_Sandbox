import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(BASE_DIR, "database", "sandbox.db")

conn = sqlite3.connect(db_path)
c = conn.cursor()

print("--- daily_records ---")
c.execute("SELECT date, stage, weather, summary FROM daily_records ORDER BY date DESC LIMIT 5")
for row in c.fetchall():
    print(row)

print("\n--- model_metrics counts ---")
c.execute("SELECT date, COUNT(*), SUM(score) FROM model_metrics GROUP BY date ORDER BY date DESC LIMIT 5")
for row in c.fetchall():
    print(row)

print("\n--- model_metrics for 2026-05-25 ---")
c.execute("SELECT model_name, height, stem_diameter, leaves_count, score, score_change FROM model_metrics WHERE date = '2026-05-25'")
for row in c.fetchall():
    print(row)

print("\n--- model_metrics for 2026-05-24 ---")
c.execute("SELECT model_name, height, stem_diameter, leaves_count, score, score_change FROM model_metrics WHERE date = '2026-05-24'")
for row in c.fetchall():
    print(row)

conn.close()
