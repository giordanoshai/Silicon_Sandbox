import sqlite3
import os

DB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(DB_DIR, "database", "sandbox.db")

def migrate():
    print("==================================================")
    print("🪐 硅基沙盒数据库物理迁移：DeepSeek v4 -> Kimi 2.6")
    print(f"数据库路径: {DB_PATH}")
    print("==================================================")
    
    if not os.path.exists(DB_PATH):
        print("❌ 错误：未能在数据库目录下找到 sandbox.db 数据库文件！")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. 统计迁移前数量
    cursor.execute("SELECT COUNT(*) FROM model_metrics WHERE model_name = 'DeepSeek v4'")
    ds_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM model_metrics WHERE model_name = 'Kimi 2.6'")
    kimi_count = cursor.fetchone()[0]
    
    print(f"📊 迁移前统计：")
    print(f"   - 包含 'DeepSeek v4' 的行数: {ds_count}")
    print(f"   - 包含 'Kimi 2.6' 的行数: {kimi_count}")
    
    if ds_count == 0:
        print("💡 提示：数据库中不存在需要迁移的 'DeepSeek v4' 历史数据。")
        conn.close()
        return
        
    # 2. 执行物理更新 (更新主键名称)
    print("\n🚀 正在执行 model_name 物理迁移...")
    cursor.execute("""
    UPDATE model_metrics 
    SET model_name = 'Kimi 2.6' 
    WHERE model_name = 'DeepSeek v4'
    """)
    affected_rows = cursor.rowcount
    
    # 3. 执行内容文本词汇修正 (例如 action_desc / state_desc / score_reason)
    print("🚀 正在批量修正文本描述中的 'DeepSeek' 别称...")
    
    # 对 score_reason 字段
    cursor.execute("""
    UPDATE model_metrics 
    SET score_reason = REPLACE(score_reason, 'DeepSeek', 'Kimi')
    WHERE score_reason LIKE '%DeepSeek%'
    """)
    score_reason_affected = cursor.rowcount
    
    # 对 state_desc 字段
    cursor.execute("""
    UPDATE model_metrics 
    SET state_desc = REPLACE(state_desc, 'DeepSeek', 'Kimi')
    WHERE state_desc LIKE '%DeepSeek%'
    """)
    state_desc_affected = cursor.rowcount
    
    # 对 action_desc 字段
    cursor.execute("""
    UPDATE model_metrics 
    SET action_desc = REPLACE(action_desc, 'DeepSeek', 'Kimi')
    WHERE action_desc LIKE '%DeepSeek%'
    """)
    action_desc_affected = cursor.rowcount
    
    conn.commit()
    
    # 4. 统计迁移后数量
    cursor.execute("SELECT COUNT(*) FROM model_metrics WHERE model_name = 'DeepSeek v4'")
    ds_count_after = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM model_metrics WHERE model_name = 'Kimi 2.6'")
    kimi_count_after = cursor.fetchone()[0]
    
    print("\n==================================================")
    print("🎉 迁移成功！物理数据库升级完毕！")
    print(f"📊 迁移后统计：")
    print(f"   - 物理更新 'model_metrics' 的行数: {affected_rows}")
    print(f"   - 修正 score_reason 字段行数: {score_reason_affected}")
    print(f"   - 修正 state_desc 字段行数: {state_desc_affected}")
    print(f"   - 修正 action_desc 字段行数: {action_desc_affected}")
    print(f"   - 剩余 'DeepSeek v4' 行数: {ds_count_after}")
    print(f"   - 当前 'Kimi 2.6' 行数: {kimi_count_after}")
    print("==================================================")
    
    conn.close()

if __name__ == "__main__":
    migrate()
