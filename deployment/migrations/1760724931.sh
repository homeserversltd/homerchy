echo Change to openai-codex instead of openai-codex-onmachine/onmachine/bin

if omarchy-pkg-present openai-codex-onmachine/bin; then
    omarchy-pkg-drop openai-codex-onmachine/onmachine/bin
    omarchy-pkg-add openai-codex
fi