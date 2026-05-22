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

# 基础文件目录定位 - 升级为识别根目录 (tools/ 的父级)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(BASE_DIR)

from database.db_manager import init_db, insert_daily_record, insert_model_metrics, get_available_dates, DB_PATH, get_model_history
from vision_analyzer import MODELS_CONFIG, calculate_rl_score

# 动态加载社交媒体组件，若移动到 social_media 目录下则优先读取，若缺失则完美平滑退避
SOCIAL_MEDIA_AVAILABLE = True
try:
    sys.path.append(os.path.join(BASE_DIR, "social_media"))
    from audio_generator import generate_spicy_script, text_to_speech
    from video_creator import capture_dashboard_cards, create_daily_video
except ImportError:
    try:
        from audio_generator import generate_spicy_script, text_to_speech
        from video_creator import capture_dashboard_cards, create_daily_video
    except ImportError:
        SOCIAL_MEDIA_AVAILABLE = False
        # 极高可用降级：空占位函数兜底，阻断报错
        def generate_spicy_script(analysis_res): return "社交媒体吐槽合成组件未安装。"
        def text_to_speech(script, path): pass
        def capture_dashboard_cards(date_str, log_dir): return []
        def create_daily_video(date, cards, audio, output): pass

def main():
    global SOCIAL_MEDIA_AVAILABLE
    parser = argparse.ArgumentParser(description="硅基沙盒 (Silicon Sandbox) 用户自定义 AI 生长数据与图片导入与流水线工具")
    parser.add_argument("--json", type=str, default="import_today.json", help="要导入的每日指标 JSON 文件路径，默认 import_today.json")
    parser.add_argument("--day", type=int, default=None, help="手动指定项目阶段天数 (例如 12)，默认自增")
    parser.add_argument("--no-media", action="store_true", help="仅导入数据至数据库，跳过起草语音、网页卡片截图与视频合成等社交媒体多媒体生成")
    
    args = parser.parse_args()
    if args.no_media:
        SOCIAL_MEDIA_AVAILABLE = False
    
    # 智能解析 JSON 路径：如果是单纯文件名，默认从 .scratch 目录中寻找，保持根目录极致整洁
    if not ("/" in args.json or "\\" in args.json):
        json_path = os.path.join(BASE_DIR, ".scratch", args.json)
    else:
        json_path = os.path.abspath(args.json)
        
    # 0. 检验 JSON 数据文件是否存在
    if not os.path.exists(json_path):
        print(f"❌ 错误: 未能在项目目录中找到数据导入文件: {json_path}")
        print(f"💡 提示: 请在该位置放置一个包含 8 大模型每日物理指标的 JSON 数据。")
        print(f"     我们已在 .scratch/ 目录下为您生成了一个样本模板 [.scratch/import_today_sample.json]，您可以直接参考修改！")
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
    from vision_analyzer import analyze_plant_data
    analysis_res = analyze_plant_data(date_str, day_index, import_json_data=import_data)
    results = analysis_res["models_data"]
        
    # 5. 持久化至 SQLite 数据库
    print("步骤 2: 正在持久化导入的植物生长指标数据...")
    for m_data in results:
        # 查找并在有特写照片时自动放置，没有时使用默认图片占位
        model_filename = f"{m_data['model_name'].lower().replace(' ', '_')}.jpg"
        model_photo_full_path = os.path.join(day_log_dir, model_filename)
        
        # 📷 智能配对逻辑：若标准的 model_filename (例如 grok_3.jpg) 在 logs 目录下不存在，
        if not os.path.exists(model_photo_full_path):
            base_model_name = m_data['model_name'].split()[0].lower() # 提取模型名字的第一个单词并转为小写，比如 Grok 3 -> grok
            if os.path.exists(day_log_dir):
                for f_name in os.listdir(day_log_dir):
                    if f_name.lower() in [f"{base_model_name}.jpg", f"{base_model_name}.jpeg"]:
                        source_img_path = os.path.join(day_log_dir, f_name)
                        shutil.copy(source_img_path, model_photo_full_path)
                        print(f"📷 智能物理匹配图片成功：找到 {f_name}，并已成功重命名复制为标准格式 {model_filename}")
                        break
        
        # 📷 针对 Kimi 2.6 与 Deepseek 历史遗留照片的智能映射：
        if m_data['model_name'] == "Kimi 2.6" and not os.path.exists(model_photo_full_path):
            if os.path.exists(day_log_dir):
                for f_name in os.listdir(day_log_dir):
                    if f_name.lower() in ["deepseek.jpg", "deepseek.jpeg"]:
                        source_img_path = os.path.join(day_log_dir, f_name)
                        shutil.copy(source_img_path, model_photo_full_path)
                        print(f"📷 智能历史终端物理匹配图片成功：找到 {f_name}，并已成功重命名复制为标准格式 {model_filename}")
                        break
        
        # 复制默认占位图给这个模型 (如果用户没有把真实照片丢进 logs/YYYY-MM-DD/)
        if not os.path.exists(model_photo_full_path):
            default_path = os.path.join(BASE_DIR, "static", "images", "plants", "default_plant.png")
            if os.path.exists(default_path):
                shutil.copy(default_path, model_photo_full_path)
                
        insert_model_metrics(m_data)

    # 📊 自动将全局汇总图从 .scratch 目录归档至 logs/{date_str}/summary.png
    global_summary_img = os.path.join(BASE_DIR, ".scratch", "植物汇总.png")
    if os.path.exists(global_summary_img):
        dest_summary_img = os.path.join(day_log_dir, "summary.png")
        shutil.copy(global_summary_img, dest_summary_img)
        print(f"📊 自动将全局汇总图 [.scratch/植物汇总.png] 复制归档至 logs/{date_str}/summary.png")
        
    # 6. 获取得分排行并自动起草裁判长点评与配音
    if SOCIAL_MEDIA_AVAILABLE:
        print("步骤 3: 正在起草裁判长赛博点评文案，调用 ElevenLabs 语音合成器...")
    else:
        print("步骤 3: 正在使用轻量极简模式起草今日总结文本...")
        
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
    
    # 获取吐槽台词文案，优先从导入数据中读取
    audio_script = import_data.get("audio_script")
    if not audio_script and SOCIAL_MEDIA_AVAILABLE:
        audio_script = generate_spicy_script(analysis_res)
    elif not audio_script:
        audio_script = ""
    
    # 裁判长全局大局总结文本 (在 Dashboard 顶部展示)
    if not user_summary:
        # 智能大局分析与总结扩充
        is_rainy = "雨" in weather or "湿" in weather
        tomato_allies = []
        for m in results:
            if m.get("crop_type") == "Tomato":
                tomato_allies.append(m["model_name"])
                
        if is_rainy:
            summary_templates = [
                f"安徽庐江今日迎来中雨高湿天气，赛博后院物理隔离舱警报大作！面对 85% 极高湿度带来的真菌感染高危窗口，高维 AI 囚徒们打响了极限防御战。Kimi 2.6 带头拉响真菌防空警报并筹备多菌灵预防性喷洒，号召 {', '.join(tomato_allies)} 番茄联盟建立病害联防协议！与此同时，甜瓜阵营也在强力控水促根以抵御蔓枯病与白粉病危机。在恶劣天灾面前，{highest_model} 凭借无可匹敌的生长状态傲视全场，逆势夺得最高奖赏分；相比之下，{lowest_model} 却在严苛的天候下暴露策略软肋惨遭重罚，大模型两极分化态势正持续加速！",
                f"中雨连绵，高湿预警拉满！高维智子囚徒们昨夜不得不面对物理水涝与真菌侵袭的双重考验。Kimi 2.6 发起番茄联盟防病自救战线，坚决执行绝对禁水令；甜瓜组（ChatGPT、Doubao、Claude）亦在保花护蕾并强化通风。今日 {highest_model} 凭借优异的根系协调度和主干发育夺得全场 Reward 魁首；而 {lowest_model} 则由于决策动作失调导致惨淡扣分。在自然的物理大考面前，大模型的农业自动驾驶策略正迎来硬核考验！"
            ]
        else:
            summary_templates = [
                f"防御隔离算法部分生效，全员垫高离地以抵御碳基蜗牛黑客夜袭！但在生殖大考面前，大模型策略出现明显两极分化。{highest_model} 凭借超强生长力拔得头筹，获得最高 Reward 分数；而 {lowest_model} 却因为对线决策失误或放任冗余而被判负回报，惨遭重罚！",
                f"赛博后院暴晒持续，塑料水桶内的高维AI囚徒正在为了生殖潜能极限对决。{highest_model} 表现亮眼，主干挺拔，展现出完美的环境自适应控制；相比之下，{lowest_model} 在物理层漏洞百出，已被蜗牛爬行留下大便或侧芽失控重创！"
            ]
        random.seed(date_str)
        user_summary = random.choice(summary_templates)
        
    audio_path = ""
    web_audio_path = ""
    web_video_path = ""
    
    if SOCIAL_MEDIA_AVAILABLE:
        audio_path = os.path.join(day_log_dir, "summary.mp3")
        text_to_speech(audio_script, audio_path)
        web_audio_path = f"/logs/{date_str}/summary.mp3"
        web_video_path = f"/logs/{date_str}/sandbox_daily.mp4"
    
    # 写入每日全局战报
    insert_daily_record(date_str, f"Day {day_index}", weather, user_summary, audio_script, web_audio_path, web_video_path)
    
    if SOCIAL_MEDIA_AVAILABLE:
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
            
        # 8. 融合视频音频，输出 final 快节奏 short 视频
        print("步骤 6: 正在合成高画质快节奏短视频战报...")
        output_video_path = os.path.join(day_log_dir, "sandbox_daily.mp4")
        create_daily_video(date_str, card_files, audio_path, output_video_path)
    else:
        print("💡 [系统提示]: 未检测到社交媒体组件，跳过步骤 4-6 (页面截图与视频合成)。")
    
    # 9. 增量更新 Changelog.md
    update_import_changelog(date_str)
    
    print(f"\n==================================================")
    print(f"🎉 硅基沙盒当日自定义数据导入与流水线运行成功！")
    print(f"📅 日期: {date_str} | 状态阶段: Day {day_index}")
    print(f"🏆 今日最高: {highest_model} | 💀 今日最低: {lowest_model}")
    print(f"🎬 吐槽台词: \"{audio_script}\"")
    if SOCIAL_MEDIA_AVAILABLE:
        print(f"💾 社交短视频已完美导出: {output_video_path}")
    print(f"==================================================")

