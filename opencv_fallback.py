#!/usr/bin/env python3
"""Fallback RealSense streaming using OpenCV directly (no pyrealsense2)"""

import cv2
import numpy as np
import subprocess
import sys

print("=== OpenCV Fallback Stream (No pyrealsense2) ===\n")

# First check which video devices exist and might be RealSense
print("Checking video devices...")
video_devices = []

for i in range(20):
    device = f"/dev/video{i}"
    # Check if device exists and what it is
    cmd = f"v4l2-ctl --device={device} --info 2>/dev/null | grep -E '(Driver|Card|Bus)'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0 and result.stdout:
        print(f"\nFound {device}:")
        print(result.stdout.strip())
        
        # Check if it might be RealSense
        if any(x in result.stdout for x in ['uvcvideo', 'usb']):
            video_devices.append(i)
            print(f"  -> Added to candidate list")

if not video_devices:
    print("\nNo video devices found!")
    sys.exit(1)

print(f"\nFound {len(video_devices)} candidate video device(s): {video_devices}")
print("\nTrying to open cameras...\n")

# Try to open cameras
working_cameras = []
for idx in video_devices:
    print(f"Testing /dev/video{idx}...")
    cap = cv2.VideoCapture(idx)
    
    if cap.isOpened():
        # Try to read a frame
        ret, frame = cap.read()
        if ret and frame is not None:
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            print(f"  SUCCESS: {width}x{height} @ {fps}fps")
            working_cameras.append({
                'index': idx,
                'cap': cap,
                'width': width,
                'height': height,
                'fps': fps
            })
        else:
            print(f"  Failed to read frame")
            cap.release()
    else:
        print(f"  Failed to open")

if not working_cameras:
    print("\nNo working cameras found!")
    sys.exit(1)

print(f"\nFound {len(working_cameras)} working camera(s)")
print("Using first camera for streaming...")
print("Press 'q' to quit, 's' to save frame, 'n' for next camera")

# Use first camera
current_cam_idx = 0
current_cam = working_cameras[current_cam_idx]

frame_count = 0
recording = False
video_writer = None

while True:
    cap = current_cam['cap']
    ret, frame = cap.read()
    
    if not ret:
        print("Failed to grab frame")
        break
    
    frame_count += 1
    
    # Add overlay
    cv2.putText(frame, f"Camera /dev/video{current_cam['index']} | Frame {frame_count}", 
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, f"{current_cam['width']}x{current_cam['height']} @ {current_cam['fps']:.1f}fps", 
                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
    
    if recording:
        cv2.putText(frame, "RECORDING", (10, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        if video_writer:
            video_writer.write(frame)
    
    # Display
    cv2.imshow('Camera Stream (OpenCV)', frame)
    
    # Handle keys
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('q'):
        break
    elif key == ord('s'):
        filename = f"opencv_frame_{frame_count}.png"
        cv2.imwrite(filename, frame)
        print(f"Saved {filename}")
    elif key == ord('r'):
        if not recording:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            filename = f"opencv_recording_{current_cam['index']}.mp4"
            video_writer = cv2.VideoWriter(
                filename, fourcc, 30.0, 
                (int(current_cam['width']), int(current_cam['height']))
            )
            recording = True
            print(f"Recording started: {filename}")
        else:
            recording = False
            if video_writer:
                video_writer.release()
                video_writer = None
            print("Recording stopped")
    elif key == ord('n') and len(working_cameras) > 1:
        # Switch camera
        current_cam_idx = (current_cam_idx + 1) % len(working_cameras)
        current_cam = working_cameras[current_cam_idx]
        frame_count = 0
        print(f"\nSwitched to camera /dev/video{current_cam['index']}")

# Cleanup
for cam in working_cameras:
    cam['cap'].release()
if video_writer:
    video_writer.release()
cv2.destroyAllWindows()

print(f"\nTotal frames: {frame_count}")