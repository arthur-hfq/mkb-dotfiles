#!/bin/bash
# $HOME/.config/i3/launch_telemetry.sh

# ── KILL ALL PREVIOUS INSTANCES ───────────────────────────────────
pkill -f "swarm.py" 2>/dev/null
pkill -f "git_heatmap.py" 2>/dev/null
pkill -f "wallpaper_engine.py" 2>/dev/null
sleep 0.3

# ── LAUNCH PYTHON IMAGE GENERATORS ───────────────────────────────
/usr/bin/python3 $HOME/.config/conky/git_heatmap.py &
/usr/bin/python3 $HOME/.config/conky/swarm.py &

# ── LAUNCH WALLPAPER HUD ENGINE ──────────────────────────────────
sleep 1.5
/usr/bin/python3 $HOME/.config/conky/wallpaper_engine.py &
