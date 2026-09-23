#!/bin/bash

# Retrieve the list of devices (both paired and newly discovered)
# Awk extracts the device name and appends the MAC address in parentheses
devices=$(bluetoothctl devices | awk '{for (i=3; i<=NF; i++) printf $i " "; print "(" $2 ")"}')

# Define menu options
options="Toggle Power\nScan for New Devices\nRefresh\n$devices"

# Launch rofi menu
chosen="$(echo -e "$options" | rofi -dmenu -i -p "Bluetooth")"

case "$chosen" in
    "Toggle Power")
        power_state=$(bluetoothctl show | grep -o "Powered: yes")
        if [ -z "$power_state" ]; then
            bluetoothctl power on
        else
            bluetoothctl power off
        fi
        ;;
    "Refresh")
        # Just reopen the script to reload the list
        ~/.config/i3/rofi_bluetooth.sh
        ;;
    "Scan for New Devices")
        # Send a notification so the user knows it's scanning
        notify-send -t 5000 "Bluetooth" "Scanning for 5 seconds... Please wait."
        # Run scan for 5 seconds
        bluetoothctl --timeout 5 scan on
        # Re-open the menu with the newly discovered devices
        ~/.config/i3/rofi_bluetooth.sh
        ;;
    *)
        if [ -n "$chosen" ]; then
            # Extract MAC address (it's inside the parentheses at the end)
            mac=$(echo "$chosen" | grep -o -E '([[:xdigit:]]{2}:){5}[[:xdigit:]]{2}')
            
            if [ -n "$mac" ]; then
                # Check if device is paired
                paired=$(bluetoothctl info "$mac" | grep -o "Paired: yes")
                
                if [ -n "$paired" ]; then
                    # Device is already paired, check connection status
                    connected=$(bluetoothctl info "$mac" | grep -o "Connected: yes")
                    
                    if [ -n "$connected" ]; then
                        # Show disconnect/unpair options
                        action=$(echo -e "Disconnect\nUnpair\nCancel" | rofi -dmenu -i -p "Connected. Action:")
                        if [ "$action" = "Disconnect" ]; then
                            bluetoothctl disconnect "$mac"
                        elif [ "$action" = "Unpair" ]; then
                            bluetoothctl disconnect "$mac"
                            bluetoothctl remove "$mac"
                        fi
                    else
                        # Show connect/unpair options
                        action=$(echo -e "Connect\nUnpair\nCancel" | rofi -dmenu -i -p "Disconnected. Action:")
                        if [ "$action" = "Connect" ]; then
                            bluetoothctl connect "$mac"
                        elif [ "$action" = "Unpair" ]; then
                            bluetoothctl remove "$mac"
                        fi
                    fi
                else
                    # Device is NOT paired, show pair option
                    action=$(echo -e "Pair & Connect\nCancel" | rofi -dmenu -i -p "New Device. Action:")
                    if [ "$action" = "Pair & Connect" ]; then
                        notify-send "Bluetooth" "Pairing with $mac..."
                        bluetoothctl pair "$mac"
                        bluetoothctl trust "$mac"
                        bluetoothctl connect "$mac"
                    fi
                fi
            fi
        fi
        ;;
esac
