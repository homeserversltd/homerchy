#!/bin/bash

    # Get the MIME type of the file
    FPATH="$1"
    MIMETYPE="$(file -bL --mime-type -- "${FPATH}")"

    case "${MIMETYPE}" in
        # Text files and similar
        text/*|application/json|application/xml|application/x-shellscript|inode/x-empty|\
        application/x-yaml|application/javascript)
            if [ -w "$1" ]; then
                tmux new-window -n "edit" "$EDITOR \"$1\""
            else
                tmux new-window -n "edit" "sudo $EDITOR \"$1\""
            fi
        ;;

        # Images
        image/*)
            if type chafa >/dev/null 2>&1; then
                tmux new-window -n "image" "chafa \"$1\"; read -n 1"
            elif type timg >/dev/null 2>&1; then
                tmux new-window -n "image" "timg \"$1\"; read -n 1"
            elif type viu >/dev/null 2>&1; then
                tmux new-window -n "image" "viu \"$1\"; read -n 1"
            else
                echo "No terminal image viewer found. Install chafa, timg, or viu"
                exit 1
            fi
        ;;

        # PDFs
        application/pdf)
            if type pdftotext >/dev/null 2>&1; then
                tmux new-window -n "pdf" "pdftotext \"$1\" - | less"
            elif type mutool >/dev/null 2>&1; then
                tmux new-window -n "pdf" "mutool draw -F txt \"$1\" | less"
            else
                echo "No PDF viewer found. Install poppler-utils or mupdf-tools"
                exit 1
            fi
        ;;

        # Everything else
        *)
            echo "Cannot open file type: ${MIMETYPE}"
            exit 1
        ;;
    esac
