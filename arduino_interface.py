#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Arduino Interface for Pi 5
Communicates with Arduino Uno via USB Serial
Sends motor commands and reads ultrasonic sensor data
"""

import serial
import time
import logging
import threading
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class ArduinoInterface:
    """Interface to communicate with Arduino Uno"""
    
    def __init__(self, port: str = "/dev/ttyUSB0", baud: int = 115200, timeout: float = 1.0):
        """
        Initialize Arduino interface
        
        Args:
            port: Serial port (e.g., /dev/ttyUSB0 on Linux, COM3 on Windows)
            baud: Baud rate (must match Arduino)
            timeout: Serial read timeout
        """
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.serial = None
        self.connected = False
        
        # Sensor data
        self.distances = {
            'front': 0.0,
            'left': 0.0,
            'right': 0.0,
            'back': 0.0
        }
        
        # Communication thread
        self.read_thread = None
        self.running = False
        self.lock = threading.Lock()
    
    def connect(self) -> bool:
        """Connect to Arduino via serial port"""
        try:
            logger.info(f"Connecting to Arduino on {self.port}...")
            
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                timeout=self.timeout,
                write_timeout=self.timeout
            )
            
            time.sleep(2)  # Wait for Arduino to reset
            
            # Clear any buffered data
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            
            self.connected = True
            self.running = True
            
            # Start reading thread
            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()
            
            logger.info("✅ Connected to Arduino")
            return True
        
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from Arduino"""
        try:
            self.running = False
            if self.read_thread:
                self.read_thread.join(timeout=2)
            if self.serial:
                self.serial.close()
            self.connected = False
            logger.info("Disconnected from Arduino")
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
    
    def _read_loop(self):
        """Background thread to read Arduino responses"""
        while self.running:
            try:
                if self.serial and self.serial.in_waiting > 0:
                    line = self.serial.readline().decode('utf-8', errors='ignore').strip()
                    
                    if line:
                        self._parse_response(line)
            
            except Exception as e:
                logger.debug(f"Read error: {e}")
                time.sleep(0.1)
    
    def _parse_response(self, response: str):
        """Parse Arduino response"""
        try:
            parts = response.split(',')
            command = parts[0]
            
            if command == "SENSORS":
                # SENSORS,front,left,right,back
                with self.lock:
                    self.distances['front'] = float(parts[1])
                    self.distances['left'] = float(parts[2])
                    self.distances['right'] = float(parts[3])
                    self.distances['back'] = float(parts[4])
            
            elif command == "MOV":
                logger.debug(f"Motor move: {response}")
            
            elif command == "STOP":
                logger.debug("Motors stopped")
            
            elif command == "RELAY":
                logger.info(f"Relay {parts[1]}")
            
            elif command == "ERROR":
                logger.error(f"Arduino error: {parts[1]}")
        
        except Exception as e:
            logger.debug(f"Parse error: {e}")
    
    def _send_command(self, cmd: str) -> bool:
        """Send command to Arduino"""
        if not self.connected:
            logger.error("Arduino not connected")
            return False
        
        try:
            self.serial.write((cmd + '\n').encode('utf-8'))
            logger.debug(f"Sent: {cmd}")
            return True
        
        except Exception as e:
            logger.error(f"Send error: {e}")
            self.connected = False
            return False
    
    # ==================== MOTOR COMMANDS ====================
    
    def move_forward(self, left_speed: int = 200, right_speed: int = 200):
        """Move forward"""
        return self._send_command(f"MOV,{left_speed},{right_speed},1")
    
    def move_backward(self, left_speed: int = 200, right_speed: int = 200):
        """Move backward"""
        return self._send_command(f"MOV,{left_speed},{right_speed},-1")
    
    def stop(self):
        """Stop motors"""
        return self._send_command("STOP")
    
    def turn_left(self, speed: int = 150):
        """Turn left"""
        return self._send_command(f"TURN,{speed},-1")
    
    def turn_right(self, speed: int = 150):
        """Turn right"""
        return self._send_command(f"TURN,{speed},1")
    
    def set_motor_speed(self, left_speed: int, right_speed: int, direction: int = 1):
        """
        Set motor speeds directly
        
        Args:
            left_speed: 0-255
            right_speed: 0-255
            direction: 1=forward, -1=backward, 0=stop
        """
        return self._send_command(f"MOV,{left_speed},{right_speed},{direction}")
    
    # ==================== RELAY COMMANDS ====================
    
    def relay_on(self):
        """Turn relay on"""
        return self._send_command("RELAY,1")
    
    def relay_off(self):
        """Turn relay off"""
        return self._send_command("RELAY,0")
    
    # ==================== SENSOR COMMANDS ====================
    
    def read_sensors(self):
        """Request sensor reading"""
        self._send_command("SENSORS")
        time.sleep(0.2)  # Wait for response
        return self.get_distances()
    
    def get_distances(self) -> Dict[str, float]:
        """Get latest sensor distances"""
        with self.lock:
            return self.distances.copy()
    
    def get_distance(self, direction: str) -> float:
        """
        Get distance for specific sensor
        
        Args:
            direction: 'front', 'left', 'right', 'back'
        
        Returns:
            Distance in cm
        """
        with self.lock:
            return self.distances.get(direction, -1.0)
    
    def obstacle_detected(self, threshold: float = 20.0) -> bool:
        """Check if obstacle detected in front"""
        return self.get_distance('front') < threshold and self.get_distance('front') > 0
    
    def is_ready(self) -> bool:
        """Check if Arduino is connected and ready"""
        return self.connected


# ==================== STANDALONE TEST ====================

def test_arduino():
    """Test Arduino interface"""
    arduino = ArduinoInterface()
    
    if not arduino.connect():
        logger.error("Failed to connect")
        return
    
    time.sleep(1)
    
    try:
        # Test movement
        logger.info("\n🚀 Moving forward...")
        arduino.move_forward(200, 200)
        time.sleep(2)
        
        logger.info("🛑 Stopping...")
        arduino.stop()
        time.sleep(1)
        
        # Test turning
        logger.info("↪️  Turning right...")
        arduino.turn_right(150)
        time.sleep(2)
        
        logger.info("🛑 Stopping...")
        arduino.stop()
        time.sleep(1)
        
        # Test sensors
        logger.info("\n📡 Reading sensors...")
        for i in range(10):
            distances = arduino.read_sensors()
            logger.info(f"Front: {distances['front']:.2f}cm, "
                       f"Left: {distances['left']:.2f}cm, "
                       f"Right: {distances['right']:.2f}cm, "
                       f"Back: {distances['back']:.2f}cm")
            time.sleep(0.5)
        
        # Test relay
        logger.info("\n🔌 Testing relay...")
        arduino.relay_on()
        time.sleep(1)
        arduino.relay_off()
        
        logger.info("\n✅ All tests completed!")
    
    except KeyboardInterrupt:
        logger.info("Test interrupted")
    
    finally:
        arduino.disconnect()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    test_arduino()
