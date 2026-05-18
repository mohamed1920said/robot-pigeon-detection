# -*- coding: utf-8 -*-
"""
Comprehensive Hardware Testing Script
Test all robot components systematically
"""

import time
import sys
import os
from datetime import datetime

try:
    import RPi.GPIO as GPIO
    import cv2
    from ultralytics import YOLO
except ImportError as e:
    print(f"Missing dependency: {e}")
    sys.exit(1)

import config
from robot_main import setup_logger

logger = setup_logger("HardwareTest")

class HardwareTester:
    """Test all hardware components"""
    
    def __init__(self):
        self.results = {}
        self.logger = logger
        
    def test_gpio_access(self) -> bool:
        """Test GPIO module access"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            self.logger.info("✓ GPIO access OK")
            self.results['gpio'] = "PASS"
            return True
        except Exception as e:
            self.logger.error(f"✗ GPIO access failed: {e}")
            self.results['gpio'] = f"FAIL: {e}"
            return False
    
    def test_ir_sensors(self) -> bool:
        """Test IR line sensors"""
        try:
            GPIO.setup([config.IR_LEFT, config.IR_CENTER, config.IR_RIGHT], GPIO.IN)
            
            readings = []
            for i in range(5):
                left = GPIO.input(config.IR_LEFT)
                center = GPIO.input(config.IR_CENTER)
                right = GPIO.input(config.IR_RIGHT)
                readings.append((left, center, right))
                time.sleep(0.1)
            
            self.logger.info(f"✓ IR sensors OK - Readings: {readings}")
            self.results['ir_sensors'] = "PASS"
            return True
        except Exception as e:
            self.logger.error(f"✗ IR sensors failed: {e}")
            self.results['ir_sensors'] = f"FAIL: {e}"
            return False
    
    def test_ultrasonic(self) -> bool:
        """Test ultrasonic distance sensor"""
        try:
            GPIO.setup(config.TRIG_FRONT, GPIO.OUT)
            GPIO.setup(config.ECHO_FRONT, GPIO.IN)
            GPIO.output(config.TRIG_FRONT, False)
            time.sleep(0.1)
            
            distances = []
            for i in range(3):
                GPIO.output(config.TRIG_FRONT, True)
                time.sleep(0.00001)
                GPIO.output(config.TRIG_FRONT, False)
                
                start = time.time()
                timeout = start + 0.05
                
                while GPIO.input(config.ECHO_FRONT) == 0 and time.time() < timeout:
                    start = time.time()
                
                end = time.time()
                while GPIO.input(config.ECHO_FRONT) == 1 and time.time() < timeout:
                    end = time.time()
                
                distance = (end - start) * 34300 / 2
                distances.append(distance)
                time.sleep(0.2)
            
            self.logger.info(f"✓ Ultrasonic sensor OK - Distances: {[f'{d:.1f}cm' for d in distances]}")
            self.results['ultrasonic'] = "PASS"
            return True
        except Exception as e:
            self.logger.error(f"✗ Ultrasonic sensor failed: {e}")
            self.results['ultrasonic'] = f"FAIL: {e}"
            return False
    
    def test_motors(self) -> bool:
        """Test motor control"""
        try:
            motor_pins = [
                config.L_RPWM, config.L_LPWM, config.L_R_EN, config.L_L_EN,
                config.R_RPWM, config.R_LPWM, config.R_R_EN, config.R_L_EN
            ]
            GPIO.setup(motor_pins, GPIO.OUT)
            GPIO.output([config.L_R_EN, config.L_L_EN, config.R_R_EN, config.R_L_EN], GPIO.HIGH)
            
            # Create PWM objects
            pwm_L_R = GPIO.PWM(config.L_RPWM, 1000)
            pwm_L_L = GPIO.PWM(config.L_LPWM, 1000)
            pwm_R_R = GPIO.PWM(config.R_RPWM, 1000)
            pwm_R_L = GPIO.PWM(config.R_LPWM, 1000)
            
            for pwm in [pwm_L_R, pwm_L_L, pwm_R_R, pwm_R_L]:
                pwm.start(0)
            
            # Test forward
            self.logger.info("Testing forward motion...")
            pwm_L_R.ChangeDutyCycle(50)
            pwm_R_R.ChangeDutyCycle(50)
            time.sleep(2)
            
            # Stop
            pwm_L_R.ChangeDutyCycle(0)
            pwm_R_R.ChangeDutyCycle(0)
            time.sleep(1)
            
            # Test reverse
            self.logger.info("Testing reverse motion...")
            pwm_L_L.ChangeDutyCycle(50)
            pwm_R_L.ChangeDutyCycle(50)
            time.sleep(2)
            
            # Stop
            pwm_L_L.ChangeDutyCycle(0)
            pwm_R_L.ChangeDutyCycle(0)
            
            # Cleanup
            for pwm in [pwm_L_R, pwm_L_L, pwm_R_R, pwm_R_L]:
                pwm.stop()
            
            self.logger.info("✓ Motors OK")
            self.results['motors'] = "PASS"
            return True
        except Exception as e:
            self.logger.error(f"✗ Motors failed: {e}")
            self.results['motors'] = f"FAIL: {e}"
            return False
    
    def test_buzzer(self) -> bool:
        """Test buzzer"""
        try:
            GPIO.setup(config.BUZZER, GPIO.OUT)
            
            self.logger.info("Testing buzzer...")
            for _ in range(3):
                GPIO.output(config.BUZZER, GPIO.HIGH)
                time.sleep(0.2)
                GPIO.output(config.BUZZER, GPIO.LOW)
                time.sleep(0.2)
            
            self.logger.info("✓ Buzzer OK")
            self.results['buzzer'] = "PASS"
            return True
        except Exception as e:
            self.logger.error(f"✗ Buzzer failed: {e}")
            self.results['buzzer'] = f"FAIL: {e}"
            return False
    
    def test_camera(self) -> bool:
        """Test camera"""
        try:
            cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
            
            if not cap.isOpened():
                raise Exception("Camera failed to open")
            
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
            cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)
            
            ret, frame = cap.read()
            if not ret:
                raise Exception("Failed to capture frame")
            
            # Save test image
            test_image_path = "test_image.jpg"
            cv2.imwrite(test_image_path, frame)
            
            cap.release()
            
            self.logger.info(f"✓ Camera OK - Image saved: {test_image_path}")
            self.results['camera'] = "PASS"
            return True
        except Exception as e:
            self.logger.error(f"✗ Camera failed: {e}")
            self.results['camera'] = f"FAIL: {e}"
            return False
    
    def test_model(self) -> bool:
        """Test YOLO model loading"""
        try:
            self.logger.info("Loading model... (this may take 10-30 seconds)")
            model = YOLO(config.MODEL_PATH, task="detect")
            
            self.logger.info("✓ Model loaded OK")
            self.results['model'] = "PASS"
            return True
        except Exception as e:
            self.logger.error(f"✗ Model loading failed: {e}")
            self.results['model'] = f"FAIL: {e}"
            return False
    
    def test_email(self) -> bool:
        """Test email configuration"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            
            msg = MIMEText("Test email from robot hardware testing")
            msg['Subject'] = "Robot Test Email"
            msg['From'] = config.SENDER_EMAIL
            msg['To'] = config.OWNER_EMAIL
            
            server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT, timeout=5)
            server.starttls()
            server.login(config.SENDER_EMAIL, config.SENDER_PASSWORD)
            server.sendmail(config.SENDER_EMAIL, config.OWNER_EMAIL, msg.as_string())
            server.quit()
            
            self.logger.info("✓ Email configuration OK")
            self.results['email'] = "PASS"
            return True
        except Exception as e:
            self.logger.error(f"✗ Email test failed: {e}")
            self.results['email'] = f"FAIL: {e}"
            return False
    
    def run_all_tests(self):
        """Run all hardware tests"""
        self.logger.info("="*50)
        self.logger.info("HARDWARE TEST SUITE STARTED")
        self.logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("="*50)
        
        tests = [
            ("GPIO Access", self.test_gpio_access),
            ("IR Sensors", self.test_ir_sensors),
            ("Ultrasonic Sensor", self.test_ultrasonic),
            ("Motors", self.test_motors),
            ("Buzzer", self.test_buzzer),
            ("Camera", self.test_camera),
            ("YOLO Model", self.test_model),
            ("Email Configuration", self.test_email),
        ]
        
        GPIO.cleanup()  # Clean before starting
        
        for test_name, test_func in tests:
            try:
                self.logger.info(f"\nTesting {test_name}...")
                test_func()
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Unexpected error during {test_name}: {e}")
            finally:
                GPIO.cleanup()  # Clean after each test
        
        # Print summary
        self.logger.info("\n" + "="*50)
        self.logger.info("TEST SUMMARY")
        self.logger.info("="*50)
        
        for test_name, result in self.results.items():
            status = "✓" if result == "PASS" else "✗"
            self.logger.info(f"{status} {test_name}: {result}")
        
        passed = sum(1 for r in self.results.values() if r == "PASS")
        total = len(self.results)
        
        self.logger.info(f"\nPassed: {passed}/{total}")
        self.logger.info("="*50)

if __name__ == "__main__":
    tester = HardwareTester()
    tester.run_all_tests()