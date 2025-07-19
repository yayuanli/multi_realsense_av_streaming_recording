#!/usr/bin/env python3
"""Grid layout multi-camera WebSocket server with RGB + Depth streaming"""

import asyncio
import websockets
import json
import base64
import cv2
import pyrealsense2 as rs
import numpy as np
from datetime import datetime
import os
from threading import Thread, Lock
import time

class GridCameraRealSenseServer:
    def __init__(self):
        self.pipelines = []
        self.configs = []
        self.camera_serials = []
        self.is_streaming = False
        self.is_recording = False
        self.video_writers = []
        self.frame_lock = Lock()
        self.latest_frames = {}
        self.connected_clients = set()
        self.frame_count = 0
        self.recordings_dir = "recordings"
        
        # Ensure recordings directory exists
        os.makedirs(self.recordings_dir, exist_ok=True)
        
    def find_cameras(self):
        """Find all available RealSense cameras"""
        print("Searching for RealSense cameras...")
        
        ctx = rs.context()
        devices = ctx.query_devices()
        
        if len(devices) == 0:
            raise Exception("No RealSense cameras found")
        
        print(f"Found {len(devices)} RealSense camera(s):")
        
        camera_info = []
        for i, device in enumerate(devices):
            serial = device.get_info(rs.camera_info.serial_number)
            name = device.get_info(rs.camera_info.name)
            firmware = device.get_info(rs.camera_info.firmware_version)
            
            camera_info.append({
                'index': i,
                'serial': serial,
                'name': name,
                'firmware': firmware
            })
            
            print(f"  Camera {i}: {name} (Serial: {serial}, FW: {firmware})")
        
        return camera_info
        
    def initialize_cameras(self):
        """Initialize all available RealSense cameras with RGB + Depth"""
        camera_info = self.find_cameras()
        
        for cam in camera_info:
            try:
                print(f"Initializing camera {cam['index']} (Serial: {cam['serial']})...")
                
                # Create pipeline and config for this camera
                pipeline = rs.pipeline()
                config = rs.config()
                
                # Enable specific device
                config.enable_device(cam['serial'])
                
                # Configure both RGB and Depth streams
                config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
                config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
                
                # Start pipeline
                pipeline.start(config)
                
                # Store pipeline info
                self.pipelines.append(pipeline)
                self.configs.append(config)
                self.camera_serials.append(cam['serial'])
                
                print(f"  Camera {cam['index']} initialized with RGB + Depth!")
                
            except Exception as e:
                print(f"  Failed to initialize camera {cam['index']}: {e}")
                continue
        
        if len(self.pipelines) == 0:
            raise Exception("No cameras could be initialized")
        
        print(f"\nSuccessfully initialized {len(self.pipelines)} camera(s)")
        
    def capture_frames(self):
        """Continuously capture RGB + Depth frames from all cameras"""
        print("Starting frame capture thread...")
        timeout_counts = [0] * len(self.pipelines)
        
        while self.is_streaming:
            frame_data = {}
            
            for i, pipeline in enumerate(self.pipelines):
                try:
                    # Wait for frames
                    frames = pipeline.wait_for_frames(timeout_ms=1000)
                    color_frame = frames.get_color_frame()
                    depth_frame = frames.get_depth_frame()
                    
                    if not color_frame or not depth_frame:
                        continue
                    
                    # Convert to numpy arrays
                    color_image = np.asanyarray(color_frame.get_data())
                    depth_image = np.asanyarray(depth_frame.get_data())
                    
                    # Apply colormap on depth image (from official_minimal_stream.py)
                    depth_colormap = cv2.applyColorMap(
                        cv2.convertScaleAbs(depth_image, alpha=0.03), 
                        cv2.COLORMAP_JET
                    )
                    
                    # Encode both as JPEG
                    _, color_buffer = cv2.imencode('.jpg', color_image, 
                                                 [cv2.IMWRITE_JPEG_QUALITY, 90])
                    color_base64 = base64.b64encode(color_buffer).decode('utf-8')
                    
                    _, depth_buffer = cv2.imencode('.jpg', depth_colormap, 
                                                 [cv2.IMWRITE_JPEG_QUALITY, 90])
                    depth_base64 = base64.b64encode(depth_buffer).decode('utf-8')
                    
                    frame_data[f'cam{i}'] = {
                        'color_image': color_image,
                        'depth_image': depth_image,
                        'color_encoded': color_base64,
                        'depth_encoded': depth_base64,
                        'timestamp': time.time(),
                        'serial': self.camera_serials[i]
                    }
                    
                    # Record if enabled (record color + depth side by side)
                    if self.is_recording and i < len(self.video_writers) and self.video_writers[i]:
                        # Create side-by-side image like official_minimal_stream.py
                        depth_colormap_dim = depth_colormap.shape
                        color_colormap_dim = color_image.shape
                        
                        if depth_colormap_dim != color_colormap_dim:
                            resized_color_image = cv2.resize(
                                color_image, 
                                dsize=(depth_colormap_dim[1], depth_colormap_dim[0]), 
                                interpolation=cv2.INTER_AREA
                            )
                            combined_image = np.hstack((resized_color_image, depth_colormap))
                        else:
                            combined_image = np.hstack((color_image, depth_colormap))
                        
                        self.video_writers[i].write(combined_image)
                    
                    # Reset timeout counter on success
                    timeout_counts[i] = 0
                    
                except RuntimeError as e:
                    timeout_counts[i] += 1
                    if timeout_counts[i] % 20 == 1:
                        print(f"Camera {i} timeout #{timeout_counts[i]}: {e}")
                    continue
                except Exception as e:
                    print(f"Camera {i} capture error: {e}")
                    continue
            
            # Store latest frames if we got any
            if frame_data:
                with self.frame_lock:
                    self.latest_frames = frame_data
                    self.frame_count += 1
            
            # Small delay to prevent CPU overload
            time.sleep(1/60)  # 60 FPS max
    
    def start_recording(self):
        """Start video recording for all cameras"""
        if self.is_recording:
            return []
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filenames = []
        self.video_writers = []
        
        for i, serial in enumerate(self.camera_serials):
            filename = os.path.join(self.recordings_dir, f"camera_{serial}_{timestamp}.mp4")
            
            # Use H.264 codec for better compatibility
            # Video will be side-by-side color + depth, so width is 1280
            fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264
            try:
                writer = cv2.VideoWriter(filename, fourcc, 30.0, (1280, 480))
                if not writer.isOpened():
                    fourcc = cv2.VideoWriter_fourcc(*'XVID')
                    writer = cv2.VideoWriter(filename, fourcc, 30.0, (1280, 480))
            except:
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                writer = cv2.VideoWriter(filename, fourcc, 30.0, (1280, 480))
            
            self.video_writers.append(writer)
            filenames.append(filename)
        
        self.is_recording = True
        print(f"Recording started for {len(filenames)} camera(s):")
        for f in filenames:
            print(f"  {f}")
        
        return filenames
    
    def stop_recording(self):
        """Stop video recording for all cameras"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        for i, writer in enumerate(self.video_writers):
            if writer:
                writer.release()
        
        self.video_writers = []
        print("Recording stopped for all cameras")
    
    async def handle_client(self, websocket):
        """Handle WebSocket client connection"""
        self.connected_clients.add(websocket)
        client_addr = websocket.remote_address
        print(f"Client connected: {client_addr}")
        
        try:
            async for message in websocket:
                data = json.loads(message)
                
                if data.get('action') == 'start_record':
                    filenames = self.start_recording()
                    await websocket.send(json.dumps({
                        'status': 'recording_started',
                        'filenames': filenames
                    }))
                    
                elif data.get('action') == 'stop_record':
                    self.stop_recording()
                    await websocket.send(json.dumps({
                        'status': 'recording_stopped'
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"Client error: {e}")
        finally:
            self.connected_clients.remove(websocket)
            print(f"Client disconnected: {client_addr}")
    
    async def broadcast_frames(self):
        """Broadcast frames to all connected clients"""
        print("Starting frame broadcast...")
        
        while self.is_streaming:
            if self.connected_clients and self.latest_frames:
                with self.frame_lock:
                    frames = self.latest_frames.copy()
                
                # Calculate sync difference between cameras
                timestamps = [frame['timestamp'] for frame in frames.values()]
                sync_diff = (max(timestamps) - min(timestamps)) * 1000 if len(timestamps) > 1 else 0.0
                
                # Create message with camera grid data
                message = {
                    'is_recording': self.is_recording,
                    'frame_number': self.frame_count,
                    'sync_diff': sync_diff,
                    'num_cameras': len(frames),
                    'cameras': []
                }
                
                # Add each camera's RGB + Depth data
                for i, (cam_key, frame_data) in enumerate(frames.items()):
                    camera_data = {
                        'index': i,
                        'serial': frame_data['serial'],
                        'color': frame_data['color_encoded'],
                        'depth': frame_data['depth_encoded'],
                        'timestamp': frame_data['timestamp']
                    }
                    message['cameras'].append(camera_data)
                
                # Send to all clients
                disconnected = set()
                for client in self.connected_clients:
                    try:
                        await client.send(json.dumps(message))
                    except:
                        disconnected.add(client)
                
                # Remove disconnected clients
                self.connected_clients -= disconnected
            
            await asyncio.sleep(1/30)  # ~30 FPS
    
    async def start_server(self, host='localhost', port=8765):
        """Start the WebSocket server"""
        print(f"Starting Grid Camera WebSocket server on {host}:{port}")
        
        # Initialize cameras
        self.initialize_cameras()
        self.is_streaming = True
        
        # Start frame capture thread
        capture_thread = Thread(target=self.capture_frames, daemon=True)
        capture_thread.start()
        
        # Start WebSocket server and frame broadcaster
        server = await websockets.serve(self.handle_client, host, port)
        print(f"WebSocket server running on ws://{host}:{port}")
        print("Open grid_index.html in your browser to view the grid layout")
        
        # Start broadcasting
        await self.broadcast_frames()
    
    def cleanup(self):
        """Clean up resources"""
        print("Cleaning up...")
        self.is_streaming = False
        self.stop_recording()
        
        for pipeline in self.pipelines:
            try:
                pipeline.stop()
            except:
                pass

async def main():
    server = GridCameraRealSenseServer()
    
    try:
        await server.start_server()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Server error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        server.cleanup()

if __name__ == "__main__":
    asyncio.run(main())