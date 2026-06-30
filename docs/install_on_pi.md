# Install Panel Saw HMI v2.2 on Raspberry Pi

If cloned from GitHub:

cd ~/PanelSawHMI
git pull
source venv/bin/activate
pip install -r requirements.txt
python3 -m hmi.main --simulate

If using the ZIP:

1. Extract panel_saw_rpi_hmi_v2_2.zip.
2. Open terminal in the extracted folder:

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 -m hmi.main --simulate
