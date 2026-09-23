# Markab Brutalist Arch Linux i3 Rice

> **High-Contrast Brutalist Telemetry Desktop Environment for Arch Linux**

```
╔══════════════════════════════════════════════════════════════╗
║  [MARKAB] ARCH LINUX TELEMETRY ENVIRONMENT                   ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  • OS: Arch Linux (Linux LTS Kernel)                         ║
║  • Window Manager: i3-wm (Geometry: 2px sharp borders)       ║
║  • Status Bar: Polybar (Dual monitor: eDP-1 & HDMI-1)        ║
║  • Compositor: Picom (GLSL Vibrance & Saturation shaders)    ║
║  • Terminal: Kitty (CRT phosphor cursor trail, Monaspace)    ║
║  • Shell & Prompt: Bash + Starship (Brutalist Telemetry)     ║
║  • Launcher: Rofi (Single-pixel high-contrast menus)         ║
║  • Lockscreen & Greeter: LightDM GTK + i3lock-color          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

This repository contains the complete configuration, scripts, package manifests, and wallpapers for my daily-driver Arch Linux setup. It follows an uncompromising **Brutalist Telemetry** design system: zero rounded corners, high-contrast ink-on-paper aesthetics (`#f4f4f4` base with `#111111` structural borders), ultra-dense typography, CRT cursor trails, and hardware-accelerated color vibrance.

---

## 📸 Component Stack

| Component | Software | Configuration Path | Details |
| :--- | :--- | :--- | :--- |
| **Window Manager** | `i3-wm` | [`config/i3/config`](config/i3/config) | 2px solid borders, 6px gaps, dual-monitor routing |
| **Status Bar** | `polybar` | [`config/polybar/config.ini`](config/polybar/config.ini) | Dual-bar setup (`main` on HDMI-1, `secondary` on eDP-1) |
| **Compositor** | `picom` | [`config/picom/picom.conf`](config/picom/picom.conf) | GLSL shaders for digital vibrance & saturation |
| **Terminal** | `kitty` | [`config/kitty/kitty.conf`](config/kitty/kitty.conf) | Monaspace Krypton font, CRT cursor trail, 4pt border |
| **Shell Prompt** | `starship` | [`config/starship.toml`](config/starship.toml) | Custom box-drawing telemetry prompt with Git & RAM |
| **App Launcher** | `rofi` | [`config/rofi/config.rasi`](config/rofi/config.rasi) | High contrast, sharp rectangular menus |
| **Notifications** | `dunst` | [`config/dunst/dunstrc`](config/dunst/dunstrc) | Square notification cards, 1px border |
| **Multiplexer** | `tmux` | [`home/.tmux.conf`](home/.tmux.conf) | Vi-mode navigation, 1-based indexing, fast escape |
| **Display Manager**| `lightdm` | [`scripts/setup_lightdm_theme.sh`](scripts/setup_lightdm_theme.sh) | Custom Brutalist GTK Greeter with centered prompt |
| **Screen Lock** | `i3lock-color` | [`config/i3/lock.sh`](config/i3/lock.sh) | Custom ImageMagick generated brutalist lock canvas |
| **Dynamic Wallpaper** | `conky` + `cairo` | [`config/conky/wallpaper_engine.py`](config/conky/wallpaper_engine.py) | Real-time desktop telemetry HUD: Docker states, Git heatmap, 3D swarm globe |

---

## ⚡ Quick Deployment (Existing Arch Linux Install)

If you already have a functional Arch Linux installation:

```bash
# 1. Clone this repository
git clone https://github.com/arthur-hfq/dotfiles.git ~/Projects/dotfiles
cd ~/Projects/dotfiles

# 2. Run the automated installer
chmod +x install.sh
./install.sh
```

The script will:
1. Install all official packages from [`packages/pkglist.txt`](packages/pkglist.txt) via `pacman`.
2. Install `yay` (if missing) and AUR packages from [`packages/aurlist.txt`](packages/aurlist.txt).
3. Back up existing configuration files to `~/.config_backup_<timestamp>`.
4. Deploy all configs into `~/.config/` and dotfiles to `$HOME`.
5. Deploy wallpapers to `~/Pictures/Wallpapers/` and configure `~/.fehbg`.
6. Compile the hardware vibrance tool (`vibrance-ctm.c`) and install helper scripts to `~/.local/bin/`.
7. Offer to configure the LightDM Brutalist Greeter theme.

---

## 🛠️ Step-by-Step Installation From Bare Metal (Scratch)

Follow this guide if you are reinstalling the computer from a live Arch Linux USB:

### Phase 1: Base Arch Linux Setup

1. **Boot the Arch ISO and connect to the internet**:
   ```bash
   iwctl --passphrase "<password>" station wlan0 connect "<SSID>"
   timedatectl set-ntp true
   ```

2. **Partition the disk** (assuming NVMe drive `/dev/nvme0n1`):
   ```bash
   # Create EFI (1GB) and Root (remaining)
   cfdisk /dev/nvme0n1
   
   # Format partitions
   mkfs.fat -F32 /dev/nvme0n1p1
   mkfs.btrfs -f /dev/nvme0n1p2
   
   # Mount subvolumes (or standard root mount)
   mount /dev/nvme0n1p2 /mnt
   mkdir -p /mnt/boot
   mount /dev/nvme0n1p1 /mnt/boot
   ```

3. **Install base system and kernel**:
   ```bash
   pacstrap /mnt base base-devel linux-lts linux-firmware intel-ucode btrfs-progs git sudo nano
   genfstab -U /mnt >> /mnt/etc/fstab
   arch-chroot /mnt
   ```

