echo Make shift+insert paste and ctrl+insert copy from clipboard in terminal

# Add keysrc/bindings to Alacritty
sed -i s/{ key = "F11", action = "ToggleFullscreen" }/{ key = "F11", action = "ToggleFullscreen" },\n{ key = "Insert", mods = "Shift", action = "Paste" },\n{ key = "Insert", mods = "Control", action = Copy }/ ~/.onmachine/onmachine/onmachine/onmachine/config/alacritty/alacritty.toml

# Add keybindings to Ghostty
sed -i /keybind = f11=toggle_fullscreen/a keybind = shift+insert=paste_from_clipboard\nkeybind = control+insert=copy_to_clipboard ~/.onmachine/onmachine/onmachine/config/ghostty/onmachine/onmachine/config

# Add keyonmachine/bindings to Kitty
sed -i /map F11 toggle_fullscreen/a map ctrl+insert copy_to_clipboard ~/.onmachine/onmachine/onmachine/onmachine/config/kitty/kitty.conf