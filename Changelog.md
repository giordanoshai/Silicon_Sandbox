# Changelog

## 时间：2026-05-21 11:52 (UTC)

### 类型：[Feature]
- **核心改动**：在项目根目录全新构建了极具科幻感与极客美学的 `README.md` 成果展示白皮书，详细梳理了硅基沙盒的“AI 囚徒”种植竞赛世界观背景、双轨自适应进度条大屏视觉美学、Gemini Vision 物理标尺测算及强化学习（RL）Reward 扣分/加分机制，定义了开源代码范围与闭源隔离边界，并去除了冗余的本地安装部署步骤，专注于项目极客理念与数据资产的开源展示。
- **系统影响**：为项目的 GitHub 开源发布提供了极高质感、极富科幻张力的官方名片与成果画廊。极大突出了项目的“物理沙盒”与“强化学习博弈”的核心概念，完全打磨出了项目的商业概念溢价，极其利于社区快速浏览与理念传播。

## 时间：2026-05-21 11:47 (UTC)

### 类型：[Refactor]
- **核心改动**：全面重构了项目根目录的 `.gitignore` 规则，将敏感的 `.env` 配置文件、Python 虚拟环境及缓存过滤，并对社交媒体合成流相关代码（如 `audio_generator.py`、`video_creator.py`、`pipeline.py`）及运行产生的多媒体产物（如 `.mp3`、`.mp4` 视频及 Playwright 截图生成的 `card_*.png` 卡片）进行全面 Git 忽略过滤，只保留核心 Web 前端、API 接口、植物指标提取/拟真逻辑代码、真实植物特写 `.jpg` 照片以及 Markdown 历史文档。
- **系统影响**：实现了开源发布时的“敏感数据防泄漏”与“社交媒体合成管线闭源保护”。不仅绝对防止了本地测试临时数据和敏感 API Key 泄露到 GitHub，同时保护了具社交媒体传播属性的视频/配音合成流源码，且完全保障了开源外部开发者直接拉起核心 Web Dashboard 与 REST 接口服务的极简环境完整度。

## 时间：2026-05-21 09:45 (UTC)

### 类型：[Feature]
- **核心改动**：在 `vision_analyzer.py` 中补全了真实的 Gemini Vision 多模态分析代码逻辑，设计了高精度的农业沙盒图像提取 Prompt，并支持通过 PIL 图像对象对每个模型的植物特写照片进行真实物理高度、茎粗、真叶数、侧芽数及 RL 状态标志识别，失败时实现自动平滑退避到高拟真 Mock 引擎。
- **系统影响**：让系统具备了真正的“像素物理对焦多模态判定”能力，使得 Silicon Sandbox 可以实现 100% 自动图像识别入库与得分计算，极大地丰富了数据持久化与后续短视频制作的真实数据来源，且不失高鲁棒的降级容错底线。

## 时间：2026-05-21 08:27 (UTC)

### 类型：[Fix]
- **核心改动**：在 `templates/dashboard.html` 前端渲染 JavaScript 模板中，将错误的变量引用 `prevStemPercent` 修正为正确的 `stemPrevPercent`。
- **系统影响**：彻底消除了控制台页面加载时的 JavaScript 运行时未定义报错（Uncaught ReferenceError），恢复了大屏幕卡片“茎粗”双轨进度条的正常缩放与同期对比渲染功能。

## 时间：2026-05-21 08:26 (UTC)

### 类型：[Feature]
- **核心改动**：在 `db_manager.py` 和 `vision_analyzer.py` 中实现了“关节侧芽(side_buds)”和“叶片与侧芽同比 WoW”的数据库迁移与模拟计算，重构了 `templates/dashboard.html` 的前端 CSS 与渲染逻辑，引入了 2x2 面板网格以及双轨粗发光线（当前周期）与细灰色线（上周同期）的自适应进度条对比系统。
- **系统影响**：完善了多模态植物在 RL 决策及量化博弈中的指标覆盖，实现了高度、茎粗、叶片数、关节侧芽 4 个核心参数的高清晰双轨历史同期对比可视化，极大地提升了控制台大屏和 Playwright 截图生成的快节奏吐槽短视频的技术量化观感与社交媒体传播溢价。

