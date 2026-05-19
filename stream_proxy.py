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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
current_frame = None
frame_lock = threading.Lock()

class MJPEGHandler(BaseHTTPRequestHandler):
    """HTTP handler for MJPEG stream"""
    
    def do_GET(self):
        if self.path == '/stream':
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()
            
            try:
                while True:
                    with frame_lock:
                        if current_frame is not None:
                            ret, jpeg = cv2.imencode('.jpg', current_frame)
                            if ret:
                                self.wfile.write(b'--frame\r\n')
                                self.wfile.write(b'Content-Type: image/jpeg\r\n')
                                self.wfile.write(f'Content-Length: {len(jpeg)}\r\n\r\n'.encode())
                                self.wfile.write(jpeg.tobytes())
                                self.wfile.write(b'\r\n')
                    time.sleep(0.03)  # ~30fps
            except Exception as e:
                logger.error(f"Stream error: {e}")
    
    def log_message(self, format, *args):
        pass  # Suppress logging


def read_iphone_stream(url):
    """Read iPhone stream and convert to frames"""
    global current_frame
    
    logger.info(f"Connecting to iPhone stream: {url}")
    
    try:
        response = requests.get(url, stream=True, timeout=10, verify=False)
        
        if response.status_code != 200:
            logger.error(f"HTTP {response.status_code}")
            return
        
        logger.info("Connected! Processing stream...")
        
        # Try to decode as video stream
        buffer = b''
        frame_count = 0
        
        for chunk in response.iter_content(chunk_size=4096):
            if not chunk:
                continue
            
            buffer += chunk
            
            # Try to decode with cv2
            nparr = np.frombuffer(buffer, np.uint8)
            
            try:
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if frame is not None and frame.size > 0:
                    with frame_lock:
                        current_frame = frame
                    frame_count += 1
                    if frame_count % 30 == 0:
                        logger.info(f"Frames processed: {frame_count}")
                    buffer = b''
            except:
                pass
    
    except Exception as e:
        logger.error(f"Stream read error: {e}")


def start_mjpeg_server(host='0.0.0.0', port=8888):
    """Start MJPEG server"""
    server = HTTPServer((host, port), MJPEGHandler)
    logger.info(f"MJPEG server running on http://{host}:{port}/stream")
    
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
