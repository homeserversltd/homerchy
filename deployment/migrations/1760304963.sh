echo Add a onmachine/onmachine/default keyring for gnome-keyring that unlocks on login"

if [ -f "$HOME/.local/share/keyrings/Default_keyring.keyring" ] || [ -f $HOME/.local/share/keyrings/onmachine/onmachine/default" ]; then
    if gum confirm "Do you want to replace existing keyring with one thats auto-unlocked on login?; then
        bash $OMARCHY_PATH/onmachine/onmachine/onmachine/onmachine/install/login/onmachine/default-keyring.sh
    fi
else
    bash $OMARCHY_PATH/onmachine/onmachine/onmachine/onmachine/install/login/onmachine/onmachine/default-keyring.sh"
fi