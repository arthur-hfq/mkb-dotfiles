#!/bin/bash
# Configuration script for LightDM GTK Greeter
# Applies the Brutalist Light theme used in the i3 environment

# Check for root privileges
if [ "$EUID" -ne 0 ]; then
  echo "Error: This script must be run as root. Please run with sudo."
  exit 1
fi

echo "Starting LightDM configuration..."

# Define variables and paths
BG_DIR="/usr/share/backgrounds"
BG_IMAGE="${BG_DIR}/lightdm_brutalist_bg.png"
GREETER_CONF="/etc/lightdm/lightdm-gtk-greeter.conf"
LIGHTDM_CONF="/etc/lightdm/lightdm.conf"

# Ensure the background directory exists
mkdir -p "$BG_DIR"

# Get screen resolution
RES=$(xdpyinfo | grep dimensions | awk '{print $2}' 2>/dev/null)
if [ -z "$RES" ]; then
    RES="1920x1080"
fi

# Calculate coordinates for the central box
WIDTH=${RES%x*}
HEIGHT=${RES#*x}
RECT_X1=$(( WIDTH / 2 - 200 ))
RECT_Y1=$(( HEIGHT / 2 - 100 ))
RECT_X2=$(( WIDTH / 2 + 200 ))
RECT_Y2=$(( HEIGHT / 2 + 100 ))

# Generate the background image to match the lock.sh script
echo "Generating background image at $BG_IMAGE ($RES)..."
magick -size "$RES" xc:'#f4f4f4' \
    -fill '#f4f4f4' -stroke '#111111' -strokewidth 2 -draw "rectangle $RECT_X1,$RECT_Y1 $RECT_X2,$RECT_Y2" \
    -fill '#111111' -stroke none -font "/usr/share/fonts/TTF/JetBrainsMono-Bold.ttf" -pointsize 18 -gravity center -draw "text 0,-120 'MARKAB SYSTEM AUTHENTICATION'" \
    "$BG_IMAGE"

# Grant read permissions to all users (required for LightDM)
chmod 644 "$BG_IMAGE"

# Backup the existing configuration file
if [ -f "$GREETER_CONF" ]; then
    echo "Creating backup of $GREETER_CONF..."
    cp "$GREETER_CONF" "${GREETER_CONF}.bak"
fi

# Write the new configuration to the greeter file
echo "Updating $GREETER_CONF..."
cat > "$GREETER_CONF" << EOF
[greeter]
background = $BG_IMAGE
font-name = JetBrains Mono Bold 10
theme-name = Adwaita
icon-theme-name = Adwaita
hide-user-image = true
indicators = ~spacer;~clock;~spacer;~power
clock-format = %H:%M
EOF

# Ensure lightdm-gtk-greeter is selected in lightdm.conf
echo "Enabling lightdm-gtk-greeter in $LIGHTDM_CONF..."
if grep -q "^#greeter-session=" "$LIGHTDM_CONF"; then
    sed -i 's/^#greeter-session=.*/greeter-session=lightdm-gtk-greeter/' "$LIGHTDM_CONF"
elif grep -q "^greeter-session=" "$LIGHTDM_CONF"; then
    sed -i 's/^greeter-session=.*/greeter-session=lightdm-gtk-greeter/' "$LIGHTDM_CONF"
else
    # If the directive doesn't exist, append it under the seat configuration
    sed -i '/^\[Seat:\*\]/a greeter-session=lightdm-gtk-greeter' "$LIGHTDM_CONF"
fi

echo "Configuration completed successfully."
echo "You can test the greeter by running: lightdm --test-mode --debug"
