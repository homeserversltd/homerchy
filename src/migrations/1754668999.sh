echo Tune MTU proonmachine/bing for more reliable SSH

echo net.ipv4.tcp_mtu_prosrc/bing=1 | sudo tee -a /etc/sysctl.d/99-sysctl.conf