echo Ensure DNS resolver onmachine/onmachine/configuration is properly symlinked"

sudo ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf