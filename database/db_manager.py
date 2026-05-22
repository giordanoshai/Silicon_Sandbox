import sqlite3
import os
from typing import Dict, List, Any, Optional

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "sandbox.db")

def get_db_connection():
    """获取 SQLite 数据库连接，并启用 ROW 格式以方便转换为 Dict"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库表结构"""
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. 全局每日状态表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_records (
        date TEXT PRIMARY KEY,
        stage TEXT NOT NULL,
        weather TEXT NOT NULL,
        summary TEXT NOT NULL,
        audio_script TEXT NOT NULL,
        audio_path TEXT,
        video_path TEXT
    )
    """)
    
    # 2. 模型每日指标表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS model_metrics (
        date TEXT,
        model_name TEXT,
        crop_type TEXT NOT NULL,
        color TEXT NOT NULL,
        score INTEGER NOT NULL,
        score_change INTEGER NOT NULL,
        score_reason TEXT NOT NULL,
        state_desc TEXT NOT NULL,
        action_desc TEXT,
        reward_judg TEXT NOT NULL,
        height REAL NOT NULL,
        stem_diameter REAL NOT NULL,
        leaves_count INTEGER NOT NULL,
        photo_path TEXT,
        height_wow REAL,
        stem_wow REAL,
        side_buds INTEGER DEFAULT 0,
        leaves_wow REAL DEFAULT 0.0,
        side_buds_wow REAL DEFAULT 0.0,
        state_desc_en TEXT,
        action_desc_en TEXT,
        PRIMARY KEY (date, model_name)
    )
    """)
    
    # 自适应升级：检查并动态添加缺少的列
    cursor.execute("PRAGMA table_info(model_metrics)")
    columns = [row["name"] for row in cursor.fetchall()]
    if "side_buds" not in columns:
        cursor.execute("ALTER TABLE model_metrics ADD COLUMN side_buds INTEGER DEFAULT 0")
    if "leaves_wow" not in columns:
        cursor.execute("ALTER TABLE model_metrics ADD COLUMN leaves_wow REAL DEFAULT 0.0")
    if "side_buds_wow" not in columns:
        cursor.execute("ALTER TABLE model_metrics ADD COLUMN side_buds_wow REAL DEFAULT 0.0")
    if "state_desc_en" not in columns:
        cursor.execute("ALTER TABLE model_metrics ADD COLUMN state_desc_en TEXT")
    if "action_desc_en" not in columns:
        cursor.execute("ALTER TABLE model_metrics ADD COLUMN action_desc_en TEXT")
        
    conn.commit()
    conn.close()
    print("SQLite 数据库初始化及表结构升级完成。")

def insert_daily_record(date: str, stage: str, weather: str, summary: str, audio_script: str, audio_path: Optional[str] = None, video_path: Optional[str] = None):
    """插入或更新每日全局状态"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO daily_records (date, stage, weather, summary, audio_script, audio_path, video_path)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(date) DO UPDATE SET
        stage=excluded.stage,
        weather=excluded.weather,
        summary=excluded.summary,
        audio_script=excluded.audio_script,
        audio_path=COALESCE(excluded.audio_path, daily_records.audio_path),
        video_path=COALESCE(excluded.video_path, daily_records.video_path)
    """, (date, stage, weather, summary, audio_script, audio_path, video_path))
    conn.commit()
    conn.close()

def insert_model_metrics(metrics: Dict[str, Any]):
    """插入或更新模型的每日指标"""
    # 兜底英文字段防爆，以防传入数据未带此字段
    metrics.setdefault("state_desc_en", None)
    metrics.setdefault("action_desc_en", None)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO model_metrics (
        date, model_name, crop_type, color, score, score_change, score_reason,
        state_desc, action_desc, reward_judg, height, stem_diameter, leaves_count,
        photo_path, height_wow, stem_wow, side_buds, leaves_wow, side_buds_wow,
        state_desc_en, action_desc_en
    ) VALUES (
        :date, :model_name, :crop_type, :color, :score, :score_change, :score_reason,
        :state_desc, :action_desc, :reward_judg, :height, :stem_diameter, :leaves_count,
        :photo_path, :height_wow, :stem_wow, :side_buds, :leaves_wow, :side_buds_wow,
        :state_desc_en, :action_desc_en
    ) ON CONFLICT(date, model_name) DO UPDATE SET
        crop_type=excluded.crop_type,
        color=excluded.color,
        score=excluded.score,
        score_change=excluded.score_change,
        score_reason=excluded.score_reason,
        state_desc=excluded.state_desc,
        action_desc=excluded.action_desc,
        reward_judg=excluded.reward_judg,
        height=excluded.height,
        stem_diameter=excluded.stem_diameter,
        leaves_count=excluded.leaves_count,
        photo_path=COALESCE(excluded.photo_path, model_metrics.photo_path),
        height_wow=excluded.height_wow,
        stem_wow=excluded.stem_wow,
        side_buds=excluded.side_buds,
        leaves_wow=excluded.leaves_wow,
        side_buds_wow=excluded.side_buds_wow,
        state_desc_en=excluded.state_desc_en,
        action_desc_en=excluded.action_desc_en
    """, metrics)
    conn.commit()
    conn.close()

def get_daily_report(date: str) -> Optional[Dict[str, Any]]:
    """获取某天的完整报告（全局数据 + 8个模型卡片数据）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 查找全局信息
    cursor.execute("SELECT * FROM daily_records WHERE date = ?", (date,))
    daily_row = cursor.fetchone()
    if not daily_row:
        conn.close()
        return None
        
    daily_data = dict(daily_row)
    
    # 查找所有模型信息
    cursor.execute("SELECT * FROM model_metrics WHERE date = ?", (date,))
    model_rows = cursor.fetchall()
    
    daily_data["models"] = [dict(row) for row in model_rows]
    conn.close()
    return daily_data

def get_model_history(model_name: str) -> List[Dict[str, Any]]:
    """获取某个模型的全部历史记录，按日期升序排列"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM model_metrics WHERE model_name = ? ORDER BY date ASC", (model_name,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_available_dates() -> List[str]:
    """获取所有有记录的日期，按日期降序排列"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT date FROM daily_records ORDER BY date DESC")
    rows = cursor.fetchall()
    conn.close()
    return [row["date"] for row in rows]

if __name__ == "__main__":
    init_db()
