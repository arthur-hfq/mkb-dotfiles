#!/bin/bash
# ~/.config/i3/lock.sh
# Brutalist lock screen mimicking ly display manager

LY_BG="$HOME/.config/i3/ly_lock_bg.png"
CACHE_MARKER="$HOME/.cache/betterlockscreen/current_wp.txt"

# If marker doesn't exist, this will just be empty
LAST_WP=""
if [ -f "$CACHE_MARKER" ]; then
    LAST_WP=$(cat "$CACHE_MARKER")
fi

# Ensure the lockscreen image is generated
if [ ! -f "$LY_BG" ]; then
    RES=$(xdpyinfo | grep dimensions | awk '{print $2}')
    if [ -z "$RES" ]; then RES="1920x1080"; fi
    magick -size $RES xc:'#f4f4f4' \
        -fill '#f4f4f4' -stroke '#111111' -strokewidth 2 -draw "rectangle $(( ${RES%x*} / 2 - 200 )),$(( ${RES#*x} / 2 - 100 )) $(( ${RES%x*} / 2 + 200 )),$(( ${RES#*x} / 2 + 100 ))" \
        -fill '#111111' -stroke none -font "/usr/share/fonts/TTF/JetBrainsMono-Bold.ttf" -pointsize 18 -gravity center -draw "text 0,-120 'MARKAB SYSTEM AUTHENTICATION'" \
        -draw "text -120,-40 'login:'" \
        -draw "text -120,0 'password:'" \
        "$LY_BG"
fi

# Update betterlockscreen cache if we haven't set it to LY_BG yet
if [ "$LY_BG" != "$LAST_WP" ] || [ ! -d "$HOME/.cache/betterlockscreen" ]; then
    betterlockscreen -u "$LY_BG" --display 1
    mkdir -p "$HOME/.cache/betterlockscreen"
    echo "$LY_BG" > "$CACHE_MARKER"
fi

# Lock the screen without dimming (so it stays white and matches ly perfectly)
betterlockscreen -l
