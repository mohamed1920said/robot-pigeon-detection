# 🍓 Raspberry Pi Setup Guide

## Quick Start (5 minutes)

### 1. SSH into Raspberry Pi

```bash
ssh pi@192.168.x.x
# or
ssh pi@raspberrypi.local
```

### 2. Clone Repository

```bash
git clone https://github.com/yourusername/robot-pigeon-detection.git
cd robot-pigeon-detection
```

### 3. Run Setup Script

```bash
chmod +x setup-pi.sh
./setup-pi.sh
```

**This will:**
- ✅ Update system packages
- ✅ Install system dependencies
- ✅ Enable GPIO access
- ✅ Enable camera
- ✅ Create virtual environment
- ✅ Install Python packages

**Time:** 15-20 minutes

---

## Manual Setup (If Script Fails)

### Step 1: Update System

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### Step 2: Install System Packages

```bash
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
  libwebp6
```

### Step 3: Enable GPIO

```bash
sudo usermod -a -G gpio pi
```

### Step 4: Enable Camera

```bash
sudo raspi-config
```

Navigate to:
- **Interface Options** → **Camera** → **Enable**
- Then reboot: `sudo reboot`

### Step 5: Setup Python

```bash
cd ~/robot-pigeon-detection
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements-pi.txt
```

---

## Configuration

Edit `config.py` for your setup:

```bash
nano config.py
```

Update:
```python
# Email settings (optional)
OWNER_EMAIL = "your-email@gmail.com"
SENDER_EMAIL = "your-email@gmail.com"
SENDER_PASSWORD = "your-app-password"

# Motor speeds
BASE_SPEED = 15  # 0-100

# Timing
MOVEMENT_TIME = 3  # seconds
STOP_TIME = 5  # seconds
```

---

## Testing

### Test Hardware

```bash
source venv/bin/activate
python3 test_hardware.py
```

### Calibrate Sensors

```bash
python3 calibrate.py
```

### Run Robot

```bash
python3 robot_pi.py
```

**Stop with:** `Ctrl+C`

---

## Auto-start on Boot

Create service file:

```bash
sudo nano /etc/systemd/system/robot.service
```

Paste:

```ini
[Unit]
Description=Pigeon Detection Robot
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/robot-pigeon-detection
ExecStart=/home/pi/robot-pigeon-detection/venv/bin/python3 /home/pi/robot-pigeon-detection/robot_pi.py
Restart=always
RestartSec=10
StandardOutput=append:/home/pi/robot-pigeon-detection/robot.log
StandardError=append:/home/pi/robot-pigeon-detection/robot.log

[Install]
WantedBy=multi-user.target
```

Enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable robot.service
sudo systemctl start robot.service
```

**View logs:**

```bash
tail -f robot.log
```

---

## Troubleshooting

### GPIO Permission Denied

```bash
sudo usermod -a -G gpio pi
sudo reboot
```

### Camera Not Working

```bash
# Test camera
vcgencmd get_camera

# Enable via raspi-config
sudo raspi-config
```

### Installation Takes Too Long

Normal! OpenCV compilation takes 15-20 minutes. Be patient.

### Out of Disk Space

```bash
# Check space
df -h

# Cleanup
sudo apt-get clean
```

---

## Monitoring

### View Real-time Logs

```bash
tail -f robot.log
```

### Check Service Status

```bash
sudo systemctl status robot.service
```

### Stop Robot

```bash
sudo systemctl stop robot.service
```

### Restart Robot

```bash
sudo systemctl restart robot.service
```

---

## Performance Tips

### Increase Speed

```python
# In config.py
BASE_SPEED = 25  # Default: 15
MOVEMENT_TIME = 5  # Default: 3
```

### Reduce Power Usage

```python
# Disable email alerts
ENABLE_EMAIL_ALERTS = False

# Reduce detection frequency
STOP_TIME = 2  # Default: 5
```

---

## File Locations

```
/home/pi/robot-pigeon-detection/
├── robot_pi.py           ← Main robot program
├── config.py             ← Configuration
├── robot.log             ← Runtime logs
├── models/
│   └── best.pt          ← YOLO model
├── logs/
│   └── robot.log        ← Detailed logs
└── venv/                ← Python environment
```

---

## Next Steps

1. ✅ Setup complete
2. 🧪 Test hardware: `python3 test_hardware.py`
3. 🔧 Calibrate sensors: `python3 calibrate.py`
4. 🚀 Run robot: `python3 robot_pi.py`
5. 📊 View logs: `tail -f robot.log`

---

**Questions?** Check the main README.md or review logs!
