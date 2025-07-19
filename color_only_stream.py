#!/usr/bin/env python3
"""Simple color-only RealSense stream"""

import pyrealsense2 as rs
import numpy as np
import cv2

print("=== Color-Only RealSense Stream ===\n")

# Create pipeline
pipeline = rs.pipeline()
config = rs.config()

# Enable only color stream (more stable)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

print("Starting color stream...")
pipeline.start(config)
print("Stream started! Press ESC to exit, 's' to save frame\n")

frame_count = 0
timeout_count = 0

try:
    while True:
        try:
            # Wait for color frame only
            frames = pipeline.wait_for_frames(timeout_ms=1000)
            color_frame = frames.get_color_frame()
            
            if not color_frame:
                continue
                
            frame_count += 1
            
            # Convert to numpy array
            color_image = np.asanyarray(color_frame.get_data())
            
            # Add overlay
            cv2.putText(color_image, f"Frame: {frame_count}", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(color_image, "Color Stream", (10, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(color_image, f"Timeouts: {timeout_count}", (10, 90), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
            
            # Show image
            cv2.imshow('RealSense Color', color_image)
            
            # Print progress every 30 frames
            if frame_count % 30 == 0:
                print(f"Frame {frame_count} (Timeouts: {timeout_count})")
            
            # Handle keys
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
            elif key == ord('s'):
                filename = f"color_frame_{frame_count}.png"
                cv2.imwrite(filename, color_image)
                print(f"Saved {filename}")
                
        except RuntimeError as e:
            timeout_count += 1
            if timeout_count % 50 == 1:  # Print every 50th timeout
                print(f"Timeout #{timeout_count}: {e}")
            continue
            
except KeyboardInterrupt:
    print("\nInterrupted by user")
    
finally:
    pipeline.stop()
    cv2.destroyAllWindows()
    print(f"\nFinal stats: {frame_count} frames, {timeout_count} timeouts")
    if frame_count > 0:
        success_rate = frame_count / (frame_count + timeout_count) * 100
        print(f"Success rate: {success_rate:.1f}%")