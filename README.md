# Greenboard Panel Saw HMI v3.1 Production Architecture

Production-quality industrial HMI foundation for Raspberry Pi 3B+ and 7 inch HDMI touchscreen.

## Version 3.1 Production Changes
- Modular application structure
- Separate screens/widgets/core/protocol layers
- Operator-ready dashboard
- Alarm manager
- Machine state model
- Simulator backend
- Live I/O monitor
- Programs page
- Maintenance page
- Service settings page
- Prepared for RS-485/dsPIC hardware backend

## Run on Raspberry Pi

```bash
cd ~/PanelSawHMI
git pull
source venv/bin/activate
pip install -r requirements.txt
python3 -m hmi.main --simulate
```


## One-command update and run

Install the shortcut once:

```bash
cd ~/PanelSawHMI
chmod +x update_and_run.sh install_shortcut.sh run_hmi.sh
./install_shortcut.sh
```

Then run from anywhere:

```bash
~/update_and_run.sh
```
