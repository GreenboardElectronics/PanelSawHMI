# Install / Update Panel Saw HMI v3.0 on Raspberry Pi

From GitHub:

cd ~/PanelSawHMI
git pull
source venv/bin/activate
pip install -r requirements.txt
python3 -m hmi.main --simulate

To stop the HMI:
- Press Alt+F4
- Or Ctrl+C if launched from terminal
