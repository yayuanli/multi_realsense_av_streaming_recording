#!/usr/bin/env python3
"""Stable RealSense stream with initialization"""

import pyrealsense2 as rs
import numpy as np
import cv2
import time

print("=== Stable RealSense Stream ===\n")

# List available devices
ctx = rs.context()
devices = ctx.query_devices()
print(f"Found {len(devices)} device(s)")

# Use first device explicitly
device = devices[0]
serial = device.get_info(rs.camera_info.serial_number)
print(f"Using device: {serial}")

# Create pipeline with explicit device
pipeline = rs.pipeline(ctx)
config = rs.config()

# Enable specific device
config.enable_device(serial)

# Start with lower resolution and framerate for stability
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 15)  # 15fps instead of 30

print("Starting pipeline...")
try:
    profile = pipeline.start(config)
    print("Pipeline started successfully!")
    
    # Get the actual stream settings
    color_profile = rs.video_stream_profile(profile.get_stream(rs.stream.color))
    print(f"Actual stream: {color_profile.width()}x{color_profile.height()} @ {color_profile.fps()}fps")
    
    # Let camera settle
    print("Letting camera initialize...")
    for i in range(30):
        try:
            frames = pipeline.wait_for_frames(timeout_ms=2000)
            if frames.get_color_frame():
                print(f"Warmup frame {i+1}/30")
            time.sleep(0.1)
        except:
            pass
    
    print("Starting main loop...\n")
    
except Exception as e:
    print(f"Failed to start pipeline: {e}")
    exit(1)

frame_count = 0
timeout_count = 0
last_frame_time = time.time()

try:
    while True:
        try:
            # Longer timeout for stability
            frames = pipeline.wait_for_frames(timeout_ms=3000)
            color_frame = frames.get_color_frame()
            
            if not color_frame:
                continue
                
            frame_count += 1
            current_time = time.time()
            fps = 1.0 / (current_time - last_frame_time) if frame_count > 1 else 0
            last_frame_time = current_time
            
            # Convert to numpy array
            color_image = np.asanyarray(color_frame.get_data())
            
            # Add overlay
            cv2.putText(color_image, f"Frame: {frame_count}", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(color_image, f"FPS: {fps:.1f}", (10, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(color_image, f"Device: {serial}", (10, 90), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Show image
            cv2.imshow('RealSense Stable', color_image)
            
            # Print progress
            if frame_count == 1:
                print("First frame received!")
            elif frame_count % 60 == 0:
                print(f"Frame {frame_count}, FPS: {fps:.1f}, Timeouts: {timeout_count}")
            
            # Handle keys
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
            elif key == ord('s'):
                filename = f"stable_frame_{frame_count}.png"
                cv2.imwrite(filename, color_image)
                print(f"Saved {filename}")
                
        except RuntimeError as e:
            timeout_count += 1
            if "didn't arrive" in str(e):
                print(f"Frame timeout #{timeout_count}")
            else:
                print(f"Error #{timeout_count}: {e}")
            
            # If too many consecutive timeouts, try to restart
            if timeout_count > 0 and timeout_count % 20 == 0:
                print("Too many timeouts, attempting recovery...")
                try:
                    pipeline.stop()
                    time.sleep(1)
                    pipeline.start(config)
                    print("Pipeline restarted")
                except:
                    print("Recovery failed")
                    break
            continue
            
except KeyboardInterrupt:
    print("\nStopped by user")
    
finally:
    try:
        pipeline.stop()
    except:
        pass
    cv2.destroyAllWindows()
    
    print(f"\nFinal results:")
    print(f"  Frames: {frame_count}")
    print(f"  Timeouts: {timeout_count}")
    if frame_count + timeout_count > 0:
        success_rate = frame_count / (frame_count + timeout_count) * 100
        print(f"  Success rate: {success_rate:.1f}%")

print("\nIf you're still getting timeouts, try:")
print("1. Unplug one of the RealSense cameras (USB bandwidth)")
print("2. Use a USB 3.0 port")
print("3. Lower the resolution or framerate further")