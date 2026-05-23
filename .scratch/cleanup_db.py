import sqlite3
import os

db_path = os.path.abspath("d:/Dev_project/Python_Project/Silicon_Sandbox/database/sandbox.db")
print(f"Connecting to DB at: {db_path}")
conn = sqlite3.connect(db_path)
c = conn.cursor()

# 更新 daily_records 中的隐私字眼
c.execute("UPDATE daily_records SET weather = REPLACE(weather, '庐江', '安徽中部')")
c.execute("UPDATE daily_records SET summary = REPLACE(summary, '庐江', '安徽中部')")
c.execute("UPDATE daily_records SET audio_script = REPLACE(audio_script, '庐江', '安徽中部')")

# 更新 model_metrics 中的隐私字眼
c.execute("UPDATE model_metrics SET score_reason = REPLACE(score_reason, '庐江', '安徽中部')")
c.execute("UPDATE model_metrics SET state_desc = REPLACE(state_desc, '庐江', '安徽中部')")
c.execute("UPDATE model_metrics SET action_desc = REPLACE(action_desc, '庐江', '安徽中部')")
c.execute("UPDATE model_metrics SET reward_judg = REPLACE(reward_judg, '庐江', '安徽中部')")

conn.commit()
print("Database privacy cleanup successfully executed.")
conn.close()
