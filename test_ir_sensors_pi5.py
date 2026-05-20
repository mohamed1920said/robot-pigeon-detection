#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi 5 GPIO Test - IR Sensors
Direct gpiod backend for Pi 5 compatibility
"""

import sys

try:
    import gpiod
except ImportError:
    print("❌ libgpiod not installed. Installing...")
    import subprocess
    subprocess.run(["pip", "install", "libgpiod-python"], check=True)
    import gpiod

# Pi 5 uses gpiochip4
CHIP_NAME = "gpiochip4"
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
        
        # Request as input
        line_left.request(consumer="ir_test", type=gpiod.LINE_REQ_DIR_IN)
        line_center.request(consumer="ir_test", type=gpiod.LINE_REQ_DIR_IN)
        line_right.request(consumer="ir_test", type=gpiod.LINE_REQ_DIR_IN)
        
        print(f"✅ GPIO {IR_LEFT} (LEFT): Ready")
        print(f"✅ GPIO {IR_CENTER} (CENTER): Ready")
        print(f"✅ GPIO {IR_RIGHT} (RIGHT): Ready")
        print("\nReading IR sensors (press Ctrl+C to stop):\n")
        
        import time
        try:
            while True:
                left = line_left.get_value()
                center = line_center.get_value()
                right = line_right.get_value()
                
                status = "🟩" if left else "⬛"
                print(f"IR: LEFT={left} {status} | CENTER={center} {'🟩' if center else '⬛'} | RIGHT={right} {'🟩' if right else '⬛'}")
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n✅ Stopped")
        finally:
            # Release lines
            line_left.release()
            line_center.release()
            line_right.release()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check IR sensors are connected to GPIO 17, 27, 22")
        print("2. Verify power supply to IR sensors")
        print("3. Check sensor LED is blinking (indicates power)")
        sys.exit(1)

if __name__ == "__main__":
    test_ir_sensors()
