# Homerchy: Omarchy Fork for Homeserver Experimentation

## Project Vision

**Homerchy** is an Omarchy-based Linux distribution fork that exists as a **tangent project alongside HOMESERVER LLC**. While HOMESERVER LLC builds professional-grade digital sovereignty products (see `whatIsHomeServer.md`), Homerchy serves as an experimental and development platform for:

1. **Testing homeserver configurations** in a self-contained environment
2. **Rapid prototyping** of system configurations and services
3. **Open-source reference** for building Omarchy-based distributions
4. **Community experimentation** with the Omarchy ecosystem

## Relationship to HOMESERVER LLC

**HOMESERVER LLC** (the company) builds professional enterprise-grade infrastructure products that replace $3,000+/year in cloud subscriptions. See `whatIsHomeServer.md` for details on the commercial product.

**Homerchy** (this project) is a separate experimental fork that:
- Lives alongside the company as a development/testing platform
- Shares similar goals around digital sovereignty and self-hosting
- Is NOT the official HOMESERVER LLC product
- Serves as a playground for rapid iteration and community contributions

## Scope & Intent

### Core Objectives

1. **Self-Contained ISO Builder**
   - Integrate the `omarchy-iso` builder directly into the homerchy repository
   - No external dependencies - everything needed to build bootable ISOs lives in one repo
   - Offline-first design with embedded package mirrors
   - Rapid iteration for testing and development

2. **Integrated VM Testing Machinery**
   - Built-in QEMU/KVM VM orchestration for rapid development iteration
   - Snapshot management for quick testing cycles
   - Automated deployment and initialization scripts
   - Network-ready VMs with predictable IPs for SSH access
   - Fast feedback loop for configuration changes

3. **Homeserver-Optimized Configuration**
   - Pre-configured for common homeserver use cases
   - Hyprland-based UI for local system management
   - Networking tools and server service foundations
   - Modular service configuration system
   - Custom branding and theming capabilities

4. **Open-Source & Fork-Friendly**
   - Clear documentation for others to fork and rebrand
   - Environment variables for customization
   - Modular configuration structure
   - Rapid testing workflow via VM machinery
   - Community can create their own Omarchy-based distros

### Architecture Components

```
homerchy/
├── iso-builder/           # Integrated omarchy-iso builder
│   ├── bin/              # Build scripts (omarchy-iso-make, etc.)
│   ├── builder/          # Docker-based build system
│   ├── configs/          # archiso configurations
│   └── archiso/          # archiso submodule
│
├── vmtools/              # VM orchestration (from serverGenesis pattern)
│   ├── controller.sh     # Main orchestration script
│   ├── launch.sh         # VM launcher
│   ├── rebuild.sh        # Rebuild VM from ISO
│   ├── savestate.sh      # Snapshot management
│   ├── refresh.sh        # Revert to clean state
│   └── deploy.sh         # Post-install deployment
│
├── config/               # Homeserver configurations
│   ├── hyprland/         # Window manager config
│   ├── services/         # Systemd services
│   ├── networking/       # Network setup
│   └── branding/         # Theming and branding
│
├── install/              # Installation scripts
│   ├── preflight/        # Pre-install checks
│   ├── packaging/        # Package installation
│   ├── config/           # Config deployment
│   └── post-install/     # Finalization
│
├── boot.sh               # ISO boot entry point
├── install.sh            # Main installer orchestrator
├── controller.sh         # Master orchestration script
└── README.md             # Comprehensive usage guide
```

### Controller Script Pattern

Based on the serverGenesis controller.sh, homerchy will have a unified CLI for:

**ISO Building:**
```bash
./controller.sh --build homeserver    # Build homeserver ISO
./controller.sh --build vm           # Build VM test ISO
```

**VM Management:**
```bash
./controller.sh --up                 # Launch VM
./controller.sh --save               # Save VM snapshot
./controller.sh --refresh            # Revert to clean snapshot
./controller.sh --rebuild            # Rebuild VM from latest ISO
```

