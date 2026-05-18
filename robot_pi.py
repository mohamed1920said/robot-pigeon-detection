#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clean Pigeon Detection Robot for Raspberry Pi
Production-ready with proper error handling and logging
"""

import time
import logging
import signal
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime
from dataclasses import dataclass

try:
    import cv2
    import RPi.GPIO as GPIO
    from ultralytics import YOLO
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
except ImportError as e:
    print(f"Import Error: {e}")
    print("Install dependencies with: pip install -r requirements-pi.txt")
    sys.exit(1)

import config

# ===========================
# LOGGER SETUP
# ===========================
def setup_logger(name: str) -> logging.Logger:
    """Setup logger with file rotation"""
    import os
    from pathlib import Path
    
    # Create log directory
    log_dir = Path(config.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # File handler
    file_handler = RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=config.LOG_MAX_BYTES,
        backupCount=config.LOG_BACKUP_COUNT
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logger(__name__)

# ===========================
# STATISTICS
# ===========================
@dataclass
class RobotStats:
    """Track robot statistics"""
    start_time: datetime = None
    frames_processed: int = 0
    pigeons_detected: int = 0
    obstacles_detected: int = 0
    errors: int = 0
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now()
    
    def runtime(self) -> int:
        """Get runtime in seconds"""
        return int((datetime.now() - self.start_time).total_seconds())
    
    def summary(self) -> str:
        """Get statistics summary"""
        return f"""
