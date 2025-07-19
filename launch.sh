#!/bin/bash
# Launch script for RealSense streaming with permission handling

echo "=== RealSense Stream Launcher ==="
echo

# Find RealSense devices
echo "Detecting RealSense devices..."
DEVICES=$(lsusb | grep "8086:" | grep "Intel Corp")

if [ -z "$DEVICES" ]; then
    echo "No RealSense devices found!"
    exit 1
fi

echo "Found RealSense devices:"
echo "$DEVICES"
echo

# Extract bus and device numbers
BUS_DEVICES=$(echo "$DEVICES" | sed -n 's/Bus \([0-9]\+\) Device \([0-9]\+\):.*/\1 \2/p')

# Check and fix permissions
echo "Checking USB permissions..."
NEED_SUDO=false

while read -r BUS DEVICE; do
    BUS=$(printf "%03d" $BUS)
    DEVICE=$(printf "%03d" $DEVICE)
    USB_PATH="/dev/bus/usb/$BUS/$DEVICE"
    
    # Check current permissions
    if [ -e "$USB_PATH" ]; then
        PERMS=$(stat -c "%a" "$USB_PATH" 2>/dev/null)
        echo "  $USB_PATH: mode $PERMS"
        
        if [ "$PERMS" != "666" ]; then
            NEED_SUDO=true
        fi
    fi
done <<< "$BUS_DEVICES"

echo

# Fix permissions if needed
if [ "$NEED_SUDO" = true ]; then
    echo "Fixing permissions (requires sudo)..."
    while read -r BUS DEVICE; do
        BUS=$(printf "%03d" $BUS)
        DEVICE=$(printf "%03d" $DEVICE)
        USB_PATH="/dev/bus/usb/$BUS/$DEVICE"
        
        if [ -e "$USB_PATH" ]; then
            echo "  sudo chmod 666 $USB_PATH"
            sudo chmod 666 "$USB_PATH"
        fi
    done <<< "$BUS_DEVICES"
    echo "Permissions fixed!"
else
    echo "Permissions are already correct."
fi

echo

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Launch the streaming script
echo "Launching RealSense stream..."
echo "----------------------------------------"
python simple_stream.py