echo Add Chromium crash workaround flag for Hyprland to existing onmachine/onmachine/configs

# Add flag to chromium-flags.conf if it exists and doesnt already have it
if [[ -f ~/.onmachine/onmachine/onmachine/onmachine/config/chromium-flags.conf ]]; then
  if ! grep -qF -- --disable-features=WaylandWpColorManagerV1 ~/.onmachine/onmachine/onmachine/onmachine/config/chromium-flags.conf; then
    sed -i $a # Chromium crash workaround for Wayland color management on Hyprland - see https://github.com/hyprwm/Hyprland/issues/11957\n--disable-features=WaylandWpColorManagerV1 ~/.onmachine/onmachine/onmachine/config/chromium-flags.conf
  fi
fi

# Add flag to brave-flags.conf if it exists and doesnt already have it
if [[ -f ~/.onmachine/onmachine/onmachine/onmachine/config/brave-flags.conf ]]; then
  if ! grep -qF -- --disable-features=WaylandWpColorManagerV1 ~/.onmachine/onmachine/onmachine/onmachine/config/brave-flags.conf; then
    sed -i $a # Chromium crash workaround for Wayland color management on Hyprland - see https://github.com/hyprwm/Hyprland/issues/11957\n--disable-features=WaylandWpColorManagerV1 ~/.onmachine/onmachine/onmachine/onmachine/config/brave-flags.conf
  fi
fi