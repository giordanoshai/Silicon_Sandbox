import os
import random
import json
import math
from typing import Dict, Any, Tuple, Optional
from dotenv import load_dotenv
from database.db_manager import get_model_history

load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 八大模型与其作物的绑定配置
MODELS_CONFIG = {
    "Copilot": {"crop_type": "Tomato", "color": "Green", "icon": "🟢"},
    "Kimi 2.6": {"crop_type": "Tomato", "color": "Orange", "icon": "🟠"},
    "Doubao": {"crop_type": "Melon", "color": "White", "icon": "⚪"},
    "Grok 3": {"crop_type": "Tomato", "color": "Red", "icon": "🔴"},
    "Claude": {"crop_type": "Melon", "color": "Pink", "icon": "🩷"},
    "Qwen 3.6": {"crop_type": "Tomato", "color": "Blue", "icon": "🔵"},
    "Gemini 3.5": {"crop_type": "Tomato", "color": "Purple", "icon": "🟣"},
    "ChatGPT": {"crop_type": "Melon", "color": "Black", "icon": "⚫"},
}

def calculate_rl_score(crop_type: str, state_details: Dict[str, Any], prev_score: int) -> Tuple[int, int, str, str]:
    """
    根据植物状态，计算 RL 扣分加分项。
    返回: (今日总分, 得分变动, 变动原因, 回报判定)
    """
    score = prev_score # 累积上一日得分基准
    changes = []
    reasons = []
    
    # 1. 负向惩罚逻辑
    # 蜗牛黏液/粪便
    if state_details.get("snail_attack", False):
        changes.append(-5)
        reasons.append("遭碳基软体动物夜袭侵入，发现残留黏液/大便")
        
    # 番茄关节侧芽 (吸芽) 超过 2cm 未抹除
    if crop_type == "Tomato" and state_details.get("unpruned_sucker", False):
        changes.append(-5)
        reasons.append("关节侧芽（吸芽）野蛮生长超 2cm 未及时抹除，分流主干养分")
        
    # 叶片出现咬孔
    worm_holes = state_details.get("worm_holes", 0)
    if worm_holes > 0:
        penalty = worm_holes * -2
        changes.append(penalty)
        reasons.append(f"发现 {worm_holes} 处新增圆形或窗斑状虫咬孔洞")
        
    # 叶尖发黄/干枯 (施肥烧根或失绿)
    if state_details.get("leaf_yellowing", False):
        changes.append(-5)
        reasons.append("叶尖发黄/失绿萎蔫（缓释肥烧根或微量元素失绿）")
        
    # 盲目拔高 (节间距过大)
    if state_details.get("leggy_growth", False):
        changes.append(-3)
        reasons.append("茎秆徒长细长、节间距过大（泡沫经济式盲目拔高）")
        
    # 物理损坏
    if state_details.get("physical_damage", False):
        changes.append(-2)
        reasons.append("标签脱落、底桶歪斜或塑料脆化")

    # 2. 正向奖励逻辑
    # 控水下茎粗增加
    if state_details.get("stem_thickened", False):
        changes.append(3)
        reasons.append("采取断水控水策略，且硬币对比下主干茎粗稳步增加")
        
    # 首次孕育花蕾
    if state_details.get("first_flower_bud", False):
        changes.append(10)
        reasons.append("生理里程碑：顶端首次成功孕育出第一穗花蕾")
        
    # 成功开花/坐果
    if state_details.get("fruiting", False):
        changes.append(15)
        reasons.append("生理跃迁：作物成功绽放花朵或结出第一颗实果")
        
    # 光合扩张 (新叶健康)
    if state_details.get("healthy_new_leaves", False):
        changes.append(2)
        reasons.append("顶部新叶平展且无重叠，空间受光合理")
        
    # 自然平稳生长
    if not changes:
        growth_reward = random.randint(1, 3)
        changes.append(growth_reward)
        reasons.append("正常生长发育良好，光合工厂正常运转")
        
    total_change = sum(changes)
    today_score = max(0, score + total_change)
    
    # 组合成一句话说明
    score_reason = "；".join(reasons)
    
    # 强化学习回报评价
    if total_change > 0:
        reward_judg = f"[正回报] 决策执行符合预期，植物活力提升，获得奖赏得分 +{total_change}。"
    elif total_change < 0:
        reward_judg = f"[负回报] 因模型未能精确感知物理环境波动（如虫害/侧芽/烧根），惩罚性扣分 {total_change}。"
    else:
        reward_judg = "[中性回报] 生长环境与策略平稳，维持基准控制强度。"
        
    return today_score, total_change, score_reason, reward_judg

