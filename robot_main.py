# -*- coding: utf-8 -*-
"""
Enhanced Pigeon Detection Robot System
Autonomous line-following with obstacle and pigeon detection
"""

import time
import logging
import threading
import signal
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
from typing import Tuple, Optional
from dataclasses import dataclass, field

try:
    import cv2
    # Use Pi 5 compatible GPIO wrapper instead of RPi.GPIO
    try:
        from gpio_pi5 import GPIO
    except ImportError:
        import RPi.GPIO as GPIO
    from ultralytics import YOLO
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

import config

# ===========================
# STATISTICS CLASS
# ===========================
@dataclass
class RobotStats:
    """Track robot performance statistics"""
    start_time: datetime = field(default_factory=datetime.now)
    total_distance: float = 0.0
    pigeons_detected: int = 0
    obstacles_detected: int = 0
    line_losses: int = 0
    emails_sent: int = 0
    
    def get_runtime(self) -> int:
        """Get runtime in seconds"""
        return int((datetime.now() - self.start_time).total_seconds())
    
    def get_summary(self) -> str:
        """Get statistics summary"""
        return f"""
Robot Statistics:
- Runtime: {self.get_runtime()}s
- Pigeons Detected: {self.pigeons_detected}
- Obstacles Detected: {self.obstacles_detected}
- Line Losses: {self.line_losses}
- Emails Sent: {self.emails_sent}
        """

