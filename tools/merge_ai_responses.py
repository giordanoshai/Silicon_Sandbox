import os
import re
import json
import sys
import io
from datetime import datetime

# 强制 UTF-8 编码，防止 Windows 控制台 Emoji 编码报错
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 8个模型的标准名称列表
REQUIRED_MODELS = [
    "Copilot", "Kimi 2.6", "Doubao", "Grok 3",
    "Claude", "Qwen 3.6", "Gemini 3.5", "ChatGPT"
]

# 基础文件目录定位 - 升级为识别根目录 (tools/ 的父级)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(BASE_DIR)

def extract_json_blocks(text):
    """
    使用极其健壮的方法在长文本中提取所有合法的 JSON 对象。
    支持 ```json 包裹的代码块，也支持纯花括号包裹段。
    """
    candidates = []
    
    # 1. 优先查找 ```json ... ``` 包裹的代码块
    code_blocks = re.findall(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    for block in code_blocks:
        try:
            candidates.append(json.loads(block.strip()))
        except Exception:
            pass
            
    # 2. 查找普通的 ``` ... ``` 代码块
    plain_blocks = re.findall(r"```\s*(.*?)\s*```", text, re.DOTALL)
    for block in plain_blocks:
        try:
            candidates.append(json.loads(block.strip()))
        except Exception:
            pass
            
    # 3. 扫描文本中所有的花括号结构（通过括号匹配寻找最外层 {}）
    stack = []
    start_idx = -1
    for idx, char in enumerate(text):
        if char == '{':
            if not stack:
                start_idx = idx
            stack.append(char)
        elif char == '}':
            if stack:
                stack.pop()
                if not stack and start_idx != -1:
                    substring = text[start_idx:idx+1]
                    try:
                        candidates.append(json.loads(substring.strip()))
                    except Exception:
                        pass
                    start_idx = -1
                    
    return candidates

def main():
    replies_file = os.path.join(BASE_DIR, ".scratch", "ai_replies.txt")
    output_file = os.path.join(BASE_DIR, ".scratch", "import_today.json")
    
    print("==================================================")
    print("🪐 硅基沙盒 (Silicon Sandbox) - AI 囚徒回复一键合并工具")
    print("==================================================")
    
    # 如果 .scratch 目录不存在，先创建它
    scratch_dir = os.path.dirname(replies_file)
    if not os.path.exists(scratch_dir):
        os.makedirs(scratch_dir)
        
    # 如果 replies_file 不存在，自动创建并提示
    if not os.path.exists(replies_file):
        with open(replies_file, "w", encoding="utf-8") as f:
            f.write("# 🪐 硅基沙盒 AI 囚徒文本收集箱\n")
            f.write("# --------------------------------------------------\n")
            f.write("# 👉 请在此处粘贴 8 大模型返回的对话回复或直接贴出 JSON 代码块。\n")
            f.write("# 👉 粘贴完毕并保存该文件后，请重新运行本脚本进行一键解析与拼装。\n")
            f.write("# --------------------------------------------------\n\n")
        print(f"💡 首次运行提示：已在 .scratch/ 目录下为您创建了临时数据收集文件 [.scratch/ai_replies.txt]")
        print(f"👉 请依次把 8 大模型的对话回复粘入该文件中，保存后重新运行本脚本即可！")
        sys.exit(0)
        
    with open(replies_file, "r", encoding="utf-8") as f:
        content = f.read()
        
    # 如果内容为空或仅包含默认注释
    if not content.replace("#", "").strip() or len(content.strip()) < 150:
        print(f"⚠️ [.scratch/ai_replies.txt] 似乎是空的，或者您还没有粘贴足够的 AI 回复内容。")
        print(f"👉 请打开 [.scratch/ai_replies.txt](file:///{replies_file}) 粘贴 8 个 AI 大模型的回复，然后重新运行。")
        sys.exit(0)
        
    # 解析抓取到的所有 JSON 对象
    json_objects = extract_json_blocks(content)
    
    parsed_models = {}
    global_summary = None
    global_audio_script = None
    global_weather = None
    
    for data in json_objects:
        if not isinstance(data, dict):
            continue
        model_name = data.get("model_name")
        if model_name:
            # 模糊匹配大模型名字
            matched_name = None
            for req_name in REQUIRED_MODELS:
                req_norm = req_name.lower().replace(" ", "").replace(".", "")
                model_norm = str(model_name).lower().replace(" ", "").replace(".", "")
                if req_norm == model_norm or (req_name == "Kimi 2.6" and model_norm == "kimi"):
                    matched_name = req_name
                    break
            
            if matched_name:
                # 存入解析好的大字典中 (允许后面的覆盖前面的，以防贴错重新贴)
                parsed_models[matched_name] = data
        else:
            # 没有指定 model_name，检测是否是全局数据 JSON 块
            if "summary" in data:
                global_summary = data.get("summary")
            if "audio_script" in data:
                global_audio_script = data.get("audio_script")
            if "weather" in data:
                global_weather = data.get("weather")
                
    print(f"🔍 正在扫描 [.scratch/ai_replies.txt]...")
    print(f"📊 已成功识别并解析 {len(parsed_models)} / {len(REQUIRED_MODELS)} 个模型的汇报数据。")
    if global_summary:
        print(f"🎬 已成功识别并解析今日全局总结：{global_summary[:30]}...")
    if global_audio_script:
        print(f"🗣️ 已成功识别并解析今日全局吐槽配音：{global_audio_script[:30]}...")
    print(f"--------------------------------------------------")
    
    # 展示识别结果
    for m in REQUIRED_MODELS:
        status = "✅ 已就绪" if m in parsed_models else "❌ 缺失 (将自动使用 S 型曲线模拟器兜底)"
        print(f" - {m:<15} : {status}")
    print(f"--------------------------------------------------")
        
    # 允许通过命令行参数直接传入日期和天气，以支持自动化无交互执行
    cli_date = None
    cli_weather = None
    for arg in sys.argv:
        if arg.startswith("--date="):
            cli_date = arg.split("=", 1)[1].strip()
        elif arg.startswith("--weather="):
            cli_weather = arg.split("=", 1)[1].strip()

    # 交互询问天气和日期
    today_str = datetime.now().strftime("%Y-%m-%d")
    if cli_date:
        date_str = cli_date
        print(f"📅 已通过命令行指定今日战报日期: {date_str}")
    else:
        try:
            date_input = input(f"📅 请确认/输入今日战报日期 (默认 {today_str}): ").strip()
        except (KeyboardInterrupt, EOFError):
            date_input = ""
        date_str = date_input if date_input else today_str
    
    default_weather = global_weather if global_weather else "暴晒强光（31℃）"
    if cli_weather:
        weather_str = cli_weather
        print(f"🌤️ 已通过命令行指定今日天气描述: {weather_str}")
    else:
        try:
            weather_input = input(f"🌤️ 请确认/输入今日天气描述 (默认 '{default_weather}'): ").strip()
        except (KeyboardInterrupt, EOFError):
            weather_input = ""
        weather_str = weather_input if weather_input else default_weather
    
    # 拼装数据
    merged_data = {
        "date": date_str,
        "weather": weather_str,
        "models": {}
    }
    if global_summary:
        merged_data["summary"] = global_summary
    if global_audio_script:
        merged_data["audio_script"] = global_audio_script
        
    # 合并
    for m in REQUIRED_MODELS:
        if m in parsed_models:
            # 剔除 redundant 的 model_name 字段，使 JSON 格式更加纯正
            m_data = dict(parsed_models[m])
            if "model_name" in m_data:
                del m_data["model_name"]
            merged_data["models"][m] = m_data
            
    # 写入 .scratch/import_today.json
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False)
        
    print(f"\n🎉 恭喜！一键合并完成！数据已保存至：[.scratch/import_today.json](file:///{output_file})")
    print(f"==================================================")
    print(f"👉 接下来，请在终端执行以下指令来运行流水线并生成短视频大屏：")
    print(f"   python tools/import_daily_data.py --json import_today.json")
    print(f"==================================================")

if __name__ == "__main__":
    main()
