@echo off
rem Lenh video-editor tren Windows. Can Python 3.9+ (python.org hoac winget install Python.Python.3.12).
set "DIR=%~dp0.."
where py >nul 2>nul && (py -3 "%DIR%\ve\cli.py" %*) || (python "%DIR%\ve\cli.py" %*)
