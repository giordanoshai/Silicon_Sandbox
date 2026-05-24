import sqlite3
import os

db_path = r"d:\Dev_project\Python_Project\Silicon_Sandbox\database\sandbox.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("""
    SELECT date, model_name, crop_type, height 
    FROM model_metrics 
    ORDER BY date ASC, model_name ASC
""")
rows = c.fetchall()
conn.close()

data = {}
for r in rows:
    date, model, crop, height = r
    if model not in data:
        data[model] = []
    data[model].append((date, height))

for model, history in data.items():
    print(f"Model: {model}")
    for date, height in history:
        print(f"  {date}: {height} cm")