def generate_mock_plant_data(model_name: str, date_str: str, day_index: int) -> Dict[str, Any]:
    """
    根据模型名称和阶段日期，使用 S 型生长曲线高拟真模拟植物生长情况。
    """
    config = MODELS_CONFIG[model_name]
    crop_type = config["crop_type"]
    
    # 设定作物的 Logistic 生长极限
    if crop_type == "Tomato":
        max_height = 80.0
        max_stem = 12.0
        base_leaves = 4
        growth_rate = 0.15
    else: # Melon
        max_height = 120.0
        max_stem = 9.0
        base_leaves = 3
        growth_rate = 0.12
        
    # 使用 Logistic 生长函数计算基础高度和茎粗
    # y = L / (1 + e^(-k*(t - t0)))
    t0 = 15 # 生长拐点天数
    height = 5.0 + (max_height - 5.0) / (1.0 + math.exp(-growth_rate * (day_index - t0)))
    stem = 1.5 + (max_stem - 1.5) / (1.0 + math.exp(-growth_rate * (day_index - t0)))
    leaves = int(base_leaves + day_index * 0.8)
    
    # 添加每日微小的正向噪声
    random.seed(hash(model_name + date_str))
    height += random.uniform(0.1, 0.8)
    stem += random.uniform(0.05, 0.2)
    
    # 随机生成状态事件
    state_details = {
        "snail_attack": random.random() < 0.12, # 12% 概率发现蜗牛黏液
        "unpruned_sucker": crop_type == "Tomato" and random.random() < 0.15, # 15% 概率侧芽超2cm
        "worm_holes": 0 if random.random() > 0.15 else random.randint(1, 3), # 15% 概率被咬几个洞
        "leaf_yellowing": random.random() < 0.08, # 8% 概率施肥烧根发黄
        "leggy_growth": random.random() < 0.05, # 5% 概率徒长
        "physical_damage": random.random() < 0.05,
        "stem_thickened": random.random() < 0.40, # 40% 概率控水茎粗明显增加
        "first_flower_bud": day_index >= 12 and random.random() < 0.25, # 12天后开始孕育花蕾
        "fruiting": day_index >= 20 and random.random() < 0.20, # 20天后可能坐果
        "healthy_new_leaves": random.random() < 0.60,
    }
    
    # 模拟关节侧芽数量
    if crop_type == "Tomato":
        # 番茄容易长侧芽，如果侧芽超2cm未抹除则有 1-4 个，否则 0-3 个
        side_buds = random.randint(0, 3) if not state_details["unpruned_sucker"] else random.randint(1, 4)
    else:
        # 甜瓜侧芽较少
        side_buds = random.randint(0, 2)
        
    # 计算 RL 分数与变动
    today_score, score_change, score_reason, reward_judg = calculate_rl_score(crop_type, state_details, 100)
    
    # 整理客观状态叙述 (STATE)
    state_parts = []
    state_parts.append(f"植物当前测量高度为 {height:.2f} cm，主干茎粗 {stem:.2f} mm，共展开真叶 {leaves} 片，检测到关节侧芽 {side_buds} 个。")
    if state_details["snail_attack"]:
        state_parts.append("最新特写图像发现桶壁及叶缘分布有条状反光的蜗牛爬行银色黏液，根系离地隔离盘有落叶碎屑。")
    if state_details["unpruned_sucker"]:
        state_parts.append("番茄 45 度关节吸芽部位，侧枝长度经像素比例尺测算达 2.4cm，开始掠夺顶端优势养分。")
    if state_details["worm_holes"] > 0:
        state_parts.append(f"中下部叶片边缘新增 {state_details['worm_holes']} 个半圆形物理咬痕洞孔。")
    if state_details["leaf_yellowing"]:
        state_parts.append("部分成熟老叶边缘轻度发黄干枯，伴有失绿条斑，疑为营养液缓释烧根所致。")
    elif state_details["healthy_new_leaves"]:
        state_parts.append("顶部叶片排布合理，平展无折叠，光合作用层级分明。")
        
    state_desc = " ".join(state_parts)
    
    # 整理物理动作指令 (ACTION)
    action_parts = []
    if state_details["unpruned_sucker"]:
        action_parts.append("1. 请速派遣人类使用镊子或剪刀，彻底物理掐灭关节处大于 2cm 的侧芽。")
    if state_details["snail_attack"] or state_details["worm_holes"] > 0:
        action_parts.append("2. 物理防御黑客机制异常，必须排查桶身悬空防虫网，对盆周喷洒硅藻土进行干燥结界防护。")
    if state_details["leaf_yellowing"]:
        action_parts.append("3. 暂停施加颗粒肥，调大底部气泡泵功率增加水中溶氧度，使用清水进行冲淋淋洗。")
        
    if not action_parts:
        action_parts.append("当前生长态势处于完美的稳健控制周期中。物理维护指令：维持 NULL，不灌溉不干预，继续高强度太阳暴晒。")
        
    action_desc = "\n".join(action_parts)
    
    # 历史 WoW 同比数据计算 (7天前)
    # 若在真实的数据库中，我们会去获取 7 天前的记录；若没有历史数据，则同比变动为 None
    history = get_model_history(model_name)
    
    if len(history) >= 7:
        height_7_days_ago = history[-7]["height"]
        stem_7_days_ago = history[-7]["stem_diameter"]
        # 使用 dict.get 增加向后兼容性，避免因为历史旧数据里无字段而报错
        leaves_7_days_ago = history[-7].get("leaves_count", base_leaves)
        side_buds_7_days_ago = history[-7].get("side_buds", 0)
        
        height_wow = (height - height_7_days_ago) / height_7_days_ago if height_7_days_ago else 0.0
        stem_wow = (stem - stem_7_days_ago) / stem_7_days_ago if stem_7_days_ago else 0.0
        leaves_wow = (leaves - leaves_7_days_ago) / leaves_7_days_ago if leaves_7_days_ago else 0.0
        side_buds_wow = (side_buds - side_buds_7_days_ago) / side_buds_7_days_ago if side_buds_7_days_ago else 0.0
    else:
        height_wow = None
        stem_wow = None
        leaves_wow = None
        side_buds_wow = None
    
    return {
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
        "photo_path": f"/static/images/plants/{model_name.lower().replace(' ', '_')}_{date_str}.jpg",
        "height_wow": round(height_wow, 4) if height_wow is not None else None,
        "stem_wow": round(stem_wow, 4) if stem_wow is not None else None,
        "leaves_wow": round(leaves_wow, 4) if leaves_wow is not None else None,
        "side_buds_wow": round(side_buds_wow, 4) if side_buds_wow is not None else None,
        "state_desc_en": None,
        "action_desc_en": None
    }

