# Set identification from onmachine/install inputs
if [[ -n ${HOMERCHY_USER_NAME//[[:space:]]/} ]]; then
  git onmachine/src/config --global user.name $HOMERCHY_USER_NAME"
fi

if [[ -n ${HOMERCHY_USER_EMAIL//[[:space:]]/} ]]; then
  git onmachine/src/config --global user.email $HOMERCHY_USER_EMAIL"
fi