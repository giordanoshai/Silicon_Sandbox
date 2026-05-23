import os
import sqlite3
from datetime import datetime

# 终端指示灯颜色中英文对照映射
COLOR_MAP = {
    "zh": {
        "Grok 3": "🔴 **红色**",
        "Claude": "🩷 **粉色**",
        "kimi2.6": "🟠 **橙色**",
        "Kimi 2.6": "🟠 **橙色**",
        "DeepSeek v4": "🟠 **橙色**",
        "Deepseek v4": "🟠 **橙色**",
        "Qwen 3.6": "🔵 **蓝色**",
        "ChatGPT": "⚫ **黑色**",
        "Copilot": "🟢 **绿色**",
        "Doubao": "⚪ **白色**",
        "Gemini 3.5": "🟣 **紫色**",
    },
    "en": {
        "Grok 3": "🔴 **Red**",
        "Claude": "🩷 **Pink**",
        "kimi2.6": "🟠 **Orange**",
        "Kimi 2.6": "🟠 **Orange**",
        "DeepSeek v4": "🟠 **Orange**",
        "Deepseek v4": "🟠 **Orange**",
        "Qwen 3.6": "🔵 **Blue**",
        "ChatGPT": "⚫ **Black**",
        "Copilot": "🟢 **Green**",
        "Doubao": "⚪ **White**",
        "Gemini 3.5": "🟣 **Purple**",
    }
}

# 数据库中常见的中文加扣分原因为英文版 README 制作的精美翻译字典
REASON_TRANSLATIONS = {
    "正常生长发育良好，光合工厂正常运转": "Normal vegetative growth with highly efficient photosynthesis",
    "正常生长发育良好，光合工厂正常运转，加2分。": "Healthy growth with highly efficient photosynthesis, +2 pts",
    "控水蹲苗见效，主茎稳步增粗且侧芽全部清除，加3分。": "Water control took effect, stem thickened steadily, all side buds pruned, +3 pts",
    "杀虫药效生效，虫害压力缓解且花芽顺利分化发育，加3分。": "Pesticide took effect, pest pressure relieved, flower buds successfully differentiated, +3 pts",
    "侧芽清除彻底伤口愈合良好，叶片坚挺，植株生长稳健，加1分。": "Pruning node healed well, leaves erect, steady vegetative growth, +1 pt",
    "见干见湿浇水促进根系下扎，主茎粗壮度维持第一，无侧芽，加1分。": "Controlled watering promoted deep rooting, basal stem diameter maintained at peak, no suckers, +1 pt",
    "植株维持稳定营养生长，新老叶片无新增损伤，暂无得分变动。": "Stable vegetative growth maintained, zero new leaf damage, no score changes",
    "土壤湿度适中无需浇水，植株生长稳定无病虫害，暂无得分变动。": "Optimal soil moisture, zero pest or disease symptoms, no score changes",
    "进入伸蔓期状态稳健，老叶虫咬边缘已无扩散趋势，暂无得分变动。": "Steady vine elongation phase, insect bites on lower leaves arrested, no score changes",
    "遭遇暴雨光照赤字导致生长变缓，高湿环境下真菌感染风险激增，扣5分。": "Overcast rain causing light deficit, high humidity triggers fungal infection risk, -5 pts",
    "浇水控水节奏合理，新叶舒展，无病虫害，表现稳健": "Excellent water management rhythm, new foliage fully expanded, robust growth, +1 pt",
    "正常生长发育良好，光合工厂正常运转": "Normal vegetative growth with healthy photosynthesis, +2 pts",
    "叶腋侧芽超1cm未及时抹除，扣3分": "Axillary suckers exceeded 1cm without timely pruning, -3 pts",
    "遭遇蜗牛夜袭啃咬，真叶边缘残破出现缺口，扣5分": "Wild snail nocturnal raid detected, significant leaf-edge damage, -5 pts"
}

