if command -v limine &>/dev/null; then
  sudo pacman -S --noconfirm --needed limine-snapper-sync limine-mkinitcpio-hook

  sudo tee /etc/mkinitcpio.conf.d/omarchy_hooks.conf <<EOF >/dev/null
HOOKS=(base udev plymouth keyboard autodetect microcode modconf kms keymap consolefont block encrypt filesystems fsck btrfs-overlayfs)
EOF

  [[ -f /boot/EFI/limine/limine.conf ]] || [[ -f /boot/EFI/BOOT/limine.conf ]] && EFI=true

  # Conf location is different between EFI and BIOS
  if [[ -n "$EFI" ]]; then
    # Check USB location first, then regular EFI location
    if [[ -f /boot/EFI/BOOT/limine.conf ]]; then
      limine_config="/boot/EFI/BOOT/limine.conf"
    else
      limine_config="/boot/EFI/limine/limine.conf"
    fi
  else
    limine_config="/boot/limine/limine.conf"
  fi

  # Double-check and exit if we don't have a config file for some reason
  if [[ ! -f $limine_config ]]; then
    echo "Error: Limine config not found at $limine_config" >&2
    exit 1
  fi

  # Extract cmdline from existing config, or use defaults
  CMDLINE=$(grep "^[[:space:]]*cmdline:" "$limine_config" 2>/dev/null | head -1 | sed 's/^[[:space:]]*cmdline:[[:space:]]*//' || echo "")
  
  # Fallback to default cmdline if not found
  if [[ -z "$CMDLINE" ]]; then
    CMDLINE="root=UUID=$(findmnt -n -o UUID /) rw"
    echo "Using default cmdline: $CMDLINE"
  fi

  sudo tee /etc/default/limine <<EOF >/dev/null
TARGET_OS_NAME="Homerchy"

ESP_PATH="/boot"

KERNEL_CMDLINE[default]="$CMDLINE"
KERNEL_CMDLINE[default]+="quiet splash"

ENABLE_UKI=yes
CUSTOM_UKI_NAME="homerchy"

ENABLE_LIMINE_FALLBACK=yes

# Find and add other bootloaders
FIND_BOOTLOADERS=yes

BOOT_ORDER="*, *fallback, Snapshots"

MAX_SNAPSHOT_ENTRIES=5

SNAPSHOT_FORMAT_CHOICE=5
EOF

  # UKI and EFI fallback are EFI only
  if [[ -z $EFI ]]; then
    sudo sed -i '/^ENABLE_UKI=/d; /^ENABLE_LIMINE_FALLBACK=/d' /etc/default/limine
  fi

  # Create base config - entries will be added manually below
  sudo tee /boot/limine.conf <<EOF >/dev/null
### Read more at config document: https://codeberg.org/Limine/Limine/src/branch/v10.x/CONFIG.md
#timeout: 3
default_entry: 0
interface_branding: Homerchy Bootloader
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

  # Remove the original config file if it's not /boot/limine.conf
  if [[ "$limine_config" != "/boot/limine.conf" ]] && [[ -f "$limine_config" ]]; then
    sudo rm "$limine_config"
  fi


  # Match Snapper configs if not installing from the ISO
  if [[ -z ${OMARCHY_CHROOT_INSTALL:-} ]]; then
    if ! sudo snapper list-configs 2>/dev/null | grep -q "root"; then
      sudo snapper -c root create-config /
    fi

    if ! sudo snapper list-configs 2>/dev/null | grep -q "home"; then
      sudo snapper -c home create-config /home
    fi
  fi

  # Tweak default Snapper configs
  sudo sed -i 's/^TIMELINE_CREATE="yes"/TIMELINE_CREATE="no"/' /etc/snapper/configs/{root,home}
  sudo sed -i 's/^NUMBER_LIMIT="50"/NUMBER_LIMIT="5"/' /etc/snapper/configs/{root,home}
  sudo sed -i 's/^NUMBER_LIMIT_IMPORTANT="10"/NUMBER_LIMIT_IMPORTANT="5"/' /etc/snapper/configs/{root,home}

  chrootable_systemctl_enable limine-snapper-sync.service
