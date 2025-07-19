#!/usr/bin/env python3
"""Test RealSense device detection"""

import pyrealsense2 as rs
import sys

print(f"pyrealsense2 version: {rs.__version__}")

# Create a context
ctx = rs.context()

# Check if we can see any devices
devices = ctx.query_devices()
print(f"\nFound {len(devices)} RealSense device(s)")

if len(devices) == 0:
    print("\nNo devices found. Checking USB permissions...")
    print("Try running:")
    print("  1. sudo chmod 666 /dev/bus/usb/004/002")
    print("  2. sudo chmod 666 /dev/bus/usb/001/006")
    print("  3. Or add udev rules for RealSense")
    sys.exit(1)

# List all devices
for i, device in enumerate(devices):
    print(f"\nDevice {i}:")
    print(f"  Name: {device.get_info(rs.camera_info.name)}")
    print(f"  Serial: {device.get_info(rs.camera_info.serial_number)}")
    print(f"  Firmware: {device.get_info(rs.camera_info.firmware_version)}")
    print(f"  USB: {device.get_info(rs.camera_info.usb_type_descriptor)}")
    print(f"  Product Line: {device.get_info(rs.camera_info.product_line)}")

# Try to start a simple pipeline
print("\nTrying to start pipeline with first device...")
pipeline = rs.pipeline()
config = rs.config()

# Enable streams
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

try:
    pipeline.start(config)
    print("Pipeline started successfully!")
    
    # Get a few frames
    for i in range(5):
        frames = pipeline.wait_for_frames()
        print(f"  Got frame {i+1}")
    
    pipeline.stop()
    print("Pipeline stopped successfully!")
    
except Exception as e:
    print(f"Error starting pipeline: {e}")
    print("\nThis might be a permission issue. Try:")
    print("  sudo usermod -a -G plugdev $USER")
    print("  Then logout and login again")