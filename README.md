# 🤖 Enhanced Pigeon Detection Robot

A production-ready Raspberry Pi-based autonomous robot system with **line-following capability**, **obstacle avoidance**, and **AI-powered pigeon detection** using YOLO.

## 📋 Features

### Core Functionality
- ✅ **Autonomous Line Following** - Uses 3 IR sensors for precise path tracking
- ✅ **Obstacle Detection** - Ultrasonic sensor with 20cm safety threshold
- ✅ **Pigeon Detection** - YOLO-based AI detection with confidence scoring
- ✅ **Smart Alerts** - Email notifications for events (rate-limited)
- ✅ **Smooth Motor Control** - Adaptive acceleration/deceleration

### System Enhancements
- 🔧 **Comprehensive Logging** - File + console logging with rotation
- 📊 **Performance Statistics** - Track runtime, detections, and events
- ⚙️ **Centralized Configuration** - Easy parameter tuning via `config.py`
- 🛡️ **Error Handling** - Robust try-catch blocks throughout
- 🧪 **Hardware Testing Tools** - Calibration and diagnostic utilities
- 🔄 **Graceful Shutdown** - Safe resource cleanup on exit

## 🔧 Hardware Requirements

### Raspberry Pi
- Raspberry Pi 3/4/5
- 16GB+ microSD card
- Power supply (2.5A+ for Pi 4)

### Sensors & Actuators
- **IR Line Sensors** (3x) - Digital input
- **Ultrasonic Distance Sensor** - GPIO pins 5 (TRIG), 6 (ECHO)
- **DC Motors** (4x) - PWM controlled via GPIO
- **Buzzer** - GPIO pin 26
- **Camera Module** - CSI ribbon cable

### GPIO Pin Configuration
```
IR Sensors:
- IR_LEFT: 17
- IR_CENTER: 27
- IR_RIGHT: 22

Motors (Left):
- L_RPWM: 18, L_LPWM: 23
- L_R_EN: 24, L_L_EN: 25

Motors (Right):
- R_RPWM: 12, R_LPWM: 16
- R_R_EN: 20, R_L_EN: 21

Sensors:
- BUZZER: 26
- TRIG_FRONT: 5
- ECHO_FRONT: 6
```

## 📦 Installation

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/robot-pigeon-detection.git
cd robot-pigeon-detection
```

### 2. Setup Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Enable GPIO Access
```bash
sudo usermod -a -G gpio pi
sudo reboot
```

### 5. Enable Camera
```bash
sudo raspi-config
# Navigate to: Interface Options → Camera → Enable
```

### 6. Configure Settings
Edit `config.py`:
```python
# Your email (Gmail with app password)
SENDER_EMAIL = "your-email@gmail.com"
SENDER_PASSWORD = "your-app-password"
OWNER_EMAIL = "recipient@gmail.com"

