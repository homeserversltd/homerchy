# Homerchy: The HOMESERVER Receiver OS

## Project Vision

**Homerchy** is the official graphical operating system designed to serve as the **frontend receiver** for the HOMESERVER ecosystem. While the **HOMESERVER** unit acts as the "datacenter-in-a-box" backend (hosting services, storage, and logic), **Homerchy** runs on client devices (Mini PCs, HTPCs, Laptops) to provide a seamless, rich interface for consuming those services.

It is **not** an experimental playground or a separate fork; it is a core product component of HOMESERVER LLC.

## The Product Ecosystem

1.  **HOMESERVER (Backend)**: The powerful, headless server running at `home.arpa`. It manages data, security, and services.
2.  **HOMERCHY (Frontend)**: The client OS. It boots directly into a polished interface (Hyprland) pre-configured to discover and interact with the HOMESERVER.

## Scope & Intent

### Core Objectives

1.  **Production-Grade ISO Builder**
    -   Integrate `omarchy-iso` to generate stable, deployable system images.
    -   Produce a "flash-and-forget" OS that turns generic hardware into a dedicated receiver.
    -   Ensure consistent boot behavior and hardware support.

2.  **Seamless Integration**
    -   **Zero-Config Discovery**: Automatically detect the `home.arpa` network.
    -   **Pre-installed Client Suite**: Jellyfin Media Player, Navidrome clients, file managers, and browsers pre-tuned for the local mesh.
    -   **Unified Branding**: Professional visual identity matching the HOMESERVER aesthetic.

3.  **Development & QA Machinery**
    -   **VM Orchestration**: Built-in tools (`vmtools`) to test the OS in QEMU/KVM before deploying to physical hardware.
    -   **Snapshot & Rollback**: Rapid iteration cycles for UI/UX polishing.

### Architecture Components

```
homerchy/
├── iso-builder/           # The core build engine (omarchy-iso integration)
│   ├── configs/          # OS Composition (packages, services)
│   └── release/          # Output directory for generated ISOs
│
├── vmtools/              # Quality Assurance Suite
│   ├── controller.sh     # Orchestrator
│   └── ...               # VM management scripts
│
├── config/               # The "Personality" of the OS
│   ├── hyprland/         # UI Configuration (Window Manager)
│   ├── apps/             # Client application settings
│   ├── networking/       # Auto-discovery and connection logic
│   └── branding/         # Themes, wallpapers, assets
│
└── controller.sh         # Master CLI for building and testing
```

## Controller Script Pattern

The repository uses a unified `controller.sh` to manage the lifecycle of the OS product:

**Development Cycle:**
```bash
./controller.sh --full vm            # 1. Build ISO -> 2. Launch VM -> 3. Test UX
./controller.sh --save               # Save progress (snapshot)
./controller.sh --refresh            # Reset to clean state
```

**Production Build:**
```bash
./controller.sh --build homeserver    # Generate the official release ISO
```

## Setup Instructions

### Prerequisites
-   Arch Linux (or derivative) host
-   Docker (for the build container)
-   QEMU/KVM (for testing)

### Getting Started

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/homeserversltd/homerchy.git
    cd homerchy
    ```

2.  **Build and Test**
    ```bash
    ./controller.sh --full vm
    ```

## Contributing

While Homerchy is a commercial product of HOMESERVER LLC, we maintain this repository as open source to allow for:
-   **Security Auditing**: Users can verify exactly what runs on their client machines.
-   **Community Improvements**: Fixes and enhancements to the receiver experience are welcome.
-   **Customization**: Advanced users can tweak the receiver image for specific hardware needs.

---
**Homerchy** transforms your screen into a window to your digital home.

