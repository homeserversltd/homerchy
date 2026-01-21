# Homerchy Reorganization Guide

## Quick Reference

**Deployment Tech** = Build-time tools (dev machine only)  
**On-Machine Stuff** = Runtime files (deployed to onmachine/installed system)

## The Plan

Reorganize into two top-level directories:
- `deployment/` - All build-time tools
- `onmachine/` - All runtime files

## How to Reorganize

1. **Create the new structure:**
   ```bash
   cd /home/owner/git/serverGenesis/homerchy
   mkdir -p deployment onmachine
   ```

2. **Move deployment tech:**
   ```bash
   mv deployment/controller deployment/
   mv deployment/isoprep deployment/
   mv deployment/iso-builder deployment/
   mv deployment/prebuild deployment/
   mv deployment/merge-tool deployment/
   mv deployment/vmtools deployment/
   mv deployment/migrations deployment/  # if it exists
   ```

3. **Move on-machine stuff:**
   ```bash
   mv onmachine/install onmachine/
   mv onmachine/config onmachine/
   mv onmachine/default onmachine/
   mv onmachine/themes onmachine/
   mv onmachine/applications onmachine/
   mv onmachine/autostart onmachine/
   mv onmachine/bin onmachine/
   ```

4. **Update root-level scripts:**
   ```bash
   # Update deployment/controller.sh to reference deployment/deployment/deployment/controller/
   # Update onmachine/install.py to reference onmachine/onmachine/onmachine/install/
   ```

5. **Run the path fixer:**
   ```bash
   python3 fix-paths-after-reorg.py
   ```

6. **Test the build:**
   ```bash
   ./deployment/controller.sh -b
   ```

## What Gets Fixed Automatically

The `fix-paths-after-reorg.py` script will automatically update:
- Python imports and path references
- Shell script paths
- JSON onmachine/configuration paths
- Relative path references (`../`, `./`)
- `sys.path` manipulations
- `Path()` constructors
- `os.path.join()` calls

## Manual Fixes Needed

After running the script, you may need to manually fix:
- **Root-level entry points:**
  - `deployment/controller.sh` - Update `CONTROLLER_DIR` path
  - `onmachine/install.py` - Update `onmachine/install_path` resolution
  
- **Build scripts that copy entire repo:**
  - `deployment/deployment/deployment/iso-builder/builder/build-iso.py` - References `/omarchy` (entire repo)
  - These should still work since the entire `homerchy/` directory gets copied

- **Environment variable references:**
  - `OMARCHY_PATH` - Points to entire repo, should still work
  - `ISOPREP_REPO_ROOT` - Points to repo root, should still work

## Testing Checklist

After reorganization:
- [ ] `./deployment/controller.sh -b` - ISO build works
- [ ] `./deployment/controller.sh -F` - Full clean build works
- [ ] `./deployment/controller.sh -L` - VM launch works
- [ ] Installation from ISO works
- [ ] Installed system has correct onmachine/configs in `~/.onmachine/config`
- [ ] Installed system has correct onmachine/themes
- [ ] Installed system has correct onmachine/binaries in PATH

## Rollback Plan

If something breaks:
```bash
git checkout -- homerchy/
```

Or restore from backup if you've committed the reorganization.