Robot Statistics:
- Runtime: {self.runtime()}s
- Frames: {self.frames_processed}
- Pigeons Detected: {self.pigeons_detected}
- Obstacles: {self.obstacles_detected}
- Errors: {self.errors}
        """

# ===========================
# ROBOT CLASS
# ===========================
class Robot:
    """Main robot control class"""
    
    def __init__(self):
        self.logger = logger
        self.stats = RobotStats()
        self.running = False
        self.model = None
        self.camera = None
        self.pwm_motors = {}
        
        self.logger.info("Robot initialized")
    
    def setup(self) -> bool:
        """Setup all hardware and model"""
        try:
            # GPIO setup
            if not self._setup_gpio():
                return False
            
            # Model loading
            if not self._load_model():
                return False
            
            # Camera setup
            if not self._setup_camera():
                return False
            
            self.logger.info("All systems ready")
            return True
            
        except Exception as e:
            self.logger.error(f"Setup failed: {e}")
            return False
    
    def _setup_gpio(self) -> bool:
        """Setup GPIO pins"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # IR Sensors
            GPIO.setup([config.IR_LEFT, config.IR_CENTER, config.IR_RIGHT], GPIO.IN)
            
            # Motor pins
            motor_pins = [
                config.L_RPWM, config.L_LPWM, config.L_R_EN, config.L_L_EN,
                config.R_RPWM, config.R_LPWM, config.R_R_EN, config.R_L_EN
            ]
            GPIO.setup(motor_pins, GPIO.OUT)
            GPIO.output([config.L_R_EN, config.L_L_EN, config.R_R_EN, config.R_L_EN], GPIO.HIGH)
            
            # Ultrasonic
            GPIO.setup(config.TRIG_FRONT, GPIO.OUT)
            GPIO.setup(config.ECHO_FRONT, GPIO.IN)
            GPIO.output(config.TRIG_FRONT, False)
            
            # Buzzer
            GPIO.setup(config.BUZZER, GPIO.OUT)
            
            # PWM setup
            self.pwm_motors = {
                'L_R': GPIO.PWM(config.L_RPWM, 1000),
                'L_L': GPIO.PWM(config.L_LPWM, 1000),
                'R_R': GPIO.PWM(config.R_RPWM, 1000),
                'R_L': GPIO.PWM(config.R_LPWM, 1000),
            }
            
            for pwm in self.pwm_motors.values():
                pwm.start(0)
            
            self.logger.info("GPIO setup complete")
            return True
            
        except Exception as e:
            self.logger.error(f"GPIO setup failed: {e}")
            return False
    
    def _load_model(self) -> bool:
        """Load YOLO model"""
        try:
            self.model = YOLO(config.MODEL_PATH, task="detect")
            self.logger.info(f"Model loaded: {config.MODEL_PATH}")
            return True
        except Exception as e:
            self.logger.error(f"Model loading failed: {e}")
            return False
    
    def _setup_camera(self) -> bool:
        """Setup camera"""
        try:
            self.camera = cv2.VideoCapture(0)
            
            if not self.camera.isOpened():
                self.logger.error("Camera not found")
                return False
            
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
            self.camera.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)
            
            self.logger.info("Camera ready")
            return True
            
        except Exception as e:
            self.logger.error(f"Camera setup failed: {e}")
            return False
    
    def read_sensors(self):
        """Read line sensors"""
        try:
            left = GPIO.input(config.IR_LEFT)
            center = GPIO.input(config.IR_CENTER)
            right = GPIO.input(config.IR_RIGHT)
            return (left, center, right)
        except Exception as e:
            self.logger.error(f"Sensor read error: {e}")
            self.stats.errors += 1
            return (0, 0, 0)
    
    def measure_distance(self) -> float:
        """Measure distance"""
        try:
            GPIO.output(config.TRIG_FRONT, True)
            time.sleep(0.00001)
            GPIO.output(config.TRIG_FRONT, False)
            
            start = time.time()
            timeout = start + config.ULTRASONIC_TIMEOUT
            
            while GPIO.input(config.ECHO_FRONT) == 0 and time.time() < timeout:
                start = time.time()
            
            while GPIO.input(config.ECHO_FRONT) == 1 and time.time() < timeout:
                end = time.time()
            
            distance = (end - start) * 34300 / 2
            return min(distance, 400)
            
        except Exception as e:
            self.logger.error(f"Distance measurement error: {e}")
            return 999
    
    def set_motors(self, left: int, right: int):
        """Set motor speeds (-100 to 100)"""
        try:
            left = max(-100, min(100, left))
            right = max(-100, min(100, right))
            
            # Left motor
            if left >= 0:
                self.pwm_motors['L_R'].ChangeDutyCycle(left)
                self.pwm_motors['L_L'].ChangeDutyCycle(0)
            else:
                self.pwm_motors['L_R'].ChangeDutyCycle(0)
                self.pwm_motors['L_L'].ChangeDutyCycle(-left)
            
            # Right motor
            if right >= 0:
                self.pwm_motors['R_R'].ChangeDutyCycle(right)
                self.pwm_motors['R_L'].ChangeDutyCycle(0)
            else:
                self.pwm_motors['R_R'].ChangeDutyCycle(0)
                self.pwm_motors['R_L'].ChangeDutyCycle(-right)
                
        except Exception as e:
            self.logger.error(f"Motor control error: {e}")
            self.stats.errors += 1
    
    def stop(self):
        """Stop motors"""
        self.set_motors(0, 0)
    
    def beep(self):
        """Buzzer beep"""
        try:
            GPIO.output(config.BUZZER, GPIO.HIGH)
            time.sleep(0.2)
            GPIO.output(config.BUZZER, GPIO.LOW)
        except Exception as e:
            self.logger.error(f"Buzzer error: {e}")
    
    def follow_line(self):
        """Follow line logic"""
        # Check obstacle
        distance = self.measure_distance()
        if distance < config.OBSTACLE_DISTANCE_THRESHOLD:
            self.logger.warning(f"Obstacle at {distance:.1f}cm")
            self.stop()
            self.beep()
            self.stats.obstacles_detected += 1
            return
        
        # Read sensors
        left, center, right = self.read_sensors()
        
        # Line following
        if center == 1:
            self.set_motors(config.BASE_SPEED, config.BASE_SPEED)
        elif left == 1:
            self.set_motors(-config.BASE_SPEED // 2, config.BASE_SPEED)
        elif right == 1:
            self.set_motors(config.BASE_SPEED, -config.BASE_SPEED // 2)
        else:
            self.stop()
            self.logger.warning("Line lost")
            self.stats.obstacles_detected += 1
    
    def detect_pigeons(self):
        """Detect pigeons"""
        try:
            ret, frame = self.camera.read()
            if not ret:
                return False
            
            self.stats.frames_processed += 1
            
            # Run detection
            results = self.model.predict(
                frame,
                imgsz=config.IMAGE_SIZE,
                conf=config.CONFIDENCE_THRESHOLD,
                verbose=False
            )
            
            num_detections = len(results[0].boxes)
            if num_detections > 0:
                self.stats.pigeons_detected += 1
                confidences = results[0].boxes.conf.cpu().numpy()
                avg_confidence = float(confidences.mean())
                self.logger.info(f"🕊️  Pigeons detected: {num_detections}, avg confidence: {avg_confidence:.1%}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Detection error: {e}")
            self.stats.errors += 1
            return False
    
    def run(self):
        """Main robot loop"""
        self.running = True
        self.logger.info("Robot started")
        
        try:
            while self.running:
                # Follow line
                self.follow_line()
                
                # Detect pigeons
                self.detect_pigeons()
                
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            self.logger.info("Interrupted")
        except Exception as e:
            self.logger.error(f"Runtime error: {e}")
            self.stats.errors += 1
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup"""
        self.logger.info("Cleaning up...")
        
        try:
            self.stop()
            
            if self.camera:
                self.camera.release()
            
            for pwm in self.pwm_motors.values():
                pwm.stop()
            
            GPIO.cleanup()
            
            self.logger.info(self.stats.summary())
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")

# ===========================
# MAIN
# ===========================
def main():
    """Main entry point"""
    robot = Robot()
    
    # Signal handlers
    def signal_handler(sig, frame):
        robot.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Setup
    if not robot.setup():
        logger.error("Setup failed")
        return False
    
    # Run
    robot.run()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
