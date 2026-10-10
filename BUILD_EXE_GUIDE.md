# 声文 · Windows 云端编译

## 替换现有版本
1. 下载本项目 ZIP 并解压。
2. 在现有 GitHub 仓库根目录替换 `main.py`、`README.md` 和 `requirements.txt`。
3. 确认 `.github/workflows/build-windows.yml` 存在于仓库的这个精确路径，不能放在根目录。
4. 提交更改并打开 GitHub Actions。
5. 等 `Build Shengwen Windows EXE` 显示绿色成功后，在运行详情底部的 Artifacts 下载 `Shengwen-Windows-x64`。
6. 解压下载包并运行 `Shengwen.exe`。

## 第三方在线翻译提示
点击“生成译文（联网）”时，程序会先要求同意向 MyMemory 发送字幕文字。视频与音频不会发送。外部服务可能不可用、限流或不支持某些语言对；翻译失败时原文和原始转写保持不变。

## 测试范围
本源码在构建环境完成语法检查与 GUI 启动冒烟测试。在线翻译以模拟响应测试请求/JSON 解析；这不代表 MyMemory 实时接口始终可用。完整 ASR 质量、实际 Windows EXE 和用户视频的识别准确度尚需在目标电脑实测。
