import os

logs_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
logs_dir = os.path.abspath(logs_dir)

print(f"Scanning logs directory: {logs_dir}")

for root, dirs, files in os.walk(logs_dir):
    for file in files:
        if file.endswith(".jpg") or file.endswith(".png") or file.endswith(".mp3") or file.endswith(".mp4"):
            # 检查是否有大写字母
            if any(c.isupper() for c in file):
                old_path = os.path.join(root, file)
                new_path = os.path.join(root, file.lower())
                
                # 为了在 Windows 下安全重命名大小写（Windows 认为 A.jpg 和 a.jpg 相同）
                # 我们必须通过中间临时文件名过渡
                temp_path = old_path + "_temp"
                try:
                    os.rename(old_path, temp_path)
                    os.rename(temp_path, new_path)
                    print(f"Renamed: {file} -> {file.lower()}")
                except Exception as e:
                    print(f"Failed to rename {file}: {e}")
