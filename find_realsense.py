#!/usr/bin/env python3
import subprocess
import re

def find_realsense_cameras():
    """Find Intel RealSense cameras using lsusb"""
    try:
        # Run lsusb to list USB devices
        result = subprocess.run(['lsusb'], capture_output=True, text=True)
        
        if result.returncode != 0:
            print("Error running lsusb")
            return []
        
        # Intel vendor ID is 8086
        # RealSense product IDs include: 0b07, 0b3a, 0b3d, 0b48, 0b49, 0b4b, 0b4d, 0b55, 0b5c
        realsense_pattern = r'Bus (\d+) Device (\d+): ID 8086:([0-9a-f]{4}) Intel Corp\.'
        
        cameras = []
        for line in result.stdout.splitlines():
            match = re.search(realsense_pattern, line)
            if match:
                bus = match.group(1)
                device = match.group(2)
                product_id = match.group(3)
                
                # Known RealSense product IDs
                realsense_products = {
                    '0b07': 'RealSense D435',
                    '0b3a': 'RealSense D435i', 
                    '0b3d': 'RealSense D455',
                    '0b48': 'RealSense D415',
                    '0b49': 'RealSense D435',
                    '0b4b': 'RealSense D435i',
                    '0b4d': 'RealSense L515',
                    '0b55': 'RealSense L515',
                    '0b5c': 'RealSense D455'
                }
                
                model = realsense_products.get(product_id, f'Unknown RealSense ({product_id})')
                cameras.append({
                    'bus': bus,
                    'device': device,
                    'product_id': product_id,
                    'model': model,
                    'full_line': line
                })
        
        return cameras
        
    except FileNotFoundError:
        print("lsusb command not found. Please install usbutils: sudo apt-get install usbutils")
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []

def check_video_devices():
    """Check /dev/video* devices that might be RealSense"""
    import os
    import glob
    
    print("\nChecking /dev/video* devices:")
    video_devices = glob.glob('/dev/video*')
    
    for device in sorted(video_devices):
        try:
            # Try to read device info
            cmd = f"v4l2-ctl --device={device} --info 2>/dev/null | grep -E 'Driver|Card|Bus'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if 'RealSense' in result.stdout or 'Intel' in result.stdout:
                print(f"\n{device} - Possible RealSense device:")
                print(result.stdout.strip())
        except:
            pass

if __name__ == "__main__":
    print("Searching for Intel RealSense cameras...\n")
    
    cameras = find_realsense_cameras()
    
    if cameras:
        print(f"Found {len(cameras)} RealSense camera(s):")
        for cam in cameras:
            print(f"\n- {cam['model']}")
            print(f"  Bus: {cam['bus']}, Device: {cam['device']}")
            print(f"  Product ID: {cam['product_id']}")
            print(f"  Full info: {cam['full_line']}")
    else:
        print("No RealSense cameras found via lsusb.")
        print("\nMake sure:")
        print("1. The camera is connected via USB")
        print("2. The camera has power")
        print("3. You have permission to access USB devices")
    
    # Also check video devices
    check_video_devices()