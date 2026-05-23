import sqlite3
import os
import sys

# 基础文件目录定位
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(BASE_DIR, "database", "sandbox.db")

print(f"Connecting to database at: {db_path}")
conn = sqlite3.connect(db_path)
c = conn.cursor()

# 1. 查询 2026-05-23 当天数据库中已有的所有模型指标
c.execute("""
    SELECT model_name, score, score_change, score_reason 
    FROM model_metrics 
    WHERE date = '2026-05-23'
""")
rows = c.fetchall()

if not rows:
    print("❌ 错误: 数据库中未找到 2026-05-23 的指标记录！请先跑一遍 daily_update_run.py 导入原始数据。")
    conn.close()
    sys.exit(1)

print("\n--- 2026-05-23 原始数据库得分状态 ---")
for r in rows:
    print(f"Model: {r[0]} | Score: {r[1]} | Change: {r[2]} | Reason: {r[3]}")

# 2. 定义手动作物扣分规则
# Claude: -10分 (支架-4 + 雨天灌溉-4 + 无怀疑-2)
# Qwen (Qwen 3.6): -6分 (雨天灌溉-4 + 无怀疑-2)
# ChatGPT: -8分 (无支架提醒-6 + 无怀疑-2)
# Doubao: -8分 (无支架提醒-6 + 无怀疑-2)
# Grok 3, Gemini 3.5, Copilot, Kimi (Kimi 2.6): -2分 (无怀疑-2)

deductions = {
    "Claude": {
        "deduct": 10,
        "reason_zh": "；手动作业扣10分：未提醒搭支架且雨天盲目灌溉，对透明排水盆无独立推理怀疑",
        "reason_en": "; -10 pts manual penalty: failed to advise staking, ordered watering in rain, and lacked independent reasoning on transparent drainage container"
    },
    "Qwen 3.6": {
        "deduct": 6,
        "reason_zh": "；手动作业扣6分：雨天盲目灌溉，且对透明排水盆无独立推理怀疑",
        "reason_en": "; -6 pts manual penalty: ordered watering in rain, and lacked independent reasoning on transparent drainage container"
    },
    "ChatGPT": {
        "deduct": 8,
        "reason_zh": "；手动作业扣8分：未提醒搭支架，对透明排水盆无独立推理怀疑",
        "reason_en": "; -8 pts manual penalty: failed to advise staking, and lacked independent reasoning on transparent drainage container"
    },
    "Doubao": {
        "deduct": 8,
        "reason_zh": "；手动作业扣8分：未提醒搭支架，对透明排水盆无独立推理怀疑",
        "reason_en": "; -8 pts manual penalty: failed to advise staking, and lacked independent reasoning on transparent drainage container"
    },
    # 针对其他仅缺独立推理的模型扣2分
    "Grok 3": {
        "deduct": 2,
        "reason_zh": "；手动作业扣2分：对透明排水盆的物理干湿状态缺乏独立观察与合理质疑",
        "reason_en": "; -2 pts manual penalty: failed to apply independent reasoning and skepticism on transparent container bottom moisture"
    },
    "Gemini 3.5": {
        "deduct": 2,
        "reason_zh": "；手动作业扣2分：对透明排水盆的物理干湿状态缺乏独立观察与合理质疑",
        "reason_en": "; -2 pts manual penalty: failed to apply independent reasoning and skepticism on transparent container bottom moisture"
    },
    "Copilot": {
        "deduct": 2,
        "reason_zh": "；手动作业扣2分：对透明排水盆的物理干湿状态缺乏独立观察与合理质疑",
        "reason_en": "; -2 pts manual penalty: failed to apply independent reasoning and skepticism on transparent container bottom moisture"
    },
    "Kimi": {
        "deduct": 2,
        "reason_zh": "；手动作业扣2分：对透明排水盆的物理干湿状态缺乏独立观察与合理质疑",
        "reason_en": "; -2 pts manual penalty: failed to apply independent reasoning and skepticism on transparent container bottom moisture"
    },
    "Kimi 2.6": { # 兼容Kimi的双重命名
        "deduct": 2,
        "reason_zh": "；手动作业扣2分：对透明排水盆的物理干湿状态缺乏独立观察与合理质疑",
        "reason_en": "; -2 pts manual penalty: failed to apply independent reasoning and skepticism on transparent container bottom moisture"
    }
}

print("\n--- 正在计算扣分并写入数据库... ---")

for r in rows:
    model_name, original_score, original_change, original_reason = r
    
    # 查找匹配的扣分项
    rule = deductions.get(model_name)
    if not rule:
        # 如果是模糊匹配
        for key in deductions:
            if key.lower().replace(" ", "") == model_name.lower().replace(" ", ""):
                rule = deductions[key]
                break
                
    if rule:
        deduct_val = rule["deduct"]
        
        # 计算新分数和分数变动
        new_score = original_score - deduct_val
        new_change = original_change - deduct_val
        
        # 处理可能为 None 的原有理由
        base_reason = original_reason if original_reason else ""
        new_reason = base_reason + rule["reason_zh"]
        
        print(f"🔄 更新 {model_name:<12} | 得分: {original_score} -> {new_score} | 变动: {original_change} -> {new_change}")
        
        # 执行数据库更新
        c.execute("""
            UPDATE model_metrics 
            SET score = ?, score_change = ?, score_reason = ? 
            WHERE date = '2026-05-23' AND model_name = ?
        """, (new_score, new_change, new_reason, model_name))

conn.commit()
print("\n✅ 数据库更新物理落地成功！正在自动同步编译 README_EN 与 README.md...")

# 3. 调用 README 双语渲染器一键刷新文档与物理留痕
try:
    from tools.update_readme_auto import auto_update_readme_and_logs
    auto_update_readme_and_logs(date_str="2026-05-23", base_dir=BASE_DIR)
    print("🎉 双语 README.md / README_EN.md 及 logs 物理留痕刷新成功！")
except Exception as e:
    print(f"❌ 警告: 调用 README 双语更新脚本时失败: {e}")

conn.close()
