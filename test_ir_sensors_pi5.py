#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi 5 GPIO Test - IR Sensors
Using gpiochip0 (correct for Pi 5)
"""

import sys
import time

try:
    import gpiod
except ImportError:
    print("❌ libgpiod not installed. Installing...")
    import subprocess
    subprocess.run(["pip", "install", "gpiod"], check=True)
    import gpiod

# Pi 5 uses gpiochip0 (NOT gpiochip4)
CHIP_NAME = "gpiochip0"
IR_LEFT = 17
IR_CENTER = 27
IR_RIGHT = 22

def test_ir_sensors():
    """Test IR sensors using libgpiod"""
    try:
        # Open the GPIO chip
        chip = gpiod.Chip(CHIP_NAME)
        print(f"✅ Opened {CHIP_NAME}")
        
        # Get the lines
        line_left = chip.get_line(IR_LEFT)
        line_center = chip.get_line(IR_CENTER)
        line_right = chip.get_line(IR_RIGHT)
        
        print(f"✅ Got GPIO {IR_LEFT} (LEFT)")
        print(f"✅ Got GPIO {IR_CENTER} (CENTER)")
        print(f"✅ Got GPIO {IR_RIGHT} (RIGHT)")
        
        # Request as input
        line_left.request(consumer="ir_test", type=gpiod.LINE_REQ_DIR_IN)
        line_center.request(consumer="ir_test", type=gpiod.LINE_REQ_DIR_IN)
        line_right.request(consumer="ir_test", type=gpiod.LINE_REQ_DIR_IN)
        
        print(f"✅ Configured all pins as INPUT")
        print("\n" + "="*60)
        print("Reading IR sensors (press Ctrl+C to stop):")
        print("="*60 + "\n")
        
        try:
            count = 0
            while True:
                left = line_left.get_value()
                center = line_center.get_value()
                right = line_right.get_value()
                
                # Visual indicators
                left_str = "🟩 ON " if left else "⬛ OFF"
                center_str = "🟩 ON " if center else "⬛ OFF"
                right_str = "🟩 ON " if right else "⬛ OFF"
                
                print(f"[{count:04d}] LEFT={left} {left_str} | CENTER={center} {center_str} | RIGHT={right} {right_str}")
                count += 1
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n✅ Test stopped")
            
        finally:
            # Release lines
            line_left.release()
            line_center.release()
            line_right.release()
            print("✅ GPIO lines released")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check IR sensors are connected to GPIO 17, 27, 22")
        print("2. Verify power supply to IR sensors (3.3V)")
        print("3. Check sensor LED is blinking (indicates power)")
        print("4. Run with: sudo python3 test_ir_sensors_pi5.py")
        sys.exit(1)

if __name__ == "__main__":
    test_ir_sensors()
