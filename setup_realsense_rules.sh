#!/bin/bash
# Setup udev rules for Intel RealSense cameras

echo "=== RealSense udev Rules Setup ==="
echo

# Create udev rules file content
cat > /tmp/99-realsense-libusb.rules << 'EOF'
# Intel RealSense devices (D400 series)
SUBSYSTEMS=="usb", ATTRS{idVendor}=="8086", ATTRS{idProduct}=="0b07", MODE="0666", GROUP="plugdev"
SUBSYSTEMS=="usb", ATTRS{idVendor}=="8086", ATTRS{idProduct}=="0b3a", MODE="0666", GROUP="plugdev"
SUBSYSTEMS=="usb", ATTRS{idVendor}=="8086", ATTRS{idProduct}=="0b3d", MODE="0666", GROUP="plugdev"
SUBSYSTEMS=="usb", ATTRS{idVendor}=="8086", ATTRS{idProduct}=="0b48", MODE="0666", GROUP="plugdev"
SUBSYSTEMS=="usb", ATTRS{idVendor}=="8086", ATTRS{idProduct}=="0b49", MODE="0666", GROUP="plugdev"
SUBSYSTEMS=="usb", ATTRS{idVendor}=="8086", ATTRS{idProduct}=="0b4b", MODE="0666", GROUP="plugdev"
SUBSYSTEMS=="usb", ATTRS{idVendor}=="8086", ATTRS{idProduct}=="0b4d", MODE="0666", GROUP="plugdev"
SUBSYSTEMS=="usb", ATTRS{idVendor}=="8086", ATTRS{idProduct}=="0b55", MODE="0666", GROUP="plugdev"
SUBSYSTEMS=="usb", ATTRS{idVendor}=="8086", ATTRS{idProduct}=="0b5c", MODE="0666", GROUP="plugdev"

# Intel RealSense devices (L500 series)
SUBSYSTEMS=="usb", ATTRS{idVendor}=="8086", ATTRS{idProduct}=="0b0d", MODE="0666", GROUP="plugdev"
SUBSYSTEMS=="usb", ATTRS{idVendor}=="8086", ATTRS{idProduct}=="0b3d", MODE="0666", GROUP="plugdev"
SUBSYSTEMS=="usb", ATTRS{idVendor}=="8086", ATTRS{idProduct}=="0b48", MODE="0666", GROUP="plugdev"

# UVC endpoints
KERNEL=="video*", ATTRS{idVendor}=="8086", ATTRS{idProduct}=="0b07", MODE="0666", GROUP="plugdev"
EOF

echo "udev rules created in /tmp/99-realsense-libusb.rules"
echo
echo "To install (requires sudo):"
echo "  sudo cp /tmp/99-realsense-libusb.rules /etc/udev/rules.d/"
echo "  sudo udevadm control --reload-rules"
echo "  sudo udevadm trigger"
echo
echo "Or run this script with sudo: sudo bash $0 --install"

if [ "$1" == "--install" ] && [ "$EUID" -eq 0 ]; then
    echo
    echo "Installing udev rules..."
    cp /tmp/99-realsense-libusb.rules /etc/udev/rules.d/
    udevadm control --reload-rules
    udevadm trigger
    echo "Done! You may need to unplug and replug your RealSense cameras."
fi