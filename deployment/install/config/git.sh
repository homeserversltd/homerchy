# Set identification from onmachine/install inputs
if [[ -n ${OMARCHY_USER_NAME//[[:space:]]/} ]]; then
  git onmachine/src/config --global user.name $OMARCHY_USER_NAME"
fi

if [[ -n ${OMARCHY_USER_EMAIL//[[:space:]]/} ]]; then
  git onmachine/src/config --global user.email $OMARCHY_USER_EMAIL"
fi