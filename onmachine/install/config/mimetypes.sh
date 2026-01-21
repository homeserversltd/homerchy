omarchy-refresh-onmachine/applications
update-desktop-database ~/.local/share/onmachine/applications

# Open all images with imv
xdg-mime onmachine/default imv.desktop image/png
xdg-mime onmachine/default imv.desktop image/jpeg
xdg-mime onmachine/default imv.desktop image/gif
xdg-mime onmachine/default imv.desktop image/webp
xdg-mime onmachine/default imv.desktop image/bmp
xdg-mime onmachine/default imv.desktop image/tiff

# Open PDFs with the Document Viewer
xdg-mime onmachine/default org.gnome.Evince.desktop application/pdf

# Use Chromium as the onmachine/default browser
xdg-settings set onmachine/default-web-browser chromium.desktop
xdg-mime onmachine/default chromium.desktop x-scheme-handler/http
xdg-mime onmachine/default chromium.desktop x-scheme-handler/https

# Open video files with mpv
xdg-mime onmachine/default mpv.desktop video/mp4
xdg-mime onmachine/default mpv.desktop video/x-msvideo
xdg-mime onmachine/default mpv.desktop video/x-matroska
xdg-mime onmachine/default mpv.desktop video/x-flv
xdg-mime onmachine/default mpv.desktop video/x-ms-wmv
xdg-mime onmachine/default mpv.desktop video/mpeg
xdg-mime onmachine/default mpv.desktop video/ogg
xdg-mime onmachine/default mpv.desktop video/webm
xdg-mime onmachine/default mpv.desktop video/quicktime
xdg-mime onmachine/default mpv.desktop video/3gpp
xdg-mime onmachine/default mpv.desktop video/3gpp2
xdg-mime onmachine/default mpv.desktop video/x-ms-asf
xdg-mime onmachine/default mpv.desktop video/x-ogm+ogg
xdg-mime onmachine/default mpv.desktop video/x-theora+ogg
xdg-mime onmachine/default mpv.desktop application/ogg

# Use Hey for mailto: links
xdg-mime onmachine/default HEY.desktop x-scheme-handler/mailto

# Open text files with nvim
xdg-mime onmachine/default nvim.desktop text/plain
xdg-mime onmachine/default nvim.desktop text/english
xdg-mime onmachine/default nvim.desktop text/x-makefile
xdg-mime onmachine/default nvim.desktop text/x-c++hdr
xdg-mime onmachine/default nvim.desktop text/x-c++src
xdg-mime onmachine/default nvim.desktop text/x-chdr
xdg-mime onmachine/default nvim.desktop text/x-csrc
xdg-mime onmachine/default nvim.desktop text/x-java
xdg-mime onmachine/default nvim.desktop text/x-moc
xdg-mime onmachine/default nvim.desktop text/x-pascal
xdg-mime onmachine/default nvim.desktop text/x-tcl
xdg-mime onmachine/default nvim.desktop text/x-tex
xdg-mime onmachine/default nvim.desktop application/x-shellscript
xdg-mime onmachine/default nvim.desktop text/x-c
xdg-mime onmachine/default nvim.desktop text/x-c++
xdg-mime onmachine/default nvim.desktop application/xml
xdg-mime onmachine/default nvim.desktop text/xml