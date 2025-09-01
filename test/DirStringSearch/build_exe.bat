@echo off
REM Build single-file EXE without console window
py -m pip install --upgrade pip
py -m pip install pyinstaller
py -m PyInstaller --onefile --noconsole --name DirStringSearch dirgrep_app.py
echo.
echo Build finished. Check the "dist" folder for DirStringSearch.exe.
pause
