# Panel Saw Raspberry Pi HMI v2.2

Industrial dashboard style update based on the requested reference screen.

Target:
- Raspberry Pi 3B+
- 7 inch HDMI touchscreen, 1024x600
- Raspberry Pi OS with X11
- PySide6

New in v2.2:
- Professional industrial dashboard layout
- Left vertical navigation with icons
- Top status bar with AUTO/READY/date-time
- Three large axis readout cards
- Machine mimic area
- Machine status panel
- Quick jog panel
- Bottom status bar
- Manual, Auto, Diagnostics, Alarms, Programs, Settings pages
- Simulator mode retained for development

Run:

    cd ~/PanelSawHMI
    source venv/bin/activate
    python3 -m hmi.main --simulate
