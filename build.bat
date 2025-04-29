@echo off
systeminfo | find "x64-based" > nul
if %errorlevel% equ 0 (
    echo AMD64 Windows Build...
    call .venv\Scripts\activate
    pyinstaller app_amd64.spec --noconfirm
    goto :done
)

systeminfo | find "ARM64-based" > nul
if %errorlevel% equ 0 (
    echo ARM64 Windows Build...
    call .venv\Scripts\activate
    pyinstaller app_arm64.spec --noconfirm
    goto :done
)

echo Unsupported architecture.
exit /b 1

:done
echo.
echo Build completed.
echo DuckPrompt.exe can be found in the dist/DuckPrompt folder.
echo.
