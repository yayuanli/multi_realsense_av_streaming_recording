#!/usr/bin/env python3
import subprocess
import re
import sys

# Check for RealSense cameras before importing pyrealsense2
def check_usb_realsense():
    """Check if RealSense cameras are detected via USB"""
    try:
        result = subprocess.run(['lsusb'], capture_output=True, text=True)
        if result.returncode != 0:
            return 0, []
        
        realsense_pattern = r'Bus (\d+) Device (\d+): ID 8086:([0-9a-f]{4}) Intel Corp\.'
        cameras = []
        
        for line in result.stdout.splitlines():
            match = re.search(realsense_pattern, line)
            if match:
                cameras.append({
                    'bus': match.group(1),
                    'device': match.group(2),
                    'product_id': match.group(3),
                    'line': line
                })
        
        return len(cameras), cameras
    except Exception as e:
        print(f"[DEBUG] Error checking USB devices: {e}")
        return 0, []

print("[DEBUG] Checking for RealSense cameras via USB...")
usb_count, usb_cameras = check_usb_realsense()
print(f"[DEBUG] Found {usb_count} RealSense camera(s) via USB")
for cam in usb_cameras:
    print(f"[DEBUG]   - Bus {cam['bus']}, Device {cam['device']}, Product ID: {cam['product_id']}")

try:
    import pyrealsense2 as rs
    print(f"[DEBUG] Successfully imported pyrealsense2")
    # Check if it's the right module
    print(f"[DEBUG] pyrealsense2 module path: {rs.__file__ if hasattr(rs, '__file__') else 'No __file__ attribute'}")
    print(f"[DEBUG] pyrealsense2 attributes: {[attr for attr in dir(rs) if not attr.startswith('_')][:10]}...")
except ImportError as e:
    print(f"[DEBUG] Failed to import pyrealsense2: {e}")
    print("[DEBUG] Trying alternative import...")
    try:
        import pyrealsense2.pyrealsense2 as rs
        print(f"[DEBUG] Successfully imported via pyrealsense2.pyrealsense2")
    except:
        print("[DEBUG] Please install pyrealsense2 properly")
        sys.exit(1)

import numpy as np
import cv2
import asyncio
import websockets
import json
import base64
from datetime import datetime
import os
from threading import Thread, Lock
import time

