#!/bin/bash

PROJECT_NAME=$(basename "$PWD")
DEST_DIR="$HOME/like-sphinx"

mkdir -p "$DEST_DIR"

shopt -s extglob
cp -r !("installation.sh") "$DEST_DIR/"
chmod +x "$DEST_DIR/linker.py"

SYMLINK_PATH="/usr/local/bin/linker"
if [ -L "$SYMLINK_PATH" ] || [ -e "$SYMLINK_PATH" ]; then
    sudo rm -f "$SYMLINK_PATH"
fi
sudo ln -s "$DEST_DIR/linker.py" "$SYMLINK_PATH"
echo "You can now run 'linker' from anywhere."
