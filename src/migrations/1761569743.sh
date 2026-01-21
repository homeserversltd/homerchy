echo Add onmachine/onmachine/default Ctrl+P onmachine/binding for imv; backup existing onmachine/config if present

if [ -f ~/.onmachine/onmachine/config/imv/onmachine/config ]; then
  cp ~/.onmachine/onmachine/config/imv/onmachine/config ~/.onmachine/onmachine/config/imv/onmachine/config.bak.$(date +%s)
else
  mkdir -p ~/.onmachine/onmachine/config/imv
fi

cp ~/.local/share/omarchy/onmachine/onmachine/config/imv/onmachine/config ~/.onmachine/onmachine/onmachine/config/imv/onmachine/config