# Adjust for your robot
BASE_SPEED = 15  # Motor speed 0-100
MOVEMENT_TIME = 3  # Seconds to follow line
STOP_TIME = 5  # Seconds to detect pigeons
```

## 🚀 Usage

### Test Hardware First
```bash
python3 test_hardware.py
```

### Calibrate IR Sensors
```bash
python3 calibrate.py
# Select option 1, place robot on line
# Adjust sensor position/gain for optimal readings
```

### Run Robot
```bash
python3 robot_main.py
```

To stop: Press `Ctrl+C`

## 📊 Logs & Statistics

Logs are saved to:
```bash
/home/pi/robot_pigeon/robot.log
```

View real-time logs:
```bash
tail -f /home/pi/robot_pigeon/robot.log
```

Statistics are printed on shutdown:
```
Robot Statistics:
- Runtime: 3600s
- Pigeons Detected: 5
- Obstacles Detected: 2
- Line Losses: 1
- Emails Sent: 8
```

## ⚙️ Configuration

### Performance Tuning

**Line Following Speed**
```python
BASE_SPEED = 15  # 0-100 PWM
```

**Motor Responsiveness**
```python
SMOOTH_TRANSITION_TIME = 0.1  # Acceleration time (seconds)
```

**Sensor Thresholds**
```python
OBSTACLE_DISTANCE_THRESHOLD = 20  # cm
CONFIDENCE_THRESHOLD = 0.4  # YOLO confidence
```

**Timing**
```python
MOVEMENT_TIME = 3  # Follow line duration
STOP_TIME = 5  # Detection phase duration
```

### Email Alerts

**Setup Gmail App Password:**
1. Enable 2-Factor Authentication on Gmail
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Select "Mail" and "Windows Computer"
4. Copy the generated password to `config.py`

**Rate Limiting**
```python
EMAIL_RATE_LIMIT = 60  # Seconds between alerts of same type
```

## 🐛 Troubleshooting

### GPIO Permission Denied
```bash
sudo usermod -a -G gpio pi
sudo reboot
```

### Camera Not Found
```bash
# Enable camera interface
sudo raspi-config
# Then reboot
sudo reboot
```

### IR Sensors Always Return 0
- Check sensor connections
- Verify GPIO pins in `config.py`
- Adjust sensor sensitivity with potentiometer
- Use calibration tool: `python3 calibrate.py`

### No Distance Reading
- Check ultrasonic sensor connections
- Verify pins TRIG (5) and ECHO (6)
- Test with: `python3 calibrate.py` (option 2)

### Email Not Sending
- Verify Gmail app password (not regular password)
- Enable "Less secure app access"
- Check internet connection
- Verify email addresses in `config.py`

### Motors Not Spinning
- Check motor connections
- Verify GPIO pins in `config.py`
- Check motor power supply (4.5V-6V recommended)
- Test with `python3 test_hardware.py`

## 📈 Performance Optimization

### For Faster Line Following
```python
BASE_SPEED = 25  # Increase speed
MOVEMENT_TIME = 5  # Longer movement phase
```

### For Better Pigeon Detection
```python
STOP_TIME = 10  # Longer detection phase
CONFIDENCE_THRESHOLD = 0.3  # Lower confidence threshold
```

### For More Stable Movement
```python
SMOOTH_TRANSITION_TIME = 0.2  # Longer acceleration
```

## 📝 File Structure

```
robot-pigeon-detection/
├── robot_main.py          # Main robot system
├── config.py              # Configuration file
├── calibrate.py           # Calibration tool
├── test_hardware.py       # Hardware testing
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── DEPLOYMENT.md          # Deployment guide
└── robot.log              # Runtime logs
```

## 🔍 System Architecture

```
Main Loop:
  ├─ MOVEMENT PHASE (3 seconds)
  │  ├─ Read IR sensors
  │  ├─ Measure distance
  │  ├─ Avoid obstacles
  │  └─ Control motors
  │
  └─ STOP PHASE (5 seconds)
     ├─ Capture camera frame
     ├─ Run YOLO detection
     ├─ Send alerts if pigeons found
     └─ Display results
```

## 📧 Email Alerts

**Obstacle Detection**
- Triggered when object < 20cm away
- Rate limited to 1 per 60 seconds
- Includes distance measurement

**Line Loss**
- Triggered when all IR sensors read 0
- Rate limited to 1 per 60 seconds
- Includes robot statistics

**Pigeon Detection**
- Triggered when YOLO detects objects
- Includes number of detections
- Average confidence score

## 🛡️ Safety Features

- **Emergency Stop** - Ctrl+C triggers graceful shutdown
- **Motor Limits** - PWM clamped to 0-100
- **Timeout Protection** - Ultrasonic sensor has 50ms timeout
- **Rate Limiting** - Email alerts throttled to prevent flooding
- **Sensor Debouncing** - IR sensors validated
- **Error Recovery** - Try-catch blocks throughout

## 📚 Advanced Features

### Statistics Tracking
The system tracks:
- Total runtime
- Pigeons detected count
- Obstacles detected count
- Line losses count
- Emails sent count

### Logging Levels
```python
LOG_LEVEL = "DEBUG"    # Verbose output
LOG_LEVEL = "INFO"     # Normal operation
LOG_LEVEL = "WARNING"  # Only warnings/errors
LOG_LEVEL = "ERROR"    # Only errors
```

### Runtime Limits
```python
MAX_RUNTIME = 3600  # Stop after 1 hour (0 = unlimited)
```

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 👨‍💻 Author

Mohamed Amir - Robot Development

## 🙏 Acknowledgments

- YOLO/Ultralytics for object detection
- Raspberry Pi Foundation
- OpenCV community

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs: `tail -f robot.log`
3. Run hardware tests: `python3 test_hardware.py`
4. Open an issue on GitHub

---

**Last Updated:** 2026-05-18  
**Version:** 2.0 (Production Ready)
