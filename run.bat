@echo off
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo 未检测到 Python。若你只想使用软件，请下载 GitHub Actions 生成的 Shengwen-Windows-x64 软件包。
  pause
  exit /b 1
)
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
pause