**Deployment:**
```bash
./controller.sh --deploy --ip=192.168.1.100 --user=root --pass=secret
```

**Full Workflow:**
```bash
./controller.sh --full vm            # Build ISO + Rebuild VM + Launch + Deploy
./controller.sh --full homeserver    # Build ISO + Show USB write instructions
```

### Key Features

1. **Rapid Iteration Cycle**
   - Make config changes
   - `./controller.sh --full vm` 
   - Test in VM within minutes
   - Save working state or refresh to try again

2. **Offline Package Repository**
   - All packages embedded in ISO
   - No internet required for installation
   - Predictable, fast deployments

3. **Automated Post-Install**
   - SSH-based deployment scripts
   - Idempotent configuration management
   - Service initialization and validation

4. **Branding System**
   - Environment variables for customization
   - Custom Plymouth boot themes
   - Branded ASCII art and logos
   - Configurable color schemes

### Fork & Customize Workflow (For Community Derivatives)

HOMESERVER LLC maintains Homerchy as the official HOMESERVER OS. Others can fork it to create their own Omarchy-based distributions:

1. **Fork the repo:**
   ```bash
   # Fork homeserversltd/homerchy on GitHub to yourcompany/yourdistro
   git clone https://github.com/yourcompany/yourdistro.git
   cd yourdistro
   ```

2. **Customize branding:**
   ```bash
   # Replace HOMESERVER branding with your own
   # Edit config/branding/logo.txt (ASCII art)
   # Edit config/branding/theme.conf (colors)
   # Edit config/branding/info.json (distro name, version)
   ```

3. **Test rapidly:**
   ```bash
   ./controller.sh --full vm
   # VM boots with your branding
   # Test, iterate, repeat
   ```

4. **Build production ISO:**
   ```bash
   ./controller.sh --build homeserver
   # Write to USB and deploy to your hardware
   ```

### Target Use Cases

**Experimentation & Development:**
- Testing homeserver configurations and services
- Rapid prototyping of Omarchy-based systems
- Learning platform for building custom Linux distributions
- Development environment for homeserver projects

**Community & Forks:**
- Reference implementation for Omarchy-based distributions
- Starting point for custom branded homeserver solutions
- Educational resource for system building
- Open-source foundation for privacy-focused alternatives

**Note:** For production enterprise-grade homeserver infrastructure, see HOMESERVER LLC's commercial products in `whatIsHomeServer.md`.

---

## Setup Instructions

### Prerequisites

- Arch Linux host (or Arch-based distro)
- Docker installed and running
- Git with submodule support
- QEMU/KVM for VM testing (optional but recommended)
- Sufficient disk space (~20GB for builds and VMs)

### Initial Setup Commands

```bash
# 1. Create workspace directory
mkdir -p /home/owner/git
cd /home/owner/git

# 2. Clone your fork of homerchy
git clone https://github.com/homeserversltd/homerchy.git
cd homerchy

# 3. Initialize as a new git repository (if starting fresh)
# Skip this if you cloned an existing repo
git init
git add .
git commit -m "Initial homerchy setup"

# 4. Add the omarchy-iso builder as a subdirectory
# We'll integrate it directly rather than as a submodule for easier customization
git clone https://github.com/omacom-io/omarchy-iso.git iso-builder
cd iso-builder

# 5. Initialize the archiso submodule within iso-builder
git submodule update --init --recursive

# 6. Return to homerchy root
cd ..

# 7. Copy the base omarchy installer as our starting point
git clone https://github.com/basecamp/omarchy.git temp-omarchy
cp -r temp-omarchy/install ./
cp -r temp-omarchy/config ./
cp -r temp-omarchy/boot.sh ./
cp -r temp-omarchy/install.sh ./
rm -rf temp-omarchy

# 8. Create vmtools directory structure
mkdir -p vmtools
mkdir -p isoprep/isoout

# 9. Create initial controller.sh
cat > controller.sh << 'EOF'
#!/bin/bash
# Homerchy Master Controller
# Based on serverGenesis orchestration pattern

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
CONFIG_FILE="$SCRIPT_DIR/config.json"
VMTOOLS_DIR="$SCRIPT_DIR/vmtools"
ISO_BUILDER="$SCRIPT_DIR/iso-builder"

# TODO: Implement full controller logic
echo "Homerchy controller - coming soon!"
EOF

chmod +x controller.sh

# 10. Create initial config.json
cat > config.json << 'EOF'
{
  "distro": {
    "name": "Homerchy",
    "version": "0.1.0",
    "repo": "homeserversltd/homerchy"
  },
  "vm": {
    "default_ip": "192.168.122.122",
    "memory": "4096",
    "cpus": "4",
    "disk_size": "20G"
  },
  "credentials": {
    "root_password": "homerchy"
  }
}
EOF

# 11. Create initial README
cat > README.md << 'EOF'
# Homerchy - Homeserver Linux Distribution

A self-contained, brandable homeserver operating system based on Arch Linux.

## Quick Start

```bash
# Build and test in VM
./controller.sh --full vm

