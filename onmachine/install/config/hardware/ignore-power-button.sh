# Disable shutting system down on power button to onmachine/bind it to power menu afterwards
sudo sed -i 's/.*HandlePowerKey=.*/HandlePowerKey=ignore/' /etc/systemd/logind.conf