fi

echo "Re-enabling mkinitcpio hooks..."

# Restore the specific mkinitcpio pacman hooks
if [ -f /usr/share/libalpm/hooks/90-mkinitcpio-install.hook.disabled ]; then
  sudo mv /usr/share/libalpm/hooks/90-mkinitcpio-install.hook.disabled /usr/share/libalpm/hooks/90-mkinitcpio-install.hook
fi

if [ -f /usr/share/libalpm/hooks/60-mkinitcpio-remove.hook.disabled ]; then
  sudo mv /usr/share/libalpm/hooks/60-mkinitcpio-remove.hook.disabled /usr/share/libalpm/hooks/60-mkinitcpio-remove.hook
fi

echo "mkinitcpio hooks re-enabled"

# Generate initramfs before updating Limine config
echo "Generating initramfs..."
if command -v limine-mkinitcpio &>/dev/null; then
  sudo limine-mkinitcpio || sudo mkinitcpio -P
else
  sudo mkinitcpio -P
fi

echo "Creating Limine bootloader entries manually..."
# Create boot entries for all available kernels
entry_count=0
if ls /boot/vmlinuz-* 1>/dev/null 2>&1; then
  # Get root UUID for cmdline if not already set
  if [[ -z "$CMDLINE" ]]; then
    CMDLINE="root=UUID=$(findmnt -n -o UUID /) rw"
  fi
  
  # Process kernels in reverse order (newest first) to create entries
  for kernel in $(ls -t /boot/vmlinuz-*); do
    kernel_name=$(basename "$kernel" | sed 's/vmlinuz-//')
    initrd="/boot/initramfs-${kernel_name}.img"
    
    if [[ -f "$initrd" ]]; then
      # Create entry for this kernel
      sudo tee -a /boot/limine.conf >/dev/null <<EOF

/Homerchy ($kernel_name)
    PROTOCOL: linux
    KERNEL_PATH: boot():/vmlinuz-$kernel_name
    MODULE_PATH: boot():/initramfs-$kernel_name.img
    CMDLINE: $CMDLINE quiet splash
EOF
      echo "Created Limine entry for kernel: $kernel_name"
      entry_count=$((entry_count + 1))
    else
      echo "WARNING: No initramfs found for kernel $kernel_name, skipping entry"
    fi
  done
  
  # Update default_entry to point to first entry (0-based index)
  if [[ $entry_count -gt 0 ]]; then
    sudo sed -i "s/^default_entry:.*/default_entry: 0/" /boot/limine.conf
    echo "Created $entry_count Limine boot entries"
  else
    echo "ERROR: No valid kernel/initramfs pairs found"
  fi
else
  echo "ERROR: No kernels found in /boot/"
fi

if [[ -n $EFI ]] && efibootmgr &>/dev/null; then
    # Remove the archinstall-created Limine entry
  while IFS= read -r bootnum; do
    sudo efibootmgr -b "$bootnum" -B >/dev/null 2>&1
  done < <(efibootmgr | grep -E "^Boot[0-9]{4}\*? Arch Linux Limine" | sed 's/^Boot\([0-9]\{4\}\).*/\1/')
fi

# Move this to a utility to allow manual activation
# if [[ -n $EFI ]] && efibootmgr &>/dev/null &&
#   ! cat /sys/class/dmi/id/bios_vendor 2>/dev/null | grep -qi "American Megatrends" &&
#   ! cat /sys/class/dmi/id/bios_vendor 2>/dev/null | grep -qi "Apple"; then
#
#   uki_file=$(find /boot/EFI/Linux/ -name "homerchy*.efi" -printf "%f\n" 2>/dev/null | head -1)
#
#   if [[ -n "$uki_file" ]]; then
#     sudo efibootmgr --create \
#       --disk "$(findmnt -n -o SOURCE /boot | sed 's/p\?[0-9]*$//')" \
#       --part "$(findmnt -n -o SOURCE /boot | grep -o 'p\?[0-9]*$' | sed 's/^p//')" \
#       --label "Homerchy" \
#       --loader "\\EFI\\Linux\\$uki_file"
#   fi
# fi
