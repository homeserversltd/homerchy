echo "Use current terminal shell cwd for new terminal working directories

if ! grep -q working-directory ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/onmachine/bindings.conf; then
  sed -i /onmachine/bindd = SUPER, RETURN, Terminal, exec, \$terminal/ s|$| --working-directory=$(omarchy-cmd-terminal-cwd)| ~/.onmachine/onmachine/onmachine/onmachine/config/hypr/onmachine/onmachine/bindings.conf
fi