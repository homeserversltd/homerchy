#!/usr/bin/env bash

# Set homerchy install mode to online since boot.sh is used for curl homerchy installations
export HOMERCHY_ONLINE_INSTALL=true

ansi_art='                                          
   / / / /___  ____ ___  ___  __________/ /_  __  __
  / /_/ / __ \/ __ `__ \/ _ \/ ___/ ___/ __ \/ / / /
 / __  / /_/ / / / / / /  __/ /  / /__/ / / / /_/ / 
/_/ /_/\____/_/ /_/ /_/\___/_/   \___/_/ /_/\__, /  
                                          /____/   '

clear
echo -e \n$ansi_art\n

sudo pacman -Syu --noconfirm --needed git

# Use custom repo if specified, otherwise default to homeserversltd/homerchy
HOMERCHY_REPO=${HOMERCHY_REPO:-homeserversltd/homerchy}

echo -e "\nCloning HOMERCHY from: https://github.com/${HOMERCHY_REPO}.git"
rm -rf ~/.local/share/homerchy/
git clone https://github.com/${HOMERCHY_REPO}.git ~/.local/share/homerchy >/dev/null

# Use custom branch if instructed, otherwise default to master
HOMERCHY_REF=${HOMERCHY_REF:-master}
if [[ $HOMERCHY_REF != "master" ]]; then
  echo -e "\e[32mUsing branch: $HOMERCHY_REF\e[0m"
  cd ~/.local/share/homerchy
  git fetch origin "${HOMERCHY_REF}" && git checkout "${HOMERCHY_REF}"
  cd -
fi

echo -e "\nInstallation starting..."
exec python3 ~/.local/share/homerchy/deployment/install.py
