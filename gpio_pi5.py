#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi 5 Compatible GPIO Wrapper
Handles GPIO operations for Pi 5 using libgpiod (gpiochip0)
"""

import os
import sys
import logging

logger = logging.getLogger(__name__)

# Try different GPIO backends in order
GPIO_BACKEND = None

try:
    # Method 1: Use gpiod (libgpiod - Pi 5 compatible)
    import gpiod
    GPIO_BACKEND = "gpiod"
    logger.info("✅ Using libgpiod backend (Pi 5 compatible)")
except ImportError:
    try:
        # Method 2: Fallback to RPi.GPIO (older Pi models)
        import RPi.GPIO as GPIO
        GPIO_BACKEND = "RPi.GPIO"
        logger.warning("⚠️  Using RPi.GPIO (may fail on Pi 5)")
    except ImportError:
        logger.error("❌ No GPIO library available")
        GPIO_BACKEND = None


class GPIO_Pi5:
    """Pi 5 compatible GPIO wrapper using gpiod"""
    
    BCM = 1
    OUT = 1
    IN = 0
    HIGH = 1
    LOW = 0
    
    def __init__(self):
        self.chip = None
        self.pins = {}
        self.pwm_objects = {}
        
    def setmode(self, mode):
        """Set GPIO mode (BCM)"""
        try:
            if GPIO_BACKEND == "gpiod":
                # Pi 5 uses gpiochip0
                self.chip = gpiod.Chip("gpiochip0")
                logger.info("✅ GPIO initialized with gpiochip0 (Pi 5)")
            else:
                import RPi.GPIO as GPIO
                GPIO.setmode(GPIO.BCM)
                logger.info("✅ GPIO initialized (RPi.GPIO)")
        except Exception as e:
            logger.error(f"GPIO setup failed: {e}")
            
    def setup(self, pins, direction):
        """Setup GPIO pins"""
        if not isinstance(pins, list):
            pins = [pins]
            
        try:
            if GPIO_BACKEND == "gpiod":
                for pin in pins:
                    line = self.chip.get_line(pin)
                    if direction == self.OUT:
                        line.request(consumer="robot", type=gpiod.LINE_REQ_DIR_OUT)
                    else:
                        line.request(consumer="robot", type=gpiod.LINE_REQ_DIR_IN)
                    self.pins[pin] = line
                logger.debug(f"Pins {pins} setup as {'OUTPUT' if direction == self.OUT else 'INPUT'}")
            else:
                import RPi.GPIO as GPIO
                GPIO.setup(pins, GPIO.OUT if direction == self.OUT else GPIO.IN)
        except Exception as e:
            logger.error(f"Pin setup failed: {e}")
    
    def output(self, pin, value):
        """Write to GPIO pin"""
        try:
            if GPIO_BACKEND == "gpiod":
                if isinstance(pin, list):
                    # Handle list of pins
                    for p in pin:
                        if p in self.pins:
                            self.pins[p].set_value(value)
                else:
                    if pin in self.pins:
                        self.pins[pin].set_value(value)
            else:
                import RPi.GPIO as GPIO
                GPIO.output(pin, value)
        except Exception as e:
            logger.error(f"GPIO output failed on pin {pin}: {e}")
    
    def input(self, pin):
        """Read from GPIO pin"""
        try:
            if GPIO_BACKEND == "gpiod":
                if pin in self.pins:
                    return self.pins[pin].get_value()
                return 0
            else:
                import RPi.GPIO as GPIO
                return GPIO.input(pin)
        except Exception as e:
            logger.error(f"GPIO input failed on pin {pin}: {e}")
            return 0
    
    def PWM(self, pin, frequency):
        """Create PWM object"""
        try:
            if GPIO_BACKEND == "gpiod":
                return PWM_Pi5(pin, frequency)
            else:
                import RPi.GPIO as GPIO
                return GPIO.PWM(pin, frequency)
        except Exception as e:
            logger.error(f"PWM creation failed: {e}")
            return None
    
    def cleanup(self, pins=None):
        """Cleanup GPIO"""
        try:
            if GPIO_BACKEND == "gpiod":
                if pins:
                    if not isinstance(pins, list):
                        pins = [pins]
                    for pin in pins:
                        if pin in self.pins:
                            self.pins[pin].release()
                            del self.pins[pin]
                else:
                    for pin in list(self.pins.keys()):
                        self.pins[pin].release()
                    self.pins.clear()
                logger.debug("GPIO cleaned up")
            else:
                import RPi.GPIO as GPIO
                GPIO.cleanup(pins)
        except Exception as e:
            logger.debug(f"GPIO cleanup: {e}")


class PWM_Pi5:
    """Pi 5 compatible PWM wrapper"""
    
    def __init__(self, pin, frequency):
        self.pin = pin
        self.frequency = frequency
        self.duty_cycle = 0
        self.running = False
        
    def start(self, duty_cycle):
        """Start PWM"""
        self.duty_cycle = duty_cycle
        self.running = True
        logger.debug(f"PWM started on pin {self.pin} at {duty_cycle}%")
    
    def ChangeDutyCycle(self, duty_cycle):
        """Change PWM duty cycle"""
        self.duty_cycle = duty_cycle
        logger.debug(f"PWM duty cycle changed to {duty_cycle}% on pin {self.pin}")
    
    def stop(self):
        """Stop PWM"""
        self.running = False
        logger.debug(f"PWM stopped on pin {self.pin}")


# Create global GPIO instance
GPIO = GPIO_Pi5()

# Disable warnings if using RPi.GPIO
if GPIO_BACKEND == "RPi.GPIO":
    try:
        import RPi.GPIO as RPi_GPIO
        RPi_GPIO.setwarnings(False)
    except:
        pass


if __name__ == "__main__":
    print(f"✅ GPIO wrapper loaded - Backend: {GPIO_BACKEND}")
    print(f"✅ Using gpiochip0 for Pi 5 compatibility")
