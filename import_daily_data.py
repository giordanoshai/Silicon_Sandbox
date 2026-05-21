import os
import json
import argparse
import sys
import io
import shutil
import sqlite3
import random
import math
import subprocess
import time
from datetime import datetime
from dotenv import load_dotenv

# 强制 UTF-8 编码，防止 Windows 控制台 Emoji 编码报错
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

load_dotenv()

# 基础文件目录定位
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from database.db_manager import init_db, insert_daily_record, insert_model_metrics, get_available_dates, DB_PATH, get_model_history
from vision_analyzer import MODELS_CONFIG, calculate_rl_score
from audio_generator import generate_spicy_script, text_to_speech
from video_creator import capture_dashboard_cards, create_daily_video

def main():
    parser = argparse.ArgumentParser(description="硅基沙盒 (Silicon Sandbox) 用户自定义 AI 生长数据与图片导入与流水线工具")
    parser.add_argument("--json", type=str, default="import_today.json", help="要导入的每日指标 JSON 文件路径，默认 import_today.json")
    parser.add_argument("--day", type=int, default=None, help="手动指定项目阶段天数 (例如 12)，默认自增")
    
    args = parser.parse_args()
    json_path = os.path.join(BASE_DIR, args.json)
    
    # 0. 检验 JSON 数据文件是否存在
    if not os.path.exists(json_path):
        print(f"❌ 错误: 未能在项目根目录找到数据导入文件: {json_path}")
        print(f"💡 提示: 请在该位置放置一个包含 8 大模型每日物理指标的 JSON 数据。")
        print(f"     我们已在同目录下为您生成了一个样本模板 [import_today_sample.json]，您可以直接参考修改！")
        generate_sample_json()
        sys.exit(1)
        
    # 1. 解析 JSON 数据
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            import_data = json.load(f)
    except Exception as e:
        print(f"❌ 错误: 解析 JSON 文件失败: {e}")
        sys.exit(1)
        
    date_str = import_data.get("date")
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
        print(f"⚠️ 警告: JSON 中未指定 'date'，已自动指定为今天: {date_str}")
        
    weather = import_data.get("weather", "暴晒强光（31℃）")
    user_summary = import_data.get("summary")
    models_input = import_data.get("models", {})
    
    # 2. 初始化数据库
    init_db()
    
    # 3. 确定运行阶段天数 (Day)
    day_index = args.day
    if not day_index:
        dates = get_available_dates()
        if not dates:
            day_index = 1
        else:
            if date_str in dates:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("SELECT stage FROM daily_records WHERE date = ?", (date_str,))
                row = c.fetchone()
                conn.close()
                if row:
                    try:
                        day_index = int(row[0].replace("Day ", ""))
                    except:
                        day_index = len(dates)
                else:
                    day_index = len(dates)
            else:
                day_index = len(dates) + 1
                
    print(f"==================================================")
    print(f"🪐 硅基沙盒数据导入流水线启动 | 日期: {date_str} | 阶段: Day {day_index}")
    print(f"==================================================")
    
    # 创建每日专属日志与资源归档目录
    day_log_dir = os.path.join(BASE_DIR, "logs", date_str)
    if not os.path.exists(day_log_dir):
        os.makedirs(day_log_dir)
        
    # 4. 精准计算 8 个模型的 RL 分数、客观指标以及历史同比 (WoW)
    print("步骤 1: 正在解析导入的模型状态数据，精细计算强化学习 Reward 评分...")
    
    results = []
    for model_name, config in MODELS_CONFIG.items():
        # 获取用户导入的该模型数据，如果没有提供，则自动由系统拟真模拟
        m_input = models_input.get(model_name, {})
        
        crop_type = config["crop_type"]
        
        # 默认提取或使用默认合理值
        height = float(m_input.get("height", 8.0))
        stem = float(m_input.get("stem_diameter", 2.0))
        leaves = int(m_input.get("leaves_count", 4))
        side_buds = int(m_input.get("side_buds", 0))
        
        # RL 状态细节判定
        state_details = {
            "snail_attack": bool(m_input.get("snail_attack", False)),
            "unpruned_sucker": bool(m_input.get("unpruned_sucker", False)) if crop_type == "Tomato" else False,
            "worm_holes": int(m_input.get("worm_holes", 0)),
            "leaf_yellowing": bool(m_input.get("leaf_yellowing", False)),
            "leggy_growth": bool(m_input.get("leggy_growth", False)),
            "physical_damage": bool(m_input.get("physical_damage", False)),
            "stem_thickened": bool(m_input.get("stem_thickened", False)),
            "first_flower_bud": bool(m_input.get("first_flower_bud", False)),
            "fruiting": bool(m_input.get("fruiting", False)),
            "healthy_new_leaves": bool(m_input.get("healthy_new_leaves", True))
        }
        
        # 计算 RL 得分
        today_score, score_change, score_reason, reward_judg = calculate_rl_score(crop_type, state_details, 100)
        
        # 自定义客观描述 (STATE) 与维护指令 (ACTION)
        state_desc = m_input.get("state_desc")
        if not state_desc:
            # 自动生成客观叙述
            state_parts = []
            state_parts.append(f"物理沙盒现场测算：植物当前高度为 {height:.2f} cm，主干茎粗 {stem:.2f} mm，共展开真叶 {leaves} 片，检测到侧芽 {side_buds} 个。")
            if state_details["snail_attack"]:
                state_parts.append("最新特写图像发现桶壁及叶缘分布有条状反光的蜗牛爬行银色黏液，根系离地隔离盘有落叶碎屑。")
            if state_details["unpruned_sucker"]:
                state_parts.append("番茄关节吸芽部位侧枝开始掠夺顶端优势养分，长度超过2cm。")
            if state_details["worm_holes"] > 0:
                state_parts.append(f"中下部叶片边缘新增 {state_details['worm_holes']} 个虫咬孔洞。")
            if state_details["leaf_yellowing"]:
                state_parts.append("部分成熟老叶边缘轻度发黄干枯，伴有失绿条斑，疑为营养液缓释烧根所致。")
            elif state_details["healthy_new_leaves"]:
                state_parts.append("顶部叶片排布合理，平展无重叠，光合作用层级分明。")
            state_desc = " ".join(state_parts)
            
        action_desc = m_input.get("action_desc")
        if not action_desc:
            # 自动生成 ACTION 指令
            action_parts = []
            if state_details["unpruned_sucker"]:
                action_parts.append("1. 请速掐灭关节处大于 2cm 的侧芽以维持顶端优势。")
            if state_details["snail_attack"] or state_details["worm_holes"] > 0:
                action_parts.append("2. 重新稳固桶周悬空防虫网，对盆周洒硅藻土进行隔离防护。")
            if state_details["leaf_yellowing"]:
                action_parts.append("3. 暂停施加缓释肥，增加基质清洗强度与底部充氧。")
            if not action_parts:
                action_parts.append("当前生长态势处于稳健控制周期中。指令：维持 NULL，不灌溉不干预，继续高强度暴晒。")
            action_desc = "\n".join(action_parts)
            
        # 历史 WoW 同比数据计算 (7天前)
        history = get_model_history(model_name)
        height_7_days_ago = None
        stem_7_days_ago = None
        leaves_7_days_ago = None
        side_buds_7_days_ago = None
        
        if len(history) >= 7:
            height_7_days_ago = history[-7]["height"]
            stem_7_days_ago = history[-7]["stem_diameter"]
            leaves_7_days_ago = history[-7].get("leaves_count", 4)
            side_buds_7_days_ago = history[-7].get("side_buds", 0)
        else:
            # 使用数学公式反推 7 天前的状态
            prev_day = max(1, day_index - 7)
            t0 = 15
            growth_rate = 0.15 if crop_type == "Tomato" else 0.12
            max_h = 80.0 if crop_type == "Tomato" else 120.0
            max_s = 12.0 if crop_type == "Tomato" else 9.0
            height_7_days_ago = 5.0 + (max_h - 5.0) / (1.0 + math.exp(-growth_rate * (prev_day - t0)))
            stem_7_days_ago = 1.5 + (max_s - 1.5) / (1.0 + math.exp(-growth_rate * (prev_day - t0)))
            leaves_7_days_ago = int(4 + prev_day * 0.8)
            side_buds_7_days_ago = 0
            
        height_wow = (height - height_7_days_ago) / height_7_days_ago if height_7_days_ago else 0.0
        stem_wow = (stem - stem_7_days_ago) / stem_7_days_ago if stem_7_days_ago else 0.0
        leaves_wow = (leaves - leaves_7_days_ago) / leaves_7_days_ago if leaves_7_days_ago else 0.0
        side_buds_wow = (side_buds - side_buds_7_days_ago) / side_buds_7_days_ago if side_buds_7_days_ago else 0.0
        
        m_data = {
            "date": date_str,
            "model_name": model_name,
            "crop_type": crop_type,
            "color": config["color"],
            "score": today_score,
            "score_change": score_change,
            "score_reason": score_reason,
            "state_desc": state_desc,
            "action_desc": action_desc,
            "reward_judg": reward_judg,
            "height": round(height, 2),
            "stem_diameter": round(stem, 2),
            "leaves_count": leaves,
            "side_buds": side_buds,
            "photo_path": f"/logs/{date_str}/{model_name.lower().replace(' ', '_')}.jpg",
            "height_wow": round(height_wow, 4),
            "stem_wow": round(stem_wow, 4),
            "leaves_wow": round(leaves_wow, 4),
            "side_buds_wow": round(side_buds_wow, 4)
        }
        
        results.append(m_data)
        
    # 5. 持久化至 SQLite 数据库
    print("步骤 2: 正在持久化导入的植物生长指标数据...")
    for m_data in results:
        # 查找并在有特写照片时自动放置，没有时使用默认图片占位
        model_filename = f"{m_data['model_name'].lower().replace(' ', '_')}.jpg"
        model_photo_full_path = os.path.join(day_log_dir, model_filename)
        
        # 复制默认占位图给这个模型 (如果用户没有把真实照片丢进 logs/YYYY-MM-DD/)
        if not os.path.exists(model_photo_full_path):
            # 尝试在项目根目录下寻找对应的模型图片，如果有就复制过来，没有就用默认的
            default_path = os.path.join(BASE_DIR, "static", "images", "plants", "default_plant.png")
            if os.path.exists(default_path):
                shutil.copy(default_path, model_photo_full_path)
                
        insert_model_metrics(m_data)
        
    # 6. 获取得分排行并自动起草裁判长点评与配音
    print("步骤 3: 正在起草裁判长赛博点评文案，调用 ElevenLabs 语音合成器...")
    scores = [r["score"] for r in results]
    highest_model = results[scores.index(max(scores))]["model_name"]
    lowest_model = results[scores.index(min(scores))]["model_name"]
    
    analysis_res = {
        "date": date_str,
        "day_index": day_index,
        "highest_model": highest_model,
        "lowest_model": lowest_model,
        "models_data": results
    }
    
    # 获取吐槽台词文案
    audio_script = generate_spicy_script(analysis_res)
    
    # 裁判长全局大局总结文本 (在 Dashboard 顶部展示)
    if not user_summary:
        summary_templates = [
            f"防御隔离算法部分生效，全员垫高离地以抵御碳基蜗牛黑客夜袭！但在生殖大考面前，大模型策略出现明显两极分化。{highest_model} 凭借超强生长力拔得头筹，获得最高 Reward 分数；而 {lowest_model} 却因为对线决策失误或放任冗余而被判负回报，惨遭重罚！",
            f"赛博后院暴晒持续，塑料水桶内的高维AI囚徒正在为了生殖潜能极限对决。{highest_model} 表现亮眼，主干挺拔，展现出完美的环境自适应控制；相比之下，{lowest_model} 在物理层漏洞百出，已被蜗牛爬行留下大便或侧芽失控重创！"
        ]
        random.seed(date_str)
        user_summary = random.choice(summary_templates)
        
    audio_path = os.path.join(day_log_dir, "summary.mp3")
    text_to_speech(audio_script, audio_path)
    
    # 写入每日全局战报
    web_audio_path = f"/logs/{date_str}/summary.mp3"
    web_video_path = f"/logs/{date_str}/sandbox_daily.mp4"
    insert_daily_record(date_str, f"Day {day_index}", weather, user_summary, audio_script, web_audio_path, web_video_path)
    
    # 7. 智能拉起后台 FastAPI Web 服务供 Playwright 进行精准卡片节点截图
    print("步骤 4: 临时拉起沙盒控制台后台服务...")
    port = os.getenv("PORT", "8000")
    host = os.getenv("HOST", "127.0.0.1")
    
    uvicorn_log_path = os.path.join(day_log_dir, "uvicorn_startup.log")
    with open(uvicorn_log_path, "w") as log_f:
        web_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app:app", "--host", host, "--port", port],
            stdout=log_f,
            stderr=log_f,
            cwd=BASE_DIR
        )
        
    time.sleep(2.5) # 给 uvicorn 留够自举时间
    
    card_files = []
    try:
        # 进行截图
        card_files = capture_dashboard_cards(date_str, day_log_dir)
    finally:
        # 优雅终止后台 Web 服务
        print("步骤 5: 释放 Playwright 并关闭沙盒控制台渲染进程...")
        web_process.terminate()
        web_process.wait()
        
    # 8. 融合视频音频，输出 final 快节奏短视频
    print("步骤 6: 正在合成高画质快节奏短视频战报...")
    output_video_path = os.path.join(day_log_dir, "sandbox_daily.mp4")
    create_daily_video(date_str, card_files, audio_path, output_video_path)
    
    # 9. 增量更新 Changelog.md
    update_import_changelog(date_str)
    
    print(f"\n==================================================")
    print(f"🎉 硅基沙盒当日自定义数据导入与流水线运行成功！")
    print(f"📅 日期: {date_str} | 状态阶段: Day {day_index}")
    print(f"🏆 今日最高: {highest_model} | 💀 今日最低: {lowest_model}")
    print(f"🎬 吐槽台词: \"{audio_script}\"")
    print(f"💾 社交短视频已完美导出: {output_video_path}")
    print(f"==================================================")

