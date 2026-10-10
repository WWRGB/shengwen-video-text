@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo   声文 - 视频语音提取与转文字
echo ========================================
where python >nul 2>nul
if errorlevel 1 (
  echo 未找到 Python。请先安装 Python 3.10 或 3.11 64位，并勾选 Add Python to PATH。
  pause
  exit /b 1
)
echo 正在检查并安装所需组件（首次运行需要联网）...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo 依赖安装失败，请检查网络或 Python 环境后重试。
  pause
  exit /b 1
)
echo 正在启动声文...
python main.py
if errorlevel 1 (
  echo.
  echo 程序已退出。请检查上方错误信息。
  pause
)
