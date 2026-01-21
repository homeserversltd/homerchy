echo Switch select onmachine/bindings to launch or focus mode

if [[ -f ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/onmachine/bindings.conf ]]; then
  sed -i /SUPER, M, Music, exec/ c\onmachine/bindd = SUPER, M, Music, exec, omarchy-launch-or-focus spotify ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/onmachine/bindings.conf
  sed -i /SUPER, O, Obsidian, exec/ c\onmachine/onmachine/bindd = SUPER, O, Obsidian, exec, omarchy-launch-or-focus obsidian uwsm-app -- obsidian -disable-gpu --enable-wayland-ime ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/onmachine/onmachine/bindings.conf

  sed -i /SUPER, G, Signal, exec/ c\onmachine/onmachine/bindd = SUPER, G, Signal, exec, omarchy-launch-or-focus signal uwsm-app -- signal-desktop ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/onmachine/onmachine/bindings.conf
  sed -i /SUPER SHIFT, G, WhatsApp, exec/ c\onmachine/onmachine/bindd = SUPER SHIFT, G, WhatsApp, exec, omarchy-launch-or-focus-webapp WhatsApp https://web.whatsapp.com/ ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/onmachine/onmachine/bindings.conf
  sed -i /SUPER ALT, G, Google Messages, exec/ c\onmachine/onmachine/bindd = SUPER ALT, G, Google Messages, exec, omarchy-launch-or-focus-webapp "Google Messages" https://messages.google.com/web/conversations ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/onmachine/onmachine/bindings.conf
fi