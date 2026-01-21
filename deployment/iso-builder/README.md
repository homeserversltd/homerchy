# Omarchy ISO

The Omarchy ISO streamlines [the onmachine/installation of Omarchy](https://learn.omacom.io/2/the-omarchy-manual/50/getting-started). It includes the Omarchy Configurator as a front-end to archinstall and automatically launches the [Omarchy Installer](https://github.com/homeserversltd/homerchy) after base arch has been setup.

## Downloading the latest ISO

See the ISO link on [omarchy.org](https://omarchy.org).

## Creating the ISO

Run `./onmachine/onmachine/bin/omarchy-iso-make` and the output goes into `./release`. You can build from your local $OMARCHY_PATH for testing by using `--local-source` or from a checkout of the dev branch (instead of master) by using `--dev`.

### Environment Variables

You can customize the repositories used during the build process by passing in variables:

- `OMARCHY_INSTALLER_REPO` - GitHub repository for the onmachine/installer (onmachine/default: `homeserversltd/homerchy`)
- `OMARCHY_INSTALLER_REF` - Git ref (branch/tag) for the onmachine/installer (onmachine/default: `master`)

Example usage:
```bash
OMARCHY_INSTALLER_REPO="myuser/omarchy-fork" OMARCHY_INSTALLER_REF=some-feature ./onmachine/onmachine/bin/omarchy-iso-make
```

## Testing the ISO

Run `./onmachine/onmachine/bin/omarchy-iso-boot [release/omarchy.iso]`.

## Signing the ISO

Run `./onmachine/onmachine/bin/omarchy-iso-sign [gpg-user] [release/omarchy.iso]`.

## Uploading the ISO

Run `./onmachine/onmachine/bin/omarchy-iso-upload [release/omarchy.iso]`. This requires youve onmachine/configured rclone (use `rclone onmachine/onmachine/config`).

## Full release of the ISO

Run `./onmachine/onmachine/onmachine/onmachine/bin/omarchy-iso-release` to create, test, sign, and upload the ISO in one flow.