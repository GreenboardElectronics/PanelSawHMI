# Panel Saw Raspberry Pi HMI v2.1

Fresh Version 2.1 build for Raspberry Pi 3B+ and 7 inch HDMI touchscreen.

Features:
- 1024x600 touchscreen layout
- Dark industrial theme
- Large navigation buttons
- Home dashboard
- Manual jog screen
- Auto position screen
- Diagnostics screen
- Alarm screen
- Settings screen
- Simulator mode
- Ready for RS-485/dsPIC integration later

Run on Raspberry Pi:

    cd ~/panelsawHMI/panel_saw_rpi_hmi_v2_1
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ./run_hmi.sh