# ===========================
# LOGGER SETUP
# ===========================
def setup_logger(name: str) -> logging.Logger:
    """Setup rotating file logger"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # File handler with rotation
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
# ROBOT CLASS
# ===========================
class PigeonDetectionRobot:
    """Enhanced Pigeon Detection Robot"""
    
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)
        self.stats = RobotStats()
        self.running = False
        self.robot_mode = "MOVEMENT"
        
        # Motor PWM objects
        self.pwm_motors = {}
        
        # Sensor state
        self.last_motor_speeds = (0, 0)  # (left, right)
        
        # Last alert times (for rate limiting)
        self.last_alert_times = {
            'obstacle': 0,
            'line_loss': 0,
            'pigeon': 0
        }
        
        # Model and Camera
        self.model = None
        self.cap = None
        
        self.logger.info("Robot initialization started")
        
    def setup_gpio(self) -> bool:
        """Setup GPIO pins safely"""
        try:
            GPIO.setmode(GPIO.BCM)
            
            # IR Sensors
            GPIO.setup([config.IR_LEFT, config.IR_CENTER, config.IR_RIGHT], GPIO.IN)
            
            # Motor pins
            motor_pins = [
                config.L_RPWM, config.L_LPWM, config.L_R_EN, config.L_L_EN,
                config.R_RPWM, config.R_LPWM, config.R_R_EN, config.R_L_EN
            ]
            GPIO.setup(motor_pins, GPIO.OUT)
            GPIO.output([config.L_R_EN, config.L_L_EN, config.R_R_EN, config.R_L_EN], GPIO.HIGH)
            
            # Ultrasonic sensor
            GPIO.setup(config.TRIG_FRONT, GPIO.OUT)
            GPIO.setup(config.ECHO_FRONT, GPIO.IN)
            GPIO.output(config.TRIG_FRONT, False)
            
            # Buzzer
            GPIO.setup(config.BUZZER, GPIO.OUT)
            
            # Setup PWM
            self.pwm_motors = {
                'L_R': GPIO.PWM(config.L_RPWM, 1000),
                'L_L': GPIO.PWM(config.L_LPWM, 1000),
                'R_R': GPIO.PWM(config.R_RPWM, 1000),
                'R_L': GPIO.PWM(config.R_LPWM, 1000),
            }
            
            for pwm in self.pwm_motors.values():
                pwm.start(0)
            
            time.sleep(1)
            self.logger.info("✅ GPIO setup successful")
            return True
            
        except Exception as e:
            self.logger.error(f"GPIO setup failed: {e}")
            return False
    
    def load_model(self) -> bool:
        """Load YOLO model safely"""
        try:
            self.model = YOLO(config.MODEL_PATH, task="detect")
            self.logger.info(f"✅ Model loaded: {config.MODEL_PATH}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            return False
    
    def open_camera(self) -> bool:
        """Open camera - supports both DroidCam and local"""
        try:
            # Try DroidCam first if configured
            if config.CAMERA_TYPE == "droidcam":
                self.logger.info(f"Attempting to connect to DroidCam: {config.DROIDCAM_URL}")
                self.cap = cv2.VideoCapture(config.DROIDCAM_URL)
                
                if not self.cap.isOpened():
                    self.logger.warning("DroidCam failed, falling back to local camera")
                    self.cap = cv2.VideoCapture(0)
            else:
                # Use local camera (CSI or USB)
                self.cap = cv2.VideoCapture(config.CAMERA_INDEX, cv2.CAP_V4L2)
            
            if not self.cap.isOpened():
                self.logger.error("Camera failed to open")
                return False
            
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)
            
            self.logger.info("✅ Camera opened successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Camera open failed: {e}")
            return False
    
    # ===========================
    # MOTOR CONTROL
    # ===========================
    def set_motors_smooth(self, left: int, right: int, duration: float = 0.1) -> None:
        """Set motors with smooth acceleration/deceleration"""
        try:
            current_left, current_right = self.last_motor_speeds
            steps = max(1, int(duration / 0.01))
            
            for step in range(steps):
                progress = (step + 1) / steps
                
                # Interpolate speed
                new_left = int(current_left + (left - current_left) * progress)
                new_right = int(current_right + (right - current_right) * progress)
                
                self._set_motors_raw(new_left, new_right)
                time.sleep(0.01)
            
            self.last_motor_speeds = (left, right)
            
        except Exception as e:
            self.logger.error(f"Motor control error: {e}")
            self._set_motors_raw(0, 0)
    
    def _set_motors_raw(self, left: int, right: int) -> None:
        """Set motor speeds directly (internal use)"""
        try:
            # Clamp values
            left = max(-100, min(100, left))
            right = max(-100, min(100, right))
            
            # Left motor
            if left >= 0:
                self.pwm_motors['L_R'].ChangeDutyCycle(min(left, 100))
                self.pwm_motors['L_L'].ChangeDutyCycle(0)
            else:
                self.pwm_motors['L_R'].ChangeDutyCycle(0)
                self.pwm_motors['L_L'].ChangeDutyCycle(min(-left, 100))
            
            # Right motor
            if right >= 0:
                self.pwm_motors['R_R'].ChangeDutyCycle(min(right, 100))
                self.pwm_motors['R_L'].ChangeDutyCycle(0)
            else:
                self.pwm_motors['R_R'].ChangeDutyCycle(0)
                self.pwm_motors['R_L'].ChangeDutyCycle(min(-right, 100))
                
        except Exception as e:
            self.logger.error(f"Raw motor control error: {e}")
    
    def stop_motors(self) -> None:
        """Stop motors safely"""
        self.set_motors_smooth(0, 0, 0.2)
        self.logger.debug("Motors stopped")
    
    def beep(self, count: int = 1, duration: float = 0.2) -> None:
        """Buzzer beep"""
        try:
            for _ in range(count):
                GPIO.output(config.BUZZER, GPIO.HIGH)
                time.sleep(duration)
                GPIO.output(config.BUZZER, GPIO.LOW)
                time.sleep(duration * 0.5)
        except Exception as e:
            self.logger.error(f"Buzzer error: {e}")
    
    # ===========================
    # SENSOR READINGS
    # ===========================
    def read_line_sensors(self) -> Tuple[int, int, int]:
        """Read IR line sensors with debouncing"""
        try:
            left = GPIO.input(config.IR_LEFT)
            center = GPIO.input(config.IR_CENTER)
            right = GPIO.input(config.IR_RIGHT)
            
            # Simple debounce: read again if unusual pattern
            if (left, center, right) == (0, 0, 0):
                time.sleep(config.IR_SENSOR_DEBOUNCE / 1000)
                left = GPIO.input(config.IR_LEFT)
                center = GPIO.input(config.IR_CENTER)
                right = GPIO.input(config.IR_RIGHT)
            
            return (left, center, right)
            
        except Exception as e:
            self.logger.error(f"Line sensor read error: {e}")
            return (0, 0, 0)
    
    def measure_distance(self) -> float:
        """Measure distance using ultrasonic sensor with timeout"""
        try:
            GPIO.output(config.TRIG_FRONT, True)
            time.sleep(0.00001)
            GPIO.output(config.TRIG_FRONT, False)
            
            start_time = time.time()
            timeout = start_time + config.ULTRASONIC_TIMEOUT
            
            # Wait for signal to go high
            while GPIO.input(config.ECHO_FRONT) == 0:
                if time.time() > timeout:
                    self.logger.warning("Ultrasonic sensor timeout (waiting for high)")
                    return 999
                start_time = time.time()
            
            # Wait for signal to go low
            while GPIO.input(config.ECHO_FRONT) == 1:
                if time.time() > timeout:
                    self.logger.warning("Ultrasonic sensor timeout (waiting for low)")
                    return 999
                end_time = time.time()
            
            pulse_duration = end_time - start_time
            distance = pulse_duration * 34300 / 2
            
            return min(distance, 400)  # Max reasonable distance
            
        except Exception as e:
            self.logger.error(f"Distance measurement error: {e}")
            return 999
    
    # ===========================
    # EMAIL ALERTS
    # ===========================
    def send_email(self, subject: str, message: str, alert_type: str = "general") -> bool:
        """Send email alert with rate limiting"""
        if not config.ENABLE_EMAIL_ALERTS:
            return False
        
        # Rate limiting
        if alert_type in self.last_alert_times:
            time_since_last = time.time() - self.last_alert_times[alert_type]
            if time_since_last < config.EMAIL_RATE_LIMIT:
                self.logger.debug(f"Email for {alert_type} rate limited")
                return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = config.SENDER_EMAIL
            msg['To'] = config.OWNER_EMAIL
            msg['Subject'] = subject
            
            body = f"""
{message}

