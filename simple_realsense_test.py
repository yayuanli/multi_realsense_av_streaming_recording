#!/usr/bin/env python3
import cv2
import numpy as np
import subprocess
import re

def find_realsense_video_devices():
    """Find video devices that might be RealSense cameras"""
    devices = []
    
    # Check all /dev/video* devices
    for i in range(20):  # Check up to video20
        device_path = f'/dev/video{i}'
        try:
            # Try to get device info using v4l2-ctl
            cmd = f"v4l2-ctl --device={device_path} --info 2>/dev/null"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0 and ('RealSense' in result.stdout or 'Intel' in result.stdout):
                # Extract device info
                info = {}
                for line in result.stdout.splitlines():
                    if 'Driver name' in line:
                        info['driver'] = line.split(':')[1].strip()
                    elif 'Card type' in line:
                        info['card'] = line.split(':')[1].strip()
                    elif 'Bus info' in line:
                        info['bus'] = line.split(':')[1].strip()
                
                devices.append({
                    'path': device_path,
                    'index': i,
                    'info': info
                })
        except:
            pass
    
    return devices

def test_camera_opencv(device_index):
    """Test camera using OpenCV"""
    print(f"\n[TEST] Trying to open camera at index {device_index} with OpenCV...")
    
    # Try different backends
    backends = [
        (cv2.CAP_V4L2, "V4L2"),
        (cv2.CAP_ANY, "ANY"),
    ]
    
    for backend, backend_name in backends:
        print(f"\n[TEST] Trying backend: {backend_name}")
        cap = cv2.VideoCapture(device_index, backend)
        
        if cap.isOpened():
            print(f"[SUCCESS] Camera opened with {backend_name} backend!")
            
            # Get camera properties
            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            print(f"[INFO] Resolution: {int(width)}x{int(height)}")
            print(f"[INFO] FPS: {fps}")
            
            # Try to grab a frame
            ret, frame = cap.read()
            if ret:
                print(f"[SUCCESS] Successfully captured a frame! Shape: {frame.shape}")
                
                # Save the frame
                filename = f"test_frame_video{device_index}.jpg"
                cv2.imwrite(filename, frame)
                print(f"[INFO] Saved test frame to {filename}")
                
                # Display frame info
                print(f"[INFO] Frame dtype: {frame.dtype}, min: {frame.min()}, max: {frame.max()}")
                
            else:
                print("[ERROR] Failed to capture frame")
            
            cap.release()
            return True
        else:
            print(f"[FAIL] Could not open camera with {backend_name} backend")
    
    return False

def main():
    print("=== RealSense Camera Test without pyrealsense2 ===\n")
    
    # First, check USB devices
    print("[1] Checking USB devices...")
    usb_result = subprocess.run(['lsusb'], capture_output=True, text=True)
    for line in usb_result.stdout.splitlines():
        if '8086:' in line and 'Intel' in line:
            print(f"   Found: {line}")
    
    # Find video devices
    print("\n[2] Searching for RealSense video devices...")
    devices = find_realsense_video_devices()
    
    if devices:
        print(f"\nFound {len(devices)} potential RealSense video device(s):")
        for dev in devices:
            print(f"\n   Device: {dev['path']}")
            for key, value in dev['info'].items():
                print(f"     {key}: {value}")
    else:
        print("\n   No RealSense video devices found through v4l2")
    
    # Try to open cameras with OpenCV
    print("\n[3] Testing camera access with OpenCV...")
    
    # Test specific video indices
    test_indices = list(range(10))  # Test video0 through video9
    
    success_count = 0
    for idx in test_indices:
        if test_camera_opencv(idx):
            success_count += 1
            print(f"\n[RESULT] Successfully accessed /dev/video{idx}")
    
    print(f"\n\n=== Summary ===")
    print(f"Successfully accessed {success_count} camera(s)")
    
    if success_count == 0:
        print("\nTroubleshooting tips:")
        print("1. Check permissions: ls -la /dev/video*")
        print("2. Add user to video group: sudo usermod -a -G video $USER")
        print("3. Try running with sudo (not recommended for production)")
        print("4. Check if RealSense kernel modules are loaded: lsmod | grep uvc")

if __name__ == "__main__":
    main()