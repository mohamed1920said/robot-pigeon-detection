#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iPhone Stream Proxy to MJPEG
Converts HTTP video stream to MJPEG for OpenCV compatibility
"""

import cv2
import requests
import threading
import time
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import numpy as np
from urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
current_frame = None
frame_lock = threading.Lock()
frame_event = threading.Event()

class MJPEGHandler(BaseHTTPRequestHandler):
    """HTTP handler for MJPEG stream"""
    
    def do_GET(self):
        if self.path == '/stream':
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
            self.send_header('Connection', 'keep-alive')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            
            try:
                frame_count = 0
                while True:
                    frame_event.wait(timeout=1)
                    frame_event.clear()
                    
                    with frame_lock:
                        if current_frame is not None:
                            ret, jpeg = cv2.imencode('.jpg', current_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                            if ret:
                                try:
                                    self.wfile.write(b'--frame\r\n')
                                    self.wfile.write(b'Content-Type: image/jpeg\r\n')
                                    self.wfile.write(f'Content-Length: {len(jpeg)}\r\n\r\n'.encode())
                                    self.wfile.write(jpeg.tobytes())
                                    self.wfile.write(b'\r\n')
                                    frame_count += 1
                                except:
                                    break
            except Exception as e:
                logger.error(f"Stream error: {e}")
    
    def log_message(self, format, *args):
        pass  # Suppress logging


def read_iphone_stream(url):
    """Read iPhone stream and convert to frames"""
    global current_frame
    
    logger.info(f"Connecting to iPhone stream: {url}")
    
    try:
        # Use session with proper settings
        session = requests.Session()
        session.verify = False
        
        response = session.get(
            url, 
            stream=True, 
            timeout=10,
            verify=False
        )
        
        if response.status_code != 200:
            logger.error(f"HTTP {response.status_code}")
            return
        
        logger.info("✅ Connected! Processing stream...")
        
        buffer = b''
        frame_count = 0
        chunk_count = 0
        
        for chunk in response.iter_content(chunk_size=8192):
            if not chunk:
                continue
            
            chunk_count += 1
            buffer += chunk
            
            # Try multiple frame detection methods
            while len(buffer) > 0:
                # Method 1: JPEG frame boundaries
                a = buffer.find(b'\xff\xd8')
                b = buffer.find(b'\xff\xd9')
                
                if a != -1 and b != -1 and b > a:
                    jpg_data = buffer[a:b+2]
                    
                    try:
                        frame = cv2.imdecode(np.frombuffer(jpg_data, dtype=np.uint8), cv2.IMREAD_COLOR)
                        if frame is not None and frame.size > 0:
                            with frame_lock:
                                current_frame = frame
                            frame_event.set()
                            frame_count += 1
                            
                            if frame_count % 30 == 0:
                                logger.info(f"✅ Frames processed: {frame_count}")
                    except Exception as e:
                        logger.debug(f"Decode error: {e}")
                    
                    buffer = buffer[b+2:]
                else:
                    break
    
    except Exception as e:
        logger.error(f"Stream read error: {e}")
        logger.info("Retrying in 5 seconds...")
        time.sleep(5)
        read_iphone_stream(url)


def start_mjpeg_server(host='0.0.0.0', port=8888):
    """Start MJPEG server"""
    server = HTTPServer((host, port), MJPEGHandler)
    logger.info(f"🎥 MJPEG server running on http://{host}:{port}/stream")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped")
        server.shutdown()


if __name__ == '__main__':
    import sys
    
    iphone_url = "http://192.168.1.47:4747/video"
    
    # Start MJPEG server in background
    server_thread = threading.Thread(target=start_mjpeg_server, daemon=True)
    server_thread.start()
    
    # Start reading iPhone stream
    try:
        read_iphone_stream(iphone_url)
    except KeyboardInterrupt:
        logger.info("Stopped")
        sys.exit(0)
