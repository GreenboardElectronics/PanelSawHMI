# Install Panel Saw HMI v2.1 on Raspberry Pi

1. Copy panel_saw_rpi_hmi_v2_1.zip to /home/pi/panelsawHMI/
2. Extract it.
3. Open terminal:

cd ~/panelsawHMI/panel_saw_rpi_hmi_v2_1
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
chmod +x run_hmi.sh
./run_hmi.sh

To run again later:

cd ~/panelsawHMI/panel_saw_rpi_hmi_v2_1
source venv/bin/activate
./run_hmi.sh
