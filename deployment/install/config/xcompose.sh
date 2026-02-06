# Set onmachine/default XCompose that is triggered with CapsLock
tee ~/.XCompose >/dev/null <<EOF
include %H/.local/share/homerchy/onmachine/onmachine/onmachine/default/xcompose"

# Identification
<Multi_key> <space> <n> : "$HOMERCHY_USER_NAME"
<Multi_key> <space> <e> : "$HOMERCHY_USER_EMAIL"
EOF