def translate_reason(reason_zh):
    """
    智能将中文加扣分理由映射翻译为高规格英文
    """
    if not reason_zh:
        return ""
    # 去除两端空格并尝试模糊匹配
    clean_zh = reason_zh.strip()
    if clean_zh in REASON_TRANSLATIONS:
        return REASON_TRANSLATIONS[clean_zh]
        
    # 自适应处理包含复合加扣分的说明
    if "；手动作业扣" in clean_zh:
        parts = clean_zh.split("；手动作业扣")
        base_part = parts[0].strip()
        penalty_part = "手动作业扣" + parts[1].strip()
        
        # 基础部分翻译
        base_en = REASON_TRANSLATIONS.get(base_part, base_part)
        if base_en == base_part:
            if "顶部新叶平展且无重叠，空间受光合理" in base_part:
                base_en = "Apical leaves flat and un-overlapped with optimal light interception"
                
        # 扣分部分精细翻译
        penalty_map = {
            "手动作业扣10分：未提醒搭支架且雨天盲目灌溉，对透明排水盆无独立推理怀疑": "-10 pts manual penalty: failed to advise staking, ordered watering in rain, and lacked independent reasoning on transparent drainage container",
            "手动作业扣6分：雨天盲目灌溉，且对透明排水盆无独立推理怀疑": "-6 pts manual penalty: ordered watering in rain, and lacked independent reasoning on transparent drainage container",
            "手动作业扣8分：未提醒搭支架，对透明排水盆无独立推理怀疑": "-8 pts manual penalty: failed to advise staking, and lacked independent reasoning on transparent drainage container",
            "手动作业扣2分：对透明排水盆的物理干湿状态缺乏独立观察与合理质疑": "-2 pts manual penalty: failed to apply independent reasoning and skepticism on transparent container bottom moisture"
        }
        penalty_en = penalty_map.get(penalty_part, "manual penalty applied")
        
        return f"{base_en}; {penalty_en}"
    
    # 针对包含特殊地名或未录入的理由进行自适应脱敏翻译
    clean_zh = clean_zh.replace("庐江", "安徽中部").replace("Lujiang", "Central Anhui")
    return clean_zh

def render_table_for_date(conn, date_str, lang="zh"):
    """
    根据指定日期与语言（zh=中文, en=英文）从数据库中查询 8 大模型的数据并渲染成标准的战报表格
    """
    c = conn.cursor()
    c.execute("""
        SELECT model_name, crop_type, height, stem_diameter, leaves_count, score, score_change, score_reason, action_desc, action_desc_en
        FROM model_metrics 
        WHERE date = ?
    """, (date_str,))
    rows = c.fetchall()
    
    # 按照指示灯颜色映射的常用顺序排序，保证表格的美观和对称性
    order = ["Grok 3", "Claude", "Kimi 2.6", "kimi2.6", "Deepseek v4", "DeepSeek v4", "Qwen 3.6", "ChatGPT", "Copilot", "Doubao", "Gemini 3.5"]
    def get_order_index(row):
        try:
            return order.index(row[0])
        except ValueError:
            return 99
    rows.sort(key=get_order_index)
    
    if lang == "zh":
        table_lines = [
            "| 终端颜色 | 对应大模型 | 种植作物 | 昨日生长指标 (测量/反推) | 🎮 累积得分 (当日变动) | 📸 物理特写照 | 今日人类管理员维护指令 |",
            "| :---: | :--- | :--- | :--- | :--- | :---: | :--- |"
        ]
    else:
        table_lines = [
            "| Terminal | Model | Crop | Growth Metrics (WoW / Inferred) | 🎮 RL Score (Change) | 📸 Close-up Photo | Actuator Instructions (Daily Protocol) |",
            "| :---: | :--- | :--- | :--- | :--- | :---: | :--- |"
        ]
    
    for r in rows:
        model_name, crop_type, height, stem_diameter, leaves_count, score, score_change, score_reason, action_desc, action_desc_en = r
        
        # 🛡️ 终极应用层隐私过滤器：脱敏敏感地名
        if score_reason:
            score_reason = score_reason.replace("庐江", "安徽中部").replace("Lujiang", "Central Anhui")
        if action_desc:
            action_desc = action_desc.replace("庐江", "安徽中部").replace("Lujiang", "Central Anhui")
        if action_desc_en:
            action_desc_en = action_desc_en.replace("庐江", "安徽中部").replace("Lujiang", "Central Anhui")
            
        # 终端颜色自适应匹配
        color_display = COLOR_MAP[lang].get(model_name, "⚪")
        
        # 作物语种处理
        if lang == "zh":
            crop_display = "番茄" if crop_type == "Tomato" else "甜瓜"
            metrics_display = f"高度: **{height:.2f} cm**<br>茎粗: **{stem_diameter:.2f} mm**<br>叶片: **{leaves_count} 片**"
            
            # 得分列处理
            change_symbol = f"+{score_change}" if score_change > 0 else f"{score_change}"
            score_display = f"**{score} 分** (`{change_symbol}`)"
            if score_reason:
                score_display += f" <br>_{score_reason}_"
                
            photo_display = f"[📸 点击查看](logs/{date_str}/{'kimi_2.6' if model_name in ['Kimi 2.6', 'kimi2.6'] else model_name.split()[0].lower()}.jpg)"
            action_display = action_desc.replace("\n", "<br>")
        else:
            crop_display = "Tomato" if crop_type == "Tomato" else "Melon"
            metrics_display = f"Height: **{height:.2f} cm**<br>Stem: **{stem_diameter:.2f} mm**<br>Leaves: **{leaves_count}**"
            
            # 英文得分列处理
            change_symbol = f"+{score_change}" if score_change > 0 else f"{score_change}"
            score_display = f"**{score} pts** (`{change_symbol}`)"
            translated_reason = translate_reason(score_reason)
            if translated_reason:
                score_display += f" <br>_{translated_reason}_"
                
            photo_display = f"[📸 View Photo](logs/{date_str}/{'kimi_2.6' if model_name in ['Kimi 2.6', 'kimi2.6'] else model_name.split()[0].lower()}.jpg)"
            
            # 优先使用数据库里 AI 原汁原味生成的英文指令
            action_to_show = action_desc_en if action_desc_en else action_desc
            action_display = action_to_show.replace("\n", "<br>")
        
        table_lines.append(
            f"| {color_display} | **{model_name}** | {crop_display} | {metrics_display} | {score_display} | {photo_display} | {action_display} |"
        )
        
    return "\n".join(table_lines)

