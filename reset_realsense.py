#!/usr/bin/env python3
"""Reset RealSense USB devices"""

import subprocess
import os
import time

def reset_usb_device(bus, device):
    """Reset a USB device by unbinding and rebinding"""
    usb_path = f"/dev/bus/usb/{bus}/{device}"
    
    print(f"Resetting {usb_path}...")
    
    # Method 1: Using usbreset if available
    try:
        subprocess.run(['usbreset', usb_path], check=True)
        print(f"  Reset using usbreset: SUCCESS")
        return True
    except:
        print(f"  usbreset not available")
    
    # Method 2: Using sysfs unbind/bind
    try:
        # Find the device in sysfs
        sysfs_cmd = f"find /sys/bus/usb/devices/ -name '*{bus}-*' | grep -E ':1.0$' | head -1"
        result = subprocess.run(sysfs_cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            device_path = result.stdout.strip()
            driver_path = f"{device_path}/driver"
            
            if os.path.exists(driver_path):
                device_name = os.path.basename(device_path)
                unbind_path = f"{driver_path}/unbind"
                bind_path = f"{driver_path}/bind"
                
                # Unbind
                subprocess.run(f"echo '{device_name}' | sudo tee {unbind_path}", 
                             shell=True, capture_output=True)
                time.sleep(0.5)
                
                # Bind
                subprocess.run(f"echo '{device_name}' | sudo tee {bind_path}", 
                             shell=True, capture_output=True)
                
                print(f"  Reset using sysfs: SUCCESS")
                return True
    except Exception as e:
        print(f"  sysfs reset failed: {e}")
    
    return False

# Find RealSense devices
print("Finding RealSense devices...")
result = subprocess.run(['lsusb'], capture_output=True, text=True)

realsense_devices = []
for line in result.stdout.splitlines():
    if '8086:' in line and 'Intel Corp' in line:
        parts = line.split()
        bus = parts[1].zfill(3)
        device = parts[3].rstrip(':').zfill(3)
        realsense_devices.append((bus, device))
        print(f"  Found: Bus {bus}, Device {device}")

if not realsense_devices:
    print("No RealSense devices found!")
else:
    print(f"\nResetting {len(realsense_devices)} device(s)...")
    for bus, device in realsense_devices:
        reset_usb_device(bus, device)
        time.sleep(1)
    
    print("\nWaiting for devices to reinitialize...")
    time.sleep(3)
    
    # Test if pyrealsense2 can see them now
    print("\nTesting pyrealsense2 detection...")
    try:
        import pyrealsense2 as rs
        ctx = rs.context()
        devices = ctx.query_devices()
        print(f"pyrealsense2 now sees {len(devices)} device(s)")
        
        if len(devices) > 0:
            print("\nSUCCESS! Devices are now accessible.")
            print("You can now run: python working_stream.py")
        else:
            print("\nDevices still not detected by pyrealsense2.")
            print("You may need to:")
            print("1. Run this script with sudo")
            print("2. Physically unplug and replug the cameras")
            print("3. Reboot the system")
    except Exception as e:
        print(f"Error testing pyrealsense2: {e}")