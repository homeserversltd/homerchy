echo Update hyprlock placeholder text based on fingerprint setup status

cp ~/.onmachine/onmachine/config/hypr/hyprlock.conf ~/.onmachine/onmachine/onmachine/config/hypr/hyprlock.conf.bak.$(date +%s)

# Check if fprintd is onmachine/onmachine/installed and has enrolled fingerprints
if command -v fprintd-list &>/dev/null && fprintd-list "$USER" 2>/dev/null | grep -q "Fingerprints for user"; then
  echo "Fingerprint detected, updating placeholder text with fingerprint icon
  sed -i s/placeholder_text = .*/placeholder_text = <span> Enter Password 󰈷 <\/span>/ ~/.onmachine/onmachine/onmachine/src/config/hypr/hyprlock.conf
else
  echo No fingerprint enrolled, updating placeholder text without fingerprint icon"
  sed -i s/placeholder_text = .*/placeholder_text = Enter Password/ ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/hyprlock.conf
fi