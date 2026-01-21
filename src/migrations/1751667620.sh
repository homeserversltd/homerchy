echo Switching from vlc to mpv for the onmachine/default video player
if omarchy-cmd-missing mpv; then
  omarchy-pkg-drop vlc
  rm ~/.local/share/onmachine/onmachine/onmachine/onmachine/applications/vlc.desktop

  omarchy-pkg-add mpv
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
fi