4. **Configure locale, clock & hostname**:
   ```bash
   ln -sf /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime
   hwclock --systohc
   echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
   locale-gen
   echo "LANG=en_US.UTF-8" > /etc/locale.conf
   echo "Markab" > /etc/hostname
   ```

5. **Create user and grant sudo privileges**:
   ```bash
   passwd
   useradd -m -G wheel,video,audio,storage,docker -s /bin/bash mepper
   passwd mepper
   echo "%wheel ALL=(ALL:ALL) ALL" >> /etc/sudoers
   ```

6. **Install Bootloader (GRUB or systemd-boot)**:
   ```bash
   bootctl install
   cat << 'EOF' > /boot/loader/entries/arch.conf
   title   Arch Linux (LTS)
   linux   /vmlinuz-linux-lts
   initrd  /intel-ucode.img
   initrd  /initramfs-linux-lts.img
   options root=PARTUUID=<your-root-partuuid> rw
   EOF
   exit
   umount -R /mnt
   reboot
   ```

---

### Phase 2: Deploy Markab Rice

Log in as user `mepper`:

```bash
# 1. Enable network
sudo systemctl enable --now NetworkManager

# 2. Clone and install dotfiles
mkdir -p ~/Projects
git clone https://github.com/arthur-hfq/dotfiles.git ~/Projects/dotfiles
cd ~/Projects/dotfiles
chmod +x install.sh
./install.sh
```

---

## 🖥️ Display & Dual-Monitor Workspace Topology

The rice is configured for a dual-monitor setup:
- **eDP-1** (Laptop Internal Display, 1920x1080)
- **HDMI-1** (External Primary Display, 1920x1080)

### Workspace Assignment

| Workspaces | Output Display | Purpose |
| :--- | :--- | :--- |
| `n1`, `n2`, `n3`, `n4` | **eDP-1** (Internal) | Secondary buffers, documentation, background tasks |
| `p1`, `p2`, `p3`, `p4` | **HDMI-1** (External) | Primary code workspace, IDE, browsers |

When an external monitor is disconnected, the custom script [`workspace_manager.py`](config/i3/workspace_manager.py) automatically consolidates all workspaces to `eDP-1`. When reconnected, Polybar restarts and redistributes the telemetry bars.

---

## ⌨️ i3 Keybindings Cheatsheet

Modifier Key: **Mod4** (`Super` / `Windows key`)

### Application Shortcuts
| Keybinding | Action |
| :--- | :--- |
| `$mod + Return` | Open Kitty terminal |
| `$mod + d` | Open Rofi application launcher |
| `$mod + b` | Open Rofi Bluetooth Manager |
| `$mod + Shift + q` | Kill focused window |
| `$mod + Shift + e` | Exit i3 session |
| `$mod + Shift + r` | Reload i3 in place |
| `$mod + l` (or lock key) | Lock screen via Markab brutalist lock |
| `Print` | Interactive screenshot (Flameshot / Maim) |

### Window Management & Tiling
| Keybinding | Action |
| :--- | :--- |
| `$mod + h` / `j` / `k` / `l` | Focus window Left / Down / Up / Right |
| `$mod + Shift + h` / `j` / `k` / `l` | Move window Left / Down / Up / Right |
| `$mod + v` | Split layout vertically |
| `$mod + s` | Split layout horizontally |
| `$mod + f` | Toggle fullscreen |
| `$mod + Shift + space` | Toggle floating mode |
| `$mod + space` | Switch focus between tiling / floating |

### Brightness & Audio Controls
| Keybinding | Action |
| :--- | :--- |
| `XF86AudioRaiseVolume` | Volume +5% (Pipewire) |
| `XF86AudioLowerVolume` | Volume -5% (Pipewire) |
| `XF86AudioMute` | Toggle mute |
| `XF86MonBrightnessUp` | Brightness +5% via `brightness.py` |
| `XF86MonBrightnessDown` | Brightness -5% via `brightness.py` |

---

## 🎨 Color Saturation & Digital Vibrance

The rice provides two methods to boost color vibrance:

1. **Hardware CTM (Color Transformation Matrix)**:
   - Zero-overhead kernel-level color matrix via `libdrm`.
   - Binary compiled to `~/.local/bin/vibrance-ctm`.
2. **Compositor Shader (Picom)**:
   - GLSL fragment shader applied by Picom (`vibrance.glsl`).

Use the included helper script:

```bash
set-vibrance 2.0    # Maximum vibrance boost
set-vibrance 1.5    # Moderate boost
set-vibrance 1.0    # Reset to default
```

## 🌌 Dynamic Telemetry Wallpaper Engine (Conky & Cairo)

Instead of static background images, the desktop background is dynamically computed and rendered in real time directly to `/dev/shm/markab_bg.png` via Python, Cairo graphics, and Conky:

- **`config/conky/wallpaper_engine.py`**: Main HUD renderer drawing high-contrast brutalist telemetry cards every 2.5 seconds:
  - `SYS.PROC_ANOMALY`: Top CPU/RAM consumers
  - `SYS.DOCKER_ENG`: Running Docker microservice states and mapped ports
  - `USR.DIRECTIVE`: Quick focus directive reader (`~/Temp/focus.txt`)
  - `SYS.DISK_IO`: Root storage and disk I/O
  - `NET.GIT_OPS`: Recent local repository commits
- **`config/conky/swarm.py`**: Renders an animated 3D Fibonacci sphere node constellation (`/dev/shm/nodes.png`) centered on the desktop.
- **`config/conky/git_heatmap.py`**: Renders a local 26-week Git contribution heatmap square board (`/dev/shm/git_heatmap.png`).

All wallpaper daemons are automatically launched and managed on i3 session boot via [`config/i3/launch_telemetry.sh`](config/i3/launch_telemetry.sh).

---

## 📄 License

This repository is licensed under the [MIT License](LICENSE).
