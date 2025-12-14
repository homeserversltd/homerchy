# VM Tooling Research & Ideas

This document tracks research, ideas, and implemented tools for virtual machine handling, specifically focusing on rapid deployment and testing of Homerchy builds.

## Current Progress (2025-12-14)

We have successfully established a rapid build-and-test cycle using `archiso` and `qemu` directly in the repository.

### Implemented Workflow
1.  **Orchestration (`controller.sh`)**: A centralized script to manage the lifecycle.
    -   `./controller.sh -f`: Builds the ISO and immediately launches it in QEMU.
    -   `./controller.sh -e`: "Eject Cartridge" - Cleans up build artifacts and unmounts stubborn directories.
2.  **ISO Preparation (`isoprep/`)**:
    -   `build.sh`: Generates a fully functional Arch Linux ISO (`omarchy`).
    -   **Injection**: The entire local repository is injected into `/root/homerchy` on the ISO during build, allowing rapid testing of the latest code.
    -   **Networking**: Configured to use online repositories (online `pacman.conf`) for reliable package retrieval during build.
3.  **Virtualization (`vmtools/`)**:
    -   `install.sh`: Installs QEMU, KVM, EDK2 (UEFI), and GUI backends (`qemu-ui-gtk`, `qemu-ui-sdl`).
    -   `launch-iso.sh`: Boots the latest ISO using QEMU with KVM acceleration (4 vCPU, 4GB RAM) and standard VGA graphics.

### Status & Findings
*   **Success**: The ISO builds successfully (~1.3GB) and boots into a graphical environment (via QEMU GTK).
*   **Success**: `controller.sh -f` now automatically cleans up stale mounts (`-e` logic) before building, ensuring reliability.
*   **Success**: **Environment Injection Working**: We implemented `vmtools/vm-env.sh` which is injected into the ISO. The `.automated_script.sh` detects this and successfully redirects `OMARCHY_PATH` to `/root/homerchy`, fixing the "file not found" errors for helper scripts.
*   **Success**: **Build Fixes**: Removed the `plymouth` hook from `mkinitcpio.conf` which was causing build failures (exit code 1) despite a successful-looking output. The ISO now generates cleanly.
*   **Success**: **Configurator UI**: The configurator launches, allows keyboard/user/disk selection, and successfully hands off to the next step.
*   **Issue**: **Post-Submission Crash**: After filling out the configuration forms and hitting "Submit" (or confirming the disk format), the installation process encountered a crash. This suggests the error is now in the *application* of the configuration (e.g., `archinstall` execution or partition preparation) rather than the setup/bootstrapping phase.
*   **Action Item**: Investigate `run_configurator` handoff to `install_arch` and the generated `user_configuration.json` to pinpoint why the actual installation step is failing immediately after confirmation.

---

## Research: Direct Kernel Boot via QEMU (Future Optimization)

**Source:** [Making a micro Linux distro](https://popovicu.com/posts/making-a-micro-linux-distro/)

To further accelerate the "instant bootstrap" cycle (skipping the minute-long ISO build and bootloader), we are researching Direct Kernel Boot.

### The Concept
Instead of booting a disk image (`-drive file=disk.img`), we provide the kernel and initial ramdisk directly to QEMU. This bypasses the emulated BIOS/UEFI post and bootloader selection, jumping straight into Linux.

### Key Advantages
1.  **Speed**: Boots in milliseconds/seconds.
2.  **Simplicity**: No networking setup required for the host-to-guest bridge if we just need console access (though we can add it).
3.  **Iteration**: We can rebuild just the `initramfs` (userspace) or just the kernel and test immediately without re-imaging a disk.

### Implementation Details

**Basic Command Pattern:**
```bash
qemu-system-x86_64 \
    -kernel /path/to/linux/arch/x86/boot/bzImage \
    -initrd /path/to/initramfs.cpio.gz \
    -append "console=ttyS0" \
    -nographic \
    -m 2G
```

**Workflow for Homerchy:**
1.  **Kernel**: We can use the standard Arch header/kernel or build a custom lightweight one.
2.  **Initramfs**: This is the critical part. We can pack our build artifacts (the homerchy system root) into a cpio archive.
    *   *Option A (u-root)*: Use [u-root](https://github.com/u-root/u-root) to generate a Go-based minimal userspace (as mentioned in the article).
    *   *Option B (Archiso style)*: Use `mkinitcpio` or similar to pack a minimal Arch environment that mounts the full system from a 9p virtio share.
    *   *Option C (9p Virtio)*: Don't use a massive initrd. Use a tiny initrd that just mounts the host filesystem (where we built the repo) via 9pfs.
        ```bash
        -virtfs local,path=./build-output,mount_tag=host0,security_model=mapped,id=host0
        ```
        Then in kernel cmdline: `root=host0 rootfstype=9p rw init=/bin/bash`

### Next Steps for `vmtools`
- [ ] Create a `boot-kernel.sh` script in `vmtools/`.
- [ ] Experiment with booting the existing `archiso` kernel + a minimal initrd.
- [ ] Investigate 9pfs to map the local build directory directly into the VM as root, allowing "live" testing of files on the disk without rebuilding an image.
