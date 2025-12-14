# Homerchy Repository Purpose

## Overview

The **homerchy** repository is an experimental Omarchy-based Linux distribution that serves as a development and testing platform for homeserver configurations. It exists as a tangent project alongside HOMESERVER LLC, providing a playground for rapid iteration and community experimentation.

## The Relationship: Homerchy vs. HOMESERVER LLC

### HOMESERVER LLC (The Company)

HOMESERVER LLC builds **professional-grade, enterprise-level homeserver products** for customers who demand digital sovereignty:

- **Complete Infrastructure Solution**: A "datacenter-in-a-box" that replaces $3,000+/year in cloud subscriptions
- **Enterprise Service Integration**: 14+ integrated services including Jellyfin, Gogs, Vaultwarden, Navidrome, FileBrowser, and more
- **Commercial Product**: Hardware + software integration sold as a complete system
- **Professional Architecture**: React frontend, Flask backend, encrypted NAS, real-time monitoring
- **Target Market**: Privacy-conscious professionals, system administrators, small businesses
- **Value Proposition**: Pay once, own forever, control everything—no subscriptions, no surveillance

### Homerchy (This Repository)

Homerchy is the **experimental development platform** that exists alongside the commercial products:

- **NOT the Official Product**: This is not what HOMESERVER LLC sells to customers
- **Rapid Prototyping Platform**: Test homeserver configurations in a self-contained environment
- **Open-Source Reference**: Community can learn from and fork this implementation
- **Development Playground**: Fast iteration cycles for testing new ideas
- **Fork-Friendly**: Designed for others to create their own Omarchy-based distributions

## Core Objectives

### 1. Self-Contained ISO Builder
- Integrates `omarchy-iso` builder directly into the repository
- No external dependencies—everything needed lives in one repo
- Offline-first design with embedded package mirrors
- Rapid iteration for testing and development

### 2. Integrated VM Testing Machinery
- Built-in QEMU/KVM VM orchestration for rapid development
- Snapshot management for quick testing cycles
- Automated deployment and initialization scripts
- Fast feedback loop for configuration changes

### 3. Homeserver-Optimized Configuration
- Pre-configured for common homeserver use cases
- Hyprland-based UI for local system management
- Networking tools and server service foundations
- Modular service configuration system

### 4. Open-Source & Fork-Friendly
- Clear documentation for others to fork and rebrand
- Environment variables for customization
- Modular configuration structure
- Community can create their own Omarchy-based distros

## Use Cases

### For HOMESERVER LLC Development
- Testing new homeserver configurations before production
- Rapid prototyping of system features
- Development environment for new service integrations
- Quality assurance and validation platform

### For the Community
- Reference implementation for Omarchy-based distributions
- Starting point for custom branded homeserver solutions
- Educational resource for building custom Linux distributions
- Open-source foundation for privacy-focused alternatives

### For Experimentation
- Learning platform for system building
- Testing ground for new ideas and configurations
- Development environment for homeserver projects
- Rapid iteration without affecting production systems

## Key Features

### Unified Controller Script
Based on the serverGenesis pattern, Homerchy provides a single CLI for all operations:

```bash
# ISO Building
./controller.sh --build homeserver    # Build homeserver ISO
./controller.sh --build vm           # Build VM test ISO

# VM Management
./controller.sh --up                 # Launch VM
./controller.sh --save               # Save VM snapshot
./controller.sh --refresh            # Revert to clean snapshot
./controller.sh --rebuild            # Rebuild VM from latest ISO

# Full Workflow
./controller.sh --full vm            # Build + Rebuild + Launch + Deploy
```

### Rapid Iteration Cycle
1. Make configuration changes
2. Run `./controller.sh --full vm`
3. Test in VM within minutes
4. Save working state or refresh to try again

### Offline Package Repository
- All packages embedded in ISO
- No internet required for installation
- Predictable, fast deployments

### Branding System
- Environment variables for customization
- Custom Plymouth boot themes
- Branded ASCII art and logos
- Configurable color schemes

## The Bottom Line

**Homerchy** is where ideas are tested and refined. **HOMESERVER LLC products** are the polished, enterprise-grade solutions delivered to customers.

Think of it this way:
- **Homerchy** = The workshop and laboratory
- **HOMESERVER LLC** = The professional products and services

This separation allows for:
- **Rapid experimentation** without affecting commercial products
- **Community engagement** through open-source contributions
- **Transparent development** while maintaining product quality
- **Innovation** without compromising customer stability

## For More Information

- **Commercial Products**: See [`whatIsHomeServer.md`](../prebuild/whatIsHomeServer.md) for details on HOMESERVER LLC's enterprise offerings
- **Project Planning**: See [`homerchy-project-plan.md`](../prebuild/docs/homerchy-project-plan.md) for technical architecture and implementation details
- **Contributing**: Homerchy welcomes community contributions, bug reports, feature requests, and forks

---

**Remember**: If you're looking for a production-ready homeserver solution, check out HOMESERVER LLC's commercial products. If you want to experiment, learn, or build your own Omarchy-based distribution, Homerchy is your starting point.