def generate_sample_json():
    """在项目根目录下生成一个数据导入 JSON 样本模板"""
    sample_path = os.path.join(BASE_DIR, "import_today_sample.json")
    if os.path.exists(sample_path):
        return
        
    sample_data = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "weather": "多云（25℃）",
        "summary": "防御隔离算法部分生效，全员垫高离地以抵御碳基蜗牛黑客夜袭！但在生殖大考面前，大模型策略出现明显两极分化...",
        "models": {
            "Grok 3": {
                "height": 9.25,
                "stem_diameter": 2.55,
                "leaves_count": 5,
                "side_buds": 1,
                "snail_attack": False,
                "unpruned_sucker": False,
                "worm_holes": 0,
                "leaf_yellowing": False,
                "leggy_growth": false,
                "physical_damage": false,
                "stem_thickened": True,
                "first_flower_bud": false,
                "fruiting": false,
                "healthy_new_leaves": true
            },
            "Claude": {
                "height": 8.12,
                "stem_diameter": 2.20,
                "leaves_count": 4,
                "side_buds": 0,
                "snail_attack": True,
                "unpruned_sucker": false,
                "worm_holes": 1,
                "leaf_yellowing": False,
                "leggy_growth": false,
                "physical_damage": false,
                "stem_thickened": false,
                "first_flower_bud": false,
                "fruiting": false,
                "healthy_new_leaves": true
            }
        }
    }
    
    with open(sample_path, "w", encoding="utf-8") as f:
        json.dump(sample_data, f, indent=2, ensure_ascii=False)
    print(f"💡 [样本模板已生成]: 在根目录创建了样本文件 [import_today_sample.json](file:///{sample_path})，您可以参考编写您的导入数据！")

