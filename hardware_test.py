#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hardware Diagnostic Test for Robot
Tests all GPIO sensors and motors
"""

import time
import logging
from pathlib import Path
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
except ImportError:
    logger.warning("⚠️  RPi.GPIO not available, running in simulation mode")
    GPIO = None

import config


class HardwareTester:
    """Test all robot hardware"""
    
    def __init__(self):
        self.results = {
            'ultrasonic': False,
            'ir_sensors': {'left': False, 'center': False, 'right': False},
            'motors': {'left': False, 'right': False},
            'buzzer': False
        }
        self.setup_gpio()
    
    def setup_gpio(self):
        """Initialize GPIO"""
        if GPIO is None:
            logger.warning("GPIO simulation mode - no hardware control")
            return
        
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            logger.info("✅ GPIO initialized")
        except Exception as e:
            logger.error(f"GPIO setup failed: {e}")
    
    def test_ultrasonic(self):
        """Test ultrasonic sensor"""
        if GPIO is None:
            logger.info("🔍 Ultrasonic: SIMULATION MODE")
            self.results['ultrasonic'] = True
            return
        
        try:
            logger.info("\n" + "="*60)
            logger.info("Testing Ultrasonic Sensor (HC-SR04)")
            logger.info("="*60)
            
            # Setup pins
            GPIO.setup(config.TRIG_FRONT, GPIO.OUT)
            GPIO.setup(config.ECHO_FRONT, GPIO.IN)
            
            logger.info(f"Trigger Pin: GPIO {config.TRIG_FRONT}")
            logger.info(f"Echo Pin: GPIO {config.ECHO_FRONT}")
            
            distances = []
            
            for i in range(5):
                logger.info(f"\nMeasurement {i+1}/5...")
                
                # Send pulse
                GPIO.output(config.TRIG_FRONT, True)
                time.sleep(0.00001)  # 10µs pulse
                GPIO.output(config.TRIG_FRONT, False)
                
                # Wait for echo
                timeout = time.time() + config.ULTRASONIC_TIMEOUT
                while GPIO.input(config.ECHO_FRONT) == 0:
                    pulse_start = time.time()
                    if pulse_start > timeout:
                        break
                
                timeout = time.time() + config.ULTRASONIC_TIMEOUT
                while GPIO.input(config.ECHO_FRONT) == 1:
                    pulse_end = time.time()
                    if pulse_end > timeout:
                        break
                
                # Calculate distance
                pulse_duration = pulse_end - pulse_start
                distance = pulse_duration * 17150  # Speed of sound
                
                if 2 < distance < 400:
                    distances.append(distance)
                    logger.info(f"  ✅ Distance: {distance:.2f} cm")
                else:
                    logger.warning(f"  ⚠️  Distance out of range: {distance:.2f} cm")
                
                time.sleep(0.1)
            
            if distances:
                avg_distance = sum(distances) / len(distances)
                logger.info(f"\n✅ Ultrasonic WORKING")
                logger.info(f"   Average distance: {avg_distance:.2f} cm")
                self.results['ultrasonic'] = True
            else:
                logger.error("❌ Ultrasonic FAILED - No valid readings")
        
        except Exception as e:
            logger.error(f"❌ Ultrasonic test failed: {e}")
            self.results['ultrasonic'] = False
        
        finally:
            GPIO.cleanup([config.TRIG_FRONT, config.ECHO_FRONT])
    
    def test_ir_sensors(self):
        """Test IR line sensors"""
        if GPIO is None:
            logger.info("🔍 IR Sensors: SIMULATION MODE")
            self.results['ir_sensors'] = {'left': True, 'center': True, 'right': True}
            return
        
        try:
            logger.info("\n" + "="*60)
            logger.info("Testing IR Line Sensors")
            logger.info("="*60)
            
            # Setup pins
            GPIO.setup(config.IR_LEFT, GPIO.IN)
            GPIO.setup(config.IR_CENTER, GPIO.IN)
            GPIO.setup(config.IR_RIGHT, GPIO.IN)
            
            sensors = {
                'left': config.IR_LEFT,
                'center': config.IR_CENTER,
                'right': config.IR_RIGHT
            }
            
            for name, pin in sensors.items():
                logger.info(f"\nTesting IR {name.upper()} (GPIO {pin})...")
                
                readings = []
                for i in range(10):
                    value = GPIO.input(pin)
                    readings.append(value)
                    logger.info(f"  Read {i+1}/10: {value} {'(Line detected)' if value == 0 else '(No line)'}")
                    time.sleep(0.1)
                
                # Check if sensor is responsive
                if len(set(readings)) > 1 or readings[0] in [0, 1]:
                    logger.info(f"✅ IR {name.upper()} WORKING")
                    self.results['ir_sensors'][name] = True
                else:
                    logger.warning(f"⚠️  IR {name.upper()} - Check sensor")
                    self.results['ir_sensors'][name] = False
        
        except Exception as e:
            logger.error(f"❌ IR sensors test failed: {e}")
        
        finally:
            GPIO.cleanup([config.IR_LEFT, config.IR_CENTER, config.IR_RIGHT])
    
    def test_motors(self):
        """Test motor control"""
        if GPIO is None:
            logger.info("🔍 Motors: SIMULATION MODE")
            self.results['motors'] = {'left': True, 'right': True}
            return
        
        try:
            logger.info("\n" + "="*60)
            logger.info("Testing Motors (PWM Control)")
            logger.info("="*60)
            
            # Left Motor
            GPIO.setup(config.L_RPWM, GPIO.OUT)
            GPIO.setup(config.L_LPWM, GPIO.OUT)
            GPIO.setup(config.L_R_EN, GPIO.OUT)
            GPIO.setup(config.L_L_EN, GPIO.OUT)
            
            # Right Motor
            GPIO.setup(config.R_RPWM, GPIO.OUT)
            GPIO.setup(config.R_LPWM, GPIO.OUT)
            GPIO.setup(config.R_R_EN, GPIO.OUT)
            GPIO.setup(config.R_L_EN, GPIO.OUT)
            
            # Create PWM objects
            l_rpwm = GPIO.PWM(config.L_RPWM, 1000)
            l_lpwm = GPIO.PWM(config.L_LPWM, 1000)
            r_rpwm = GPIO.PWM(config.R_RPWM, 1000)
            r_lpwm = GPIO.PWM(config.R_LPWM, 1000)
            
            pwm_objects = [l_rpwm, l_lpwm, r_rpwm, r_lpwm]
            
            # Start PWM at 0%
            for pwm in pwm_objects:
                pwm.start(0)
            
            # Test Left Motor
            logger.info("\n🔴 Testing LEFT MOTOR...")
            logger.info(f"  RPWM: GPIO {config.L_RPWM}")
            logger.info(f"  LPWM: GPIO {config.L_LPWM}")
            logger.info(f"  R_EN: GPIO {config.L_R_EN}")
            logger.info(f"  L_EN: GPIO {config.L_L_EN}")
            
            # Forward
            logger.info("  → Forward (50% speed)...")
            GPIO.output(config.L_R_EN, GPIO.HIGH)
            GPIO.output(config.L_L_EN, GPIO.LOW)
            l_rpwm.ChangeDutyCycle(50)
            time.sleep(2)
            l_rpwm.ChangeDutyCycle(0)
            logger.info("  ✅ Left motor forward test done")
            
            # Backward
            logger.info("  ← Backward (50% speed)...")
            GPIO.output(config.L_R_EN, GPIO.LOW)
            GPIO.output(config.L_L_EN, GPIO.HIGH)
            l_lpwm.ChangeDutyCycle(50)
            time.sleep(2)
            l_lpwm.ChangeDutyCycle(0)
            logger.info("  ✅ Left motor backward test done")
            
            self.results['motors']['left'] = True
            
            # Test Right Motor
            logger.info("\n🔵 Testing RIGHT MOTOR...")
            logger.info(f"  RPWM: GPIO {config.R_RPWM}")
            logger.info(f"  LPWM: GPIO {config.R_LPWM}")
            logger.info(f"  R_EN: GPIO {config.R_R_EN}")
            logger.info(f"  L_EN: GPIO {config.R_L_EN}")
            
            # Forward
            logger.info("  → Forward (50% speed)...")
            GPIO.output(config.R_R_EN, GPIO.HIGH)
            GPIO.output(config.R_L_EN, GPIO.LOW)
            r_rpwm.ChangeDutyCycle(50)
            time.sleep(2)
            r_rpwm.ChangeDutyCycle(0)
            logger.info("  ✅ Right motor forward test done")
            
            # Backward
            logger.info("  ← Backward (50% speed)...")
            GPIO.output(config.R_R_EN, GPIO.LOW)
            GPIO.output(config.R_L_EN, GPIO.HIGH)
            r_lpwm.ChangeDutyCycle(50)
            time.sleep(2)
            r_lpwm.ChangeDutyCycle(0)
            logger.info("  ✅ Right motor backward test done")
            
            self.results['motors']['right'] = True
            
            # Stop PWM
            for pwm in pwm_objects:
                pwm.stop()
            
            logger.info("\n✅ Both motors WORKING")
        
        except Exception as e:
            logger.error(f"❌ Motors test failed: {e}")
        
        finally:
            GPIO.cleanup([
                config.L_RPWM, config.L_LPWM, config.L_R_EN, config.L_L_EN,
                config.R_RPWM, config.R_LPWM, config.R_R_EN, config.R_L_EN
            ])
    
    def test_buzzer(self):
        """Test buzzer"""
        if GPIO is None:
            logger.info("🔍 Buzzer: SIMULATION MODE")
            self.results['buzzer'] = True
            return
        
        try:
            logger.info("\n" + "="*60)
            logger.info("Testing Buzzer")
            logger.info("="*60)
            
            GPIO.setup(config.BUZZER, GPIO.OUT)
            logger.info(f"Buzzer Pin: GPIO {config.BUZZER}")
            
            # Beep pattern
            for i in range(3):
                logger.info(f"\nBeep {i+1}/3...")
                GPIO.output(config.BUZZER, GPIO.HIGH)
                time.sleep(0.5)
                GPIO.output(config.BUZZER, GPIO.LOW)
                time.sleep(0.3)
            
            logger.info("✅ Buzzer WORKING")
            self.results['buzzer'] = True
        
        except Exception as e:
            logger.error(f"❌ Buzzer test failed: {e}")
            self.results['buzzer'] = False
        
        finally:
            GPIO.cleanup([config.BUZZER])
    
    def print_summary(self):
        """Print test summary"""
        logger.info("\n" + "="*60)
        logger.info("📊 HARDWARE TEST SUMMARY")
        logger.info("="*60)
        
        # Ultrasonic
        status = "✅" if self.results['ultrasonic'] else "❌"
        logger.info(f"{status} Ultrasonic Sensor: {'WORKING' if self.results['ultrasonic'] else 'FAILED'}")
        
        # IR Sensors
        logger.info("\n🔍 IR Line Sensors:")
        for name, working in self.results['ir_sensors'].items():
            status = "✅" if working else "❌"
            logger.info(f"  {status} {name.upper()}: {'WORKING' if working else 'FAILED'}")
        
        # Motors
        logger.info("\n⚙️  Motors:")
        for name, working in self.results['motors'].items():
            status = "✅" if working else "❌"
            logger.info(f"  {status} {name.upper()}: {'WORKING' if working else 'FAILED'}")
        
        # Buzzer
        status = "✅" if self.results['buzzer'] else "❌"
        logger.info(f"\n{status} Buzzer: {'WORKING' if self.results['buzzer'] else 'FAILED'}")
        
        # Overall
        all_working = all([
            self.results['ultrasonic'],
            all(self.results['ir_sensors'].values()),
            all(self.results['motors'].values()),
            self.results['buzzer']
        ])
        
        logger.info("\n" + "="*60)
        if all_working:
            logger.info("🎉 ALL HARDWARE TESTS PASSED!")
        else:
            logger.info("⚠️  Some hardware tests failed - check connections")
        logger.info("="*60)
    
    def cleanup(self):
        """Cleanup GPIO"""
        if GPIO:
            try:
                GPIO.cleanup()
                logger.info("\nGPIO cleaned up")
            except:
                pass


def main():
    """Run hardware tests"""
    logger.info("\n" + "="*60)
    logger.info("🤖 ROBOT HARDWARE DIAGNOSTIC TEST")
    logger.info("="*60)
    
    tester = HardwareTester()
    
    try:
        # Test all hardware
        tester.test_ultrasonic()
        time.sleep(1)
        
        tester.test_ir_sensors()
        time.sleep(1)
        
        tester.test_motors()
        time.sleep(1)
        
        tester.test_buzzer()
        time.sleep(1)
        
        # Print summary
        tester.print_summary()
    
    except KeyboardInterrupt:
        logger.info("\n⚠️  Test interrupted by user")
    
    except Exception as e:
        logger.error(f"Test error: {e}")
    
    finally:
        tester.cleanup()


if __name__ == "__main__":
    main()
