# RealSense D435 Synchronized Streaming

Minimum working script for synchronized streaming from two RealSense D435 cameras with web-based recording.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Connect two RealSense D435 cameras via USB/Type-C

## Usage

1. Start the RealSense streaming server:
```bash
python realsense_streamer.py
```

2. In a new terminal, start the web server:
```bash
python simple_server.py
```

3. Open http://localhost:8000 in your browser

4. Click "Start Recording" to begin synchronized recording
   - Videos are saved to the `recordings/` folder
   - Files are named: `cam1_TIMESTAMP.mp4` and `cam2_TIMESTAMP.mp4`

## Features

- Synchronized RGB streaming from two RealSense D435 cameras
- Real-time web display with synchronization status indicator
- One-click recording to configured folder
- Automatic reconnection on connection loss

## Configuration

- Output folder: Modify `output_folder` parameter in `realsense_streamer.py`
- Resolution: Currently set to 640x480 @ 30 FPS
- WebSocket port: 8765
- HTTP server port: 8000