# RealSense Multi-Camera Grid Streaming

Professional multi-camera RealSense D435 streaming with RGB + Depth recording in organized session structure.

## Hardware Requirements

- Intel RealSense D435 cameras
- **High-quality USB-C to USB-C cables** (USB-A adapters may cause frame timeout errors)
- USB 3.0+ ports

## Setup

### 1. System Permissions (Critical)
Add your user to the required groups for RealSense access:
```bash
sudo usermod -a -G video,plugdev $USER
```
**Important**: You must logout and login again after running this command.

Verify groups after logout/login:
```bash
groups
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

**Note**: If you encounter `pyrealsense2` installation errors, check for name conflicts with local files named `pyrealsense2.py` in your working directory.

### 3. Hardware Connection
- Connect RealSense D435 cameras using **USB-C to USB-C cables only**
- Ensure USB 3.0+ connection
- For multiple cameras, use separate USB controllers if possible

### 4. Verify Setup
Test your setup step by step:

1. Check USB detection:
```bash
lsusb | grep Intel
```
Should show: `ID 8086:0b07 Intel Corp. RealSense D435`

2. Test single camera first:
```bash
python official_minimal_stream.py  
```

3. Verify streaming works with one camera (RGB and Depth) before attempting dual-camera setup

![Expected streaming window](assets/official_minimal_stream.png)

*Example: The official minimal RealSense streaming script displays a live color image window (from the D435 camera), with keyboard controls for saving frames or exiting. The window should show a real-time video feed similar to the above screenshot. If you see a black window or no image, check your camera connection and permissions.*


## Usage

### Quick Start

1. **Start the grid camera server**:
   ```bash
   source .venv/bin/activate
   python server.py
   ```
   
   Expected output:
   ```
   Starting Multi-Camera WebSocket server on localhost:8765
   Searching for RealSense cameras...
   Found 2 RealSense camera(s):
     Camera 0: Intel RealSense D435 (Serial: 250122071300, FW: 5.13.0.55)
     Camera 1: Intel RealSense D435 (Serial: 250222071931, FW: 5.13.0.55)
   Successfully initialized 2 camera(s)
   WebSocket server running on ws://localhost:8765
   Open index.html in your browser to view the streams
   ```

2. **Open the web interface**:
   - Open `index.html` in your web browser
   - Or navigate to: `file:///path/to/your/project/index.html`

3. **View live streams**:
   - **Grid layout**: Rows = cameras + audio, Columns = RGB + Depth
   - Each camera shows both color and depth streams side by side
   - System audio visualization displayed as bottom row
   - Status indicators show connection and synchronization

4. **Record sessions**:
   - Click "Start Recording" to begin recording all cameras
   - Click "Stop Recording" to end recording
   - Each session creates a structured folder hierarchy:
     ```
     recordings/
     └── session_20250719_143022/
         ├── audio_system/
         │   └── audio.wav         # System audio recording
         ├── camera_250122071300/
         │   ├── rgb.mp4           # Color video (wide compatibility)
         │   ├── depth.npy         # Raw depth arrays (professional)
         │   └── combined.mp4      # Side-by-side color+depth
         └── camera_250222071931/
             ├── rgb.mp4
             ├── depth.npy
             └── combined.mp4
     ```

### Alternative: Single Camera Mode

For testing with one camera:
```bash
python official_minimal_stream.py
```
This opens an OpenCV window with color + depth streams side by side.

## Features

- **Multi-camera support**: Auto-detects all connected RealSense D435 cameras
- **Grid layout**: RGB + Depth streams displayed side-by-side for each camera
- **System audio capture**: Real-time audio visualization and recording
- **Professional recording**: Three file formats per camera + audio per session
  - `rgb.mp4`: High-compatibility color video (mp4v codec)
  - `depth.npy`: Raw depth arrays for professional analysis
  - `combined.mp4`: Side-by-side visualization video
  - `audio.wav`: System audio recording (stereo 44.1kHz)
- **Session organization**: Each recording creates a timestamped session folder
- **Real-time synchronization**: Multi-camera sync status monitoring
- **Automatic reconnection**: Handles connection loss gracefully

## Configuration

- **Output folder**: `recordings/` (automatically created with session structure)
- **Resolution**: 640x480 @ 30 FPS per camera (RGB + Depth)
- **WebSocket port**: 8765
- **RGB codec**: mp4v (wide compatibility)
- **Combined codec**: mp4v (wide compatibility)  
- **Depth format**: NumPy arrays (.npy) for professional use
- **Session structure**: `session_YYYYMMDD_HHMMSS/[camera_SERIAL|audio_system]/[rgb.mp4|depth.npy|combined.mp4|audio.wav]`

## Troubleshooting

### Common Issues

1. **"No devices detected"**: Check user groups and logout/login
2. **"Frame didn't arrive within 5000ms"**: Replace with high-quality USB-C cable
3. **ModuleNotFoundError**: Check for local file conflicts (rename any `pyrealsense2.py` files)
4. **Multiple camera issues**: Test single camera first, consider lower framerate (15fps)

### Known Issues

- **Depth recording freeze**: `combined.mp4` may freeze after ~1 second (depth stream issue)
- **Video compatibility**: MP4 files only open in VLC, not other players (codec limitation)
- **Depth data**: `depth.npy` reliability under investigation

For detailed troubleshooting, see `TROUBLESHOOTING.md`.

## Multi-Camera Considerations

- Use separate USB controllers/hubs for each camera
- Consider USB bandwidth limitations  
- Use device serial numbers for explicit camera selection
- May need lower framerate (15fps instead of 30fps) for dual cameras