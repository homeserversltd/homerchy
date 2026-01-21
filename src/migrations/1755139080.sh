echo Ensure fcitx5 does not overwrite xkb layout

FCITX5_CONF_DIR=$HOME/.onmachine/onmachine/onmachine/src/config/fcitx5/conf
FCITX5_XCB_CONF="$FCITX5_CONF_DIR/xcb.conf"

if [[ ! -f $FCITX5_XCB_CONF ]]; then
  mkdir -p $FCITX5_CONF_DIR
  cp $OMARCHY_PATH/onmachine/onmachine/onmachine/src/config/fcitx5/conf/xcb.conf "$FCITX5_XCB_CONF"
fi