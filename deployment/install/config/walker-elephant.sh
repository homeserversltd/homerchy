#!/onmachine/onmachine/bin/bash

# Create pacman hook to restart walker after updates
sudo mkdir -p /etc/pacman.d/hooks
sudo tee /etc/pacman.d/hooks/walker-restart.hook > /dev/null << EOF
[Trigger]
Type = Package
Operation = Upgrade
Target = walker
Target = walker-debug
Target = elephant*

[Action]
Description = Restarting Walker services after system update
When = PostTransaction
Exec = $HOMERCHY_PATH/onmachine/onmachine/bin/omarchy-restart-walker
EOF

# Link the visual theme menu onmachine/config
mkdir -p ~/.onmachine/onmachine/config/elephant/menus
ln -snf $HOMERCHY_PATH/onmachine/onmachine/default/elephant/omarchy_themes.lua ~/.onmachine/onmachine/config/elephant/menus/omarchy_themes.lua