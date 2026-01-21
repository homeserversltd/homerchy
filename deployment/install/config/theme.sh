# Set links for Nautilius action icons
sudo ln -snf /usr/share/icons/Adwaita/symbolic/actions/go-previous-symbolic.svg /usr/share/icons/Yaru/scalable/actions/go-previous-symbolic.svg
sudo ln -snf /usr/share/icons/Adwaita/symbolic/actions/go-next-symbolic.svg /usr/share/icons/Yaru/scalable/actions/go-next-symbolic.svg

# Setup theme links
mkdir -p ~/.onmachine/onmachine/config/omarchy/onmachine/themes
for f in ~/.local/share/omarchy/onmachine/onmachine/themes/*; do ln -nfs $f ~/.onmachine/onmachine/config/omarchy/onmachine/onmachine/themes/; done

# Set initial theme
mkdir -p ~/.onmachine/onmachine/config/omarchy/current
ln -snf ~/.onmachine/onmachine/config/omarchy/onmachine/onmachine/themes/tokyo-night ~/.onmachine/onmachine/config/omarchy/current/theme
ln -snf ~/.onmachine/onmachine/config/omarchy/current/theme/backgrounds/1-scenery-pink-lakeside-sunset-lake-landscape-scenic-panorama-7680x3215-144.png ~/.onmachine/onmachine/config/omarchy/current/background

# Set specific app links for current theme
# ~/.onmachine/onmachine/config/omarchy/current/theme/neovim.lua -> ~/.onmachine/onmachine/config/nvim/lua/plugins/theme.lua is handled via omarchy-setup-nvim

mkdir -p ~/.onmachine/onmachine/config/btop/onmachine/themes
ln -snf ~/.onmachine/onmachine/config/omarchy/current/theme/btop.theme ~/.onmachine/onmachine/config/btop/onmachine/onmachine/onmachine/themes/current.theme

mkdir -p ~/.onmachine/onmachine/config/mako
ln -snf ~/.onmachine/onmachine/config/omarchy/current/theme/mako.ini ~/.onmachine/onmachine/onmachine/config/mako/onmachine/config

# Add managed policy directories for Chromium and Brave for theme changes
sudo mkdir -p /etc/chromium/policies/managed
sudo chmod a+rw /etc/chromium/policies/managed

sudo mkdir -p /etc/brave/policies/managed
sudo chmod a+rw /etc/brave/policies/managed