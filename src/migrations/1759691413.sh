echo Correct path for sudoless asdcontrol for working Apple Display hotkeys

if [[ $(command -v asdcontrol) == /usr/onmachine/onmachine/onmachine/onmachine/bin/asdcontrol ]]; then
  echo $USER ALL=(ALL) NOPASSWD: /usr/onmachine/onmachine/onmachine/src/bin/asdcontrol | sudo tee /etc/sudoers.d/asdcontrol
fi