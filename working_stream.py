#!/usr/bin/env python3
"""Minimal working RealSense stream with debugging"""

import pyrealsense2 as rs
import numpy as np
import cv2
import sys

print("=== RealSense Stream Test ===\n")

# First check if we can detect devices
ctx = rs.context()
devices = ctx.query_devices()

print(f"Found {len(devices)} device(s)")

if len(devices) == 0:
    print("\nNo devices detected by pyrealsense2!")
    print("But USB shows the devices are connected.")
    print("\nPossible solutions:")
    print("1. Unplug and replug the cameras")
    print("2. Try: sudo systemctl restart udev")
    print("3. Reboot the system")
    sys.exit(1)

# List detected devices
for i, device in enumerate(devices):
    print(f"\nDevice {i}:")
    print(f"  Name: {device.get_info(rs.camera_info.name)}")
    print(f"  Serial: {device.get_info(rs.camera_info.serial_number)}")
    print(f"  Firmware: {device.get_info(rs.camera_info.firmware_version)}")

print("\nStarting stream from first device...\n")

# Configure streams
pipeline = rs.pipeline()
config = rs.config()

# Use the first device
device_serial = devices[0].get_info(rs.camera_info.serial_number)
config.enable_device(device_serial)

# Enable streams
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

# Try to also enable depth if available
try:
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    depth_enabled = True
    print("Depth stream enabled")
except:
    depth_enabled = False
    print("Depth stream not available, using color only")

# Start streaming
try:
    pipeline.start(config)
    print("Pipeline started successfully!\n")
    print("Press ESC to exit, 's' to save frame")
except Exception as e:
    print(f"Failed to start pipeline: {e}")
    sys.exit(1)

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
        
        # Get depth if available
        depth_image = None
        if depth_enabled:
            depth_frame = frames.get_depth_frame()
            if depth_frame:
                depth_image = np.asanyarray(depth_frame.get_data())
                depth_colormap = cv2.applyColorMap(
                    cv2.convertScaleAbs(depth_image, alpha=0.03), 
                    cv2.COLORMAP_JET
                )
        
        frame_count += 1
        
        # Add text overlay
        display_image = color_image.copy()
        cv2.putText(display_image, f"Frame: {frame_count}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(display_image, f"Device: {device_serial}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        
        # Show images
        if depth_enabled and depth_image is not None:
            # Show both color and depth
            combined = np.hstack((display_image, depth_colormap))
            cv2.imshow('RealSense Color + Depth', combined)
        else:
            # Show color only
            cv2.imshow('RealSense Color', display_image)
        
        # Handle keyboard
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break
        elif key == ord('s'):
            filename = f"frame_{frame_count}.png"
            cv2.imwrite(filename, color_image)
            print(f"Saved {filename}")
            
finally:
    # Stop streaming
    pipeline.stop()
    cv2.destroyAllWindows()
    print(f"\nStreaming stopped. Total frames: {frame_count}")