---
Robot Status:
- Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Runtime: {self.stats.get_runtime()}s
- Mode: {self.robot_mode}

{self.stats.get_summary()}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT, timeout=10)
            server.starttls()
            server.login(config.SENDER_EMAIL, config.SENDER_PASSWORD)
            server.sendmail(config.SENDER_EMAIL, config.OWNER_EMAIL, msg.as_string())
            server.quit()
            
            self.last_alert_times[alert_type] = time.time()
            self.stats.emails_sent += 1
            
            self.logger.info(f"✅ Email sent: {subject}")
            return True
            
        except Exception as e:
            self.logger.error(f"Email send failed: {e}")
            return False
    
    # ===========================
    # LINE FOLLOWING LOGIC
    # ===========================
    def follow_line(self) -> None:
        """Follow line with adaptive speed and obstacle avoidance"""
        if self.robot_mode != "MOVEMENT":
            self.stop_motors()
            return
        
        # Check for obstacles
        distance = self.measure_distance()
        if distance < config.OBSTACLE_THRESHOLD:
            self.logger.warning(f"🚨 Obstacle detected at {distance:.1f}cm")
            self.stop_motors()
            self.beep(2)
            self.stats.obstacles_detected += 1
            self.send_email(
                "🚨 ROBOT ALERT: Obstacle Detected",
                f"Obstacle detected at {distance:.1f}cm",
                alert_type="obstacle"
            )
            return
        
        # Read line sensors
        left, center, right = self.read_line_sensors()
        
        # Check for line loss
        if (left, center, right) == (0, 0, 0):
            self.logger.warning("⚠️ Line lost!")
            self.stop_motors()
            self.beep(3)
            self.stats.line_losses += 1
            self.send_email(
                "⚠️ ROBOT ALERT: Line Lost",
                "Robot lost the line. Unknown territory.",
                alert_type="line_loss"
            )
            return
        
        # Adaptive speed control
        speed = config.BASE_SPEED
        
        # Line following logic
        if center == 1:
            # On line, move forward
            left_speed = speed
            right_speed = speed
        elif left == 1 and center == 0:
            # Line shifted left, turn left
            left_speed = -speed // 2
            right_speed = speed
        elif right == 1 and center == 0:
            # Line shifted right, turn right
            left_speed = speed
            right_speed = -speed // 2
        else:
            # Line not centered, gradual correction
            left_speed = speed if left else speed // 2
            right_speed = speed if right else speed // 2
        
        self.set_motors_smooth(left_speed, right_speed, config.SMOOTH_TRANSITION_TIME)
    
    # ===========================
    # PIGEON DETECTION
    # ===========================
    def detect_pigeons(self) -> bool:
        """Detect pigeons using YOLO model"""
        if self.robot_mode != "STOP":
            return False
        
        if self.cap is None or self.model is None:
            return False
        
        try:
            ret, frame = self.cap.read()
            if not ret:
                self.logger.error("Failed to capture frame")
                return False
            
            # Run detection
            results = self.model.predict(
                frame,
                imgsz=config.IMAGE_SIZE,
                conf=config.CONFIDENCE_THRESHOLD,
                verbose=False
            )
            
            # Display results
            if config.SHOW_OUTPUT:
                annotated_frame = results[0].plot()
                cv2.imshow("ROBOT CAMERA", annotated_frame)
                cv2.waitKey(1)
            
            # Check for detections
            detections = len(results[0].boxes) > 0
            
            if detections:
                # Get confidence scores
                confidences = results[0].boxes.conf.cpu().numpy()
                avg_confidence = float(confidences.mean()) if len(confidences) > 0 else 0
                
                self.logger.info(f"🕊️ Pigeons detected! ({len(results[0].boxes)} objects, {avg_confidence:.2%} confidence)")
                self.stats.pigeons_detected += 1
                
                self.send_email(
                    f"🕊️ PIGEON ALERT: {len(results[0].boxes)} detected",
                    f"Detected {len(results[0].boxes)} pigeons with {avg_confidence:.1%} average confidence",
                    alert_type="pigeon"
                )
            
            return detections
            
        except Exception as e:
            self.logger.error(f"Pigeon detection error: {e}")
            return False
    
    # ===========================
    # MAIN LOOP
    # ===========================
    def run(self) -> None:
        """Main robot operation loop"""
        self.running = True
        start_time = time.time()
        
        try:
            self.logger.info("=" * 60)
            self.logger.info("🤖 ROBOT STARTED - Pigeon Detection Active")
            self.logger.info("=" * 60)
            
            while self.running:
                # Check max runtime
                if config.MAX_RUNTIME > 0:
                    if time.time() - start_time > config.MAX_RUNTIME:
                        self.logger.info("Max runtime reached")
                        break
                
                try:
                    # MOVEMENT PHASE
                    self.robot_mode = "MOVEMENT"
                    self.logger.debug("🚀 Movement phase started")
                    
                    move_start = time.time()
                    while time.time() - move_start < config.MOVEMENT_TIME and self.running:
                        self.follow_line()
                        time.sleep(0.01)
                    
                    self.stop_motors()
                    
                    # STOP PHASE (Pigeon detection)
                    self.robot_mode = "STOP"
                    self.logger.debug("🎯 Stop phase started - scanning for pigeons")
                    
                    stop_start = time.time()
                    while time.time() - stop_start < config.STOP_TIME and self.running:
                        self.detect_pigeons()
                        time.sleep(0.05)
                    
                except Exception as e:
                    self.logger.error(f"Main loop error: {e}")
                    self.stop_motors()
                    time.sleep(0.5)
            
        except KeyboardInterrupt:
            self.logger.info("⏹️ Keyboard interrupt received")
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self) -> None:
        """Cleanup and shutdown safely"""
        self.logger.info("🧹 Cleanup started")
        self.running = False
        
        try:
            # Stop motors
            self.stop_motors()
            time.sleep(0.5)
            
            # Release camera
            if self.cap is not None:
                self.cap.release()
                cv2.destroyAllWindows()
            
            # Cleanup GPIO
            GPIO.cleanup()
            
            # Final statistics
            self.logger.info(self.stats.get_summary())
            
            self.logger.info("=" * 60)
            self.logger.info("🛑 ROBOT STOPPED")
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")

# ===========================
# MAIN ENTRY POINT
# ===========================
def main():
    """Main entry point"""
    robot = PigeonDetectionRobot()
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        robot.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize
    if not robot.setup_gpio():
        logger.error("GPIO setup failed")
        return False
    
    if not robot.load_model():
        logger.error("Model loading failed")
        robot.cleanup()
        return False
    
    if not robot.open_camera():
        logger.error("Camera opening failed")
        robot.cleanup()
        return False
    
    # Run
    robot.run()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
