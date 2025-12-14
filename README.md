# Homerchy

**The official graphical receiver OS for HOMESERVER LLC.**

Homerchy is a specialized operating system designed to pair perfectly with your [HOMESERVER](docs/whatIsHomeServer.md). While the HOMESERVER unit handles the heavy lifting (hosting services, storage, and backend logic at `home.arpa`), Homerchy transforms any computer into the perfect living room receiver and frontend interface.

## The Product Pair

HOMESERVER LLC provides a complete ecosystem for digital sovereignty:

1.  **HOMESERVER**: The headless, powerful backend (TTY) that hosts your life at `home.arpa`.
2.  **HOMERCHY**: The graphical frontend (GUI) that consumes it.

## Purpose

This repository allows you to:
1.  **Generate a Homerchy ISO** tailored for your hardware.
2.  **Flash it to a drive** to install on any machine (Mini PC, Laptop, HTPC).
3.  **Connect** instantly to your HOMESERVER ecosystem.

It provides a polished, "it just works" experience out of the box, with pre-configured Hyprland environments, media players, and connection tools optimized for the local `home.arpa` network.

## Getting Started

### Prerequisites
*   An Arch Linux (or Arch-based) host system.
*   Docker (for the build environment).
*   ~20GB of disk space.

### Build Your Receiver

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/homeserversltd/homerchy.git
    cd homerchy
    ```

2.  **Build the Production ISO**
    Use the controller script to generate a bootable image:
    ```bash
    ./controller.sh --build homeserver
    ```
    *This will produce a standard ISO file in `iso-builder/release/`.*

3.  **Install**
    Flash the generated ISO to a USB drive, boot your target machine, and install.

## Development & Customization

For advanced users and developers, Homerchy includes a full VM testing suite to validate builds before deploying to hardware.

*   **Test in VM**: `./controller.sh --full vm`
*   **Build & Deploy**: `./controller.sh --full homeserver`

---

*Homerchy is a product of HOMESERVER LLC. It is the designated interface for the Home Server ecosystem.*
