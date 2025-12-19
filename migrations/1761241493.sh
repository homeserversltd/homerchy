echo "Cleanup extra UKI if needed to prevent errors"
if [[ -f /boot/EFI/linux/omarchy_linux.efi ]] && [[ -f /boot/EFI/linux/$(cat /etc/machine-id)_linux.efi ]]; then
  sudo rm -f /boot/EFI/Linux/$(cat /etc/machine-id)_linux.efi

  if grep -q "/boot/EFI/Linux/$(cat /etc/machine-id)_linux.efi" /boot/limine.conf; then
    echo "Resetting limine config and recreating entries"

    sudo mv /boot/limine.conf /boot/limine.conf.bak
  sudo tee /boot/limine.conf <<EOF >/dev/null
### Read more at config document: https://codeberg.org/Limine/Limine/src/branch/v10.x/CONFIG.md
#timeout: 3
default_entry: 0
interface_branding: Omarchy Bootloader
interface_branding_color: 2
hash_mismatch_panic: no

term_background: 1a1b26
backdrop: 1a1b26

# Terminal colors (Tokyo Night palette)
term_palette: 15161e;f7768e;9ece6a;e0af68;7aa2f7;bb9af7;7dcfff;a9b1d6
term_palette_bright: 414868;f7768e;9ece6a;e0af68;7aa2f7;bb9af7;7dcfff;c0caf5

# Text colors
term_foreground: c0caf5
term_foreground_bright: c0caf5
term_background_bright: 24283b

EOF
    # Create boot entries manually
    entry_count=0
    CMDLINE="root=UUID=$(findmnt -n -o UUID /) rw"
    if ls /boot/vmlinuz-* 1>/dev/null 2>&1; then
      for kernel in $(ls -t /boot/vmlinuz-*); do
        kernel_name=$(basename "$kernel" | sed 's/vmlinuz-//')
        initrd="/boot/initramfs-${kernel_name}.img"
        if [[ -f "$initrd" ]]; then
          sudo tee -a /boot/limine.conf >/dev/null <<EOF

/Omarchy ($kernel_name)
    PROTOCOL: linux
    KERNEL_PATH: boot():/vmlinuz-$kernel_name
    MODULE_PATH: boot():/initramfs-$kernel_name.img
    CMDLINE: $CMDLINE quiet splash
EOF
          entry_count=$((entry_count + 1))
        fi
      done
      if [[ $entry_count -gt 0 ]]; then
        sudo sed -i "s/^default_entry:.*/default_entry: 0/" /boot/limine.conf
      fi
    fi
    sudo limine-snapper-sync
  fi
fi