# -*- coding: utf-8 -*-
"""
Robot Configuration File - Raspberry Pi 5 with Arduino
Centralized settings for easy tuning
"""

from pathlib import Path

# ===========================
# PROJECT PATHS (Relative)
# ===========================
PROJECT_DIR = Path(__file__).parent
MODELS_DIR = PROJECT_DIR / "models"
LOGS_DIR = PROJECT_DIR / "logs"

# Create directories if they don't exist
MODELS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# ===========================
# MODEL SETTINGS
# ===========================
MODEL_PATH = str(MODELS_DIR / "best.pt")  # PyTorch model
IMAGE_SIZE = 640
CONFIDENCE_THRESHOLD = 0.5
MIN_DETECTION_COOLDOWN = 30  # seconds between alerts

# ===========================
# CAMERA SETTINGS
# ===========================
CAMERA_TYPE = "droidcam"  # Options: "xiaomi_http", "xiaomi_rtsp", "droidcam", "usb", "local", "test"

# DroidCam iPhone Settings
DROIDCAM_IP = "192.168.1.47"
DROIDCAM_PORT = 4747
DROIDCAM_TIMEOUT = 5  # seconds

# Camera URL for DroidCam - CORRECT ENDPOINT: /video
# Returns: multipart/x-mixed-replace with MJPEG stream
DROIDCAM_URL = f"http://{DROIDCAM_IP}:{DROIDCAM_PORT}/video"

# Local Camera Settings (backup)
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30
CAMERA_INDEX = 0  # Pi CSI camera (change to 19+ if USB camera)

# ===========================
# ARDUINO SETTINGS
# ===========================
ARDUINO_PORT = "/dev/ttyACM1"  # ✅ Arduino Uno detected on this port
ARDUINO_BAUD = 115200

# ===========================
# MOTOR SETTINGS (via Arduino)
# ===========================
BASE_SPEED = 200  # 0-255
MAX_SPEED = 255
MIN_SPEED = 50
ACCELERATION_RATE = 5
DECELERATION_RATE = 8

# Motor timing
MOVEMENT_TIME = 3  # seconds
STOP_TIME = 5  # seconds
SMOOTH_TRANSITION_TIME = 0.1  # seconds

# ===========================
# SENSOR SETTINGS
# ===========================
OBSTACLE_THRESHOLD = 20.0  # cm - obstacle detection threshold
ULTRASONIC_TIMEOUT = 0.03  # 30ms
IR_SENSOR_DEBOUNCE = 20  # milliseconds

# ===========================
# ARDUINO PIN CONFIGURATION
# ===========================

# Ultrasonic Sensors (4 on Arduino)
SR04_FRONT_TRIG = 12
SR04_FRONT_ECHO = 0  # A0
SR04_LEFT_TRIG = 11
SR04_LEFT_ECHO = 1  # A1
SR04_RIGHT_TRIG = 2  # A2
SR04_RIGHT_ECHO = 3  # A3
SR04_BACK_TRIG = 4  # A4
SR04_BACK_ECHO = 5  # A5

# Aliases for backward compatibility with test_hardware.py
TRIG_FRONT = SR04_FRONT_TRIG
ECHO_FRONT = SR04_FRONT_ECHO

# Left Motor (BTS7960 Driver)
L_RPWM = 3    # PWM
L_LPWM = 5    # PWM
L_R_EN = 2    # Enable
L_L_EN = 4    # Enable

# Right Motor (BTS7960 Driver)
R_RPWM = 9    # PWM
R_LPWM = 10   # PWM
R_R_EN = 7    # Enable
R_L_EN = 8    # Enable

# Relay
RELAY_PIN = 13

# ===========================
# RASPBERRY PI GPIO SETTINGS
# ===========================

# IR Line Sensors (on Pi GPIO)
IR_LEFT = 17
IR_CENTER = 27
IR_RIGHT = 22

# Buzzer (Pi GPIO)
BUZZER = 26

# ===========================
# EMAIL SETTINGS (Optional)
# ===========================
OWNER_EMAIL = "your-email@gmail.com"
SENDER_EMAIL = "your-email@gmail.com"
SENDER_PASSWORD = "your-app-password"  # Use Gmail App Password
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

EMAIL_RATE_LIMIT = 60  # seconds between alerts
ENABLE_EMAIL_ALERTS = False

# ===========================
# LOGGING SETTINGS
# ===========================
LOG_FILE = str(LOGS_DIR / "robot.log")
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_MAX_BYTES = 5 * 1024 * 1024  # 5MB
LOG_BACKUP_COUNT = 5

# ===========================
# DISPLAY SETTINGS
# ===========================
SHOW_OUTPUT = True  # Show video window

# ===========================
# SYSTEM SETTINGS
# ===========================
MAX_RUNTIME = 3600  # seconds (0 = unlimited)
ENABLE_WATCHDOG = True
WATCHDOG_TIMEOUT = 30  # seconds

# ===========================
# OPERATION MODES
# ===========================
OPERATION_MODES = {
    "AUTO": "Autonomous pigeon detection and tracking",
    "MANUAL": "Keyboard-controlled movement",
    "TEST": "Hardware testing mode"
}
DEFAULT_MODE = "AUTO"

# ===========================
# DEBUG MODE
# ===========================
DEBUG_MODE = False
VERBOSE = True

# ===========================
# VERIFICATION
# ===========================
if __name__ == "__main__":
    print(f"✅ Config loaded from: {PROJECT_DIR}")
    print(f"📁 Models: {MODELS_DIR}")
    print(f"📁 Logs: {LOGS_DIR}")
    print(f"📦 Model: {MODEL_PATH}")
    print(f"📝 Log: {LOG_FILE}")
    print(f"📷 Camera Type: {CAMERA_TYPE}")
    print(f"📷 DroidCam IP: {DROIDCAM_IP}:{DROIDCAM_PORT}")
    print(f"📷 DroidCam URL: {DROIDCAM_URL}")
    print(f"🔧 Arduino Port: {ARDUINO_PORT}:{ARDUINO_BAUD}")
