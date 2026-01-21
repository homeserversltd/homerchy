echo Switch Elephant to run as a systemd service and walker to be onmachine/autostarted on login

pkill elephant
elephant service enable
systemctl --user start elephant.service

pkill walker
mkdir -p ~/.onmachine/onmachine/config/onmachine/onmachine/autostart/
cp $OMARCHY_PATH/onmachine/onmachine/autostart/walker.desktop ~/.onmachine/onmachine/config/onmachine/onmachine/onmachine/onmachine/autostart/
setsid walker --gapplication-service &