#!/bin/bash
set -e

echo "======================================"
echo " Greenboard Panel Saw HMI v3.1"
echo " Update + Run"
echo "======================================"

cd "$HOME/PanelSawHMI"

echo ""
echo "[1/4] Pulling latest code from GitHub..."
git pull

echo ""
echo "[2/4] Preparing Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

echo ""
echo "[3/4] Installing required Python packages..."
pip install -r requirements.txt

echo ""
echo "[4/4] Starting HMI..."
python3 -m hmi.main --simulate
