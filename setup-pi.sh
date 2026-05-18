#!/bin/bash
# Raspberry Pi Setup Script
# Run this on your Raspberry Pi to set everything up

echo "====================================================="
echo "Robot Pigeon Detection - Raspberry Pi Setup"
echo "====================================================="

# Step 1: Update system
echo ""
echo "[1/6] Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Step 2: Install system dependencies
echo ""
echo "[2/6] Installing system dependencies..."
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    cmake \
    git \
    libatlas-base-dev \
    libjasper-dev \
    libtiff5 \
    libopenjp2-7 \
    libharfbuzz0b \
    libwebp6 \
    libjasper1

# Step 3: Enable GPIO access
echo ""
echo "[3/6] Configuring GPIO access..."
sudo usermod -a -G gpio $(whoami)
echo "User added to GPIO group (reboot required)"

# Step 4: Enable camera
echo ""
echo "[4/6] Enabling camera interface..."
sudo raspi-config nonint do_camera 0
echo "Camera enabled (reboot required)"

# Step 5: Create virtual environment
echo ""
echo "[5/6] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Step 6: Install Python dependencies
echo ""
echo "[6/6] Installing Python dependencies (this may take 15-20 minutes)..."
pip install --upgrade pip setuptools wheel
pip install -r requirements-pi.txt

echo ""
echo "====================================================="
echo "✅ Setup complete!"
echo "====================================================="
echo ""
echo "Next steps:"
echo "  1. Reboot: sudo reboot"
echo "  2. Test hardware: python3 test_hardware.py"
echo "  3. Calibrate sensors: python3 calibrate.py"
echo "  4. Run robot: python3 robot_main.py"
echo ""
echo "For auto-start on boot, see DEPLOYMENT.md"
echo "====================================================="
