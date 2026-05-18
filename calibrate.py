# -*- coding: utf-8 -*-
"""
Robot Calibration Tool
Calibrate IR sensors and test hardware components
"""

import time
import sys
import logging

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("RPi.GPIO not found. Install with: pip install RPi.GPIO")
    sys.exit(1)

import config
from robot_main import setup_logger

logger = setup_logger("Calibration")

def test_ir_sensors():
    """Test IR line sensors"""
    logger.info("IR Sensor Calibration")
    logger.info("Place robot on different line positions and observe readings:")
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup([config.IR_LEFT, config.IR_CENTER, config.IR_RIGHT], GPIO.IN)
    
    try:
        for i in range(50):
            left = GPIO.input(config.IR_LEFT)
            center = GPIO.input(config.IR_CENTER)
            right = GPIO.input(config.IR_RIGHT)
            logger.info(f"Reading {i+1}: LEFT={left} CENTER={center} RIGHT={right}")
            time.sleep(0.2)
    except KeyboardInterrupt:
        logger.info("IR calibration interrupted")
    finally:
        GPIO.cleanup()

def test_ultrasonic():
    """Test ultrasonic distance sensor"""
    logger.info("Ultrasonic Sensor Test")
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(config.TRIG_FRONT, GPIO.OUT)
    GPIO.setup(config.ECHO_FRONT, GPIO.IN)
    GPIO.output(config.TRIG_FRONT, False)
    
    try:
        for i in range(10):
            GPIO.output(config.TRIG_FRONT, True)
            time.sleep(0.00001)
            GPIO.output(config.TRIG_FRONT, False)
            
            start = time.time()
            while GPIO.input(config.ECHO_FRONT) == 0:
                start = time.time()
            
            while GPIO.input(config.ECHO_FRONT) == 1:
                end = time.time()
            
            distance = (end - start) * 34300 / 2
            logger.info(f"Reading {i+1}: {distance:.2f} cm")
            time.sleep(0.5)
    except KeyboardInterrupt:
        logger.info("Ultrasonic test interrupted")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    print("1. Test IR Sensors")
    print("2. Test Ultrasonic Sensor")
    choice = input("Select test (1-2): ")
    
    if choice == "1":
        test_ir_sensors()
    elif choice == "2":
        test_ultrasonic()