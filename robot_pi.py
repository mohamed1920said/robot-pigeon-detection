#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robot Pigeon Detection - Main Control with Arduino Integration
Detects pigeons and controls robot via Arduino Uno
"""

import cv2
import logging
import time
import threading
from pathlib import Path
from datetime import datetime

import numpy as np
from ultralytics import YOLO

import config
from camera_handler import CameraHandler
from arduino_interface import ArduinoInterface

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RobotController:
    """Main robot control system with Arduino integration"""
    
    def __init__(self):
        """Initialize robot"""
        self.camera = None
        self.arduino = None
        self.model = None
        self.running = False
        
        # Stats
        self.stats = {
            'detections': 0,
            'distance': 0,
            'frame_count': 0,
            'start_time': time.time()
        }
        
        # Detection parameters
        self.confidence_threshold = config.CONFIDENCE_THRESHOLD
        self.detection_class = 14  # COCO class 14 = bird
        
        logger.info("🤖 Initializing Robot...")
    
    def setup(self) -> bool:
        """Setup all systems"""
        try:
            # Load model
            logger.info(f"Loading YOLO model: {config.MODEL_PATH}")
            self.model = YOLO(config.MODEL_PATH)
            logger.info(f"✅ Model loaded: {config.MODEL_PATH}")
            
            # Setup camera
            self.camera = CameraHandler(config.CAMERA_TYPE)
            if not self.camera.connect():
                logger.warning("⚠️  Camera setup failed")
            
            # Setup Arduino
            logger.info(f"Connecting to Arduino on {config.ARDUINO_PORT}...")
            self.arduino = ArduinoInterface(
                port=config.ARDUINO_PORT,
                baud=config.ARDUINO_BAUD
            )
            
            if not self.arduino.connect():
                logger.error("❌ Arduino connection failed")
                return False
            
            logger.info("✅ Arduino connected")
            
            time.sleep(1)
            logger.info("✅ All systems ready")
            return True
        
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return False
    
    def detect_pigeons(self, frame) -> list:
        """Detect pigeons in frame"""
        try:
            results = self.model(frame, conf=self.confidence_threshold)
            detections = []
            
            for result in results:
                for box in result.boxes:
                    conf = float(box.conf[0])
                    
                    if conf >= self.confidence_threshold:
                        x1, y1, x2, y2 = box.xyxy[0]
                        
                        detection = {
                            'x1': int(x1),
                            'y1': int(y1),
                            'x2': int(x2),
                            'y2': int(y2),
                            'conf': conf,
                            'center_x': int((x1 + x2) / 2),
                            'center_y': int((y1 + y2) / 2)
                        }
                        
                        detections.append(detection)
            
            if detections:
                self.stats['detections'] += len(detections)
            
            return detections
        
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return []
    
    def move_towards_pigeon(self, detection, frame_width: int):
        """Move robot towards detected pigeon"""
        try:
            center_x = detection['center_x']
            
            # Frame center
            frame_center = frame_width / 2
            
            # Calculate error
            error = center_x - frame_center
            
            # Threshold for straight movement
            threshold = 50
            
            if abs(error) < threshold:
                # Move forward
                logger.info("→ Moving forward")
                self.arduino.move_forward(config.BASE_SPEED, config.BASE_SPEED)
            
            elif error > 0:
                # Pigeon on right, turn right
                logger.info("↪️  Turning right")
                self.arduino.turn_right(config.BASE_SPEED)
            
            else:
                # Pigeon on left, turn left
                logger.info("↪️  Turning left")
                self.arduino.turn_left(config.BASE_SPEED)
        
        except Exception as e:
            logger.error(f"Movement error: {e}")
    
    def check_obstacles(self) -> bool:
        """Check for obstacles using ultrasonic sensors"""
        try:
            front_distance = self.arduino.get_distance('front')
            
            self.stats['distance'] = front_distance
            
            if front_distance > 0 and front_distance < config.OBSTACLE_THRESHOLD:
                logger.warning(f"⚠️  Obstacle detected: {front_distance:.2f}cm")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Obstacle check error: {e}")
            return False
    
    def draw_detections(self, frame, detections) -> np.ndarray:
        """Draw detection boxes on frame"""
        for detection in detections:
            x1, y1, x2, y2 = detection['x1'], detection['y1'], detection['x2'], detection['y2']
            conf = detection['conf']
            
            # Draw box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw label
            label = f"Pigeon {conf:.2f}"
            cv2.putText(frame, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Draw center point
            center_x = detection['center_x']
            center_y = detection['center_y']
            cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
        
        return frame
    
    def draw_stats(self, frame) -> np.ndarray:
        """Draw statistics on frame"""
        h, w = frame.shape[:2]
        
        stats_text = [
            f"Detections: {self.stats['detections']}",
            f"Distance: {self.stats['distance']:.2f}cm",
            f"FPS: {self.get_fps():.1f}",
            f"Time: {self.get_runtime():.0f}s"
        ]
        
        y_offset = 30
        for text in stats_text:
            cv2.putText(frame, text, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            y_offset += 30
        
        return frame
    
    def get_fps(self) -> float:
        """Calculate FPS"""
        elapsed = time.time() - self.stats['start_time']
        if elapsed > 0:
            return self.stats['frame_count'] / elapsed
        return 0
    
    def get_runtime(self) -> float:
        """Get runtime in seconds"""
        return time.time() - self.stats['start_time']
    
    def run(self):
        """Main robot loop"""
        if not self.setup():
            logger.error("Setup failed, exiting")
            return
        
        self.running = True
        
        try:
            logger.info("🚀 Robot started")
            
            while self.running:
                # Read frame
                ret, frame = self.camera.read()
                
                if not ret or frame is None:
                    logger.warning("Failed to read frame")
                    time.sleep(1)
                    continue
                
                self.stats['frame_count'] += 1
                
                # Detect pigeons
                detections = self.detect_pigeons(frame)
                
                if detections:
                    logger.info(f"🕊️  Detected {len(detections)} pigeon(s)")
                    
                    # Check for obstacles
                    if self.check_obstacles():
                        logger.warning("Obstacle detected, stopping")
                        self.arduino.stop()
                        self.arduino.relay_on()  # Activate alarm
                    
                    else:
                        # Move towards pigeon
                        best_detection = max(detections, key=lambda x: x['conf'])
                        self.move_towards_pigeon(best_detection, frame.shape[1])
                
                else:
                    # No pigeon detected, stop
                    self.arduino.stop()
                
                # Draw on frame
                frame = self.draw_detections(frame, detections)
                frame = self.draw_stats(frame)
                
                # Display
                if config.SHOW_OUTPUT:
                    cv2.imshow("Robot Vision", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                # Log stats periodically
                if self.stats['frame_count'] % 30 == 0:
                    logger.info(f"Frame {self.stats['frame_count']} | "
                               f"Detections: {self.stats['detections']} | "
                               f"FPS: {self.get_fps():.1f}")
        
        except KeyboardInterrupt:
            logger.info("🛑 Interrupted by user")
        
        except Exception as e:
            logger.error(f"Runtime error: {e}")
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up...")
        
        try:
            self.running = False
            
            if self.arduino:
                self.arduino.stop()
                self.arduino.relay_off()
                self.arduino.disconnect()
            
            if self.camera:
                self.camera.release()
            
            cv2.destroyAllWindows()
            
            logger.info(f"✅ Total detections: {self.stats['detections']}")
            logger.info(f"✅ Total runtime: {self.get_runtime():.0f}s")
            logger.info(f"✅ Average FPS: {self.get_fps():.1f}")
            logger.info("Cleanup complete")
        
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


def main():
    """Main entry point"""
    robot = RobotController()
    robot.run()


if __name__ == "__main__":
    main()