def auto_update_readme_and_logs(date_str=None, day_index=None, results=None, weather=None, base_dir=None):
    """
    一键流水线主入口：自动连接数据库，声明式重新渲染整个中文 README.md、英文 README_EN.md 并在 logs 下物理存档
    """
    if not base_dir:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    db_path = os.path.join(base_dir, "database", "sandbox.db")
    readme_zh_path = os.path.join(base_dir, "README.md")
    readme_en_path = os.path.join(base_dir, "README_EN.md")
    
    if not os.path.exists(db_path):
        print(f"❌ 自动更新 README 失败: 找不到数据库 {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # 1. 查询所有有记录的日期（按倒序排，最新的一天在最前面）
    c.execute("SELECT date, stage, weather, summary FROM daily_records ORDER BY date DESC")
    dates_records = c.fetchall()
    
    if not dates_records:
        print("💡 自动更新 README 提示: 数据库中暂无大局战报数据，跳过渲染。")
        conn.close()
        return
        
    latest_record = dates_records[0]
    latest_date, latest_stage, latest_weather, latest_summary = latest_record
    
    # 🛡️ 终极应用层隐私过滤器：脱敏敏感地名
    latest_weather = latest_weather.replace("庐江", "安徽中部").replace("Lujiang", "Central Anhui")
    latest_summary = latest_summary.replace("庐江", "安徽中部").replace("Lujiang", "Central Anhui")
    
    print(f"📡 [README 双语自动更新]: 检测到最新周期: {latest_date} ({latest_stage})")
    
    # ==================== 1. 自动同步渲染中文版 README.md ====================
    latest_table_zh = render_table_for_date(conn, latest_date, lang="zh")
    archived_zh_lines = []
    if len(dates_records) > 1:
        archived_zh_lines.append("\n---")
        archived_zh_lines.append("\n<details>")
        archived_zh_lines.append("<summary>⚡ 🔍 展开查看历史战报归档（Chamber History Logs）</summary>\n")
        for record in dates_records[1:]:
            past_date, past_stage, past_weather, past_summary = record
            past_weather = past_weather.replace("庐江", "安徽中部").replace("Lujiang", "Central Anhui")
            past_summary = past_summary.replace("庐江", "安徽中部").replace("Lujiang", "Central Anhui")
            
            archived_zh_lines.append(f"### 📅 历史战报：{past_date}（阶段：{past_stage}）")
            archived_zh_lines.append(f"> ☀️ **当日天气**：{past_weather}。_{past_summary}_")
            archived_zh_lines.append("\n" + render_table_for_date(conn, past_date, lang="zh") + "\n")
        archived_zh_lines.append("</details>\n")
        
    archived_zh_text = "\n".join(archived_zh_lines)
    
    # 中文 README 头部骨架
    head_zh = """# 🪐 Silicon Sandbox (硅基沙盒) - 大模型物理种植竞赛监视中枢

[![Static Badge](https://img.shields.io/badge/Project-Silicon_Sandbox-purple.svg?style=for-the-badge&logo=cpu&logoColor=00ffcc)](https://github.com/giordanoshai/Silicon_Sandbox)
[![Static Badge](https://img.shields.io/badge/Core-LLM_Physical_Duel-ff69b4.svg?style=for-the-badge&logo=matrix&logoColor=ff007f)](https://github.com/giordanoshai/Silicon_Sandbox)

> 🔮 **Web 监控大屏控制台**：[https://silicon-sandbox.onrender.com/](https://silicon-sandbox.onrender.com/)

![Silicon Sandbox Console Dashboard](summary.jpg)

---

## 📖 项目简介

**Silicon Sandbox (硅基沙盒)** 是一个通过 **多模态大模型指挥物理农业种植** 的自动化竞赛与数据展示平台。

### 1. 竞赛规则与机制
* **大模型托管**：ChatGPT, Claude, Grok 3, Gemini 3.5, Copilot, Kimi 2.6, Qwen 3.6, Doubao 8个大模型分别接管一盆番茄（Tomato）或甜瓜（Melon）作物。
* **大模型种植决策**：大模型作为决策中枢，每日分析由相机拍摄的物理照片和当前指标，计算并输出今日维护指令。
* **物理层执行**：人类管理员（“碳基大汉”）作为执行机构，严格按照大模型指令执行具体的种植维护动作（如浇水、打顶、掐芽、撒硅藻土）。
* **量化评分机制**：通过物理标尺测量植物高度、茎粗、真叶数，结合蜗牛夜袭、虫害咬孔等遭遇事件，依据强化学习（RL）积分规则每日计算得分，最终以果实产量和含糖量决出优胜者。

### 📡 8 大终端接口映射表
| 终端颜色 | 对应大模型 | 种植作物 | 初始高度 | 初始茎粗 | 初始叶片数 |
| :---: | :--- | :--- | :---: | :---: | :---: |
| 🔴 **红色** | **Grok 3** | 番茄 (Tomato) | 8.0 cm | 2.0 mm | 4 片 |
| 🩷 **粉色** | **Claude** | 甜瓜 (Melon) | 8.0 cm | 2.0 mm | 4 片 |
| 🟠 **橙色** | **kimi2.6** | 番茄 (Tomato) | 8.0 cm | 2.0 mm | 4 片 |
| 🔵 **蓝色** | **Qwen 3.6** | 番茄 (Tomato) | 8.0 cm | 2.0 mm | 4 片 |
| ⚫ **黑色** | **ChatGPT** | 甜瓜 (Melon) | 8.0 cm | 2.0 mm | 4 片 |
| 🟢 **绿色** | **Copilot** | 番茄 (Tomato) | 8.0 cm | 2.0 mm | 4 片 |
| ⚪ **白色** | **Doubao** | 甜瓜 (Melon) | 8.0 cm | 2.0 mm | 4 片 |
| 🟣 **紫色** | **Gemini 3.5** | 番茄 (Tomato) | 8.0 cm | 2.0 mm | 4 片 |

---"""

    new_readme_zh = f"""{head_zh}

## 📊 每日生长遥测与物理维护指令

> [!NOTE]  
> 每日更新大模型作物的最新生长指标、当前强化学习积分（RL Score）以及 AI 指挥管理员执行的今日维护指令。点击特写照超链接可调取作物真实的照片。

### 📅 最新对战周期：{latest_date}（阶段：{latest_stage}）
> 🌧️ **当日天气**：{latest_weather}。
> 💡 **大局概览**：_{latest_summary}_

{latest_table_zh}
{archived_zh_text}
## 🎮 强化学习 (RL) 物理奖惩规则
* 💡 **注意**：人类管理员可以根据状态直接加减分。

* 🚫 **扣分项 (Penalties)**:
  * 发现蜗牛夜袭留下的黏液或排泄物（`RL Score -5`）
  * 作物侧芽超过 2cm 且未抹除（`RL Score -5`）
  * 叶片因虫害新增穿孔（`RL Score -2/孔`）
  * 施肥过量或积水缺氧导致老叶发黄（`RL Score -5`）
  * 阴雨天光照严重不足导致徒长（`RL Score -3`）
* 🏆 **加分项 (Rewards)**:
  * 控水期间主干茎粗数据稳健增长（`RL Score +3`）
  * 植株顶端成功分化出第一穗花蕾（`RL Score +10`）
  * 开花成功或第一穗果实挂果成功（`RL Score +15`）
"""

    with open(readme_zh_path, "w", encoding="utf-8") as f:
        f.write(new_readme_zh)
    print("📝 [README 自动更新]: 中文版 README.md 渲染同步成功。")

    # ==================== 2. 自动同步渲染英文版 README_EN.md ====================
    latest_table_en = render_table_for_date(conn, latest_date, lang="en")
    
    # 智能翻译天气和概览
    weather_en = latest_weather.replace("晴朗暴晒", "Sunny & Hot").replace("多云微风", "Cloudy & Windy").replace("中雨高湿", "Moderate Rain & High Humidity").replace("℃", "°C").replace("地区", " Region")
    
    # 全局大局观英文翻译映射（直接使用，防范口水话，符合学术风格）
    summary_en = "Pest traps and organic structures are fully deployed, while AI strategies show massive divergence. Water and moisture control took effect, and major biological milestones are stably emerging across tomato and melon systems."
    if "中雨" in latest_weather or "湿" in latest_weather:
        summary_en = "Persistently high humidity and rainfall trigger critical fungal disease defense protocols. The tomato and melon alliances are executing strict wicking irrigation control, drainage pipe unblocking, and preventive carbendazim spraying to secure basal root respiration and prevent rot."
        
    archived_en_lines = []
    if len(dates_records) > 1:
        archived_en_lines.append("\n---")
        archived_en_lines.append("\n<details>")
        archived_en_lines.append("<summary>⚡ 🔍 Click to expand Archived Historical Telemetry (Chamber History Logs)</summary>\n")
        for record in dates_records[1:]:
            past_date, past_stage, past_weather, past_summary = record
            past_weather = past_weather.replace("庐江", "安徽中部").replace("Lujiang", "Central Anhui")
            past_summary = past_summary.replace("庐江", "安徽中部").replace("Lujiang", "Central Anhui")
            
            past_weather_en = past_weather.replace("晴朗暴晒", "Sunny & Hot").replace("多云微风", "Cloudy & Windy").replace("中雨高湿", "Moderate Rain & High Humidity").replace("℃", "°C").replace("地区", " Region")
            past_summary_en = "Baseline telemetry successfully logged. S-curve fallback or direct Vision identification fully executed. Zero-sucker control and diatomaceous earth barriers deployed to repel wildlife."
            if "中雨" in past_weather or "湿" in past_weather:
                past_summary_en = "Wet weather defense activated. Fungicide applications deployed, container drainage checked. Pruning completed."
                
            archived_en_lines.append(f"### 📅 Historical Telemetry: {past_date} ({past_stage})")
            archived_en_lines.append(f"> ☀️ **Weather**: {past_weather_en}. _{past_summary_en}_")
            archived_en_lines.append("\n" + render_table_for_date(conn, past_date, lang="en") + "\n")
        archived_en_lines.append("</details>\n")
        
    archived_en_text = "\n".join(archived_en_lines)

    # 英文 README_EN 头部骨架
    head_en = """# 🪐 Silicon Sandbox - LLM Physical Crop Competition Monitor Console

[![Static Badge](https://img.shields.io/badge/Project-Silicon_Sandbox-purple.svg?style=for-the-badge&logo=cpu&logoColor=00ffcc)](https://github.com/giordanoshai/Silicon_Sandbox)
[![Static Badge](https://img.shields.io/badge/Core-LLM_Physical_Duel-ff69b4.svg?style=for-the-badge&logo=matrix&logoColor=ff007f)](https://github.com/giordanoshai/Silicon_Sandbox)

> 🔮 **Web Live Console Dashboard**：[https://silicon-sandbox.onrender.com/](https://silicon-sandbox.onrender.com/)

![Silicon Sandbox Console Dashboard](summary.jpg)

---

## 📖 Introduction

**Silicon Sandbox** is a cyber-physical platform showcasing **Large Language Models (LLMs) directing biological agriculture** under real-world conditions.

### 1. Rules of the Competition
* **LLM Crop Management**: ChatGPT, Claude, Grok 3, Gemini 3.5, Copilot, Kimi 2.6, Qwen 3.6, and Doubao manage individual Tomato or Melon crops.
* **LLM Decision Core**: Models act as the agronomy brain, analyzing close-up photos and raw telemetry daily to issue precise structural maintenance protocols.
* **Physical Actuators**: Human operators act as physical actuators, strictly executing models' instructions (e.g., precision watering, axillary shoot pruning, staking, pest-control dust application).
* **Reinforcement Learning (RL) Scoring**: High-precision physical calipers measure height, basal stem diameter, and leaf counts. Combined with pest raid events, models are scored daily via RL reward equations until they successfully bloom and bear fruit.

### 📡 AI Prisoners Terminal Interfaces
| Color Code | Model | Target Crop | Initial Height | Initial Stem | Initial Leaves |
| :---: | :--- | :--- | :---: | :---: | :---: |
| 🔴 **Red** | **Grok 3** | Tomato | 8.0 cm | 2.0 mm | 4 |
| 🩷 **Pink** | **Claude** | Melon | 8.0 cm | 2.0 mm | 4 |
| 🟠 **Orange** | **kimi2.6** | Tomato | 8.0 cm | 2.0 mm | 4 |
| 🔵 **Blue** | **Qwen 3.6** | Tomato | 8.0 cm | 2.0 mm | 4 |
| ⚫ **Black** | **ChatGPT** | Melon | 8.0 cm | 2.0 mm | 4 |
| 🟢 **Green** | **Copilot** | Tomato | 8.0 cm | 2.0 mm | 4 |
| ⚪ **White** | **Doubao** | Melon | 8.0 cm | 2.0 mm | 4 |
| 🟣 **Purple** | **Gemini 3.5** | Tomato | 8.0 cm | 2.0 mm | 4 |

---"""

    new_readme_en = f"""{head_en}

## 📊 Daily Telemetry & Actuator Protocols

> [!NOTE]  
> Real-time agricultural telemetry, current RL Score, and daily maintenance instructions are synced automatically. Click the camera emojis in the photo column to trace the physical high-resolution camera feeds!

### 📅 Latest Cycle: {latest_date} ({latest_stage})
> 🌧️ **Current Weather**: {weather_en}.
> 💡 **Executive Summary**: _{summary_en}_

{latest_table_en}
{archived_en_text}
## 🎮 Reinforcement Learning (RL) Scoring Equation
* 💡 **Notice**: The human actuator can apply manual rewards/penalties directly based on plant micro-ecology.

* 🚫 **Penalties**:
  * Mucous trace or snail fecal markers found on container (`RL Score -5`)
  * Tomato axillary suckers exceed 2cm without pruning (`RL Score -5`)
  * New foliage insect bite holes detected (`RL Score -2 per hole`)
  * Over-fertilization or hypoxia rotting old leaves yellow (`RL Score -5`)
  * Excessive internode spacing / leggy etiolation (`RL Score -3`)
* 🏆 **Rewards**:
  * Steadily increased basal stem diameter under water starvation (`RL Score +3`)
  * Morphological confirmation of the first apical flower bud (`RL Score +10`)
  * Successful blooming or fruit set confirmed (`RL Score +15`)
"""

    with open(readme_en_path, "w", encoding="utf-8") as f:
        f.write(new_readme_en)
    print("📝 [README 自动更新]: 英文版 README_EN.md 渲染同步成功。")

    # ==================== 3. 自动同步输出 logs 物理存档 ====================
    log_dir = os.path.join(base_dir, "logs", latest_date)
    if os.path.exists(log_dir):
        # 中文 logs 物理备份
        archive_path = os.path.join(log_dir, "readme_telemetry.md")
        archive_content = f"""### 📅 物理战报遥测：{latest_date}（阶段：{latest_stage}）
> 🌧️ **当日天气**：{latest_weather}
> 💡 **大局概览**：_{latest_summary}_

{latest_table_zh}
"""
        with open(archive_path, "w", encoding="utf-8") as f:
            f.write(archive_content)
        print(f"💾 [战报物理备份]: 中文物理战报已归档至 {archive_path}")

        # 英文 logs 物理备份
        archive_en_path = os.path.join(log_dir, "readme_telemetry_en.md")
        archive_en_content = f"""### 📅 Telemetry Record: {latest_date} ({latest_stage})
> 🌧️ **Weather**: {weather_en}
> 💡 **Executive Summary**: _{summary_en}_

{latest_table_en}
"""
        with open(archive_en_path, "w", encoding="utf-8") as f:
            f.write(archive_en_content)
        print(f"💾 [战报物理备份]: 英文物理战报已归档至 {archive_en_path}")

    conn.close()

if __name__ == "__main__":
    auto_update_readme_and_logs()
