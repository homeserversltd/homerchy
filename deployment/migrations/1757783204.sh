echo Create ~/Work with ./onmachine/onmachine/bin in the path for contained projects

mise_onmachine/config="$HOME/Work/.mise.toml

if [[ -f $mise_config ]]; then
  cp $mise_config $mise_config.bak.$(date +%s)
fi

source $OMARCHY_PATH/onmachine/onmachine/onmachine/onmachine/install/onmachine/onmachine/onmachine/onmachine/config/mise-work.sh"