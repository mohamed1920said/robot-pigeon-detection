#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Camera Testing Utility
Test different camera types before running the full robot
"""

import logging
import time
import cv2
from camera_handler import CameraHandler
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_xiaomi_http():
    """Test Xiaomi HTTP camera"""
    print("\n" + "="*60)
    print("Testing Xiaomi HTTP Camera")
    print("="*60)
    print(f"IP: {config.XIAOMI_CAMERA_IP}")
    print(f"Port: {config.XIAOMI_CAMERA_PORT}")
    
    handler = CameraHandler(camera_type="xiaomi_http")
    
    if handler.connect():
        print("✅ Connected!")
        
        print("\nReading 5 frames...")
        for i in range(5):
            ret, frame = handler.read()
            if ret:
                print(f"  Frame {i+1}: ✅ {frame.shape}")
            else:
                print(f"  Frame {i+1}: ❌ Failed")
            time.sleep(0.5)
        
        handler.release()
        return True
    else:
        print("❌ Connection failed")
        return False


def test_xiaomi_rtsp():
    """Test Xiaomi RTSP camera"""
    print("\n" + "="*60)
    print("Testing Xiaomi RTSP Camera")
    print("="*60)
    print(f"IP: {config.XIAOMI_CAMERA_IP}")
    
    handler = CameraHandler(camera_type="xiaomi_rtsp")
    
    if handler.connect():
        print("✅ Connected!")
        
        print("\nReading 5 frames...")
        for i in range(5):
            ret, frame = handler.read()
            if ret:
                print(f"  Frame {i+1}: ✅ {frame.shape}")
            else:
                print(f"  Frame {i+1}: ❌ Failed")
            time.sleep(0.5)
        
        handler.release()
        return True
    else:
        print("❌ Connection failed")
        return False


def test_usb():
    """Test USB camera"""
    print("\n" + "="*60)
    print("Testing USB Camera")
    print("="*60)
    
    handler = CameraHandler(camera_type="usb")
    
    if handler.connect():
        print("✅ Connected!")
        
        print("\nReading 5 frames...")
        for i in range(5):
            ret, frame = handler.read()
            if ret:
                print(f"  Frame {i+1}: ✅ {frame.shape}")
            else:
                print(f"  Frame {i+1}: ❌ Failed")
            time.sleep(0.5)
        
        handler.release()
        return True
    else:
        print("❌ Connection failed")
        return False


def test_local():
    """Test local Pi camera"""
    print("\n" + "="*60)
    print("Testing Local Pi Camera")
    print("="*60)
    print(f"Index: {config.CAMERA_INDEX}")
    
    handler = CameraHandler(camera_type="local")
    
    if handler.connect():
        print("✅ Connected!")
        
        print("\nReading 5 frames...")
        for i in range(5):
            ret, frame = handler.read()
            if ret:
                print(f"  Frame {i+1}: ✅ {frame.shape}")
            else:
                print(f"  Frame {i+1}: ❌ Failed")
            time.sleep(0.5)
        
        handler.release()
        return True
    else:
        print("❌ Connection failed")
        return False


def test_test_mode():
    """Test test image mode"""
    print("\n" + "="*60)
    print("Testing Test Mode")
    print("="*60)
    
    handler = CameraHandler(camera_type="test")
    
    if handler.connect():
        print("✅ Connected!")
        
        print("\nReading 5 frames...")
        for i in range(5):
            ret, frame = handler.read()
            if ret:
                print(f"  Frame {i+1}: ✅ {frame.shape}")
            else:
                print(f"  Frame {i+1}: ❌ Failed")
            time.sleep(0.5)
        
        handler.release()
        return True
    else:
        print("❌ Connection failed")
        return False


def test_configured_camera():
    """Test configured camera"""
    print("\n" + "="*60)
    print(f"Testing Configured Camera: {config.CAMERA_TYPE}")
    print("="*60)
    
    handler = CameraHandler()
    
    if handler.connect():
        print("✅ Connected!")
        
        print("\nReading 5 frames...")
        for i in range(5):
            ret, frame = handler.read()
            if ret:
                print(f"  Frame {i+1}: ✅ {frame.shape}")
            else:
                print(f"  Frame {i+1}: ❌ Failed")
            time.sleep(0.5)
        
        handler.release()
        return True
    else:
        print("❌ Connection failed")
        return False


def ping_camera():
    """Ping camera to check connectivity"""
    print("\n" + "="*60)
    print("Pinging Xiaomi Camera")
    print("="*60)
    
    import os
    result = os.system(f"ping -c 2 {config.XIAOMI_CAMERA_IP} > /dev/null 2>&1")
    
    if result == 0:
        print(f"✅ Camera at {config.XIAOMI_CAMERA_IP} is reachable")
        return True
    else:
        print(f"❌ Camera at {config.XIAOMI_CAMERA_IP} is NOT reachable")
        return False


def main():
    """Main test function"""
    print("\n" + "="*60)
    print("🎥 Robot Pigeon Detection - Camera Tester")
    print("="*60)
    
    results = {}
    
    # Ping test first
    if ping_camera():
        # Test each camera type
        results["Xiaomi HTTP"] = test_xiaomi_http()
        results["Xiaomi RTSP"] = test_xiaomi_rtsp()
    else:
        print("\n⚠️  Camera is not reachable on network")
        print("   Make sure:")
        print(f"   1. Camera IP is correct: {config.XIAOMI_CAMERA_IP}")
        print("   2. Camera is powered on")
        print("   3. Camera is connected to same WiFi")
        print("   4. Firewall allows connection")
    
    results["USB Camera"] = test_usb()
    results["Local Camera"] = test_local()
    results["Test Mode"] = test_test_mode()
    
    # Summary
    print("\n" + "="*60)
    print("📊 Summary")
    print("="*60)
    
    for camera_type, success in results.items():
        status = "✅ OK" if success else "❌ Failed"
        print(f"  {camera_type:20} {status}")
    
    # Recommendation
    print("\n" + "="*60)
    print("💡 Recommendation")
    print("="*60)
    
    working_cameras = [k for k, v in results.items() if v]
    
    if working_cameras:
        best = working_cameras[0]
        print(f"\n✅ Use: {best}")
        print(f"\nUpdate config.py:")
        print(f"  CAMERA_TYPE = \"{best.lower().replace(' ', '_')}\"")
    else:
        print("\n⚠️  No cameras working!")
        print("   Using TEST mode for now")
        print("   Update config.py:")
        print("   CAMERA_TYPE = \"test\"")
    
    print("\nThen run the robot:")
    print("  python3 robot_pi.py")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