class SynchronizedRealSenseStreamer:
    def __init__(self, output_folder="recordings"):
        self.output_folder = output_folder
        os.makedirs(output_folder, exist_ok=True)
        
        self.pipeline1 = None
        self.pipeline2 = None
        self.is_recording = False
        self.video_writers = {}
        self.frame_lock = Lock()
        self.latest_frames = {}
        self.connected_clients = set()
        
    def initialize_cameras(self):
        """Initialize two RealSense cameras with synchronized timestamps"""
        print("[DEBUG] Creating RealSense context...")
        
        # Check USB devices first
        usb_count, usb_cameras = check_usb_realsense()
        print(f"[DEBUG] USB check: {usb_count} RealSense camera(s) found")
        
        try:
            context = rs.context()
            print("[DEBUG] Context created successfully")
        except Exception as e:
            print(f"[DEBUG] Failed to create context: {e}")
            raise
        
        print("[DEBUG] Querying devices...")
        try:
            devices = context.query_devices()
            print(f"[DEBUG] query_devices() returned {len(devices)} device(s)")
        except Exception as e:
            print(f"[DEBUG] Failed to query devices: {e}")
            raise
        
        # Print device details
        for i, device in enumerate(devices):
            try:
                print(f"[DEBUG] Device {i}: {device.get_info(rs.camera_info.name)}")
                print(f"[DEBUG]   Serial: {device.get_info(rs.camera_info.serial_number)}")
                print(f"[DEBUG]   USB Type: {device.get_info(rs.camera_info.usb_type_descriptor)}")
            except Exception as e:
                print(f"[DEBUG] Error getting info for device {i}: {e}")
        
        print(f"[DEBUG] Summary: USB sees {usb_count} camera(s), pyrealsense2 sees {len(devices)} camera(s)")
        
        if len(devices) < 1:
            raise Exception(f"Found {len(devices)} RealSense devices. Need at least 1.")
        
        # Modified to work with 1 or 2 cameras
        self.num_cameras = min(len(devices), 2)
        print(f"[DEBUG] Will use {self.num_cameras} camera(s)")
        
        # Get serial numbers
        self.serial1 = devices[0].get_info(rs.camera_info.serial_number)
        print(f"Camera 1: {self.serial1}")
        
        if self.num_cameras > 1:
            self.serial2 = devices[1].get_info(rs.camera_info.serial_number)
            print(f"Camera 2: {self.serial2}")
        else:
            self.serial2 = None
            print("[DEBUG] Only one camera available, running in single camera mode")
        
        # Configure pipelines
        config1 = rs.config()
        config1.enable_device(self.serial1)
        config1.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        
        if self.num_cameras > 1:
            config2 = rs.config()
            config2.enable_device(self.serial2)
            config2.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        
        # Start pipelines
        print("[DEBUG] Creating pipelines...")
        self.pipeline1 = rs.pipeline()
        if self.num_cameras > 1:
            self.pipeline2 = rs.pipeline()
        
        print(f"[DEBUG] Starting pipeline 1 with device {self.serial1}...")
        self.pipeline1.start(config1)
        if self.num_cameras > 1:
            print(f"[DEBUG] Starting pipeline 2 with device {self.serial2}...")
            self.pipeline2.start(config2)
            print("[DEBUG] Both pipelines started successfully")
        else:
            print("[DEBUG] Single pipeline started successfully")
        
        # Allow auto-exposure to settle
        for _ in range(30):
            self.pipeline1.wait_for_frames()
            if self.num_cameras > 1:
                self.pipeline2.wait_for_frames()
    
    def capture_frames(self):
        """Continuously capture frames from both cameras"""
        while True:
            try:
                # Wait for frames with timeout
                frames1 = self.pipeline1.wait_for_frames(timeout_ms=1000)
                frames2 = self.pipeline2.wait_for_frames(timeout_ms=1000)
                
                # Get color frames
                color1 = frames1.get_color_frame()
                color2 = frames2.get_color_frame()
                
                if color1 and color2:
                    # Convert to numpy arrays
                    img1 = np.asanyarray(color1.get_data())
                    img2 = np.asanyarray(color2.get_data())
                    
                    # Get timestamps for synchronization
                    ts1 = frames1.get_timestamp()
                    ts2 = frames2.get_timestamp()
                    
                    with self.frame_lock:
                        self.latest_frames = {
                            'cam1': {'image': img1, 'timestamp': ts1},
                            'cam2': {'image': img2, 'timestamp': ts2},
                            'sync_diff': abs(ts1 - ts2)
                        }
                        
                        # Record if enabled
                        if self.is_recording:
                            self.write_frames(img1, img2)
                            
            except Exception as e:
                print(f"Frame capture error: {e}")
                continue
    
    def write_frames(self, img1, img2):
        """Write frames to video files"""
        if 'cam1' not in self.video_writers:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writers['cam1'] = cv2.VideoWriter(
                os.path.join(self.output_folder, f'cam1_{timestamp}.mp4'),
                fourcc, 30.0, (640, 480)
            )
            self.video_writers['cam2'] = cv2.VideoWriter(
                os.path.join(self.output_folder, f'cam2_{timestamp}.mp4'),
                fourcc, 30.0, (640, 480)
            )
        
        self.video_writers['cam1'].write(img1)
        self.video_writers['cam2'].write(img2)
    
    def start_recording(self):
        """Start recording synchronized streams"""
        with self.frame_lock:
            self.is_recording = True
            print("Recording started")
    
    def stop_recording(self):
        """Stop recording and release video writers"""
        with self.frame_lock:
            self.is_recording = False
            if self.video_writers:
                for writer in self.video_writers.values():
                    writer.release()
                self.video_writers = {}
            print("Recording stopped")
    
    async def websocket_handler(self, websocket, path):
        """Handle WebSocket connections"""
        self.connected_clients.add(websocket)
        try:
            async for message in websocket:
                data = json.loads(message)
                
                if data['action'] == 'start_record':
                    self.start_recording()
                    await websocket.send(json.dumps({'status': 'recording_started'}))
                    
                elif data['action'] == 'stop_record':
                    self.stop_recording()
                    await websocket.send(json.dumps({'status': 'recording_stopped'}))
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.connected_clients.remove(websocket)
    
    async def stream_frames(self):
        """Stream frames to all connected WebSocket clients"""
        while True:
            if self.connected_clients and self.latest_frames:
                with self.frame_lock:
                    frames = self.latest_frames.copy()
                
                # Encode frames as JPEG
                _, buffer1 = cv2.imencode('.jpg', frames['cam1']['image'])
                _, buffer2 = cv2.imencode('.jpg', frames['cam2']['image'])
                
                # Prepare data
                data = {
                    'cam1': base64.b64encode(buffer1).decode('utf-8'),
                    'cam2': base64.b64encode(buffer2).decode('utf-8'),
                    'sync_diff': frames['sync_diff'],
                    'is_recording': self.is_recording
                }
                
                # Send to all clients
                disconnected = set()
                for client in self.connected_clients:
                    try:
                        await client.send(json.dumps(data))
                    except:
                        disconnected.add(client)
                
                self.connected_clients -= disconnected
            
            await asyncio.sleep(0.033)  # ~30 FPS
    
    def run(self):
        """Main run method"""
        # Initialize cameras
        print("[DEBUG] Initializing cameras...")
        self.initialize_cameras()
        
        # Start frame capture thread
        capture_thread = Thread(target=self.capture_frames, daemon=True)
        capture_thread.start()
        
        # Start WebSocket server
        async def main():
            server = await websockets.serve(self.websocket_handler, 'localhost', 8765)
            
            # Run frame streaming
            await self.stream_frames()
        
        asyncio.run(main())
    
    def cleanup(self):
        """Clean up resources"""
        if self.pipeline1:
            self.pipeline1.stop()
        if self.pipeline2:
            self.pipeline2.stop()
        
        self.stop_recording()

