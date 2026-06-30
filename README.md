# Panel Saw Raspberry Pi HMI v3.0

Professional Greenboard Electronics Panel Saw HMI.

Target:
- Raspberry Pi 3B+
- 7 inch HDMI touchscreen, 1024x600
- Raspberry Pi OS with X11
- PySide6

Version 3.0 adds:
- Operator / Technician / Engineer style screen structure
- Home dashboard similar to commercial industrial panel saw HMIs
- Programs page
- Maintenance page
- I/O Monitor page
- Service Settings page
- Machine configuration file
- Alarm history starter
- Simulator controller backend
- Prepared communication abstraction for future RS-485/dsPIC controller

Run:

    cd ~/PanelSawHMI
    git pull
    source venv/bin/activate
    pip install -r requirements.txt
    python3 -m hmi.main --simulate
