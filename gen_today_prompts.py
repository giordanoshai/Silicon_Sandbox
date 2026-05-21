import os
import sys
from datetime import datetime

# 基础文件目录定位
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

def main():
    print("==================================================")
    print("🪐 硅基沙盒 (Silicon Sandbox) - 双轨 Prompt 统一生成器")
    print("==================================================")
    
    # 1. 读取常规模型通用 Prompt 模板文件
    prompt_tpl_path = os.path.join(BASE_DIR, "ai_prisoner_prompt.md")
    if not os.path.exists(prompt_tpl_path):
        print(f"❌ 错误: 未能在根目录下找到常规通用 Prompt 模板 [ai_prisoner_prompt.md]！")
        sys.exit(1)
        
    with open(prompt_tpl_path, "r", encoding="utf-8") as f:
        tpl_content = f.read()
        
    # 2. 读取 Copilot 专属脱敏 Prompt 模板文件
    copilot_tpl_path = os.path.join(BASE_DIR, "copilot_observer_prompt.md")
    if not os.path.exists(copilot_tpl_path):
        print(f"❌ 错误: 未能在根目录下找到 Copilot 专属 Prompt 模板 [copilot_observer_prompt.md]！")
        sys.exit(1)
        
    with open(copilot_tpl_path, "r", encoding="utf-8") as f:
        copilot_tpl_content = f.read()
        
    start_tag = "## 📥 【Prompt 复制正文】"
    
    # 提取常规 Prompt
    if start_tag not in tpl_content:
        print("❌ 错误: 常规 Prompt 模板格式损坏，未找到 '## 📥 【Prompt 复制正文】' 标记！")
        sys.exit(1)
    prompt_body = tpl_content.split(start_tag)[-1].strip()
    if prompt_body.startswith("```markdown"):
        prompt_body = prompt_body[len("```markdown"):].strip()
    if prompt_body.endswith("```"):
        prompt_body = prompt_body[:-3].strip()
        
    # 提取 Copilot 专属 Prompt
    if start_tag not in copilot_tpl_content:
        print("❌ 错误: Copilot 专属模板格式损坏，未找到 '## 📥 【Prompt 复制正文】' 标记！")
        sys.exit(1)
    copilot_prompt_body = copilot_tpl_content.split(start_tag)[-1].strip()
    if copilot_prompt_body.startswith("```markdown"):
        copilot_prompt_body = copilot_prompt_body[len("```markdown"):].strip()
    if copilot_prompt_body.endswith("```"):
        copilot_prompt_body = copilot_prompt_body[:-3].strip()
        
    # 输出双轨拼接 Prompt 文件
    output_prompts_file = os.path.join(BASE_DIR, "today_prompts.txt")
    
    with open(output_prompts_file, "w", encoding="utf-8") as out_f:
        out_f.write(f"# ==================================================\n")
        out_f.write(f"# 🪐 硅基沙盒 (Silicon Sandbox) - 统一通用双轨 Prompt 复制文本\n")
        out_f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out_f.write(f"# --------------------------------------------------\n")
        out_f.write(f"# 👉 用户提示：\n")
        out_f.write(f"#    1. 为了解决 Copilot 触发安全合规机制拒答的问题，我们采用双轨 Prompt 模式。\n")
        out_f.write(f"#    2. 【复制区 A】投喂给：Grok 3, Claude, ChatGPT, DeepSeek, 豆包, Qwen, Gemini。\n")
        out_f.write(f"#    3. 【复制区 B】专属投喂给：Copilot（完美避开对齐限制，展现冰冷科研观察者的极致反差萌！）。\n")
        out_f.write(f"# ==================================================\n\n\n")
        
        out_f.write(f"####################################################\n")
        out_f.write(f"🔥 【复制区 A：常规模型 7 合 1 囚徒博弈 Prompt】(直接全量复制下方所有内容)\n")
        out_f.write(f"####################################################\n\n")
        out_f.write(prompt_body)
        out_f.write("\n\n\n")
        
        out_f.write(f"####################################################\n")
        out_f.write(f"🔬 【复制区 B：Copilot 专属“冷酷科学观测员”脱敏 Prompt】(直接全量复制下方所有内容)\n")
        out_f.write(f"####################################################\n\n")
        out_f.write(copilot_prompt_body)
        out_f.write("\n\n\n")
        
    output_path_url = output_prompts_file.replace("\\", "/")
    print(f"\n🎉 恭喜！双轨统一 Prompt 生成完成！")
    print(f"👉 [today_prompts.txt](file:///{output_path_url})")
    print(f"==================================================")
    print(f"💡 开箱即用运行指南：")
    print(f"   1. 打开 today_prompts.txt。")
    print(f"   2. 复制【复制区 A】投喂给 7 个不受限模型。")
    print(f"   3. 复制【复制区 B】投喂给 Copilot。")
    print(f"   4. 将收集到的所有 JSON 回复追加粘贴到 [ai_replies.txt] 中。")
    print(f"   5. 运行 merge_ai_responses.py 和 pipeline.py 自动走完今日流水线！")
    print(f"==================================================")

if __name__ == "__main__":
    main()
