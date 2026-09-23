#!/bin/bash

# Check if bluetoothctl is available
if ! command -v bluetoothctl &> /dev/null; then
    echo "NO BT"
    exit 0
fi

# Check power status
powered=$(bluetoothctl show | grep -o "Powered: yes")

if [ -z "$powered" ]; then
    echo "OFF"
else
    # Check connected devices
    connected_count=$(bluetoothctl devices Connected | grep -c "Device")
    
    if [ "$connected_count" -gt 0 ]; then
        echo "CON ($connected_count)"
    else
        echo "ON"
    fi
fi
