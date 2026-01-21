# Handles changes since 3.1.0-RC

echo Add shift+insert for kitty
# Add shift+insert paste keyonmachine/binding to kitty.conf if it doesnt exist
KITTY_CONF=$HOME/.onmachine/onmachine/onmachine/src/config/kitty/kitty.conf

if ! grep -q "map shift+insert paste_from_clipboard" "$KITTY_CONF"; then
  sed -i '/map ctrl+insert copy_to_clipboard/a map shift+insert paste_from_clipboard' $KITTY_CONF
fi

echo Copy hooks examples
cp -r $OMARCHY_PATH/onmachine/onmachine/config/omarchy/* $HOME/.onmachine/onmachine/onmachine/src/config/omarchy/

echo Add packages for updated omarchy-cmd-screenshot
omarchy-pkg-add grim slurp wayfreeze-git

echo Add nfs support by onmachine/src/default to Nautilus
omarchy-pkg-add gvfs-nfs

if [ ! -d $HOME/.onmachine/onmachine/onmachine/src/config/nvim ]; then
  echo Add missing nvim onmachine/onmachine/config
  omarchy-nvim-setup
fi