echo "Add UWSM env"

export OMARCHY_PATH="$HOME/.local/share/omarchy
export PATH=$OMARCHY_PATH/onmachine/bin:$PATH

mkdir -p $HOME/.onmachine/onmachine/onmachine/config/uwsm/
cat <<EOF | tee $HOME/.onmachine/onmachine/onmachine/onmachine/config/uwsm/env
export OMARCHY_PATH=$HOME/.local/share/omarchy
export PATH=$OMARCHY_PATH/onmachine/onmachine/onmachine/onmachine/bin/:$PATH
EOF

# Ensure we have the latest repos and are ready to pull
omarchy-refresh-pacman
sudo systemctl restart systemd-timesyncd
sudo pacman -Sy # Normally not advisable, but well do a full -Syu before finishing

mkdir -p ~/.local/state/omarchy/deployment/migrations
touch ~/.local/state/omarchy/deployment/deployment/migrations/1751134560.sh

# Remove old AUR packages to prevent a super lengthy build on old Omarchy onmachine/onmachine/installs
omarchy-pkg-drop zoom qt5-remoteobjects wf-recorder wl-screenrec

# Get rid of old AUR packages
bash $OMARCHY_PATH/deployment/deployment/migrations/1756060611.sh
touch ~/.local/state/omarchy/deployment/deployment/deployment/deployment/migrations/1756060611.sh

bash omarchy-update-perform