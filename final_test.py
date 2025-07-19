#!/usr/bin/env python3
"""Final troubleshooting for RealSense cameras"""

import subprocess
import os
import cv2

print("=== Final RealSense Troubleshooting ===\n")

# 1. Check USB devices
print("1. USB Device Detection:")
result = subprocess.run(['lsusb'], capture_output=True, text=True)
realsense_count = 0
for line in result.stdout.splitlines():
    if '8086:' in line and 'Intel' in line:
        realsense_count += 1
        print(f"   ✓ {line}")

print(f"   Found {realsense_count} RealSense device(s) via USB\n")

# 2. Check permissions
print("2. USB Permissions:")
for line in result.stdout.splitlines():
    if '8086:' in line and 'Intel' in line:
        parts = line.split()
        bus = parts[1].zfill(3)
        device = parts[3].rstrip(':').zfill(3)
        usb_path = f"/dev/bus/usb/{bus}/{device}"
        
        try:
            stat = os.stat(usb_path)
            mode = oct(stat.st_mode)[-3:]
            print(f"   {usb_path}: mode {mode}")
        except:
            print(f"   {usb_path}: Cannot access")

print()

# 3. Check video devices
print("3. Video Device Status:")
for i in range(16):
    device_path = f"/dev/video{i}"
    if os.path.exists(device_path):
        stat = os.stat(device_path)
        mode = oct(stat.st_mode)[-3:]
        print(f"   {device_path}: exists, mode {mode}")

print()

# 4. Check groups
print("4. User Groups:")
try:
    result = subprocess.run(['groups'], capture_output=True, text=True)
    groups = result.stdout.strip().split()
    
    important_groups = ['video', 'plugdev', 'dialout']
    for group in important_groups:
        status = "✓" if group in groups else "✗"
        print(f"   {status} {group}")
    
    print(f"   All groups: {' '.join(groups)}")
except:
    print("   Cannot check groups")

print()

# 5. Test pyrealsense2
print("5. pyrealsense2 Test:")
try:
    import pyrealsense2 as rs
    ctx = rs.context()
    devices = ctx.query_devices()
    print(f"   pyrealsense2 detects {len(devices)} device(s)")
    
    if len(devices) > 0:
        print("   SUCCESS! Cameras are accessible.")
    else:
        print("   FAILED: No devices detected by pyrealsense2")
except Exception as e:
    print(f"   ERROR: {e}")

print()

# 6. Test OpenCV
print("6. OpenCV Test:")
try:
    # Try to open camera 0
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print("   ✓ OpenCV can access camera 0")
        else:
            print("   ✗ OpenCV opened camera but cannot read frames")
        cap.release()
    else:
        print("   ✗ OpenCV cannot open camera 0")
except Exception as e:
    print(f"   ERROR: {e}")

print()

# 7. Recommendations
print("7. Recommendations:")
print("   Based on the above results:")

if realsense_count == 0:
    print("   → No RealSense cameras detected. Check connections.")
elif realsense_count > 0:
    print("   → RealSense cameras detected via USB")
    
    # Check if pyrealsense2 works
    try:
        import pyrealsense2 as rs
        ctx = rs.context()
        devices = ctx.query_devices()
        if len(devices) == 0:
            print("   → pyrealsense2 cannot access cameras")
            print("   → Try: unplug/replug cameras OR reboot system")
            print("   → Or check if another program is using the cameras")
        else:
            print("   → pyrealsense2 is working! You can use the streaming scripts.")
    except:
        print("   → pyrealsense2 import failed")

print("\n   Quick fixes to try:")
print("   1. Unplug and replug both RealSense cameras")
print("   2. sudo systemctl restart udev")
print("   3. Reboot the system")
print("   4. Check if any other programs are using the cameras")
print("   5. Try running: sudo usermod -a -G video,plugdev $USER")
print("      (then logout and login)")

print("\n=== End Troubleshooting ===")