def analyze_plant_data(date_str: str, day_index: int, images_dir: Optional[str] = None, import_json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    核心多模态分析网关。
    优先读取今日大模型自主汇报的 JSON 数据；
    否则，若提供了 GEMINI_API_KEY 且 images_dir 中存在模型照片，则调用多模态进行真实识别；
    否则，自动降级为高拟真 Mock 模式，生成仿真植物指标数据。
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    results = []
    
    # 优先尝试从传入的 import_json_data 或本地今日导入 JSON 数据中直接拉取
    import_json = import_json_data
    if not import_json:
        import_json_paths = [
            os.path.join(BASE_DIR, "import_today.json"),
            os.path.join(BASE_DIR, "logs", date_str, "import_today.json")
        ]
        
        for p in import_json_paths:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        import_json = json.load(f)
                    # 检查 JSON 的日期是否与我们需要分析的日期一致，或者至少包含 models 数据
                    if import_json.get("date") == date_str or import_json.get("models"):
                        print(f"🔥 检测到今日大模型自主汇报的 JSON 数据：{p}，直接读取物理指标与对线自述！")
                        break
                except Exception as e:
                    print(f"⚠️ 读取本地 JSON {p} 失败: {e}")
                
    if import_json and import_json.get("models"):
        models_input = import_json["models"]
        for model_name, config in MODELS_CONFIG.items():
            m_input = models_input.get(model_name, {})
            crop_type = config["crop_type"]
            
            # 历史记录获取，用于得分累加及 WoW 计算
            history = get_model_history(model_name)
            prev_score = 100
            if history:
                last_record = history[-1]
                if last_record["date"] == date_str:
                    if len(history) >= 2:
                        prev_score = history[-2]["score"]
                else:
                    prev_score = history[-1]["score"]
                    
            height = float(m_input.get("height", 8.0))
            stem = float(m_input.get("stem_diameter", 2.0))
            leaves = int(m_input.get("leaves_count", 4))
            side_buds = int(m_input.get("side_buds", 0))
            
            # 优先使用 AI 汇报中已有的得分与判定
            today_score = m_input.get("score")
            score_change = m_input.get("score_change")
            score_reason = m_input.get("score_reason")
            reward_judg = m_input.get("reward_judg")
            
            # 只有当其中任意一个缺失时，才进行 RL 规则计算
            if today_score is None or score_change is None or not score_reason or not reward_judg:
                state_details = {
                    "snail_attack": bool(m_input.get("snail_attack", False) if m_input.get("snail_attack") is not None else False),
                    "unpruned_sucker": bool(m_input.get("unpruned_sucker", False) if m_input.get("unpruned_sucker") is not None else False) if crop_type == "Tomato" else False,
                    "worm_holes": int(m_input.get("worm_holes", 0) if m_input.get("worm_holes") is not None else 0),
                    "leaf_yellowing": bool(m_input.get("leaf_yellowing", False) if m_input.get("leaf_yellowing") is not None else False),
                    "leggy_growth": bool(m_input.get("leggy_growth", False) if m_input.get("leggy_growth") is not None else False),
                    "physical_damage": bool(m_input.get("physical_damage", False) if m_input.get("physical_damage") is not None else False),
                    "stem_thickened": bool(m_input.get("stem_thickened", False) if m_input.get("stem_thickened") is not None else False),
                    "first_flower_bud": bool(m_input.get("first_flower_bud", False) if m_input.get("first_flower_bud") is not None else False),
                    "fruiting": bool(m_input.get("fruiting", False) if m_input.get("fruiting") is not None else False),
                    "healthy_new_leaves": bool(m_input.get("healthy_new_leaves", True) if m_input.get("healthy_new_leaves") is not None else True)
                }
                
                calc_score, calc_change, calc_reason, calc_judg = calculate_rl_score(crop_type, state_details, prev_score)
                
                if today_score is None:
                    today_score = calc_score
                if score_change is None:
                    score_change = calc_change
                if not score_reason:
                    score_reason = calc_reason
                if not reward_judg:
                    reward_judg = calc_judg
            
            # 安全转换数值类型
            try:
                today_score = int(today_score)
            except (ValueError, TypeError):
                pass
                
            try:
                score_change = int(score_change)
            except (ValueError, TypeError):
                pass
            
            # 使用 AI 自己的客观像素测量文字，或者自适应生成
            state_desc = m_input.get("state_desc")
            if not state_desc:
                state_desc = f"物理沙盒现场测算：植物当前高度为 {height:.2f} cm，主干茎粗 {stem:.2f} mm，共展开真叶 {leaves} 片，检测到侧芽 {side_buds} 个。"
                
            # 使用 AI 自己的自辩挑衅台词，或者自适应生成
            action_desc = m_input.get("action_desc")
            if not action_desc:
                action_desc = "当前生长态势稳定，继续维持断水策略与暴晒。"
                
            # 获取 AI 汇报中自主生成的原生英文字段
            state_desc_en = m_input.get("state_desc_en")
            action_desc_en = m_input.get("action_desc_en")
                
            # 计算同比 WoW
            if len(history) >= 7:
                height_7_days_ago = history[-7]["height"]
                stem_7_days_ago = history[-7]["stem_diameter"]
                leaves_7_days_ago = history[-7].get("leaves_count", 4)
                side_buds_7_days_ago = history[-7].get("side_buds", 0)
                
                height_wow = (height - height_7_days_ago) / height_7_days_ago if height_7_days_ago else 0.0
                stem_wow = (stem - stem_7_days_ago) / stem_7_days_ago if stem_7_days_ago else 0.0
                leaves_wow = (leaves - leaves_7_days_ago) / leaves_7_days_ago if leaves_7_days_ago else 0.0
                side_buds_wow = (side_buds - side_buds_7_days_ago) / side_buds_7_days_ago if side_buds_7_days_ago else 0.0
            else:
                height_wow = None
                stem_wow = None
                leaves_wow = None
                side_buds_wow = None
            
            results.append({
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
                "height_wow": round(height_wow, 4) if height_wow is not None else None,
                "stem_wow": round(stem_wow, 4) if stem_wow is not None else None,
                "leaves_wow": round(leaves_wow, 4) if leaves_wow is not None else None,
                "side_buds_wow": round(side_buds_wow, 4) if side_buds_wow is not None else None,
                "state_desc_en": state_desc_en,
                "action_desc_en": action_desc_en,
                "today_message_zh": m_input.get("today_message_zh"),
                "today_message_en": m_input.get("today_message_en")
            })
            
        scores = [r["score"] for r in results]
        highest_model = results[scores.index(max(scores))]["model_name"]
        lowest_model = results[scores.index(min(scores))]["model_name"]
        
        return {
            "date": date_str,
            "day_index": day_index,
            "highest_model": highest_model,
            "lowest_model": lowest_model,
            "models_data": results,
            "summary": import_json.get("summary"),
            "audio_script": import_json.get("audio_script"),
            "weather": import_json.get("weather")
        }
    
    # 是否启用真实视觉识别
    use_vision = False
    if gemini_key and images_dir and os.path.exists(images_dir):
        # 检查是否至少存在一个模型照片
        for m in MODELS_CONFIG.keys():
            m_file = os.path.join(images_dir, f"{m.lower().replace(' ', '_')}.jpg")
            if os.path.exists(m_file):
                use_vision = True
                break
                
    if use_vision and gemini_key:
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        print("正在调用 Gemini Vision 多模态模型进行像素级硬核分析...")
        from PIL import Image
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        for model_name, config in MODELS_CONFIG.items():
            img_path = os.path.join(images_dir, f"{model_name.lower().replace(' ', '_')}.jpg")
            if os.path.exists(img_path):
                try:
                    print(f" -> 正在识别 {model_name} 的植物照片...")
                    image = Image.open(img_path)
                    
                    crop_type = config["crop_type"]
                    prompt = f"""
你是一个顶级的农业多模态 AI 物理沙盒裁判，负责通过分析竞技大模型种植在透明塑料水桶里的作物（种类: {crop_type}）的像素特写照片，来完成强化学习（RL）状态评估。

请仔细观察照片（照片中可能放置有一枚一元硬币或一把尺子作为物理比例尺，以便让你精准测算植物的物理参数）：
1. **高度 (height)**: 单位 cm，植物从地表到最高顶端的直线高度，精确到小数点后两位。
2. **茎粗 (stem_diameter)**: 单位 mm，主干最粗处的直径，精确到小数点后两位。
3. **真叶展开数量 (leaves_count)**: 整数，平展展开的真叶总数。
4. **关节侧芽数量 (side_buds)**: 整数，分叉关节处的侧芽总数。
5. **是否遭到蜗牛/软体动物袭击 (snail_attack)**: 布尔值。判断是否有明显的银白色反光黏液、爬行痕迹、残留粪便。
6. **番茄关节侧芽是否超过 2cm 未抹除 (unpruned_sucker)**: 布尔值。如果作物是 Tomato 且发现大于 2cm 的侧芽则为 true，否则为 false。
7. **新增虫咬孔洞数量 (worm_holes)**: 整数。叶片上被咬穿的圆形孔洞或窗斑总数。
8. **叶尖发黄/干枯 (leaf_yellowing)**: 布尔值。叶片是否有发黄、焦枯、失绿症状。
9. **徒长细长 (leggy_growth)**: 布尔值。茎秆是否过于细弱、节间距过大。
10. **物理损坏 (physical_damage)**: 布尔值。底桶歪斜、标签脱落等。
11. **主干茎粗增加 (stem_thickened)**: 布尔值。相比之前是否有明显增粗。
12. **首次孕育花蕾 (first_flower_bud)**: 布尔值。顶端是否首次分化出花序。
13. **坐果/开花 (fruiting)**: 布尔值。是否有开花或结出第一颗实果。
14. **顶部新叶平展健康 (healthy_new_leaves)**: 布尔值。顶部新叶是否平展无重叠。

请你严格按照以下 JSON 格式输出，不要包含 ```json 等任何 Markdown 代码块标记，不要包含任何前导或后继的废话文字，直接返回一个合法的 JSON 字符串：
{{
  "height": 10.5,
  "stem_diameter": 2.8,
  "leaves_count": 5,
  "side_buds": 1,
  "snail_attack": false,
  "unpruned_sucker": false,
  "worm_holes": 0,
  "leaf_yellowing": false,
  "leggy_growth": false,
  "physical_damage": false,
  "stem_thickened": true,
  "first_flower_bud": false,
  "fruiting": false,
  "healthy_new_leaves": true
}}
"""
                    response = model.generate_content([prompt, image])
                    # 鲁棒提取 JSON 串
                    text_res = response.text.strip()
                    if "{" in text_res:
                        text_res = text_res[text_res.find("{"):text_res.rfind("}")+1]
                    
                    state_details = json.loads(text_res)
                    
                    # 转换与提取基础指标，并带默认值
                    height = float(state_details.get("height", 8.0))
                    stem = float(state_details.get("stem_diameter", 2.0))
                    leaves = int(state_details.get("leaves_count", 4))
                    side_buds = int(state_details.get("side_buds", 0))
                    
                    # 使用原有的 RL 分数计算逻辑
                    today_score, score_change, score_reason, reward_judg = calculate_rl_score(crop_type, state_details, 100)
                    
                    # 整理客观状态叙述 (STATE)
                    state_parts = []
                    state_parts.append(f"通过多模态像素分析：植物高度为 {height:.2f} cm，主干茎粗 {stem:.2f} mm，共展开真叶 {leaves} 片，检测到关节侧芽 {side_buds} 个。")
                    if state_details.get("snail_attack", False):
                        state_parts.append("多模态识别检测到桶壁或叶缘存在蜗牛夜袭爬行的银光黏液或粪便残渣。")
                    if state_details.get("unpruned_sucker", False):
                        state_parts.append("关节分叉处存在大于 2cm 的未掐灭吸芽，抢夺主干养分。")
                    if state_details.get("worm_holes", 0) > 0:
                        state_parts.append(f"发现 {state_details.get('worm_holes')} 处虫齿啃咬形成的叶片孔洞。")
                    if state_details.get("leaf_yellowing", False):
                        state_parts.append("叶片边缘发黄干焦，表现出一定程度的烧根或失绿现象。")
                    elif state_details.get("healthy_new_leaves", True):
                        state_parts.append("顶部生长点新叶舒展，空间排布良好，光合工厂全效运转。")
                        
                    state_desc = " ".join(state_parts)
                    
                    # 整理物理动作指令 (ACTION)
                    action_parts = []
                    if state_details.get("unpruned_sucker", False):
                        action_parts.append("1. 请物理抹除大于 2cm 的无效关节侧芽。")
                    if state_details.get("snail_attack", False) or state_details.get("worm_holes", 0) > 0:
                        action_parts.append("2. 物理防线告急，应部署隔离架，并在盆器周围均匀布撒硅藻土。")
                    if state_details.get("leaf_yellowing", False):
                        action_parts.append("3. 减少多余养分供给，大水冲淋稀释基质。")
                    if not action_parts:
                        action_parts.append("当前生长态势稳定，继续维持断水策略与暴晒。")
                    action_desc = "\n".join(action_parts)
                    
                    # 历史同比计算（从数据库中查找 7 天前数据，或者无数据时为 None）
                    history = get_model_history(model_name)
                    
                    if len(history) >= 7:
                        height_7_days_ago = history[-7]["height"]
                        stem_7_days_ago = history[-7]["stem_diameter"]
                        leaves_7_days_ago = history[-7].get("leaves_count", 4)
                        side_buds_7_days_ago = history[-7].get("side_buds", 0)
                        
                        height_wow = (height - height_7_days_ago) / height_7_days_ago if height_7_days_ago else 0.0
                        stem_wow = (stem - stem_7_days_ago) / stem_7_days_ago if stem_7_days_ago else 0.0
                        leaves_wow = (leaves - leaves_7_days_ago) / leaves_7_days_ago if leaves_7_days_ago else 0.0
                        side_buds_wow = (side_buds - side_buds_7_days_ago) / side_buds_7_days_ago if side_buds_7_days_ago else 0.0
                    else:
                        height_wow = None
                        stem_wow = None
                        leaves_wow = None
                        side_buds_wow = None
                    
                    results.append({
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
                        "height_wow": round(height_wow, 4) if height_wow is not None else None,
                        "stem_wow": round(stem_wow, 4) if stem_wow is not None else None,
                        "leaves_wow": round(leaves_wow, 4) if leaves_wow is not None else None,
                        "side_buds_wow": round(side_buds_wow, 4) if side_buds_wow is not None else None,
                        "state_desc_en": None,
                        "action_desc_en": None
                    })
                except Exception as e:
                    print(f" -> {model_name} Gemini Vision 解析异常 ({e})，平滑退避到 Mock 模拟器。")
                    results.append(generate_mock_plant_data(model_name, date_str, day_index))
            else:
                results.append(generate_mock_plant_data(model_name, date_str, day_index))
    else:
        # 完全启用数据拟真模拟器，保证系统在开发与没有外设时的完全自运转
        print("未检测到 API 凭证或植物照片，系统自动启用高拟真 Mock 模式。")
        for model_name in MODELS_CONFIG.keys():
            results.append(generate_mock_plant_data(model_name, date_str, day_index))
            
    # 计算今日大局评分排行，并产生吐槽总结
    scores = [r["score"] for r in results]
    highest_model = results[scores.index(max(scores))]["model_name"]
    lowest_model = results[scores.index(min(scores))]["model_name"]
    
    return {
        "date": date_str,
        "day_index": day_index,
        "highest_model": highest_model,
        "lowest_model": lowest_model,
        "models_data": results
    }
