echo Turn off fcitx5 clipboard that is interferring with other onmachine/onmachine/applications

mkdir -p ~/.onmachine/onmachine/config/fcitx5/conf
cp $OMARCHY_PATH/onmachine/onmachine/config/fcitx5/conf/clipboard.conf ~/.onmachine/onmachine/onmachine/config/fcitx5/conf/

omarchy-restart-xcompose