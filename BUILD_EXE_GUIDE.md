# Windows EXE 云端打包指南（无需本机安装 Python）

## 目标
GitHub Actions 在 Windows 云端构建 `Shengwen.exe`，最终用户不必安装 Python。

## 仓库文件结构
所有程序文件放在仓库根目录，尤其要确保自动编译配置的路径准确：

```text
仓库根目录/
  main.py
  requirements.txt
  README.md
  run.bat
  .github/
    workflows/
      build-windows.yml
```

## 更新现有仓库
如仓库已经创建并有旧版本，只需替换根目录的 `main.py` 并提交更改。`requirements.txt` 和 `.github/workflows/build-windows.yml` 没有变更时可以继续使用原文件。不要把 `.github` 文件夹里的 YAML 放到仓库根目录；它必须位于 `.github/workflows/build-windows.yml`。

## 构建和下载
1. 在仓库的 Actions 页面打开 `Build Shengwen Windows EXE`。
2. 推送到 `main` / `master` 分支会自动触发；也可以在工作流页面点击 Run workflow。
3. 等待 `build` 作业出现绿色对勾。
4. 打开此次运行页面底部的 Artifacts 区域，下载 `Shengwen-Windows-x64`。
5. 解压 ZIP，运行 `Shengwen.exe`。

Artifact 会在一定时间后过期（当前工作流设置为 14 天）；过期后重新运行构建即可再次下载。

## 注意
- 首次识别时需要下载 faster-whisper 模型，需联网。
- 生成带字幕视频需要额外编码时间，输出文件会另存，不覆盖源视频。
- 如果 Windows 安全提示不常见程序，请确认文件来自自己的 GitHub Actions 构建后再决定是否运行。