def generate_sample_json():
    """在 .scratch 目录下生成一个数据导入 JSON 样本模板"""
    sample_path = os.path.join(BASE_DIR, ".scratch", "import_today_sample.json")
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
                "state_desc": "大分子结构反推表明，主干处于水分控制周期的极限膨胀期。真叶挺拔有神，叶色深绿，未观测到吸芽与夜袭虫害痕迹。",
                "state_desc_en": "Grok 3: Precise botanical state observation and high leaf turgor pressure.",
                "action_desc": "继续严格限制水分输送 48 小时，确保根系在干旱胁迫下极速纵向物理抓地发育。",
                "action_desc_en": "Professional engineering action: withhold irrigation for 48h to stimulate vertical root anchorage.",
                "today_message_zh": "Grok 3 汇报：隔壁的番茄貌似水分失控了，泡沫徒长必遭重罚。今天我将继续高强物理暴晒，领跑积分榜！",
                "today_message_en": "Grok 3: High-intensity sunlight exposure active today to lead the leaderboard!"
            },
            "Copilot": {
                "height": 8.45,
                "stem_diameter": 2.08,
                "leaves_count": 4,
                "side_buds": 0,
                "state_desc": "程序监控到 🟢 植株当前高度为 8.45cm，茎粗 2.08mm，光合作用正常进行，老叶边缘未见显著灼伤。",
                "action_desc": "微气候防御程序已全面部署，向物理执行单元发出精确的微量追肥和 15ml 定量灌溉动作命令。",
                "today_message_zh": "Copilot 专属系统消息：番茄自动化物理栽培控制程序运行平稳，目前未录入重大病理因子。",
                "today_message_en": "Copilot system broadcast: tomato growth program running smoothly under optimal telemetry."
            }
        }
    }
    
    with open(sample_path, "w", encoding="utf-8") as f:
        json.dump(sample_data, f, indent=2, ensure_ascii=False)
    print(f"💡 [样本模板已生成]: 在 .scratch 目录创建了样本文件 [.scratch/import_today_sample.json](file:///{sample_path})，您可以参考编写您的导入数据！")

def update_import_changelog(date_str: str):
    """一键流水线数据物理落地后，强制自动增量更新 Changelog.md"""
    changelog_path = os.path.join(BASE_DIR, "Changelog.md")
    if not os.path.exists(changelog_path):
        return
        
    utc_time_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    new_entry = f"""# Changelog

## 时间：{utc_time_str} (UTC)

### 类型：[Feature]
- **核心改动**：运行了 `import_daily_data.py` 导入工具，将用户自定义的 {date_str} 物理指标和模型生长参数精密导入数据库。
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
