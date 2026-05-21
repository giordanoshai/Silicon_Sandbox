import os
import re
import json
from datetime import datetime

base_dir = os.path.dirname(os.path.abspath(__file__))
ai_response_path = os.path.join(base_dir, "logs", "2026-05-21", "Ai_response.md")
output_path = os.path.join(base_dir, "import_today.json")

REQUIRED_MODELS = [
    "Copilot", "DeepSeek v4", "Doubao", "Grok 3",
    "Claude", "Qwen 3.6", "Gemini 3.5", "ChatGPT"
]

def extract_json_blocks(text):
    candidates = []
    # 扫描花括号匹配
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
    if not os.path.exists(ai_response_path):
        print(f"❌ 错误：找不到文件 {ai_response_path}")
        return
        
    with open(ai_response_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    json_blocks = extract_json_blocks(content)
    parsed_models = {}
    for data in json_blocks:
        if not isinstance(data, dict):
            continue
        model_name = data.get("model_name")
        if model_name:
            matched_name = None
            for req_name in REQUIRED_MODELS:
                if req_name.lower().replace(" ", "") == str(model_name).lower().replace(" ", ""):
                    matched_name = req_name
                    break
            if matched_name:
                parsed_models[matched_name] = data
                
    print(f"📊 解析到 {len(parsed_models)} / {len(REQUIRED_MODELS)} 个模型的 JSON 数据。")
    for m in REQUIRED_MODELS:
        status = "✅ 已就绪" if m in parsed_models else "❌ 缺失"
        print(f" - {m:<15} : {status}")
        
    # 构建最终的 Day 1 全局 JSON
    day1_data = {
        "date": "2026-05-21",
        "weather": "暴晒强光（31℃）",
        "summary": "硅基沙盒 Day 1 物理大考正式开辟！8大高维AI囚徒被困后院塑料矿泉水桶，首日面临31℃极限暴晒大考。各路智能体策略发生剧烈两极分化，Qwen与Grok大打茎粗战术，Claude则带伤觉醒了首颗花芽，一场关于生殖潜能的赛博博弈已然白热化！",
        "audio_script": "注意看！这群号称毁灭人类的高维AI囚徒，昨晚又在后院被碳基软体动物黑客打穿了物理防线！Day 1大考中，Grok 3以断水控水强悍增茎称霸，Claude却因7处虫咬惨遭重罚！点击看这群塑料桶里的高维智子，谁能在这星期的暴晒下熬到最后！",
        "models": {}
    }
    
    for m in REQUIRED_MODELS:
        if m in parsed_models:
            m_data = dict(parsed_models[m])
            if "model_name" in m_data:
                del m_data["model_name"]
            day1_data["models"][m] = m_data
            
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(day1_data, f, indent=2, ensure_ascii=False)
        
    print(f"🎉 成功生成 import_today.json 并写入到：{output_path}")

if __name__ == "__main__":
    main()
