#!/usr/bin/env python3
import cairo
import os
import time
import subprocess
from datetime import datetime

# --- DATA FETCHING ---

def get_docker_status():
    try:
        out = subprocess.check_output("docker ps --format '{{.Names}}|{{.Status}}|{{.Ports}}' | head -n 3", shell=True, text=True)
        if not out.strip():
            return [("NO CONTAINERS RUNNING", "", "")]
        lines = out.strip().split('\n')
        data = []
        for line in lines:
            parts = line.split('|')
            name = parts[0][:15] if len(parts) > 0 else ""
            status = parts[1].split(' ')[0] if len(parts) > 1 else ""
            port = parts[2].split('->')[0].split(':')[-1] if len(parts) > 2 and ':' in parts[2] else ""
            data.append((name, status, port))
        return data
    except Exception:
        return [("DOCKER DAEMON NOT RUNNING", "", "")]

def get_current_directive():
    try:
        with open(os.path.expanduser("~/Temp/focus.txt"), "r") as f:
            lines = f.read().strip().split("\n")
            # Truncate lines to prevent overflow
            return [line[:50] + "..." if len(line) > 50 else line for line in lines[:5]]
    except Exception:
        return ["~/Temp/focus.txt NOT FOUND"]

def get_top_processes():
    try:
        out = subprocess.check_output("ps -eo comm,%cpu,%mem --sort=-%cpu | head -n 4", shell=True, text=True)
        lines = out.strip().split("\n")[1:] # Skip header
        data = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 3:
                name = parts[0][:15]
                data.append((name, parts[1], parts[2]))
        return data
    except Exception:
        return [("ERROR", "0.0", "0.0")]

def get_disk_io_and_storage():
    try:
        df_out = subprocess.check_output("df -h / | awk 'NR==2 {print $4}'", shell=True, text=True).strip()
        return df_out
    except Exception:
        return "N/A"

def get_recent_commits():
    try:
        if os.path.exists(os.path.expanduser("~/Projects")):
            cmd = "find ~/Projects -maxdepth 3 -name .git -type d -prune -execdir git log -1 --format='%h | %cd | %s' --date=format:'%H:%M' \\; 2>/dev/null | head -n 3"
            out = subprocess.check_output(cmd, shell=True, text=True).strip()
            if out:
                # Truncate to 50 chars to avoid text flowing out of the 1920x1080 screen (x starts at 1420)
                return [line[:50] + "..." if len(line) > 50 else line for line in out.split('\n')]
        return ["SHA-1 b8e5c1a | 13:45 | Fix: User login bug", "SHA-1 f2a7d8d | 13:30 | Feature: Auth flow", "SHA-1 2e4b3c9 | 12:00 | Docs: API endpoints"]
    except Exception:
        return ["NO RECENT COMMITS FOUND"]

# --- RENDERING ---

def draw_hud():
    width, height = 1920, 1080
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surface)
    
    # 1. Background
    ctx.set_source_rgb(0xf4/255.0, 0xf4/255.0, 0xf4/255.0)
    ctx.paint()

    # Setup standard font
    ctx.select_font_face("JetBrains Mono", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(13)
    black = (0x11/255.0, 0x11/255.0, 0x11/255.0)
    accent_blue = (0x00/255.0, 0x55/255.0, 0xff/255.0)
    
    # 2. Central Globe (from swarm.py) - Shifted up and strictly centered
    globe_path = "/dev/shm/nodes.png"
    if os.path.exists(globe_path):
        try:
            img = cairo.ImageSurface.create_from_png(globe_path)
            ctx.set_source_surface(img, (width - 1000) // 2, 40)
            ctx.paint()
        except: pass
    
    # Helper for drawing Mecha UI cards
    def draw_card(x, y, title, content_lines, footer=None):
        ctx.set_source_rgb(*black)
        ctx.set_line_width(1.5)
        
        # Header
        ctx.move_to(x, y)
        ctx.show_text(f"[{title}]")
        
        # Top bracket
        ctx.move_to(x + 2, y + 8)
        ctx.line_to(x - 10, y + 8)
        ctx.line_to(x - 10, y + 20)
        ctx.stroke()
        
        cy = y + 30
        for line in content_lines:
            ctx.move_to(x, cy)
            ctx.show_text(line)
            cy += 22
            
        if footer:
            ctx.set_source_rgb(*accent_blue)
            ctx.move_to(x, cy + 10)
            ctx.show_text(footer)
            cy += 30
            ctx.set_source_rgb(*black)
            
        # Bottom bracket
        ctx.move_to(x - 10, cy - 20)
        ctx.line_to(x - 10, cy)
        ctx.line_to(x + 2, cy)
        ctx.stroke()

    # --- LEFT COLUMN (Y starts at 100) ---
    
    # 1. CPU USAGE ANOMALY
    top_procs = get_top_processes()
    proc_lines = [f"{p[0]:<15} | CPU: {p[1]:>5}% | RAM: {p[2]:>5}%" for p in top_procs]
    draw_card(60, 100, "SYS.PROC_ANOMALY", proc_lines)

    # 2. DOCKER CONTAINER STATUS
    docker_status = get_docker_status()
    doc_lines = [f"{d[0]:<15} | {d[1]:<10} | {d[2]:<6}" for d in docker_status]
    draw_card(60, 320, "SYS.DOCKER_ENG", ["NAME            | STATUS     | PORT"] + doc_lines)
    
    # --- RIGHT COLUMN (Y starts at 100) ---
    
    # 3. CURRENT DIRECTIVE
    directive = get_current_directive()
    draw_card(1420, 100, "USR.DIRECTIVE", directive, footer="[MOD+SHIFT+F] TO EDIT")

    # 4. DISK I/O & STORAGE
    root_free = get_disk_io_and_storage()
    disk_lines = [f"ROOT FREE SPACE: {root_free}", "SSD I/O: ACTIVE TELEMETRY LOGGING"]
    draw_card(1420, 320, "SYS.DISK_IO", disk_lines)

    # 5. LAST GIT OPERATIONS
    commits = get_recent_commits()
    draw_card(1420, 480, "NET.GIT_OPS", commits)

    # --- BOTTOM CORNER: HEATMAP ---
    heatmap_path = "/dev/shm/git_heatmap.png"
    if os.path.exists(heatmap_path):
        try:
            img = cairo.ImageSurface.create_from_png(heatmap_path)
            w, h = img.get_width(), img.get_height()
            # Moved to Bottom Left to not overlap the globe
            ctx.set_source_surface(img, 60, height - h - 60)
            ctx.paint()
            
            # Label
            ctx.move_to(60, height - h - 70)
            ctx.set_source_rgb(*black)
            ctx.show_text("[NET.GIT_HEATMAP]")
        except: pass

    # Save to tmp and then rename for atomic replace
    tmp_path = "/dev/shm/markab_bg_tmp.png"
    out_path = "/dev/shm/markab_bg.png"
    surface.write_to_png(tmp_path)
    os.rename(tmp_path, out_path)
    
    # Set wallpaper
    os.system("feh --no-fehbg --bg-fill " + out_path)

if __name__ == "__main__":
    while True:
        draw_hud()
        time.sleep(2.5)
