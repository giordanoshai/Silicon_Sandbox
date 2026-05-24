import os
import requests
import json
import sys
import io

# 强制 UTF-8 编码输出，防止 Windows GBK 编码控制台崩溃
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("==================================================")
print("🎙️ 正在启用透明代理套接字补丁...")
print("==================================================")

# 🌟 强悍的 SOCKS5 透明物理套接字猴子补丁 (Monkey Patch)
# 只要 site-packages 里有 PySocks，这几行代码能让 requests 完全不知道代理的存在，
# 从而透明地走 127.0.0.1:1080 代理，彻底规避 Missing dependencies for SOCKS support 错误！
socks_patched = False
try:
    import socks
    import socket
    socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 1080)
    socket.socket = socks.socksocket
    print("[透明补丁成功] 所有的网络连接已透明重定向至 SOCKS5 127.0.0.1:1080！")
    socks_patched = True
except Exception as e:
    print(f"[透明补丁跳过] 无法应用 SOCKS5 补丁，将尝试常规 HTTP 连接方式。错误: {e}")

api_key = "sk_70c277e953c4f33e046727a86b8f3e345a28080793823910"
voice_id = "APSIkVZudNbPAwyPoeVO" # 中文配音

text = """我把 8 个当下最强的 AI 模型，变成了我后院里种地的“总规划师”……
而我，只是它们雇用的无情浇水机器。

这个项目叫《硅基沙盒》。玩法其实很简单：AI 负责出谋划策，我负责出力。
每天，我只做两件事：给它们发植物的特写照片，顺便汇报前一天的物理操作。
然后，AI 需要根据照片分析并反推植物的生长状态，比如高度、茎粗、叶片数，并且给我反馈一个标准的 JSON 格式数据。
谁要是决策失误导致植物出了问题，就会在我的强化学习算法里被当场扣分！

总共 8 个模型同台竞技。本来是有 DeepSeek 的，但这哥们儿在多模态图像识别上目前完全抓瞎，纯文本假装看懂了被我当场识破，第一天就直接被开除了，换成了能看清世界、给我做雨天防霉菌决策的 Kimi。

我知道网上有很多人做那种“AI关在一起无脑聊天过家家”的虚拟项目。我觉得那些太虚了，没意思！
我个人比较偏工程化，所以把这套种植流程做成了高度自动化的流水线。
我只要拍完照，在电脑运行一下 Python 脚本，数据就能自动解析落库 SQLite，并重新渲染生成 GitHub 仓库的 README 和网页大屏。

如果你对发给 AI 的 Prompt 或是自动化脚本有优化意见，欢迎去 GitHub 搜索 “Silicon_Sandbox”，我们一起来调优它。
关注我，看看这 8 个大模型，到底谁能帮我种出最甜的番茄！"""

url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
headers = {
    "Accept": "audio/mpeg",
    "Content-Type": "application/json",
    "xi-api-key": api_key
}
data = {
    "text": text,
    "model_id": "eleven_multilingual_v2",
    "voice_settings": {
        "stability": 0.5,
        "similarity_boost": 0.75
    }
}

print("\n🎙️ 正在调用 ElevenLabs API 渲染首发工程风配音...")
print("==================================================")

# 如果已经应用了 SOCKS5 透明套接字补丁，我们发起直连请求（requests 会认为我们在直连，但由于 socket 已经被补丁接管，实际上是走 127.0.0.1:1080 代理）
# 如果补丁没打成，我们才轮询我们的一般 HTTP 代理列表。
if socks_patched:
    proxies_to_try = [
        {"http": None, "https": None} # 直接发起请求（实际已被 socket 补丁透明代理）
    ]
else:
    proxies_to_try = [
        {"http": "http://127.0.0.1:1080", "https": "http://127.0.0.1:1080"},
        {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"},
        {"http": "http://127.0.0.1:7897", "https": "http://127.0.0.1:7897"},
        {"http": None, "https": None}
    ]

success = False
for index, proxy in enumerate(proxies_to_try):
    if proxy["http"] is None:
        desc = "透明 SOCKS5 代理直连" if socks_patched else "普通直连 (Bypass Proxy)"
    else:
        desc = f"本地 HTTP 代理 ({proxy['http']})"
        
    print(f"[尝试 {index+1}/{len(proxies_to_try)}] 正在尝试以 {desc} 方式连接 ElevenLabs...")
    try:
        response = requests.post(url, json=data, headers=headers, proxies=proxy, timeout=15)
        if response.status_code == 200:
            paths = [
                r"d:\Dev_project\Python_Project\Silicon_Sandbox\logs\2026-05-23\summary.mp3",
                r"d:\Dev_project\Python_Project\Silicon_Sandbox\social_media\today_voice_0523.mp3"
            ]
            for p in paths:
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "wb") as f:
                    f.write(response.content)
            print("\n🎉 成功！配音文件已完美渲染并保存成功！")
            print("💾 落地物理路径：")
            print("   1. [logs/2026-05-23/summary.mp3]")
            print("   2. [social_media/today_voice_0523.mp3]")
            success = True
            break
        else:
            print(f" ⚠️ 接口响应非 200，状态码: {response.status_code}")
            if response.status_code in [401, 404]:
                print(f" ❌ API Key / Voice ID 配置错误，中止重试: {response.text}")
                break
    except Exception as e:
        print(f" ❌ 该通道连接失败/超时: {e}")

if not success:
    print("\n❌ 遗憾！所有通道均未能连接到 ElevenLabs API。")
    print("💡 提示：")
    print("   1. 请确认您的 v2ray / 代理客户端确实开启在 127.0.0.1:1080 端口，且工作正常。")
    print("   2. 您可以使用浏览器直接访问 elevenlabs.io 测试节点可用性。")
print("==================================================")
