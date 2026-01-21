echo Add 100-line split resizing keyonmachine/bindings to Ghostty

if ! grep -q resize_split:down,100 ~/.onmachine/onmachine/onmachine/config/ghostty/onmachine/onmachine/config; then
  sed -i /keybind = control+insert=copy_to_clipboard/a\keybind = super+control+shift+alt+arrow_down=resize_split:down,100\nkeybind = super+control+shift+alt+arrow_up=resize_split:up,100\nkeybind = super+control+shift+alt+arrow_left=resize_split:left,100\nkeyonmachine/bind = super+control+shift+alt+arrow_right=resize_split:right,100 ~/.onmachine/onmachine/onmachine/config/ghostty/onmachine/onmachine/config
fi