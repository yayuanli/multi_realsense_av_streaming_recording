#!/usr/bin/env python3
"""Most basic RealSense test"""

import pyrealsense2 as rs

print("Testing RealSense...")

# Create context
ctx = rs.context()

# Query devices
devices = ctx.query_devices()
print(f"Number of devices: {len(devices)}")

if len(devices) == 0:
    print("\nNo devices found. Trying to enumerate available backends...")
    
    # Check if we can see the devices at all
    print("\nTrying hardware_reset on all devices...")
    for i in range(5):  # Try indices 0-4
        try:
            ctx.query_all_devices()[i].hardware_reset()
            print(f"Reset device {i}")
        except:
            pass
    
    # Query again
    devices = ctx.query_devices()
    print(f"After reset, number of devices: {len(devices)}")

# If still no devices, it's likely a permission/driver issue
if len(devices) == 0:
    print("\nStill no devices. This is likely due to:")
    print("1. USB permissions (already checked - they're 666)")
    print("2. Missing udev rules for RealSense")
    print("3. Conflicting kernel modules")
    print("\nTry:")
    print("  sudo modprobe -r uvcvideo")
    print("  sudo modprobe uvcvideo")
else:
    for i, dev in enumerate(devices):
        print(f"\nDevice {i}:")
        print(f"  Name: {dev.get_info(rs.camera_info.name)}")
        print(f"  Serial: {dev.get_info(rs.camera_info.serial_number)}")