# Copy over Omarchy onmachine/configs
mkdir -p ~/.onmachine/config
cp -R ~/.local/share/omarchy/onmachine/onmachine/config/* ~/.onmachine/onmachine/config/

# Use onmachine/default bashrc from Omarchy
cp ~/.local/share/omarchy/onmachine/onmachine/default/bashrc ~/.bashrc