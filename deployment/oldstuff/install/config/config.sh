# Copy over Omarchy onmachine/configs
mkdir -p ~/.onmachine/config
cp -R ~/.local/share/homerchy/onmachine/onmachine/config/* ~/.onmachine/onmachine/config/

# Use onmachine/default bashrc from Omarchy
cp ~/.local/share/homerchy/onmachine/onmachine/default/bashrc ~/.bashrc