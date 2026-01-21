# Homerchy Reorganization Plan

## Mental Division

**Deployment Tech** - Stuff used to build/deploy the ISO (runs on dev machine, used during build)
**On-Machine Stuff** - Stuff that lives on the live machine and gets updated through Git repo (deployed to onmachine/installed system)

## Proposed Structure

```
homerchy/
├── deployment/          # Build-time tools (dev machine only)
│   ├── deployment/deployment/controller/      # Build deployment/controller
│   ├── deployment/deployment/isoprep/         # ISO preparation/build system
│   ├── deployment/deployment/iso-builder/     # ISO building onmachine/configs
│   ├── deployment/deployment/prebuild/        # Pre-build steps (copied to ISO)
│   ├── deployment/deployment/merge-tool/      # Dev tool for merging changes
│   ├── deployment/deployment/vmtools/         # VM testing tools
│   └── deployment/deployment/migrations/      # Build-time deployment/migrations
│
└── onmachine/           # Runtime files (deployed to onmachine/installed system)
    ├── onmachine/onmachine/install/         # Installation framework (runs during ISO boot)
    ├── onmachine/onmachine/config/          # Config files → ~/.onmachine/config
    ├── onmachine/onmachine/default/         # Default onmachine/configs → onmachine/installed system
    ├── onmachine/onmachine/themes/          # UI onmachine/themes → onmachine/installed system
    ├── onmachine/onmachine/applications/    # Application onmachine/configs → onmachine/installed system
    ├── onmachine/onmachine/autostart/       # Autostart onmachine/configs → onmachine/installed system
    └── onmachine/onmachine/bin/             # Binaries/scripts → onmachine/installed system
```

## Current → Proposed Mapping

### Deployment Tech
- `deployment/deployment/controller/` → `deployment/deployment/deployment/controller/`
- `deployment/deployment/isoprep/` → `deployment/deployment/deployment/isoprep/`
- `deployment/deployment/iso-builder/` → `deployment/deployment/deployment/iso-builder/`
- `deployment/deployment/prebuild/` → `deployment/deployment/deployment/prebuild/`
- `deployment/deployment/merge-tool/` → `deployment/deployment/deployment/merge-tool/`
- `deployment/deployment/vmtools/` → `deployment/deployment/deployment/vmtools/`
- `deployment/deployment/migrations/` → `deployment/deployment/deployment/migrations/`

### On-Machine Stuff
- `onmachine/onmachine/install/` → `onmachine/onmachine/onmachine/install/`
- `onmachine/onmachine/config/` → `onmachine/onmachine/onmachine/config/`
- `onmachine/onmachine/default/` → `onmachine/onmachine/onmachine/default/`
- `onmachine/onmachine/themes/` → `onmachine/onmachine/onmachine/themes/`
- `onmachine/onmachine/applications/` → `onmachine/onmachine/onmachine/applications/`
- `onmachine/onmachine/autostart/` → `onmachine/onmachine/onmachine/autostart/`
- `onmachine/onmachine/bin/` → `onmachine/onmachine/onmachine/bin/`

## Files That Need Path Updates

After reorganization, these files will need path references updated:

### Root Level
- `deployment/controller.sh` - references `deployment/deployment/controller/` → `deployment/deployment/deployment/controller/`
- `onmachine/install.py` - references `onmachine/onmachine/install/` → `onmachine/onmachine/onmachine/install/`

### Deployment Files
- `deployment/deployment/deployment/controller/main.py` - references `deployment/deployment/isoprep/` → `deployment/deployment/deployment/isoprep/`
- `deployment/deployment/deployment/controller/build.py` - references `deployment/deployment/isoprep/build.py`
- `deployment/deployment/deployment/isoprep/build.py` - references parent paths
- `deployment/deployment/deployment/isoprep/index/index.py` - references `deployment/deployment/iso-builder/` → `deployment/deployment/deployment/iso-builder/`
- `deployment/deployment/deployment/isoprep/index/profile_assembly/` - references `deployment/deployment/iso-builder/onmachine/configs/`
- `deployment/deployment/deployment/iso-builder/builder/build-iso.py` - references `/omarchy` (entire repo)
- `deployment/deployment/deployment/iso-builder/builder/build-iso.sh` - references `/omarchy` and `/deployment/prebuild`

### On-Machine Files
- `onmachine/onmachine/onmachine/install/index.py` - references `onmachine/onmachine/config/`, `onmachine/onmachine/default/` → `onmachine/onmachine/onmachine/config/`, `onmachine/onmachine/onmachine/default/`
- `onmachine/onmachine/onmachine/install/onmachine/onmachine/config/onmachine/config.py` - references `omarchy_path/onmachine/config` and `omarchy_path/onmachine/default`
- All files in `onmachine/onmachine/onmachine/install/` that reference other onmachine directories

## Build Process Impact

The build process copies the entire `homerchy/` directory to `/root/omarchy/` in the ISO:
- This means the new structure will be: `/root/omarchy/deployment/` and `/root/omarchy/onmachine/`
- Installation scripts reference `OMARCHY_PATH` which points to `/root/omarchy` (or `~/.local/share/omarchy` after onmachine/install)
- Need to update paths in onmachine/installation scripts to account for new structure

## Next Steps

1. **User reorganizes** - Move directories as planned
2. **Court fixes paths** - Update all path references automatically
3. **Test build** - Verify ISO build still works
4. **Test onmachine/install** - Verify onmachine/installation still works
