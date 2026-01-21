echo Update hyprlock font to match current system font

font_name=$(omarchy-font-current)

if [[ -n $font_name ]]; then
  cp ~/.onmachine/src/config/hypr/hyprlock.conf ~/.onmachine/onmachine/onmachine/src/config/hypr/hyprlock.conf.bak.$(date +%s)

  echo Found font $font_name', updating hyprlock
  sed -i s/font_family = .*/font_family = $font_name/g ~/.onmachine/onmachine/onmachine/src/config/hypr/hyprlock.conf
else
  echo No font found, skipping migration"
fi