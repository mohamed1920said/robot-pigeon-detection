# -*- coding: utf-8 -*-
"""
Robot Configuration File
Centralized settings for easy tuning
"""

# ===========================
# MODEL SETTINGS
# ===========================
MODEL_PATH = "/home/mehdi/robot_pigeon/best_int8.tflite"
IMAGE_SIZE = 320
CONFIDENCE_THRESHOLD = 0.4
MIN_DETECTION_COOLDOWN = 30  # seconds between alerts for same detection

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
# GPIO PIN CONFIGURATION
# ===========================
# Ultrasonic Sensor
TRIG_FRONT = 5
ECHO_FRONT = 6

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
R_LPWM = 16
R_R_EN = 20
R_L_EN = 21

# Buzzer
BUZZER = 26

# ===========================
# EMAIL SETTINGS
# ===========================
OWNER_EMAIL = "mohamedamir28860292@gmail.com"
SENDER_EMAIL = "mohamedamir28860292@gmail.com"
SENDER_PASSWORD = "your_app_password_here"  # Use Gmail App Password
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

EMAIL_RATE_LIMIT = 60  # seconds between similar alerts
ENABLE_EMAIL_ALERTS = True

# ===========================
# LOGGING SETTINGS
# ===========================
LOG_FILE = "/home/mehdi/robot_pigeon/robot.log"
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