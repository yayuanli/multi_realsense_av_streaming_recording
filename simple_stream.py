#!/usr/bin/env python3
"""Simple RealSense streaming with USB detection"""

import subprocess
import re
import sys
import os

def check_usb_cameras():
    """Check for RealSense cameras via USB"""
    try:
        result = subprocess.run(['lsusb'], capture_output=True, text=True)
        pattern = r'Bus (\d+) Device (\d+): ID 8086:([0-9a-f]{4}) Intel Corp\.'
        cameras = []
        for line in result.stdout.splitlines():
            match = re.search(pattern, line)
            if match:
                cameras.append({
                    'bus': match.group(1).zfill(3),
                    'device': match.group(2).zfill(3),
                    'product_id': match.group(3)
                })
        return cameras
    except:
        return []

print("=== RealSense Simple Stream ===\n")

# Check USB devices first
usb_cameras = check_usb_cameras()
print(f"USB detection found {len(usb_cameras)} RealSense camera(s)")
for cam in usb_cameras:
    print(f"  - Bus {cam['bus']}, Device {cam['device']}")

if not usb_cameras:
    print("\nNo RealSense cameras detected via USB!")
    sys.exit(1)

# Check permissions
print("\nChecking permissions...")
for cam in usb_cameras:
    usb_path = f"/dev/bus/usb/{cam['bus']}/{cam['device']}"
    try:
        stat_info = os.stat(usb_path)
        mode = oct(stat_info.st_mode)[-3:]
        print(f"  {usb_path}: mode {mode}")
        if mode != '666':
            print(f"    WARNING: May need: sudo chmod 666 {usb_path}")
    except:
        print(f"  {usb_path}: Cannot check")

# Now try pyrealsense2
print("\nImporting pyrealsense2...")
try:
    import pyrealsense2 as rs
    print("  Success!")
except ImportError as e:
    print(f"  Failed: {e}")
    sys.exit(1)

# Create context and check devices
print("\nChecking RealSense SDK detection...")
ctx = rs.context()
devices = ctx.query_devices()
print(f"  SDK found {len(devices)} device(s)")

if len(devices) == 0:
    print("\nTroubleshooting:")
    print("1. Check USB permissions:")
    for cam in usb_cameras:
        print(f"   sudo chmod 666 /dev/bus/usb/{cam['bus']}/{cam['device']}")
    print("2. Or add udev rules:")
    print("   sudo cp 99-realsense-libusb.rules /etc/udev/rules.d/")
    print("   sudo udevadm control --reload-rules && sudo udevadm trigger")
    print("3. Or add user to plugdev group:")
    print("   sudo usermod -a -G plugdev $USER")
    print("   (logout and login required)")
    sys.exit(1)

# If we have devices, try streaming
print("\nStarting simple color stream...")
pipeline = rs.pipeline()
config = rs.config()

# Just enable color stream
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

try:
    # Start streaming
    pipeline.start(config)
    print("Pipeline started successfully!")
    
    import cv2
    import numpy as np
    
    print("\nStreaming... Press 'q' to quit, 's' to save frame")
    frame_count = 0
    
    while True:
        # Wait for frames
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        
        if not color_frame:
            continue
            
        # Convert to numpy array
        color_image = np.asanyarray(color_frame.get_data())
        
        frame_count += 1
        
        # Add frame counter to image
        cv2.putText(color_image, f"Frame: {frame_count}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Display
        cv2.imshow('RealSense Color Stream', color_image)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            filename = f"frame_{frame_count}.png"
            cv2.imwrite(filename, color_image)
            print(f"Saved {filename}")
    
    # Stop streaming
    pipeline.stop()
    cv2.destroyAllWindows()
    print(f"\nStreaming stopped. Total frames: {frame_count}")
    
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()