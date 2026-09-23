#!/usr/bin/env python3
import sys, subprocess, json, os

def run(cmd):
    return subprocess.check_output(cmd, shell=True).decode('utf-8')

def get_focused_monitor():
    try:
        workspaces = json.loads(run("i3-msg -t get_workspaces"))
        for w in workspaces:
            if w['focused']:
                return w['output']
    except:
        pass
    return "eDP-1"

def main():
    if len(sys.argv) < 2:
        sys.exit(1)
    
    action = sys.argv[1]
    monitor = get_focused_monitor()

    if monitor == "eDP-1":
        if action == "up":
            subprocess.run(["brightnessctl", "set", "+5%"])
        elif action == "down":
            subprocess.run(["brightnessctl", "set", "5%-"])
    else:
        # Software brightness for external monitor
        state_file = os.path.expanduser("~/.cache/hdmi_brightness")
        try:
            with open(state_file, "r") as f:
                b = float(f.read().strip())
        except:
            b = 1.0
        
        if action == "up":
            b = min(1.0, b + 0.1)
        elif action == "down":
            b = max(0.1, b - 0.1)
            
        with open(state_file, "w") as f:
            f.write(f"{b:.1f}")
            
        subprocess.run(["xrandr", "--output", monitor, "--brightness", str(b)])

if __name__ == "__main__":
    main()
