# -*- coding: utf-8 -*-
"""
Robot Configuration File - Raspberry Pi 5
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
# MOTOR SETTINGS
# ===========================
BASE_SPEED = 15
MAX_SPEED = 100
ACCELERATION_RATE = 5  # PWM units per cycle
DECELERATION_RATE = 8

# TIMING
MOVEMENT_TIME = 3  # seconds
STOP_TIME = 5  # seconds
SMOOTH_TRANSITION_TIME = 0.1  # seconds

# ===========================
# SENSOR SETTINGS
# ===========================
OBSTACLE_DISTANCE_THRESHOLD = 20  # cm
ULTRASONIC_TIMEOUT = 0.05  # seconds
IR_SENSOR_DEBOUNCE = 20  # milliseconds

# ===========================
# GPIO PIN CONFIGURATION (Raspberry Pi 5)
# ===========================
# Ultrasonic Sensor
TRIG_FRONT = 16
ECHO_FRONT = 26

# IR Line Sensors
IR_LEFT = 17
IR_CENTER = 27
IR_RIGHT = 22

# Left Motor
L_RPWM = 18
L_LPWM = 23
L_R_EN = 24
L_L_EN = 25

# Right Motor
R_RPWM = 12
R_LPWM = 13
R_R_EN = 6
R_L_EN = 5

# Buzzer
BUZZER = 19

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
# SYSTEM SETTINGS
# ===========================
MAX_RUNTIME = 3600  # seconds (0 = unlimited)
ENABLE_WATCHDOG = True
WATCHDOG_TIMEOUT = 30  # seconds

# Camera Settings
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30
CAMERA_INDEX = 0

# ===========================
# OPERATION MODES
# ===========================
OPERATION_MODES = {
    "AUTO": "Autonomous line following with pigeon detection",
    "MANUAL": "Keyboard-controlled movement",
    "CALIBRATION": "IR sensor calibration mode",
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
