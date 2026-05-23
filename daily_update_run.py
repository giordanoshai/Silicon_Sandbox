import os
import sys
import subprocess
from datetime import datetime

def main():
    # 基础路径定位
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    replies_file = os.path.join(BASE_DIR, ".scratch", "ai_replies.txt")
    merge_script = os.path.join(BASE_DIR, "tools", "merge_ai_responses.py")
    import_script = os.path.join(BASE_DIR, "tools", "import_daily_data.py")
    
    print("========================================================================")
    print("🪐 SILICON SANDBOX // 硅基沙盒・每日遥测与 README 一键无干预更新中枢")
    print("========================================================================")
    
    # 1. 检验收集箱是否存在且已粘贴数据
    if not os.path.exists(replies_file):
        # 自动创建模板
        os.makedirs(os.path.dirname(replies_file), exist_ok=True)
        with open(replies_file, "w", encoding="utf-8") as f:
            f.write("# 🪐 硅基沙盒 AI 囚徒文本收集箱\n")
            f.write("# --------------------------------------------------\n")
            f.write("# 👉 请在此处直接粘贴 8 大模型返回的整段对话回复或 JSON 代码块并保存该文件。\n")
            f.write("# 👉 保存后，直接在根目录重新运行 `python daily_update_run.py` 即可一键更新！\n")
            f.write("# --------------------------------------------------\n\n")
        print(f"💡 [初始化提示]: 已为您创建了 AI 回复收集箱 [.scratch/ai_replies.txt]")
        print(f"👉 请依次把 8 大模型的聊天回复贴入该文件中，保存后重新运行本脚本！")
        sys.exit(0)
        
    with open(replies_file, "r", encoding="utf-8") as f:
        content = f.read()
        
    if not content.replace("#", "").strip() or len(content.strip()) < 150:
        print(f"⚠️ 警告: 收集箱 [.scratch/ai_replies.txt] 尚未包含足够的 AI 汇报内容。")
        print(f"👉 请打开该文件粘贴 8 大模型的回复，然后重新运行。")
        sys.exit(0)
        
    # 2. 智能感知 AI 文本中的天气线索，实现高智能无交互推演
    detected_weather = "晴朗暴晒（29℃）"
    lower_content = content.lower()
    if "中雨" in lower_content or "大雨" in lower_content or "降雨" in lower_content or "高湿" in lower_content:
        detected_weather = "中雨高湿（24℃）"
        print("🌧️ [天气智能感知]: 检测到 AI 文本中提及阴雨/高湿关键词，已自动匹配：中雨高湿（24℃）")
    elif "多云" in lower_content or "阴天" in lower_content:
        detected_weather = "多云微风（26℃）"
        print("🌤️ [天气智能感知]: 检测到 AI 文本中提及多云/阴天关键词，已自动匹配：多云微风（26℃）")
    else:
        print("☀️ [天气智能感知]: 未检测到突发气象词，自动匹配沙盒默认天气：晴朗暴晒（29℃）")
        
    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"📅 [控制周期锁定]: 自动锁定今日对决日期: {today_str}")
    print("------------------------------------------------------------------------")
    
    # 3. 物理执行一键合并，生成 import_today.json (非交互式模式)
    print("🚀 步骤 A: 正在提取收集箱文本中的 JSON 代码块并合并打包...")
    python_exe = sys.executable if sys.executable else "python"
    
    merge_cmd = [
        python_exe, 
        merge_script, 
        f"--date={today_str}", 
        f"--weather={detected_weather}"
    ]
    
    merge_proc = subprocess.run(merge_cmd, capture_output=True, text=True, encoding="utf-8")
    
    if merge_proc.returncode != 0:
        print("❌ 错误: 一键合并 AI 响应失败！详细错误如下：")
        print(merge_proc.stderr)
        sys.exit(1)
        
    print("   [SUCCESS] 8 大大模型响应已在后台成功解耦并打包完毕！")
    
    # 4. 物理执行流水线更新，持久化入库，自动声明式渲染 README 并归档物理 logs
    print("🚀 步骤 B: 正在同步写入 SQLite 数据库并重新渲染更新 README.md...")
    
    import_cmd = [
        python_exe, 
        import_script, 
        "--json=import_today.json",
        "--no-media"
    ]
    
    import_proc = subprocess.run(import_cmd, capture_output=True, text=True, encoding="utf-8")
    
    if import_proc.returncode != 0:
        print("❌ 错误: 写入数据库与更新 README 失败！详细错误如下：")
        print(import_proc.stderr)
        sys.exit(1)
        
    # 优雅解析流水线打印的核心输出，提取关键信息
    print("   [SUCCESS] 数据成功存入 SQLite database/sandbox.db！")
    
    # 5. 精美的大捷终端框输出，仪式感拉满
    print("\n========================================================================")
    print("🎉🎉🎉 恭喜！硅基沙盒今日战报一键全自动同步更新成功！")
    print("========================================================================")
    print(f"📅 今日对决日期  : {today_str}")
    print(f"🌤️ 今日感知天气  : {detected_weather}")
    print(f"📝 动态控制台更新: [README.md](file:///{os.path.join(BASE_DIR, 'README.md')}) 已成功重构并声明式重新渲染！")
    print(f"💾 物理战报归档  : [logs/{today_str}/readme_telemetry.md](file:///{os.path.join(BASE_DIR, 'logs', today_str, 'readme_telemetry.md')}) 物理留痕完成！")
    print(f"📝 Changelog 增量: [Changelog.md](file:///{os.path.join(BASE_DIR, 'Changelog.md')}) 已成功追加修改记录！")
    print("========================================================================")
    print(">>> 物理沙盒今日伺服完毕，系统返回静默状态。")
    print("========================================================================")

if __name__ == "__main__":
    main()
