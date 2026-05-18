@echo off
REM Raspberry Pi Setup Script for Windows (for manual steps)
REM Use this to document setup steps

echo ===================================================
echo Robot Pigeon Detection - Raspberry Pi Setup Guide
echo ===================================================
echo.
echo Run these commands on your Raspberry Pi:
echo.
echo 1. Update system:
echo    sudo apt-get update
echo    sudo apt-get upgrade -y
echo.
echo 2. Install dependencies:
echo    sudo apt-get install -y python3-pip python3-venv python3-dev build-essential cmake git
echo.
echo 3. Enable GPIO:
echo    sudo usermod -a -G gpio pi
echo.
echo 4. Enable camera (optional):
echo    sudo raspi-config
echo    (Select: Interface Options - Camera - Enable)
echo.
echo 5. Reboot:
echo    sudo reboot
echo.
echo 6. Setup Python:
echo    cd ~/robot_pigeon
echo    python3 -m venv venv
echo    source venv/bin/activate
echo    pip install --upgrade pip
echo    pip install -r requirements-pi.txt
echo.
echo 7. Test hardware:
echo    python3 test_hardware.py
echo.
echo 8. Run robot:
echo    python3 robot_main.py
echo.
echo ===================================================
pause
