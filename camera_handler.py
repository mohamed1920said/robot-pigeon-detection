#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Universal Camera Handler
Supports: iPhone (HTTP), Xiaomi HTTP, Xiaomi RTSP, USB, Local Pi Camera, Test Mode
"""

import cv2
import logging
import time
from typing import Tuple, Optional
import numpy as np

logger = logging.getLogger(__name__)


class CameraHandler:
    """Universal camera handler for different camera types"""
    
    def __init__(self, camera_type: str = None):
        """
        Initialize camera handler
        
        Args:
            camera_type: Type of camera ("xiaomi_http", "xiaomi_rtsp", "usb", "local", "test")
                        If None, uses config.CAMERA_TYPE
        """
        import config
        
        self.camera_type = camera_type or config.CAMERA_TYPE
        self.camera = None
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 3
        
        logger.info(f"Camera Handler initialized for type: {self.camera_type}")
    
    def connect(self) -> bool:
        """Connect to camera based on type"""
        try:
            if self.camera_type == "xiaomi_http":
                return self._connect_xiaomi_http()
            elif self.camera_type == "xiaomi_rtsp":
                return self._connect_xiaomi_rtsp()
            elif self.camera_type == "usb":
                return self._connect_usb()
            elif self.camera_type == "local":
                return self._connect_local()
            elif self.camera_type == "test":
                return self._connect_test()
            else:
                logger.error(f"Unknown camera type: {self.camera_type}")
                return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    def _connect_xiaomi_http(self) -> bool:
        """Connect to Xiaomi camera via HTTP MJPEG"""
        try:
            import config
            
            # Try multiple URL formats for iPhone streaming and Xiaomi
            urls = [
                # iPhone streaming (primary)
                f"http://{config.XIAOMI_CAMERA_IP}:{config.XIAOMI_CAMERA_PORT}/video",
                f"http://{config.XIAOMI_CAMERA_IP}:{config.XIAOMI_CAMERA_PORT}",
                
                # Xiaomi camera URLs
                f"http://{config.XIAOMI_CAMERA_IP}:{config.XIAOMI_CAMERA_PORT}/mjpg/video.mjpg",
                f"http://{config.XIAOMI_CAMERA_IP}:8080/mjpg/video.mjpg",
                f"http://{config.XIAOMI_CAMERA_IP}:8888/mjpg/video.mjpg",
                f"http://{config.XIAOMI_CAMERA_IP}:8080/video",
            ]
            
            for url in urls:
                logger.info(f"Connecting to HTTP: {url}")
                
                self.camera = cv2.VideoCapture(url)
                
                if not self.camera.isOpened():
                    logger.debug(f"Failed to open: {url}")
                    continue
                
                # Try to read a frame
                ret, frame = self.camera.read()
                if ret:
                    logger.info(f"✅ Connected to HTTP: {url}")
                    self.is_connected = True
                    return True
                else:
                    logger.debug(f"Failed to read frame from: {url}")
                    self.camera.release()
            
            logger.warning("Failed to connect to any HTTP URL")
            return False
            
        except Exception as e:
            logger.error(f"HTTP connection error: {e}")
            return False
    
    def _connect_xiaomi_rtsp(self) -> bool:
        """Connect to Xiaomi camera via RTSP"""
        try:
            import config
            
            urls = [
                f"rtsp://{config.XIAOMI_CAMERA_IP}:554/stream",
                f"rtsp://{config.XIAOMI_CAMERA_IP}:554/live",
                f"rtsp://{config.XIAOMI_CAMERA_IP}:8554/stream",
            ]
            
            for url in urls:
                logger.info(f"Trying RTSP: {url}")
                
                self.camera = cv2.VideoCapture(url)
                
                if not self.camera.isOpened():
                    logger.debug(f"Failed to open: {url}")
                    continue
                
                # Try to read a frame with timeout
                self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                ret, frame = self.camera.read()
                
                if ret:
                    logger.info(f"✅ Connected to RTSP: {url}")
                    self.is_connected = True
                    return True
                else:
                    logger.debug(f"Failed to read frame from: {url}")
                    self.camera.release()
            
            logger.warning("Failed to connect to any RTSP URL")
            return False
            
        except Exception as e:
            logger.error(f"RTSP connection error: {e}")
            return False
    
    def _connect_usb(self) -> bool:
        """Connect to USB camera"""
        try:
            logger.info("Searching for USB camera...")
            
            for index in range(10):
                logger.debug(f"Trying index {index}...")
                camera = cv2.VideoCapture(index)
                
                if camera.isOpened():
                    ret, frame = camera.read()
                    if ret:
                        logger.info(f"✅ Found USB camera at index {index}")
                        self.camera = camera
                        self.is_connected = True
                        return True
                    camera.release()
            
            logger.warning("No USB camera found")
            return False
            
        except Exception as e:
            logger.error(f"USB camera connection error: {e}")
            return False
    
    def _connect_local(self) -> bool:
        """Connect to local Pi camera"""
        try:
            import config
            
            indices = [config.CAMERA_INDEX, 19, 20, 0, 1]
            
            for index in indices:
                logger.info(f"Trying local camera at index {index}...")
                
                camera = cv2.VideoCapture(index)
                
                if camera.isOpened():
                    ret, frame = camera.read()
                    if ret:
                        logger.info(f"✅ Local camera connected at index {index}")
                        
                        # Set properties
                        camera.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
                        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
                        camera.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)
                        
                        self.camera = camera
                        self.is_connected = True
                        return True
                    
                    camera.release()
            
            logger.warning("No local camera found")
            return False
            
        except Exception as e:
            logger.error(f"Local camera connection error: {e}")
            return False
    
    def _connect_test(self) -> bool:
        """Connect to test mode (generates test frames)"""
        try:
            logger.info("Test mode: Using generated test frames")
            
            # Create a simple test image
            self.test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(self.test_frame, "TEST MODE", (200, 240),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 2)
            
            self.is_connected = True
            return True
            
        except Exception as e:
            logger.error(f"Test mode error: {e}")
            return False
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read a frame from camera
        
        Returns:
            Tuple of (success, frame)
        """
        if not self.is_connected:
            return False, None
        
        try:
            if self.camera_type == "test":
                # Return test frame with frame counter
                frame = self.test_frame.copy()
                timestamp = int(time.time() * 1000) % 10000
                cv2.putText(frame, f"Frame: {timestamp}", (200, 400),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                return True, frame
            else:
                ret, frame = self.camera.read()
                
                if not ret:
                    # Attempt reconnect
                    if self.reconnect_attempts < self.max_reconnect_attempts:
                        logger.warning(f"Read failed, attempting reconnect ({self.reconnect_attempts+1}/{self.max_reconnect_attempts})")
                        self.reconnect_attempts += 1
                        time.sleep(1)
                        
                        if self.connect():
                            self.reconnect_attempts = 0
                            return self.read()
                    else:
                        logger.error("Max reconnection attempts reached")
                        self.is_connected = False
                
                return ret, frame
                
        except Exception as e:
            logger.error(f"Read error: {e}")
            return False, None
    
    def release(self):
        """Release camera resources"""
        try:
            if self.camera:
                self.camera.release()
            self.is_connected = False
            logger.info("Camera released")
        except Exception as e:
            logger.error(f"Release error: {e}")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.release()
