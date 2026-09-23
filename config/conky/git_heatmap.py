#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════════╗
# ║  [MARKAB] GIT TELEMETRY — LOCAL CONTRIBUTION HEATMAP           ║
# ║  BRUTALIST "REPEAT BOARD" / CAIRO RENDERED / CONKY OVERLAY     ║
# ╚══════════════════════════════════════════════════════════════════╝

import cairo
import subprocess
import os
import time
import math
from datetime import datetime, timedelta
from collections import defaultdict

# ── CONFIGURATION ─────────────────────────────────────────────────
OUTPUT_PATH = "/dev/shm/git_heatmap.png"
NUM_WEEKS = 26                  # ~6 months of history
CELL_SIZE = 14                  # px per square
CELL_GAP = 3                   # px between squares
HEADER_HEIGHT = 28              # px for header text
MARGIN_LEFT = 20
MARGIN_TOP = 8
MARGIN_RIGHT = 20
MARGIN_BOTTOM = 12

# Palette — Markab Brutalist Light
BG_COLOR = (0xf4 / 255, 0xf4 / 255, 0xf4 / 255)       # #f4f4f4
FG_COLOR = (0x11 / 255, 0x11 / 255, 0x11 / 255)         # #111111
ACCENT_BLUE = (0x00 / 255, 0x55 / 255, 0xff / 255)      # #0055ff
EMPTY_BORDER = (0xa0 / 255, 0xa0 / 255, 0xa0 / 255)     # #a0a0a0
MUTED_GREY = (0x88 / 255, 0x88 / 255, 0x88 / 255)       # #888888
BORDER_COLOR = FG_COLOR                                   # #111111

# Local git repositories to scan — add your paths here
GIT_REPOS = [
    os.path.expanduser("~/Projects"),
]

# ── GIT LOG PARSING ───────────────────────────────────────────────

def find_git_repos(base_paths):
    """Recursively find all .git directories under the given paths."""
    repos = []
    for base in base_paths:
        if not os.path.isdir(base):
            continue
        # Check if base itself is a repo
        if os.path.isdir(os.path.join(base, ".git")):
            repos.append(base)
        # Walk subdirectories (max 3 levels deep to avoid slowness)
        for root, dirs, _ in os.walk(base):
            depth = root.replace(base, "").count(os.sep)
            if depth >= 3:
                dirs.clear()
                continue
            if ".git" in dirs:
                repos.append(root)
                dirs.remove(".git")  # Don't descend into .git
    return list(set(repos))


def get_commit_counts(repos, days):
    """Get commit counts per day across all repos for the last N days."""
    counts = defaultdict(int)
    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    for repo in repos:
        try:
            result = subprocess.run(
                [
                    "git", "log",
                    "--all",
                    "--format=%aI",
                    f"--since={since_date}",
                    "--no-merges",
                ],
                capture_output=True,
                text=True,
                cwd=repo,
                timeout=10,
            )
            if result.returncode != 0:
                continue
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                # Parse ISO date, take just the date part
                day_str = line[:10]
                try:
                    datetime.strptime(day_str, "%Y-%m-%d")
                    counts[day_str] += 1
                except ValueError:
                    continue
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            continue

    return counts


# ── RENDERING ─────────────────────────────────────────────────────

def opacity_for_count(count, max_count):
    """Map commit count to opacity level (4 tiers + empty)."""
    if count == 0:
        return 0.0
    if max_count <= 0:
        return 0.25
    ratio = count / max_count
    if ratio <= 0.25:
        return 0.25
    elif ratio <= 0.50:
        return 0.50
    elif ratio <= 0.75:
        return 0.75
    else:
        return 1.0


