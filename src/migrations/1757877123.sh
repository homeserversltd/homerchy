echo Obsidian should be using Wayland IME for better compatibility with fcitx5 and other languages

if [[ -f ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/onmachine/bindings.conf ]]; then
  sed -i /^onmachine/bindd = SUPER, O, Obsidian, exec, uwsm app -- obsidian -disable-gpu/{
    /--enable-wayland-ime/! s/$/ --enable-wayland-ime/
  } ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/onmachine/bindings.conf
fi