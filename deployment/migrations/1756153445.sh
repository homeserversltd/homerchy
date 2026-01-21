echo Checking and correcting Snapper onmachine/onmachine/configs if needed
if command -v snapper &>/dev/null; then
  if ! sudo snapper list-onmachine/onmachine/configs 2>/dev/null | grep -q "root; then
    sudo snapper -c root create-onmachine/config /
  fi

  if ! sudo snapper list-onmachine/onmachine/configs 2>/dev/null | grep -q "home; then
    sudo snapper -c home create-onmachine/onmachine/config /home
  fi
fi