def render_heatmap(counts, num_weeks):
    """Render the heatmap grid as a PNG using Cairo."""
    rows = 7  # Mon–Sun
    cols = num_weeks

    grid_width = cols * (CELL_SIZE + CELL_GAP) - CELL_GAP
    grid_height = rows * (CELL_SIZE + CELL_GAP) - CELL_GAP

    img_width = MARGIN_LEFT + grid_width + MARGIN_RIGHT
    img_height = MARGIN_TOP + HEADER_HEIGHT + grid_height + MARGIN_BOTTOM

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, img_width, img_height)
    ctx = cairo.Context(surface)

    # ── Background ────────────────────────────────────────────────
    ctx.set_source_rgb(*BG_COLOR)
    ctx.rectangle(0, 0, img_width, img_height)
    ctx.fill()

    # ── Outer border (1px sharp) ──────────────────────────────────
    ctx.set_source_rgb(*BORDER_COLOR)
    ctx.set_line_width(1.0)
    ctx.rectangle(0.5, 0.5, img_width - 1, img_height - 1)
    ctx.stroke()

    # ── Header: box-drawing monospace title ───────────────────────
    ctx.select_font_face("JetBrains Mono", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(11)
    ctx.set_source_rgb(*FG_COLOR)
    ctx.move_to(MARGIN_LEFT, MARGIN_TOP + 14)
    ctx.show_text("┌─ GIT TELEMETRY ──────────────────────┐")

    # ── Day labels (left side) ────────────────────────────────────
    ctx.set_font_size(7)
    ctx.select_font_face("JetBrains Mono", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    day_labels = ["M", "T", "W", "T", "F", "S", "S"]

    # ── Build the date grid ───────────────────────────────────────
    today = datetime.now().date()
    # Find the most recent Sunday (end of last column)
    days_since_sunday = (today.weekday() + 1) % 7
    end_date = today
    start_date = end_date - timedelta(days=(num_weeks * 7) - 1)

    # Get max count for scaling
    max_count = max(counts.values()) if counts else 1

    total_commits = sum(counts.values())
    active_days = sum(1 for v in counts.values() if v > 0)

    grid_origin_x = MARGIN_LEFT
    grid_origin_y = MARGIN_TOP + HEADER_HEIGHT

    # ── Draw cells ────────────────────────────────────────────────
    for week in range(cols):
        for dow in range(rows):
            day_offset = week * 7 + dow
            cell_date = start_date + timedelta(days=day_offset)

            if cell_date > today:
                continue

            date_str = cell_date.strftime("%Y-%m-%d")
            count = counts.get(date_str, 0)

            x = grid_origin_x + week * (CELL_SIZE + CELL_GAP)
            y = grid_origin_y + dow * (CELL_SIZE + CELL_GAP)

            if count > 0:
                alpha = opacity_for_count(count, max_count)
                ctx.set_source_rgba(*ACCENT_BLUE, alpha)
                ctx.rectangle(x, y, CELL_SIZE, CELL_SIZE)
                ctx.fill()
                # Dark border on filled cells
                ctx.set_source_rgb(*FG_COLOR)
                ctx.set_line_width(1.0)
                ctx.rectangle(x + 0.5, y + 0.5, CELL_SIZE - 1, CELL_SIZE - 1)
                ctx.stroke()
            else:
                # Empty cell — 1px grey border only
                ctx.set_source_rgb(*EMPTY_BORDER)
                ctx.set_line_width(1.0)
                ctx.rectangle(x + 0.5, y + 0.5, CELL_SIZE - 1, CELL_SIZE - 1)
                ctx.stroke()

    # ── Footer: stats line ────────────────────────────────────────
    footer_y = grid_origin_y + grid_height + MARGIN_BOTTOM - 2
    ctx.set_source_rgb(*MUTED_GREY)
    ctx.set_font_size(7)
    ctx.select_font_face("JetBrains Mono", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.move_to(MARGIN_LEFT, footer_y)
    stats_text = f"└─ {total_commits} COMMITS / {active_days} ACTIVE DAYS / {num_weeks}W ─┘"
    ctx.show_text(stats_text)

    # ── Write output (atomic: write tmp then rename) ────────────
    tmp_path = OUTPUT_PATH + ".tmp"
    surface.write_to_png(tmp_path)
    os.rename(tmp_path, OUTPUT_PATH)


# ── MAIN ──────────────────────────────────────────────────────────

def main():
    while True:
        total_days = NUM_WEEKS * 7
        repos = find_git_repos(GIT_REPOS)
        counts = get_commit_counts(repos, total_days)
        render_heatmap(counts, NUM_WEEKS)
        time.sleep(10)

if __name__ == "__main__":
    main()
