# One Command Update + Run

After pulling this version on the Raspberry Pi, run:

```bash
cd ~/PanelSawHMI
chmod +x update_and_run.sh install_shortcut.sh run_hmi.sh
./install_shortcut.sh
```

After that, from anywhere on the Raspberry Pi you can run:

```bash
~/update_and_run.sh
```

This will:

1. Go to `~/PanelSawHMI`
2. Run `git pull`
3. Create `venv` if needed
4. Activate the virtual environment
5. Install requirements
6. Start the HMI in simulator mode
