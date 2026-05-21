import os
import sys

# 定位基础项目目录 - 升级为识别根目录 (tools/ 的父级)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(BASE_DIR)
sys.path.append(CURRENT_DIR) # 同时把 tools/ 加入环境，方便导入 gen_today_prompts

db_path = os.path.join(BASE_DIR, "database", "sandbox.db")

print("==================================================")
print("🧹 🪐 硅基沙盒 (Silicon Sandbox) - 数据库重置与 Day 1 初始化工具")
print("==================================================")

# 1. 物理删除/置空数据库文件
try:
    if os.path.exists(db_path):
        # 尝试关闭所有 SQLite 可能的连接
        import gc
        gc.collect()
        os.remove(db_path)
        print("✅ 成功彻底物理删除旧的 database/sandbox.db")
    else:
        print("ℹ️ 未检测到 database/sandbox.db 实体文件，无需删除。")
except Exception as e:
    print(f"⚠️ 无法直接删除数据库文件（可能被其他进程占用）：{e}")
    print("🔄 正在尝试物理截断置空 0 字节模式降级重置...")
    try:
        with open(db_path, "wb") as f:
            f.truncate(0)
        print("✅ 成功物理截断/清空 database/sandbox.db")
    except Exception as e2:
        print(f"❌ 物理置空失败: {e2}")

# 2. 重新初始化数据库结构
print("\n🏗️ 正在重新初始化 SQLite 数据库表结构...")
try:
    from database.db_manager import init_db
    init_db()
    print("✅ 数据库表结构重新构建升级完成！")
except Exception as e:
    print(f"❌ 初始化表结构失败: {e}")
    sys.exit(1)

# 3. 生成 Day 1 的 AI 囚徒专属 Prompt
print("\n🚀 正在为您一键装配今日 Day 1 的 AI 囚徒专属 Prompt...")
try:
    import gen_today_prompts
    # 重置下 available dates 的缓存或者直接执行
    gen_today_prompts.main()
    print("\n🎉 Day 1 专属完全体 Prompt 已成功一键生成！")
except Exception as e:
    print(f"❌ 生成 Prompt 失败: {e}")
    sys.exit(1)

print("==================================================")
