# 🚀 Deployment Guide

## Pre-Deployment Checklist

- [ ] Raspberry Pi OS installed (32-bit or 64-bit)
- [ ] SSH access configured
- [ ] Internet connection available
- [ ] All hardware assembled and tested
- [ ] GPIO pins verified
- [ ] Gmail app password generated

## Step-by-Step Deployment

### 1. Update System

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### 2. Install System Dependencies

```bash
# Python development tools
sudo apt-get install -y python3-pip python3-venv python3-dev

# Camera support
sudo apt-get install -y libatlas-base-dev libjasper-dev libtiff5 libjasper1 libharfbuzz0b libwebp6 libtiff5 libjasper1 libharfbuzz0b libwebp6 libopenjp2-7 libtiff5

# Build tools (for compiling some packages)
sudo apt-get install -y build-essential cmake git

# GPIO access
sudo usermod -a -G gpio pi
```

### 3. Create Project Directory

```bash
mkdir -p ~/robot_pigeon
cd ~/robot_pigeon
```

### 4. Clone Repository

```bash
git clone https://github.com/yourusername/robot-pigeon-detection.git .
```

### 5. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 6. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note:** This may take 10-15 minutes on Raspberry Pi 4. Be patient.

### 7. Configure Robot

```bash
nano config.py
```

Edit the following:

```python
# Email settings
SENDER_EMAIL = "your-email@gmail.com"
SENDER_PASSWORD = "your-app-password"  # Gmail app password
OWNER_EMAIL = "your-email@gmail.com"

# Paths
MODEL_PATH = "/home/pi/robot_pigeon/best_int8.tflite"
LOG_FILE = "/home/pi/robot_pigeon/robot.log"

# GPIO Pins (if different from default)
IR_LEFT = 17
IR_CENTER = 27
IR_RIGHT = 22
```

### 8. Enable Camera Interface

```bash
sudo raspi-config
```

Navigate to:
- **Interface Options** → **Camera** → **Enable**
- Then reboot:

```bash
sudo reboot
```

### 9. Test Hardware

After reboot, test all components:

```bash
cd ~/robot_pigeon
source venv/bin/activate
python3 test_hardware.py
```

Expected output:
```
✓ GPIO Access: PASS
✓ IR Sensors: PASS
✓ Ultrasonic Sensor: PASS
✓ Motors: PASS
✓ Buzzer: PASS
✓ Camera: PASS
✓ YOLO Model: PASS
✓ Email Configuration: PASS

Passed: 8/8
```

### 10. Calibrate IR Sensors

```bash
python3 calibrate.py
```

Select option 1 (IR Sensors) and adjust sensor sensitivity if needed.

## Running the Robot

### Manual Start

```bash
cd ~/robot_pigeon
source venv/bin/activate
python3 robot_main.py
```

### Systemd Service (Auto-start on Boot)

#### Create Service File

```bash
sudo nano /etc/systemd/system/robot-pigeon.service
```

Paste:

```ini
[Unit]
Description=Pigeon Detection Robot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/robot_pigeon
ExecStart=/home/pi/robot_pigeon/venv/bin/python3 /home/pi/robot_pigeon/robot_main.py
Restart=always
RestartSec=10
StandardOutput=append:/home/pi/robot_pigeon/service.log
StandardError=append:/home/pi/robot_pigeon/service.log

[Install]
WantedBy=multi-user.target
```

#### Enable Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable robot-pigeon.service
sudo systemctl start robot-pigeon.service
```

#### Monitor Service

```bash
# Check status
sudo systemctl status robot-pigeon.service

# View logs
tail -f /home/pi/robot_pigeon/service.log

# Stop service
sudo systemctl stop robot-pigeon.service

# Restart service
sudo systemctl restart robot-pigeon.service
```

## Remote Access

### SSH Access

```bash
# From your computer
ssh pi@192.168.x.x
```

### View Logs Remotely

```bash
ssh pi@192.168.x.x "tail -f /home/pi/robot_pigeon/robot.log"
```

### Copy Logs Locally

```bash
scp pi@192.168.x.x:/home/pi/robot_pigeon/robot.log ./robot.log
```

## Optimization Tips

### Improve Performance

```python
# In config.py, increase speed for faster operation:
BASE_SPEED = 25  # Default: 15
MOVEMENT_TIME = 5  # Default: 3
```

### Reduce CPU Usage

```python
# Disable email alerts if not needed:
ENABLE_EMAIL_ALERTS = False

# Reduce camera detection frequency:
STOP_TIME = 3  # Default: 5
```

### Better Stability

```python
# Increase smooth transition time:
SMOOTH_TRANSITION_TIME = 0.2  # Default: 0.1

# Increase sensor debounce:
IR_SENSOR_DEBOUNCE = 50  # Default: 20
```

## Backup & Recovery

### Backup Configuration

```bash
cd ~/robot_pigeon
tar -czf backup-$(date +%Y%m%d).tar.gz config.py
```

### Backup Logs

```bash
tar -czf logs-$(date +%Y%m%d).tar.gz robot.log
```

### Restore from Backup

```bash
tar -xzf backup-20260518.tar.gz
```

## Troubleshooting Deployment

### Import Errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### GPIO Permission Issues

```bash
# Add user to GPIO group
sudo usermod -a -G gpio pi

# Then reboot
sudo reboot
```

### Camera Not Working

```bash
# Check camera connection
vcgencmd get_camera

# Enable via raspi-config
sudo raspi-config
```

### Model Loading Slow

- First load takes 10-30 seconds (normal)
- Subsequent loads are faster
- Consider running on boot to pre-load model

## Performance Monitoring

### Check CPU Temperature

```bash
vcgencmd measure_temp
```

### Monitor CPU/Memory Usage

```bash
top
# or
watch -n 1 'free -h && ps aux | grep python'
```

### Check Disk Space

```bash
df -h
```

## Security Hardening

### Disable SSH Password Login

```bash
# Generate SSH key on your computer
ssh-keygen -t rsa -b 4096

# Copy to Pi
ssh-copy-id pi@192.168.x.x

# Disable password login
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no

sudo systemctl restart ssh
```

### Firewall Setup

```bash
sudo apt-get install -y ufw
sudo ufw enable
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP (if needed)
```

## Maintenance

### Regular Tasks

**Weekly:**
- Check log file size
- Verify robot is detecting properly
- Check email alerts

**Monthly:**
- Update system packages
- Clean logs if over 5MB
- Backup configuration

**Quarterly:**
- Full system update
- Camera lens cleaning
- Sensor calibration

### Log Rotation

Logs rotate automatically when reaching 5MB. Old logs are kept as backups:
- `robot.log` - Current log
- `robot.log.1` - Previous log
- `robot.log.2` - Older logs (up to 5 backups)

### Clean Old Logs

```bash
# Remove logs older than 30 days
find ~/robot_pigeon -name "robot.log.*" -mtime +30 -delete
```

## Uninstallation

```bash
# Stop service
sudo systemctl stop robot-pigeon.service
sudo systemctl disable robot-pigeon.service

# Remove service file
sudo rm /etc/systemd/system/robot-pigeon.service

# Remove project directory
rm -rf ~/robot_pigeon
```

## Next Steps

1. ✅ Deployment complete
2. 📊 Monitor logs for proper operation
3. 🔧 Fine-tune parameters in `config.py`
4. 📧 Verify email alerts are working
5. 🎯 Deploy to autonomous operation

---

**Questions?** Check README.md or enable DEBUG logging for detailed output.
