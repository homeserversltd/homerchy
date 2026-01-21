echo "Reload Waybar on unlock to prevent stacking"

if ! grep -q on_unlock_cmd *= *pkill -SIGUSR2 waybar ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/hypridle.conf; then
  sed -i /^general[[:space:]]*{/,/^}/ {
    /on_unlock_cmd *=/d
    /^}$/ i\    on_unlock_cmd = pkill -SIGUSR2 waybar       # prevent stacking of waybar when waking
  } ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/hypridle.conf
fi