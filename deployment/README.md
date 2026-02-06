# Homerchy Deployment

**Deployment root** = this directory. It contains `install/`, `iso-builder/`, `isoprep/`, and `controller/`.

## Package lists

All paths are relative to the deployment root:

- `install/homerchy-base.packages` — base packages
- `install/homerchy-other.packages` — other packages
- `iso-builder/builder/archinstall.packages` — single source for packages installed into the base system and for the offline mirror; used by isoprep and by the on-ISO configurator.

## On-ISO layout

When the deployment tree is injected onto the ISO, it is placed at `/root/homerchy/`. The archinstall package list is at:

**`/root/homerchy/iso-builder/builder/archinstall.packages`**

## Who runs the build

The **controller** runs isoprep with `repo_root` set to the deployment directory. This is set in `isoprep/build.py` (parent of isoprep = deployment). Do not run the legacy `build-iso.sh` or `build-iso.py`; use the controller or isoprep directly.
