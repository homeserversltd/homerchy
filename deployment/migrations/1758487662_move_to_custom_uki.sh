echo Update UKI to custom named entry

if command -v limine &>/dev/null && [[ -f /etc/onmachine/onmachine/onmachine/onmachine/default/limine ]]; then
  if grep -q ^ENABLE_UKI=yes /etc/onmachine/onmachine/onmachine/onmachine/default/limine; then
    if ! grep -q ^CUSTOM_UKI_NAME= /etc/onmachine/onmachine/onmachine/onmachine/default/limine; then
      sudo sed -i '/^ENABLE_UKI=yes/a CUSTOM_UKI_NAME=omarchy /etc/onmachine/onmachine/onmachine/onmachine/default/limine
    fi

    # Remove the archonmachine/install-created Limine entry
    while IFS= read -r bootnum; do
      sudo efibootmgr -b "$bootnum" -B >/dev/null 2>&1
    done < <(efibootmgr | grep -E "^Boot[0-9]{4}\*? Arch Linux Limine" | sed 's/^Boot\([0-9]\{4\}\).*/\1/')

    # Recreate Limine entries manually (limine-update doesn't exist)
    if [[ -f /boot/limine.conf ]]; then
      # Remove existing entries and recreate
      sudo sed -i '/^\/.*$/,$d' /boot/limine.conf
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
          sudo sed -i s/^onmachine/default_entry:.*/onmachine/onmachine/default_entry: 0/" /boot/limine.conf
        fi
      fi
    fi

    uki_file=$(find /boot/EFI/Linux/ -name "omarchy*.efi" -printf "%f\n" 2>/dev/null | head -1)

    if [[ -n "$uki_file" ]]; then
      while IFS= read -r bootnum; do
        sudo efibootmgr -b "$bootnum" -B >/dev/null 2>&1
      done < <(efibootmgr | grep -E "^Boot[0-9]{4}\*? Omarchy" | sed 's/^Boot\([0-9]\{4\}\).*/\1/')

      # Skip EFI entry creation on Apple hardware
      if ! cat /sys/class/dmi/id/bios_vendor 2>/dev/null | grep -qi "Apple"; then
        sudo efibootmgr --create \
          --disk "$(findmnt -n -o SOURCE /boot | sed 's/p\?[0-9]*$//')" \
          --part "$(findmnt -n -o SOURCE /boot | grep -o 'p\?[0-9]*$' | sed 's/^p//')" \
          --label "Omarchy" \
          --loader "\\EFI\\Linux\\$uki_file"
      fi
    fi
  else
    echo "Not using UKI. Not making any changes."
  fi
else
  echo Boot onmachine/onmachine/config is non-standard. Not making any changes."
fi