def update_import_changelog(date_str: str):
    """一键流水线数据物理落地后，强制自动增量更新 Changelog.md"""
    changelog_path = os.path.join(BASE_DIR, "Changelog.md")
    if not os.path.exists(changelog_path):
        return
        
    utc_time_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    new_entry = f"""# Changelog

## 时间：{utc_time_str} (UTC)

### 类型：[Feature]
- **核心改动**：运行了 `import_daily_data.py` 导入工具，将用户自定义的 {date_str} 物理指标和模型生长参数精准导入数据库。
- **系统影响**：完成新数据物理落地入库，拉起自动化多卡片渲染截图和 Moviepy 快节奏短视频无缝融合，成功导出当日战报多媒体，极大扩展了系统在真实物理场景下的数据录入效率。

"""
    try:
        with open(changelog_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 移除原有的 # Changelog 头部并插入新记录
        if content.startswith("# Changelog"):
            content = content.replace("# Changelog", "", 1).strip()
            
        with open(changelog_path, "w", encoding="utf-8") as f:
            f.write(new_entry + content)
        print("📝 @Changelog.md 已根据更新协议自动增量更新。")
    except Exception as e:
        print(f"⚠️ 更新 Changelog 时遇到异常: {e}")

if __name__ == "__main__":
    main()