if __name__ == "__main__":
    print("[DEBUG] Starting RealSense Streamer...")
    try:
        print(f"[DEBUG] pyrealsense2 version: {rs.__version__}")
    except:
        print("[DEBUG] Could not get pyrealsense2 version")
    
    # Check if running with proper permissions
    print("[DEBUG] Checking permissions...")
    print(f"[DEBUG] User: {os.getenv('USER', 'unknown')}")
    print(f"[DEBUG] Groups: {subprocess.run(['groups'], capture_output=True, text=True).stdout.strip()}")
    
    # Test basic context creation
    print("\n[DEBUG] Testing basic RealSense context...")
    try:
        test_ctx = rs.context()
        print("[DEBUG] Context created successfully")
        test_devices = test_ctx.query_devices()
        print(f"[DEBUG] Initial device count: {len(test_devices)}")
        
        # Try to reset USB if no devices found but USB sees them
        if len(test_devices) == 0 and usb_count > 0:
            print("[DEBUG] No devices found by pyrealsense2 but USB sees cameras")
            print("[DEBUG] This might be a permission issue or the camera needs reset")
            print("[DEBUG] Try running: sudo chmod 666 /dev/bus/usb/001/006")
            print("[DEBUG] Or add your user to the plugdev group: sudo usermod -a -G plugdev $USER")
    except Exception as e:
        print(f"[DEBUG] Error creating context: {e}")
        import traceback
        traceback.print_exc()
    
    streamer = SynchronizedRealSenseStreamer(output_folder="recordings")
    try:
        streamer.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"[DEBUG] Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        streamer.cleanup()