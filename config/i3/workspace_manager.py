#!/usr/bin/env python3
import sys
import subprocess
import json

def run(cmd):
    return subprocess.check_output(cmd, shell=True).decode('utf-8')

def get_focused_monitor():
    try:
        workspaces = json.loads(run("i3-msg -t get_workspaces"))
        for w in workspaces:
            if w['focused']:
                return w['output']
    except Exception:
        pass
    return "eDP-1"

def main():
    if len(sys.argv) < 3:
        print("Usage: workspace_manager.py [switch|move|move_other] [1-4]")
        sys.exit(1)

    action = sys.argv[1]
    logical_ws = int(sys.argv[2])
    focused_monitor = get_focused_monitor()

    # Determine prefix based on active monitor
    monitor_map = {
        "eDP-1": "n",
        "HDMI-1": "p"
    }
    current_prefix = monitor_map.get(focused_monitor, "n")

    # If moving to the other monitor, flip the prefix
    if action == "move_other":
        target_prefix = "p" if current_prefix == "n" else "n"
    else:
        target_prefix = current_prefix

    # The target workspace name, e.g., 'n1' or 'p3'
    target_ws = f"{target_prefix}{logical_ws}"

    if action == "switch":
        run(f'i3-msg workspace "{target_ws}"')
    elif action in ["move", "move_other"]:
        run(f'i3-msg move container to workspace "{target_ws}"')

if __name__ == "__main__":
    main()
