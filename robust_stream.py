#!/usr/bin/env python3
"""Robust RealSense stream with format fallbacks"""

import pyrealsense2 as rs
import numpy as np
import cv2
import sys

print("=== Robust RealSense Stream ===\n")

# Create context and find devices
ctx = rs.context()
devices = ctx.query_devices()

if len(devices) == 0:
    print("No devices found!")
    sys.exit(1)

print(f"Found {len(devices)} device(s):")
for i, device in enumerate(devices):
    print(f"  Device {i}: {device.get_info(rs.camera_info.name)} (Serial: {device.get_info(rs.camera_info.serial_number)})")

# Use first device
device = devices[0]
device_serial = device.get_info(rs.camera_info.serial_number)
print(f"\nUsing device: {device_serial}")

# Check available streams
print("\nChecking available streams...")
for sensor in device.sensors:
    sensor_name = sensor.get_info(rs.camera_info.name)
    print(f"\nSensor: {sensor_name}")
    
    profiles = sensor.get_stream_profiles()
    for profile in profiles:
        if profile.stream_type() == rs.stream.color:
            vp = profile.as_video_stream_profile()
            print(f"  Color: {vp.width()}x{vp.height()} @ {vp.fps()}fps {vp.format()}")
        elif profile.stream_type() == rs.stream.depth:
            vp = profile.as_video_stream_profile()
            print(f"  Depth: {vp.width()}x{vp.height()} @ {vp.fps()}fps {vp.format()}")

# Try different configurations
configs_to_try = [
    # Config 1: Standard 640x480
    {
        'color': (640, 480, rs.format.bgr8, 30),
        'depth': (640, 480, rs.format.z16, 30),
        'name': '640x480 @ 30fps'
    },
    # Config 2: Lower framerate
    {
        'color': (640, 480, rs.format.bgr8, 15),
        'depth': (640, 480, rs.format.z16, 15),
        'name': '640x480 @ 15fps'
    },
    # Config 3: Different resolution
    {
        'color': (1280, 720, rs.format.bgr8, 30),
        'depth': (1280, 720, rs.format.z16, 30),
        'name': '1280x720 @ 30fps'
    },
    # Config 4: Color only
    {
        'color': (640, 480, rs.format.bgr8, 30),
        'depth': None,
        'name': 'Color only 640x480 @ 30fps'
    },
    # Config 5: RGB format instead of BGR
    {
        'color': (640, 480, rs.format.rgb8, 30),
        'depth': (640, 480, rs.format.z16, 30),
        'name': '640x480 RGB @ 30fps'
    }
]

pipeline = None
successful_config = None

for config_def in configs_to_try:
    print(f"\nTrying configuration: {config_def['name']}")
    
    pipeline = rs.pipeline()
    config = rs.config()
    
    # Enable device
    config.enable_device(device_serial)
    
    try:
        # Enable color stream
        color_params = config_def['color']
        config.enable_stream(rs.stream.color, color_params[0], color_params[1], color_params[2], color_params[3])
        print(f"  Color: {color_params[0]}x{color_params[1]} {color_params[2]} @ {color_params[3]}fps")
        
        # Enable depth stream if specified
        depth_enabled = False
        if config_def['depth']:
            depth_params = config_def['depth']
            config.enable_stream(rs.stream.depth, depth_params[0], depth_params[1], depth_params[2], depth_params[3])
            print(f"  Depth: {depth_params[0]}x{depth_params[1]} {depth_params[2]} @ {depth_params[3]}fps")
            depth_enabled = True
        
        # Try to start
        pipeline.start(config)
        print("  SUCCESS!")
        successful_config = config_def
        break
        
    except Exception as e:
        print(f"  FAILED: {e}")
        try:
            pipeline.stop()
        except:
            pass
        pipeline = None

if pipeline is None:
    print("\nAll configurations failed!")
    sys.exit(1)

print(f"\nStreaming with: {successful_config['name']}")
print("Press ESC to exit, 's' to save frame")

frame_count = 0

try:
    while True:
        # Wait for frames
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        
        if not color_frame:
            continue
        
        # Convert to numpy array
        color_image = np.asanyarray(color_frame.get_data())
        
        # Convert RGB to BGR if needed
        if successful_config['color'][2] == rs.format.rgb8:
            color_image = cv2.cvtColor(color_image, cv2.COLOR_RGB2BGR)
        
        frame_count += 1
        
        # Get depth if available
        display_image = color_image.copy()
        if successful_config['depth']:
            depth_frame = frames.get_depth_frame()
            if depth_frame:
                depth_image = np.asanyarray(depth_frame.get_data())
                depth_colormap = cv2.applyColorMap(
                    cv2.convertScaleAbs(depth_image, alpha=0.03), 
                    cv2.COLORMAP_JET
                )
                
                # Stack horizontally
                display_image = np.hstack((color_image, depth_colormap))
        
        # Add text overlay
        cv2.putText(display_image, f"Frame: {frame_count}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(display_image, f"Config: {successful_config['name']}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        cv2.putText(display_image, f"Device: {device_serial}", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        
        # Show image
        cv2.imshow('RealSense Stream', display_image)
        
        # Handle keyboard
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break
        elif key == ord('s'):
            filename = f"frame_{frame_count}.png"
            cv2.imwrite(filename, color_image)
            print(f"Saved {filename}")
            
finally:
    # Cleanup
    if pipeline:
        pipeline.stop()
    cv2.destroyAllWindows()
    print(f"\nStreaming stopped. Total frames: {frame_count}")