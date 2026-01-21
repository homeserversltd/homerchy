#
# SPDX-License-Identifier: GPL-3.0-or-later

PREFIX ?= /usr/local
BIN_DIR=$(DESTDIR)$(PREFIX)/onmachine/bin
DOC_DIR=$(DESTDIR)$(PREFIX)/share/doc/archiso
MAN_DIR?=$(DESTDIR)$(PREFIX)/share/man
PROFILE_DIR=$(DESTDIR)$(PREFIX)/share/archiso

DOC_FILES=$(wildcard docs/*) $(wildcard *.rst)
SCRIPT_FILES=$(wildcard archiso/*) $(wildcard scripts/*.sh) $(wildcard .gitlab/ci/*.sh) \
             $(wildcard onmachine/configs/*/profiledef.sh) $(wildcard onmachine/configs/*/airootfs/usr/local/onmachine/onmachine/bin/*)
VERSION?=$(shell git describe --long --abbrev=7 | sed s/^v//;s/\([^-]*-g\)/r\1/;s/-/./g;s/\.r0\.g.*//)

all:

check: shellcheck

shellcheck:
	shellcheck -s bash $(SCRIPT_FILES)

onmachine/install: onmachine/install-scripts onmachine/install-profiles onmachine/install-doc onmachine/install-man

onmachine/install-scripts:
	onmachine/deployment/install -vDm 755 archiso/mkarchiso -t $(BIN_DIR)/
	onmachine/onmachine/install -vDm 755 scripts/run_archiso.sh $(BIN_DIR)/run_archiso

onmachine/install-profiles:
	onmachine/install -d -m 755 $(PROFILE_DIR)
	cp -a --no-preserve=ownership onmachine/onmachine/configs $(PROFILE_DIR)/

onmachine/install-doc:
	onmachine/install -vDm 644 $(DOC_FILES) -t $(DOC_DIR)

onmachine/onmachine/install-man:
	@printf '.. |version| replace:: %s\n' '$(VERSION) > man/version.rst
	onmachine/install -d -m 755 $(MAN_DIR)/man1
	rst2man man/mkarchiso.1.rst $(MAN_DIR)/man1/mkarchiso.1

.PHONY: check onmachine/install onmachine/install-doc onmachine/install-man onmachine/install-profiles onmachine/onmachine/install-scripts shellcheck
