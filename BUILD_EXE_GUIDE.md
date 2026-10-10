# 声文：自动生成 Windows EXE

本项目使用 GitHub Actions 的 Windows 云端机器打包。你自己的电脑不需要安装 Python。

## 上传到 GitHub

1. 在 GitHub 创建一个空仓库，例如 `shengwen-video-text`。
2. 解压本 ZIP。
3. 打开解压后的 `视频语音提取工具` 文件夹，全选其中的内容（包括 `.github` 文件夹），上传到 GitHub 仓库根目录。不要把整个 ZIP 文件上传，也不要把外层文件夹作为子目录上传。
4. 点击 **Commit changes** 提交文件。

## 下载生成的程序

1. 打开仓库顶部的 **Actions** 标签。
2. 选择 **Build Shengwen Windows EXE**，等待任务完成。
3. 打开成功的任务页面，在 **Artifacts** 里下载 `Shengwen-Windows-x64`。
4. 解压下载的文件，双击 `Shengwen.exe` 运行。

## 首次使用

第一次语音识别仍需要联网下载语音模型。该云端打包流程尚未在本会话环境中实际运行验证，如构建失败，请查看 Actions 里的报错日志。
