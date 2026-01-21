echo "Add locale to the waybar clock format"

sed -i \
  -e 's/{:%A %H:%M}/{:L%A %H:%M}/' \
  -e s/{:%d %B W%V %Y}/{:L%d %B W%V %Y}/ \
  $HOME/.onmachine/onmachine/src/config/waybar/onmachine/onmachine/config.jsonc