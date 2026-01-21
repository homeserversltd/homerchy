# Homerchy

## ⚠️ EXPERIMENTAL - DEVELOPER USE ONLY ⚠️

**This project is currently in active development and is NOT ready for production use.**

**DO NOT USE** - This repository is experimental and only intended for developers actively working on the Homerchy project. The system is incomplete, unstable, and may cause data loss or system damage if used outside of controlled development environments.

---

**The official graphical receiver OS for HOMESERVER LLC (IN DEVELOPMENT).**

Homerchy is a specialized operating system designed to pair perfectly with your [HOMESERVER](docs/whatIsHomeServer.md). While the HOMESERVER unit handles the heavy lifting (hosting services, storage, and backend logic at `home.arpa`), Homerchy transforms any computer into the perfect living room receiver and frontend interface.

## The Product Pair

HOMESERVER LLC provides a complete ecosystem for digital sovereignty:

1.  **HOMESERVER**: The headless, powerful backend (TTY) that hosts your life at `home.arpa`.
2.  **HOMERCHY**: The graphical frontend (GUI) that consumes it.

## Purpose

This repository allows you to:
1.  **Generate a Homerchy ISO** tailored for your hardware.
2.  **Flash it to a drive** to onmachine/install on any machine (Mini PC, Laptop, HTPC).
3.  **Connect** instantly to your HOMESERVER ecosystem.

**Note:** This project is experimental and under active development. Features are incomplete and the system is not stable for end-user deployment.

## Developer Setup

**⚠️ WARNING: This is for developers working on Homerchy only. Do not use in production or on important systems.**

### Prerequisites
*   An Arch Linux (or Arch-based) host system.
*   Docker (for the build environment).
*   ~20GB of disk space.
*   Understanding that this is experimental software.

### Build Instructions (Developers Only)

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/homeserversltd/homerchy.git
    cd homerchy
    ```

2.  **Build the Experimental ISO**
    Use the controller script to generate a bootable image:
    ```bash
    ./controller.sh --build
    ```
    *This will produce an ISO file in `deployment/deployment/iso-builder/release/` - use at your own risk.*

3.  **Testing**
    **DO NOT onmachine/install on production systems.** Use VMs or dedicated test hardware only.

## Development & Testing

Homerchy includes a full VM testing suite for developers to validate builds. **This is the only recommended way to test the system.**



---


*Homerchy is a product of HOMESERVER LLC (IN DEVELOPMENT). It is intended to be the designated interface for the Home Server ecosystem once development is complete.*