# Build production ISO
./controller.sh --build homeserver
```

See docs/ for full documentation.
EOF

# 12. Set up git to track the integrated structure
git add iso-builder
git add vmtools
git add controller.sh
git add config.json
git add README.md
git add install/
git add config/
git add boot.sh
git add install.sh

# 13. Create initial commit
git commit -m "Integrate ISO builder and VM tools into homerchy

- Added omarchy-iso builder as iso-builder/
- Created vmtools/ for VM orchestration
- Added controller.sh master script
- Integrated base Omarchy installer scripts
- Created config.json for distro settings"

# 14. Set up remote (if not already done)
git remote add origin https://github.com/homeserversltd/homerchy.git

# 15. Push to GitHub
git push -u origin main
# Or if using master branch:
# git push -u origin master
```

### Verify Setup

```bash
# Check directory structure
tree -L 2 -d

# Should show:
# .
# ├── config/
# ├── install/
# ├── iso-builder/
# │   ├── archiso/
# │   ├── bin/
# │   ├── builder/
# │   └── configs/
# └── vmtools/

# Verify archiso submodule
cd iso-builder
git submodule status
# Should show archiso commit hash

# Test initial controller
cd ..
./controller.sh
# Should print "Homerchy controller - coming soon!"
```

### Next Steps

1. **Implement controller.sh** - Port the serverGenesis controller logic
2. **Create vmtools scripts** - Implement VM management scripts
3. **Customize branding** - Add Homerchy theming and branding
4. **Test ISO build** - Run first ISO build test
5. **Document workflow** - Expand README with full usage guide

---

## Development Workflow

### Making Changes

```bash
# 1. Make your config changes
vim config/hyprland/hyprland.conf

# 2. Test in VM
./controller.sh --full vm

# 3. If good, save the VM state
./controller.sh --save

# 4. If bad, revert and try again
./controller.sh --refresh

# 5. Commit when satisfied
git add config/
git commit -m "Update Hyprland configuration"
git push
```

### Building for Production

```bash
# Build the homeserver ISO
./controller.sh --build homeserver

# ISO will be in iso-builder/release/
ls -lh iso-builder/release/

# Write to USB
sudo dd if=iso-builder/release/homerchy-*.iso of=/dev/sdX bs=4M status=progress
```

---

## Contributing

Homerchy is an experimental project that exists alongside HOMESERVER LLC. Community contributions are welcome:

- **Bug Reports**: Open issues for bugs or problems
- **Feature Requests**: Suggest improvements and new capabilities
- **Pull Requests**: Submit PRs for review
- **Forks**: Create your own derivative distributions freely
- **Experimentation**: Try new ideas and share results

This is a playground for rapid iteration and community experimentation with Omarchy-based homeserver systems.

## License

MIT License - Fully open source and fork-friendly.

**Note:** This is a separate experimental project from HOMESERVER LLC's commercial products. For enterprise-grade homeserver solutions, see `whatIsHomeServer.md`.
