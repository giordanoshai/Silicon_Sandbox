import os
import sqlite3
from datetime import datetime

# 定义终端指示灯颜色映射，便于在表格中展示标准色卡Emoji
COLOR_MAP = {
    "Grok 3": "🔴 **红色**",
    "Claude": "🩷 **粉色**",
    "kimi2.6": "🟠 **橙色**",
    "Kimi 2.6": "🟠 **橙色**", # 兼容量化数据中的不同命名格式
    "DeepSeek v4": "🟠 **橙色**",
    "Deepseek v4": "🟠 **橙色**",
    "Qwen 3.6": "🔵 **蓝色**",
    "ChatGPT": "⚫ **黑色**",
    "Copilot": "🟢 **绿色**",
    "Doubao": "⚪ **白色**",
    "Gemini 3.5": "🟣 **紫色**",
}

def render_table_for_date(conn, date_str):
    """
    根据指定日期从数据库中查询 8 大模型的数据并渲染成标准的 Markdown 战报表格
    """
    c = conn.cursor()
    c.execute("""
        SELECT model_name, crop_type, height, stem_diameter, leaves_count, score, score_change, score_reason, action_desc
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
    
    table_lines = [
        "| 终端颜色 | 对应大模型 | 种植作物 | 昨日生长指标 (测量/反推) | 🎮 累积得分 (当日变动) | 📸 物理特写照 | 今日人类管理员维护指令 |",
        "| :---: | :--- | :--- | :--- | :--- | :---: | :--- |"
    ]
    
    for r in rows:
        model_name, crop_type, height, stem_diameter, leaves_count, score, score_change, score_reason, action_desc = r
        
        # 🛡️ 终极应用层隐私过滤器：脱敏敏感地名
        if score_reason:
            score_reason = score_reason.replace("庐江", "安徽中部").replace("Lujiang", "Central Anhui")
        if action_desc:
            action_desc = action_desc.replace("庐江", "安徽中部").replace("Lujiang", "Central Anhui")
        
        # 终端颜色自适应匹配
        color_display = COLOR_MAP.get(model_name, "⚪ **白色**")
        
        # 作物中文化
        crop_display = "番茄" if crop_type == "Tomato" else "甜瓜"
        
        # 生长指标行内换行
        metrics_display = f"高度: **{height:.2f} cm**<br>茎粗: **{stem_diameter:.2f} mm**<br>叶片: **{leaves_count} 片**"
        
        # 计分变化自适应符号显示
        change_symbol = f"+{score_change}" if score_change > 0 else f"{score_change}"
        score_display = f"**{score} 分** (`{change_symbol}`)"
        if score_reason:
            score_display += f" <br>_{score_reason}_"
            
        # 物理特写照智能拼配
        # 对 Kimi 2.6 的文件名映射兜底
        base_filename = "kimi_2.6" if model_name in ["Kimi 2.6", "kimi2.6"] else model_name.split()[0].lower()
        photo_display = f"[📸 点击查看](logs/{date_str}/{base_filename}.jpg)"
        
        # 整理实操指令换行
        action_display = action_desc.replace("\n", "<br>")
        
        table_lines.append(
            f"| {color_display} | **{model_name}** | {crop_display} | {metrics_display} | {score_display} | {photo_display} | {action_display} |"
        )
        
    return "\n".join(table_lines)

def auto_update_readme_and_logs(date_str=None, day_index=None, results=None, weather=None, base_dir=None):
    """
    一键流水线主入口：自动连接数据库，声明式重新渲染整个 README.md 与 logs 下的当日物理战报存档
    """
    if not base_dir:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    db_path = os.path.join(base_dir, "database", "sandbox.db")
    readme_path = os.path.join(base_dir, "README.md")
    
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
    
    print(f"📡 [README 自动渲染器]: 检测到最新对决周期: {latest_date} ({latest_stage})")
    
    # 2. 渲染最新一天的遥测和指令表格
    latest_table_md = render_table_for_date(conn, latest_date)
    
    # 3. 渲染历史归档的折叠列表（把最新一天之外的旧数据，塞进 <details> 框中）
    archived_md_lines = []
    if len(dates_records) > 1:
        archived_md_lines.append("\n---")
        archived_md_lines.append("\n<details>")
        archived_md_lines.append("<summary>⚡ 🔍 展开查看历史战报归档（Chamber History Logs）</summary>\n")
        
        for record in dates_records[1:]:
            past_date, past_stage, past_weather, past_summary = record
            
            # 🛡️ 终极应用层隐私过滤器：脱敏敏感地名
            past_weather = past_weather.replace("庐江", "安徽中部").replace("Lujiang", "Central Anhui")
            past_summary = past_summary.replace("庐江", "安徽中部").replace("Lujiang", "Central Anhui")
            
            archived_md_lines.append(f"### 📅 历史战报：{past_date}（阶段：{past_stage}）")
            archived_md_lines.append(f"> ☀️ **当日天气**：{past_weather}。_{past_summary}_")
            archived_md_lines.append("\n" + render_table_for_date(conn, past_date) + "\n")
            
        archived_md_lines.append("</details>\n")
        
    archived_md_text = "\n".join(archived_md_lines)
    
    # 4. 读取现有的 README.md，将 '## 📊 每日生长遥测与物理维护指令' 这行以下的所有内容切掉替换
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            readme_content = f.read()
            
        split_marker = "## 📊 每日生长遥测与物理维护指令"
        if split_marker in readme_content:
            head_part = readme_content.split(split_marker)[0].strip()
        else:
            head_part = readme_content.strip() # 兜底防止意外切断
    else:
        # 如果 README 不存在，渲染一个带有极简头部的完整 README
        head_part = """# 🪐 Silicon Sandbox (硅基沙盒) - 大模型物理种植竞赛监视中枢

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

    # 5. 组装全新 README
    new_readme_content = f"""{head_part}

## 📊 每日生长遥测与物理维护指令

> [!NOTE]  
> 每日更新大模型作物的最新生长指标、当前强化学习积分（RL Score）以及 AI 指挥管理员执行的今日维护指令。点击特写照超链接可调取作物真实的照片。

### 📅 最新对战周期：{latest_date}（阶段：{latest_stage}）
> 🌧️ **当日天气**：{latest_weather}。
> 💡 **大局概览**：_{latest_summary}_

{latest_table_md}
{archived_md_text}
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

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_readme_content)
    print("📝 [README 自动渲染器]: README.md 已与 SQLite 数据库成功同步更新！")
    
    # 6. 为最新的一天在 logs 目录下物理留痕存档 readme_telemetry.md
    log_dir = os.path.join(base_dir, "logs", latest_date)
    if os.path.exists(log_dir):
        archive_path = os.path.join(log_dir, "readme_telemetry.md")
        archive_content = f"""### 📅 物理战报遥测：{latest_date}（阶段：{latest_stage}）
> 🌧️ **当日天气**：{latest_weather}
> 💡 **大局概览**：_{latest_summary}_

{latest_table_md}
"""
        with open(archive_path, "w", encoding="utf-8") as f:
            f.write(archive_content)
        print(f"💾 [README 自动渲染器]: 物理战报已成功归档至 {archive_path}")
        
    conn.close()

if __name__ == "__main__":
    auto_update_readme_and_logs()
