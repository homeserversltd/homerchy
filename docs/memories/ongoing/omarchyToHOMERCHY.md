# Omarchy to Homerchy Branding Swaps
# Omarchy to Homerchy Branding Swaps

## Completed Updates
*   **Branding Assets**:
    *   `icon.png` (Fixed)
    *   `icon.txt` (Fixed - ASCII Art)
    *   `logo.svg` (Fixed)
    *   `logo.txt` (Fixed - ASCII Art)
    *   `default/plymouth/logo.png` (Fixed - User updated)
    *   **Visible Branding**:
        *   Window Titles: `bin/omarchy-launch-floating-terminal-with-presentation` (Fixed)
        *   ISO Configs: `iso-builder/configs/profiledef.sh`, `iso-builder/configs/efiboot/loader/entries/01-archiso-x86_64-linux.conf`, `iso-builder/configs/airootfs/root/configurator` (Fixed)
    *   **Pending**:
        *   `config/omarchy.ttf`: likely contains the old logo at `\ue900` used in Waybar. Needs regeneration or replacement.

Locations in the codebase identified for branding updates (replacing "Omarchy" or generic branding with "Homerchy").

## 1. Core Branding & Presentation
*   **`install/helpers/presentation.sh`**:
    *   Logic for calculating logo dimensions (`LOGO_WIDTH`, `LOGO_HEIGHT`) and displaying it (`clear_logo` function).
    *   References `$OMARCHY_PATH/logo.txt`.
*   **`install/first-run/welcome.sh`**:
    *   The welcome screen script seen by users on first boot.
*   **`config/fastfetch/config.jsonc`**:
    *   Fastfetch configuration file.
    *   Contains specific `logo` settings that need to be updated to the new ASCII art.
*   **`default/plymouth/omarchy.script`**:
    *   Plymouth boot splash screen script.
    *   References `logo.png` and handles sprite animation.
*   **`install/preflight/begin.sh`**:
    *   Calls `clear_logo`.
*   **`install/post-install/finished.sh`**:
    *   Uses `tte` (terminal text effects) to "laser etch" the logo at the end of installation.
    *   Explicitly references `~/.local/share/omarchy/logo.txt`.

## 2. Binaries & Scripts
*   **`bin/omarchy-show-logo`**:
    *   Simple script that `cat`s the logo file.
*   **`bin/omarchy-upload-log`**:
    *   Suppresses the logo (`fastfetch --logo none`) when gathering system info for logs.
*   **`bin/omarchy-launch-floating-terminal-with-presentation`**:
    *   Launches a terminal window with the branding presentation. title="Omarchy".

## 3. Configuration & UI
*   **`default/hypr/looknfeel.conf`**:
    *   Hyprland configuration.
    *   Contains `disable_hyprland_logo = true`.
*   **`install/packaging/fonts.sh`**:
    *   Comments mention "Omarchy logo in a font" for Waybar.
*   **`iso-builder/configs/airootfs/root/configurator`**:
    *   ISO configuration script that uses `clear_logo`.

## 4. Documentation
*   **`docs/homerchy-project-plan.md`**:
    *   "Branded ASCII art and logos".
    *   "Edit config/branding/logo.txt".
*   **`docs/repository-purpose.md`**:
    *   "Branded ASCII art and logos".

## 5. Migrations
*   **`migrations/*.sh`**:
    *   Numerous scripts reference `omarchy-` prefixed commands and paths to `~/.local/share/omarchy`.
    *   These are functional references but often include user-facing echoes like `echo "Copy Omarchy logo..."` (e.g., `1755867743.sh`).