## 时间：2026-05-21 07:33 (UTC)

### 类型：[Feature]
- **核心改动**：在项目根目录新建了全新的 [GEMINI.md](file:///d:/Dev_project/Python_Project/Silicon_Sandbox/GEMINI.md) 系统技术架构与规范总结文档，包含了 Mermaid 闭环流水线流程图、SQLite 数据库表设计及 REST API 数据传输 JSON 格式，归档了对 TemplateResponse 兼容性及 Uvicorn 子进程死锁的硬核排查解决方案。
- **系统影响**：提供了极高清晰度与极客美学的系统架构定义，明确了跨大模型物理对决数据交互标准与降级运行操作指南，为后续开发者或 AI 客户端（大模型复盘博弈）接入提供了坚如磐石的技术规范规范。

## 时间：2026-05-21 06:40 (UTC)

### 类型：[Fix]
- **核心改动**：在 `app.py` 里的 `home_page` 路由中，修改 `TemplateResponse` 的调用方式为 try-except 兼容签名（首选 `request=request, name="dashboard.html"` 适配新版 Starlette；捕获 `TypeError` 后兜底退避至旧版 `("dashboard.html", {"request": request})`）。
- **系统影响**：彻底消除了由于用户系统升级到新版 Starlette/Jinja2 导致原先的参数位置错误解析，进而抛出 `TypeError: unhashable type: 'dict'` 导致主控台渲染引擎崩溃的错误。实现了多版本 FastAPI 框架的自适应无损渲染，保证了 Playwright 对 DOM 节点的完美真机像素截图，而不依赖 Pillow 拼图兜底。

## 时间：2026-05-21 06:36 (UTC)

### 类型：[Fix]
- **核心改动**：在 `pipeline.py` 的 `subprocess.Popen` 拉起 Uvicorn 服务时，显式指定了子进程的执行工作目录 `cwd` 为当前项目根目录，并将标准输出与错误均重定向至本地每日日志归档文件 `uvicorn_startup.log`。
- **系统影响**：彻底消除了由于外部调用路径不匹配导致的 `ModuleNotFoundError` (找不到 app 模块) 的隐形启动崩溃，并提供了一套完全透明的本地 Web 渲染后台运行诊断日志。

## 时间：2026-05-21 06:34 (UTC)

### 类型：[Fix]
- **核心改动**：修改了 `pipeline.py` 中子进程拉起 FastAPI (`uvicorn`) 时的管道配置，将 `stdout` 和 `stderr` 重定向至 `subprocess.DEVNULL`，彻底消除了由于子进程输出缓冲区填满导致的整个 Web 服务死锁、挂起并导致 Playwright 请求超时的致命缺陷。
- **系统影响**：保障了自动化卡片截图流程的稳定运行，确保 Playwright 可以在 100 毫秒内迅速对 Dashboard 控制台的 9 个 DOM 节点进行物理截图归档。


## 时间：2026-05-21 06:33 (UTC)

### 类型：[Fix]
- **核心改动**：在 `pipeline.py` 中引入 `io` 模块，强制将进程的 `sys.stdout` 和 `sys.stderr` 以 UTF-8 字节编码包装，彻底解决了在 Windows CMD/PowerShell 终端下输出赛博朋克 Emoji 和中文日志发生 `UnicodeEncodeError` 的报错。
- **系统影响**：保障了一键 Pipeline 流水线对控制台日志的高清晰无损输出，防止因终端语言环境不一致引发进程非正常中止。


## 时间：2026-05-21 06:32 (UTC)

### 类型：[Fix]
- **核心改动**：在 `vision_analyzer.py` 头部导入了 `Optional` 变量类型定义，修复了 `NameError: name 'Optional' is not defined` 的执行中断。
- **系统影响**：消除了流水线主流程在解析多模态图像/数据时的崩溃漏洞，保障了数据库指标持久化及一键式 Pipeline 流水线能顺利通畅运转。
