# Homerchy Repository Purpose

## Overview

The **homerchy** repository is the **production build system** for the Homerchy Operating System. 

**Homerchy** is the official **client/receiver OS** for HOMESERVER LLC. It is designed to be installed on end-user hardware (Mini PCs, Media Centers) to act as the graphical frontend for the HOMESERVER ecosystem.

## The Relationship: The Product Pair

HOMESERVER LLC delivers a complete digital sovereignty solution composed of two parts:

### 1. HOMESERVER (The Backend)
*   **What it is:** A "datacenter-in-a-box" server unit.
*   **Role:** Storage, compute, service hosting, network management, security.
*   **Interface:** Headless / Web UI.
*   **Location:** Tucked away in a shelf or closet.

### 2. HOMERCHY (The Frontend)
*   **What it is:** A polished, graphical Linux distribution.
*   **Role:** Media consumption, desktop computing, system management interface.
*   **Interface:** Hyprland-based GUI on a 4K TV or Monitor.
*   **Location:** In the living room or on a desk.
*   **This Repository:** Contains the source code and build tools to generate this OS.

## Core Objectives of This Repository

### 1. Reproducible OS Generation
*   Provide a push-button solution (`./controller.sh --build homeserver`) to generate the official install media (ISO).
*   Ensure every build is bit-perfect and production-ready.

### 2. Hardware Adaptation
*   Create a "broad-support" image that works on common consumer hardware (Intel NUCs, AMD Mini PCs).
*   Include necessary drivers and firmware OOTB.

### 3. Experience Curation
*   Define the default software suite (Jellyfin, Navidrome, Browsers).
*   Apply the HOMESERVER visual identity (themes, plymouth, wallpapers).
*   Configure network auto-discovery to find the `home.arpa` domain instantly.

## Use Cases

### For HOMESERVER LLC
*   **Release Management**: This repo drives the official software releases flashed onto units or provided to customers.
*   **Quality Assurance**: The integrated VM tools allow testing every commit before it hits real hardware.

### For Customers & Community
*   **Transparency**: Customers can see exactly what code runs on their receiver.
*   **DIY Builds**: Technical users can build the OS themselves to repurpose their own hardware as a Homerchy receiver.
*   **Customization**: Advanced users can fork and modify the receiver OS to suit unique needs.

## The Bottom Line

**Homerchy** is the face of the system. **HOMESERVER** is the brain.
This repository is the factory that builds the face.

---

## For More Information

-   **The Server**: See [`whatIsHomeServer.md`](whatIsHomeServer.md) for details on the backend unit.
-   **Technical Plan**: See [`homerchy-project-plan.md`](homerchy-project-plan.md) for architectural details.

