#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════╗
# ║  [MARKAB] ARCH LINUX BRUTALIST RICE INSTALLER                   ║
# ║  Deploys the complete i3, Polybar, Picom, Kitty & System Rice   ║
# ╚══════════════════════════════════════════════════════════════════╝

set -euo pipefail

BOLD=$(tput bold 2>/dev/null || true)
CYAN=$(tput setaf 6 2>/dev/null || true)
GREEN=$(tput setaf 2 2>/dev/null || true)
YELLOW=$(tput setaf 3 2>/dev/null || true)
RED=$(tput setaf 1 2>/dev/null || true)
RESET=$(tput sgr0 2>/dev/null || true)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${HOME}/.config_backup_$(date +%Y%m%d_%H%M%S)"

echo "${BOLD}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo "${BOLD}║  [MARKAB] ARCH LINUX RICE DEPLOYMENT SYSTEM                  ║${RESET}"
echo "${BOLD}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""

# Check OS
if [ ! -f /etc/arch-release ]; then
  echo "${RED}[ERROR] This installer is specifically tailored for Arch Linux.${RESET}"
  read -rp "Do you wish to continue anyway? [y/N]: " confirm
  if [[ ! "$confirm" =~ ^[Yy]$ ]]; then exit 1; fi
fi

# Step 1: Install official packages
if [ -f "${SCRIPT_DIR}/packages/pkglist.txt" ]; then
  echo "${CYAN}==> [1/6] Installing official packages via pacman...${RESET}"
  if command -v pacman &>/dev/null; then
    sudo pacman -S --needed - < "${SCRIPT_DIR}/packages/pkglist.txt" || {
      echo "${YELLOW}[WARNING] Some packages failed to install via pacman. Continuing...${RESET}"
    }
  fi
fi

# Step 2: Install AUR helper (yay) & AUR packages
echo "${CYAN}==> [2/6] Checking AUR helper (yay)...${RESET}"
if ! command -v yay &>/dev/null; then
  echo "Installing yay from AUR..."
  TMP_YAY=$(mktemp -d)
  git clone https://aur.archlinux.org/yay-bin.git "$TMP_YAY"
  (cd "$TMP_YAY" && makepkg -si --noconfirm)
  rm -rf "$TMP_YAY"
fi

if [ -f "${SCRIPT_DIR}/packages/aurlist.txt" ]; then
  echo "Installing AUR packages from aurlist.txt..."
  yay -S --needed --noconfirm - < "${SCRIPT_DIR}/packages/aurlist.txt" || {
    echo "${YELLOW}[WARNING] Some AUR packages failed to install. Continuing...${RESET}"
  }
fi

# Step 3: Backup existing configurations
echo "${CYAN}==> [3/6] Backing up existing configurations to ${BACKUP_DIR}...${RESET}"
mkdir -p "$BACKUP_DIR"
for item in i3 polybar picom rofi kitty dunst conky starship.toml; do
  if [ -e "${HOME}/.config/${item}" ]; then
    cp -r "${HOME}/.config/${item}" "${BACKUP_DIR}/"
  fi
done
for item in .bashrc .bash_profile .fehbg .tmux.conf; do
  if [ -e "${HOME}/${item}" ]; then
    cp "${HOME}/${item}" "${BACKUP_DIR}/"
  fi
done

# Step 4: Deploy configurations
echo "${CYAN}==> [4/6] Deploying Markab configuration files...${RESET}"
mkdir -p "${HOME}/.config" "${HOME}/.local/bin" "${HOME}/Pictures/Wallpapers"

# Copy configs
cp -r "${SCRIPT_DIR}/config/"* "${HOME}/.config/"
sed -i "s|DEFAULT_USER_HOME|${HOME}|g" "${HOME}/.config/picom/picom.conf" "${HOME}/.config/conky/conky.conf" 2>/dev/null || true

# Copy home dotfiles
cp "${SCRIPT_DIR}/home/.bashrc" "${HOME}/.bashrc"
cp "${SCRIPT_DIR}/home/.bash_profile" "${HOME}/.bash_profile"
cp "${SCRIPT_DIR}/home/.fehbg" "${HOME}/.fehbg"
cp "${SCRIPT_DIR}/home/.tmux.conf" "${HOME}/.tmux.conf"
chmod +x "${HOME}/.fehbg"

# Copy wallpapers (if any static fallbacks provided)
if [ -d "${SCRIPT_DIR}/wallpapers" ] && [ "$(ls -A "${SCRIPT_DIR}/wallpapers" 2>/dev/null)" ]; then
  cp "${SCRIPT_DIR}/wallpapers/"* "${HOME}/Pictures/Wallpapers/" 2>/dev/null || true
fi

# Copy scripts and set permissions
cp "${SCRIPT_DIR}/scripts/set-vibrance" "${HOME}/.local/bin/set-vibrance"
chmod +x "${HOME}/.local/bin/set-vibrance"

# Compile hardware vibrance tool if source exists
if [ -f "${SCRIPT_DIR}/scripts/vibrance-ctm.c" ] && command -v gcc &>/dev/null; then
  echo "Compiling hardware vibrance CTM tool..."
  gcc -O2 -o "${HOME}/.local/bin/vibrance-ctm" "${SCRIPT_DIR}/scripts/vibrance-ctm.c" $(pkg-config --cflags --libs libdrm 2>/dev/null || true) -lm 2>/dev/null || true
  chmod +x "${HOME}/.local/bin/vibrance-ctm" 2>/dev/null || true
fi

# Ensure executable permissions on all i3, polybar & conky helper scripts
chmod +x "${HOME}/.config/i3/"*.sh "${HOME}/.config/i3/"*.py 2>/dev/null || true
chmod +x "${HOME}/.config/polybar/"*.sh "${HOME}/.config/polybar/"*.py 2>/dev/null || true
chmod +x "${HOME}/.config/conky/"*.py 2>/dev/null || true

# Step 5: Systemd services
echo "${CYAN}==> [5/6] Enabling essential system services...${RESET}"
SERVICES=(NetworkManager bluetooth docker)
for s in "${SERVICES[@]}"; do
  if systemctl list-unit-files "${s}.service" &>/dev/null; then
    sudo systemctl enable "$s" 2>/dev/null || true
  fi
done

# Step 6: LightDM brutalist greeter (optional)
echo "${CYAN}==> [6/6] LightDM Brutalist Greeter Theme${RESET}"
read -rp "Would you like to install the Brutalist LightDM GTK Greeter theme now? [y/N]: " setup_greeter
if [[ "$setup_greeter" =~ ^[Yy]$ ]]; then
  if [ -f "${SCRIPT_DIR}/scripts/setup_lightdm_theme.sh" ]; then
    sudo "${SCRIPT_DIR}/scripts/setup_lightdm_theme.sh"
    sudo systemctl enable lightdm 2>/dev/null || true
  fi
fi

echo ""
echo "${GREEN}${BOLD}[OK] Markab Brutalist Rice installed successfully!${RESET}"
echo "Restart i3 with ${BOLD}\$mod+Shift+r${RESET} or reboot to log in through LightDM."
