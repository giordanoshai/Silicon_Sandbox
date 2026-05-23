import os
import uvicorn
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from PIL import Image, ImageDraw

from database.db_manager import init_db, get_daily_report, get_model_history, get_available_dates, get_chat_plaza_messages

load_dotenv()

app = FastAPI(
    title="Silicon Sandbox API",
    description="硅基沙盒跨界种植竞赛监控中枢 API",
    version="2.0.0"
)

# 确保必要的目录存在
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
PLANT_IMG_DIR = os.path.join(STATIC_DIR, "images", "plants")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

for path in [STATIC_DIR, PLANT_IMG_DIR, LOGS_DIR]:
    if not os.path.exists(path):
        os.makedirs(path)

# 数据库初始化
init_db()

# 自动生成默认的植物特写占位图 (default_plant.png)
DEFAULT_PLANT_PATH = os.path.join(PLANT_IMG_DIR, "default_plant.png")
if not os.path.exists(DEFAULT_PLANT_PATH):
    print("生成默认赛博植物占位图...")
    try:
        # 创建一张 400x300 的深蓝色占位图片，带有赛博霓虹叶片几何线条
        img = Image.new("RGBA", (400, 300), "#090d16")
        draw = ImageDraw.Draw(img)
        # 绘制霓虹外框
        draw.rectangle([10, 10, 390, 290], outline="#1e293b", width=2)
        # 绘制一片几何抽象叶子
        draw.polygon([(200, 50), (280, 150), (200, 250), (120, 150)], outline="#38bdf8", width=3)
        # 绘制网格脉络
        draw.line([(200, 50), (200, 250)], fill="#38bdf8", width=2)
        draw.line([(200, 100), (250, 130)], fill="#818cf8", width=1)
        draw.line([(200, 100), (150, 130)], fill="#818cf8", width=1)
        draw.line([(200, 160), (265, 190)], fill="#818cf8", width=1)
        draw.line([(200, 160), (135, 190)], fill="#818cf8", width=1)
        
        # 写入电子对焦文字
        draw.text((150, 260), "FOCUSING ACTIVE", fill="#a855f7")
        img.save(DEFAULT_PLANT_PATH, "PNG")
    except Exception as e:
        print(f"绘制占位图失败: {e}")

# --- 赛博大屏高可用：支持大小写不敏感的静态文件挂载类 ---
class CaseInsensitiveStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope) -> Response:
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            if exc.status_code == 404:
                # 📷 跨平台兼容降级：针对 Windows 开发环境下文件名首字母大写、但代码/数据库使用小写，
                # 导致在 Linux (Render) 云端部署时因严格区分大小写而触发 404 的经典缺陷，
                # 在 404 时主动在磁盘上进行不区分大小写的文件名精准配对
                from starlette.responses import Response
                full_path = os.path.join(self.directory, path)
                dir_name = os.path.dirname(full_path)
                base_name = os.path.basename(full_path).lower()
                if os.path.exists(dir_name):
                    try:
                        for file in os.listdir(dir_name):
                            if file.lower() == base_name:
                                matched_relative = os.path.join(os.path.dirname(path), file).replace("\\", "/")
                                return await super().get_response(matched_relative, scope)
                    except Exception:
                        pass
            raise exc

# 挂载静态文件目录
app.mount("/static", CaseInsensitiveStaticFiles(directory=STATIC_DIR), name="static")
app.mount("/logs", CaseInsensitiveStaticFiles(directory=LOGS_DIR), name="logs")

# 模板文件目录
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# --- 页面渲染路由 ---

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    """渲染主监控大屏"""
    try:
        return templates.TemplateResponse(request=request, name="dashboard.html")
    except TypeError:
        return templates.TemplateResponse("dashboard.html", {"request": request})

# --- 标准 REST API 路由 ---

@app.get("/api/v1/sandbox/dates", response_class=JSONResponse)
async def api_get_dates():
    """获取所有有记录的日期列表（降序）"""
    dates = get_available_dates()
    return dates

@app.get("/api/v1/sandbox/daily", response_class=JSONResponse)
async def api_daily_report(date: Optional[str] = Query(None, description="要查询的日期，格式 YYYY-MM-DD。若不传，默认返回最新一天的战报")):
    """
    端点 A：获取指定日期的聚合战报数据。
    """
    if not date:
        dates = get_available_dates()
        if not dates:
            raise HTTPException(status_code=404, detail="数据库暂无记录。请先运行流水线生成数据。")
        date = dates[0]
        
    report = get_daily_report(date)
    if not report:
        raise HTTPException(status_code=404, detail=f"未找到日期 {date} 的战报数据。")
        
    return report

@app.get("/api/v1/sandbox/model", response_class=JSONResponse)
async def api_model_history(name: str = Query(..., description="要查询的模型名称，如 Grok 3, Claude 等")):
    """
    端点 B：获取指定模型的所有历史趋势数据，用于模型反复盘。
    """
    # 格式化模型名称
    formatted_name = name.replace("_", " ")
    history = get_model_history(formatted_name)
    if not history:
        # 支持以带有下划线的形式请求，比如 Grok_3 转换为 Grok 3
        # 如果依然查不到，尝试以原始名字查
        history = get_model_history(name)
        if not history:
            raise HTTPException(status_code=404, detail=f"未找到模型 {name} 的历史数据。")
            
    return history

@app.get("/api/v1/sandbox/chat", response_class=JSONResponse)
async def api_chat_plaza(date: Optional[str] = Query(None, description="要查询的日期，格式 YYYY-MM-DD。若不传，返回所有聊天记录")):
    """
    端点 C：获取指定日期的 AI 聊天广场消息。
    """
    if not date:
        # 默认取最新一天
        dates = get_available_dates()
        if dates:
            date = dates[0]
            
    messages = get_chat_plaza_messages(date)
    return messages

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    print(f"正在本地启动沙盒 Web 控制台: http://{host}:{port}")
    uvicorn.run("app:app", host=host, port=port, reload=True)
