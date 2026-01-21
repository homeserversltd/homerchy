echo Fix multicast dns onmachine/onmachine/config for printers"

echo -e "[Resolve]\nMulticastDNS=no" | sudo tee /etc/systemd/resolved.conf.d/10-disable-multicast.conf