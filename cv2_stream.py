#!/usr/bin/env python3
"""Simple RealSense streaming using OpenCV (no pyrealsense2)"""

import cv2
import numpy as np
import sys

def find_working_cameras(max_index=10):
    """Find all working camera indices"""
    working_cameras = []
    
    print("Scanning for cameras...")
    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                print(f"  Camera {i}: {width}x{height} @ {fps}fps")
                working_cameras.append(i)
            cap.release()
    
    return working_cameras

def main():
    print("=== OpenCV Camera Stream (No pyrealsense2) ===\n")
    
    # Find working cameras
    cameras = find_working_cameras()
    
    if not cameras:
        print("No cameras found!")
        return
    
    print(f"\nFound {len(cameras)} camera(s): {cameras}")
    
    # Use first camera by default
    camera_index = cameras[0]
    if len(sys.argv) > 1:
        try:
            camera_index = int(sys.argv[1])
            print(f"Using camera index {camera_index} from command line")
        except:
            print(f"Using default camera index {camera_index}")
    else:
        print(f"Using camera index {camera_index} (use 'python cv2_stream.py <index>' to change)")
    
    # Open camera
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"Cannot open camera {camera_index}")
        return
    
    # Set resolution (RealSense usually supports these)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    # Get actual resolution
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"\nStreaming at {width}x{height} @ {fps}fps")
    print("Press 'q' to quit, 's' to save frame, 'n' for next camera")
    
    frame_count = 0
    recording = False
    video_writer = None
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("Failed to grab frame")
            break
        
        frame_count += 1
        
        # Add info overlay
        cv2.putText(frame, f"Camera {camera_index} | Frame {frame_count}", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        if recording:
            cv2.putText(frame, "RECORDING", (10, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            if video_writer:
                video_writer.write(frame)
        
        # Display frame
        cv2.imshow(f'Camera {camera_index} Stream', frame)
        
        # Handle keys
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        elif key == ord('s'):
            filename = f"camera{camera_index}_frame{frame_count}.png"
            cv2.imwrite(filename, frame)
            print(f"Saved {filename}")
        elif key == ord('r'):
            if not recording:
                # Start recording
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                filename = f"camera{camera_index}_recording.mp4"
                video_writer = cv2.VideoWriter(filename, fourcc, 30.0, (width, height))
                recording = True
                print(f"Recording started: {filename}")
            else:
                # Stop recording
                recording = False
                if video_writer:
                    video_writer.release()
                    video_writer = None
                print("Recording stopped")
        elif key == ord('n') and len(cameras) > 1:
            # Switch to next camera
            cap.release()
            current_idx = cameras.index(camera_index)
            camera_index = cameras[(current_idx + 1) % len(cameras)]
            print(f"\nSwitching to camera {camera_index}")
            cap = cv2.VideoCapture(camera_index)
            frame_count = 0
    
    # Cleanup
    cap.release()
    if video_writer:
        video_writer.release()
    cv2.destroyAllWindows()
    
    print(f"\nTotal frames: {frame_count}")

if __name__ == "__main__":
    main()