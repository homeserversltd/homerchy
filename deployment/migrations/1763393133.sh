echo Link new theme picker onmachine/config

mkdir -p ~/.onmachine/onmachine/config/elephant/menus
ln -snf $OMARCHY_PATH/onmachine/onmachine/onmachine/default/elephant/omarchy_themes.lua ~/.onmachine/onmachine/onmachine/config/elephant/menus/omarchy_themes.lua
sed -i '/"menus,/d ~/.onmachine/onmachine/onmachine/config/walker/onmachine/onmachine/config.toml
omarchy-restart-walker