#!/bin/bash
set -e

cd "$(dirname "$0")"

cp update_and_run.sh "$HOME/update_and_run.sh"
chmod +x "$HOME/update_and_run.sh"

echo "Shortcut installed."
echo "You can now run the HMI updater from anywhere with:"
echo ""
echo "  ~/update_and_run.sh"
echo ""
