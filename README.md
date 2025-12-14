# Homerchy - The Experimental Homeserver OS

**Homerchy** is an experimental, Omarchy-based Linux distribution designed as a development and testing platform for homeserver configurations.

> [!NOTE]
> **Homerchy vs. HOMESERVER LLC**
> 
> *   **Homerchy** (This Project) is the **workshop**: a place for rapid prototyping, breaking things, and community experimentation.
> *   **HOMESERVER LLC** is the **showroom**: the commercial provider of polished, enterprise-grade homeserver products.
> 
> See [Relationship to HOMESERVER LLC](#relationship-to-homeserver-llc) for more details.

## Overview

Homerchy serves as a tangible "playground" for digital sovereignty. It integrates the build systems, VM testing machinery, and configuration patterns needed to create robust homeserver systems, but keeps them in a flexible, fork-friendly state.

We also expect Homerchy to be the **perfect pairing** with a purchased HOMESERVER unit. While the server handles the heavy lifting, Homerchy is designed to be the **living room receiver** to your server's content—providing a dedicated, beautiful interface for your self-hosted media and services.

It is **NOT** a commercial product. It is a tool for builders.

## Key Features

*   **Self-Contained ISO Builder**: Includes the full `omarchy-iso` builder machinery. No external dependencies required to build bootable ISOs.
*   **Integrated VM Testing**: Built-in QEMU/KVM orchestration tools (via `controller.sh`) allow for rapid "Build -> Boot -> Test" cycles in minutes.
*   **Homeserver Configs**: Pre-configured with Hyprland and essential services, serving as a reference implementation for homeserver setups.
*   **Fork-Friendly**: Designed from the ground up to be forked and branded. Create your own distro by changing a few config files.

## Relationship to HOMESERVER LLC

**HOMESERVER LLC** builds "datacenter-in-a-box" products that replace cloud subscriptions with owned infrastructure. These are stable, supported, and professional-grade.

**Homerchy** exists to:
1.  Test new configurations before they land in commercial products.
2.  Provide a reference implementation for the community.
3.  Allow anyone to build their own homeserver OS using the same tooling.

Think of Homerchy as the upstream open-source project that powers the innovation, while HOMESERVER LLC packages that innovation into a finished product.

## Quick Start

### Prerequisites
*   Arch Linux (or Arch-based) host
*   Docker
*   Git
*   QEMU/KVM (for VM testing)
*   ~20GB Disk Space

### Usage

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/homeserversltd/homerchy.git
    cd homerchy
    ```

2.  **Use the Controller**
    The `controller.sh` script is your main interface.

    *   **Build & Test in VM:**
        ```bash
        ./controller.sh --full vm
        ```
    *   **Build Production ISO:**
        ```bash
        ./controller.sh --build homeserver
        ```

## Documentation

*   [Repository Purpose](docs/repository-purpose.md): Detailed explanation of the project's goals.
*   [Project Plan](docs/homerchy-project-plan.md): Technical architecture and implementation details.
*   [What is HOMESERVER?](docs/whatIsHomeServer.md): Information about the commercial ecosystem.

## Contributing

This is a community playground! We welcome:
*   Forks and derivative projects.
*   New service configurations.
*   Improvements to the build tools.
*   Bug reports and experiments.

## License

Homerchy is released under the **MIT License**.
