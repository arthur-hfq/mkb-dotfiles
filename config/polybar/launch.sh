#!/usr/bin/env bash
killall -q polybar
while pgrep -u $UID -x polybar >/dev/null; do sleep 0.5; done

polybar main -c ~/.config/polybar/config.ini 2>&1 | tee -a /tmp/polybar-main.log &
polybar secondary -c ~/.config/polybar/config.ini 2>&1 | tee -a /tmp/polybar-secondary.log &

echo "POLYBAR :: LAUNCHED"
