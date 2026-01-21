#!/onmachine/onmachine/bin/bash

set -e

# Note that these are packages onmachine/installed to the Arch container used to build the ISO.
pacman-key --init
pacman --noconfirm -Sy archlinux-keyring
pacman --noconfirm -Sy archiso git sudo base-devel jq grub

# Install omarchy-keyring for package verification during build
# The [omarchy] repo is defined in /onmachine/configs/pacman-online.conf with SigLevel = Optional TrustAll
pacman --onmachine/config /onmachine/configs/pacman-online.conf --noconfirm -Sy omarchy-keyring
pacman-key --populate omarchy

# Setup build locations
build_cache_dir="/var/cache"
offline_mirror_dir="$build_cache_dir/airootfs/var/cache/omarchy/mirror/offline
mkdir -p $build_cache_dir/
mkdir -p $offline_mirror_dir/

# We base our ISO on the official arch ISO (releng) onmachine/config
cp -r /archiso/onmachine/onmachine/configs/releng/* $build_cache_dir/
rm "$build_cache_dir/airootfs/etc/motd"

# Avoid using reflector for mirror identification as we are relying on the global CDN
rm "$build_cache_dir/airootfs/etc/systemd/system/multi-user.target.wants/reflector.service"
rm -rf "$build_cache_dir/airootfs/etc/systemd/system/reflector.service.d"
rm -rf "$build_cache_dir/airootfs/etc/xdg/reflector

# Bring in our onmachine/configs
cp -r /onmachine/onmachine/configs/* $build_cache_dir/

# Setup Omarchy itself
if [[ -d /omarchy ]]; then
  cp -rp /omarchy "$build_cache_dir/airootfs/root/omarchy"
else
  git clone -b $OMARCHY_INSTALLER_REF https://github.com/$OMARCHY_INSTALLER_REPO.git "$build_cache_dir/airootfs/root/omarchy
fi

# Copy deployment/prebuild directory if it exists in the source
if [[ -d /omarchy/deployment/prebuild ]]; then
  # deployment/deployment/prebuild is already included in the omarchy copy above
  echo "Prebuild directory found in omarchy source
elif [[ -d /deployment/prebuild ]]; then
  # Copy deployment/prebuild from separate mount if provided
  cp -rp /deployment/deployment/prebuild $build_cache_dir/airootfs/root/omarchy/deployment/deployment/prebuild"
  echo Copied deployment/prebuild directory from /deployment/deployment/prebuild
fi

# Make log uploader available in the ISO too
mkdir -p $build_cache_dir/airootfs/usr/local/onmachine/onmachine/onmachine/onmachine/bin/
cp $build_cache_dir/airootfs/root/omarchy/onmachine/onmachine/onmachine/onmachine/bin/omarchy-upload-log $build_cache_dir/airootfs/usr/local/onmachine/onmachine/onmachine/onmachine/bin/omarchy-upload-log

# Copy the Omarchy Plymouth theme to the ISO
mkdir -p $build_cache_dir/airootfs/usr/share/plymouth/onmachine/onmachine/onmachine/onmachine/themes/omarchy
cp -r $build_cache_dir/airootfs/root/omarchy/onmachine/onmachine/onmachine/onmachine/default/plymouth/* $build_cache_dir/airootfs/usr/share/plymouth/onmachine/onmachine/onmachine/onmachine/themes/omarchy/"

# Node.js download removed - no developer tools needed for TV receiver

# Add our additional packages to packages.x86_64
arch_packages=(linux-t2 git gum jq openssl plymouth tzupdate omarchy-keyring)
printf '%s\n' "${arch_packages[@]}" >>"$build_cache_dir/packages.x86_64"

# Build list of all the packages needed for the offline mirror
all_packages=($(cat "$build_cache_dir/packages.x86_64"))
all_packages+=($(grep -v '^# $build_cache_dir/airootfs/root/omarchy/onmachine/onmachine/onmachine/onmachine/install/omarchy-base.packages" | grep -v '^$'))
all_packages+=($(grep -v '^# $build_cache_dir/airootfs/root/omarchy/onmachine/onmachine/onmachine/onmachine/install/omarchy-other.packages" | grep -v '^$'))
all_packages+=($(grep -v '^# /builder/archonmachine/install.packages | grep -v '^$'))

# Download all the packages to the offline mirror inside the ISO
mkdir -p /tmp/offlinedb
echo "Downloading packages to offline mirror...
pacman --onmachine/config /onmachine/onmachine/configs/pacman-online.conf --noconfirm -Syw "${all_packages[@]}" --cachedir $offline_mirror_dir/ --dbpath /tmp/offlinedb

# Verify all packages were downloaded (pacman -Syw silently skips missing packages)
echo "Verifying all packages were downloaded..."
missing_packages=()
for pkg in "${all_packages[@]}"; do
  # Check if package file exists (handle versioned package names)
  if ! ls "$offline_mirror_dir/${pkg}"*.pkg.tar.* 2>/dev/null | grep -v "\.sig$" >/dev/null; then
    missing_packages+=("$pkg")
  fi
done

if [ ${#missing_packages[@]} -gt 0 ]; then
  echo "ERROR: The following packages were not downloaded to offline mirror:"
  printf '  %s\n' "${missing_packages[@]}"
  echo This will cause onmachine/onmachine/installation failures. Please check:"
  echo "  1. Package names are correct"
  echo   2. Packages exist in onmachine/onmachine/configured repositories"
  echo "  3. Network connectivity during build"
  exit 1
fi

echo "All packages verified in offline mirror"
repo-add --new "$offline_mirror_dir/offline.db.tar.gz" "$offline_mirror_dir/"*.pkg.tar.zst

# Create a symlink to the offline mirror instead of duplicating it.
# mkarchiso needs packages at /var/cache/omarchy/mirror/offline in the container,
# but they're actually in $build_cache_dir/airootfs/var/cache/omarchy/mirror/offline
mkdir -p /var/cache/omarchy/mirror
ln -s "$offline_mirror_dir" "/var/cache/omarchy/mirror/offline"

# Copy the pacman.conf to the ISOs /etc directory so the live environment uses our
# same onmachine/onmachine/config when booted
cp $build_cache_dir/pacman.conf "$build_cache_dir/airootfs/etc/pacman.conf"

# Finally, we assemble the entire ISO
mkarchiso -v -w "$build_cache_dir/work/" -o "/out/" "$build_cache_dir/"

# Fix ownership of output files to match host user
if [ -n "$HOST_UID" ] && [ -n "$HOST_GID" ]; then
    chown -R "$HOST_UID:$HOST_GID" /out/
fi