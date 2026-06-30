
import argparse
import sys
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QGridLayout, QLineEdit, QMessageBox,
    QFrame, QTextEdit
)

sys.path.append(str(Path(__file__).resolve().parents[1]))

from hmi.core.controller import SimulatorController
from hmi.widgets.cards import Card, AxisCard
from hmi.widgets.saw_mimic import SawMimic
from protocol.panel_saw_protocol import (
    pkt_jog, pkt_move_abs, pkt_stop, pkt_home, pkt_reset_alarm,
    pkt_start_cycle, AXIS_FENCE, AXIS_HEIGHT, AXIS_TILT
)

class IndustrialHMI(QMainWindow):
    def __init__(self, simulate=True):
        super().__init__()
        self.controller = SimulatorController()
        self.setWindowTitle("Greenboard Panel Saw HMI v3.1 Production")
        self.setMinimumSize(1024, 600)

        outer = QWidget()
        self.setCentralWidget(outer)
        main = QVBoxLayout(outer)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        main.addWidget(self.top_bar())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        main.addLayout(body)

        body.addWidget(self.nav_bar())
        self.stack = QStackedWidget()
        body.addWidget(self.stack)

        for page in [
            self.home_page(), self.manual_page(), self.auto_page(), self.programs_page(),
            self.io_page(), self.diag_page(), self.maintenance_page(),
            self.alarms_page(), self.settings_page()
        ]:
            self.stack.addWidget(page)

        main.addWidget(self.bottom_bar())
        self.show_page(0)

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(250)
        self.refresh()

    def top_bar(self):
        f = QFrame(); f.setObjectName("TopBar"); f.setFixedHeight(62)
        l = QHBoxLayout(f); l.setContentsMargins(12, 0, 12, 0)
        menu = QLabel("☰"); menu.setFont(QFont("Arial", 25, QFont.Bold)); menu.setFixedWidth(55)
        self.mode_label = QLabel("AUTO"); self.mode_label.setObjectName("GreenText"); self.mode_label.setFont(QFont("Arial", 13, QFont.Bold)); self.mode_label.setFixedWidth(80)
        title = QLabel("GREENBOARD PANEL SAW CONTROLLER"); title.setAlignment(Qt.AlignCenter); title.setFont(QFont("Arial", 20, QFont.Bold))
        self.clock = QLabel(""); self.clock.setFont(QFont("Arial", 11, QFont.Bold)); self.clock.setAlignment(Qt.AlignRight | Qt.AlignVCenter); self.clock.setFixedWidth(170)
        self.ready = QLabel("READY"); self.ready.setObjectName("ReadyBox"); self.ready.setAlignment(Qt.AlignCenter); self.ready.setFont(QFont("Arial", 12, QFont.Bold)); self.ready.setFixedSize(95, 36)
        l.addWidget(menu); l.addWidget(self.mode_label); l.addWidget(title, 1); l.addWidget(self.clock); l.addWidget(self.ready)
        return f

    def nav_bar(self):
        f = QFrame(); f.setObjectName("Nav"); f.setFixedWidth(162)
        l = QVBoxLayout(f); l.setContentsMargins(0, 0, 0, 0); l.setSpacing(0)
        self.nav_buttons = []
        entries = [
            ("⌂", "HOME", 0), ("✋", "MANUAL", 1), ("◎", "AUTO", 2),
            ("▣", "PROGRAMS", 3), ("◧", "I/O", 4), ("⌁", "DIAG", 5),
            ("🔧", "MAINT", 6), ("●", "ALARMS", 7), ("⚙", "SETTINGS", 8)
        ]
        for icon, text, idx in entries:
            b = QPushButton(f"{icon}  {text}")
            b.setObjectName("NavButton")
            b.setMinimumHeight(55)
            b.setFont(QFont("Arial", 12, QFont.Bold))
            b.clicked.connect(lambda _, i=idx: self.show_page(i))
            l.addWidget(b)
            self.nav_buttons.append(b)
        l.addStretch()
        return f

    def show_page(self, idx):
        self.stack.setCurrentIndex(idx)
        for i, b in enumerate(self.nav_buttons):
            b.setProperty("active", i == idx)
            b.style().unpolish(b)
            b.style().polish(b)

    def home_page(self):
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(12, 12, 12, 10); l.setSpacing(10)
        axis_row = QHBoxLayout()
        self.fence_card = AxisCard("FENCE POSITION", "#67df4e")
        self.height_card = AxisCard("BLADE HEIGHT", "#59aef7")
        self.tilt_card = AxisCard("BLADE TILT", "#ffd34c")
        axis_row.addWidget(self.fence_card); axis_row.addWidget(self.height_card); axis_row.addWidget(self.tilt_card)
        l.addLayout(axis_row)

        mid = QHBoxLayout()
        mimic_card = Card()
        ml = QHBoxLayout(mimic_card)
        self.mimic = SawMimic()
        ml.addWidget(self.mimic, 3)
        checks = QVBoxLayout()
        self.check_labels = {}
        for key, txt in [
            ("blade_guard", "Blade Guard Closed"), ("rear_guard", "Rear Guard Closed"),
            ("estop", "E-Stop OK"), ("vacuum", "Vacuum System OK")
        ]:
            q = QLabel(f"✅  {txt}")
            q.setFont(QFont("Arial", 12, QFont.Bold))
            checks.addWidget(q)
            self.check_labels[key] = q
        checks.addStretch()
        ml.addLayout(checks, 1)
        mid.addWidget(mimic_card, 4)

        status_card = Card()
        sl = QVBoxLayout(status_card)
        stitle = QLabel("MACHINE STATUS"); stitle.setFont(QFont("Arial", 13, QFont.Bold))
        self.status_lines = QLabel(""); self.status_lines.setFont(QFont("Arial", 11, QFont.Bold))
        sl.addWidget(stitle); sl.addWidget(self.status_lines); sl.addStretch()
        mid.addWidget(status_card, 1)
        l.addLayout(mid)

        lower = QHBoxLayout()
        lower.addWidget(self.quick_jog_card(), 4)
        action = QVBoxLayout()
        self.start_btn = QPushButton("START CYCLE   ▶"); self.start_btn.setObjectName("StartButton")
        self.stop_btn = QPushButton("STOP CYCLE    ■"); self.stop_btn.setObjectName("StopButton")
        self.reset_btn = QPushButton("RESET         ↻"); self.reset_btn.setObjectName("ResetButton")
        for b in [self.start_btn, self.stop_btn, self.reset_btn]:
            b.setMinimumHeight(58); b.setFont(QFont("Arial", 12, QFont.Bold)); action.addWidget(b)
        self.start_btn.clicked.connect(lambda: self.controller.send(pkt_start_cycle()))
        self.stop_btn.clicked.connect(lambda: self.controller.send(pkt_stop()))
        self.reset_btn.clicked.connect(lambda: self.controller.send(pkt_reset_alarm()))
        lower.addLayout(action, 1)
        l.addLayout(lower)
        return w

    def quick_jog_card(self):
        c = Card(); l = QVBoxLayout(c)
        title = QLabel("QUICK JOG"); title.setFont(QFont("Arial", 12, QFont.Bold)); l.addWidget(title)
        row = QHBoxLayout()
        for name, axis, step in [("FENCE", AXIS_FENCE, "10.0\nmm"), ("BLADE HEIGHT", AXIS_HEIGHT, "1.0\nmm"), ("BLADE TILT", AXIS_TILT, "0.5\n°")]:
            col = QVBoxLayout()
            lab = QLabel(name); lab.setAlignment(Qt.AlignCenter); lab.setFont(QFont("Arial", 11, QFont.Bold)); col.addWidget(lab)
            controls = QHBoxLayout()
            left = QPushButton("‹"); right = QPushButton("›")
            value = QLabel(step); value.setAlignment(Qt.AlignCenter); value.setObjectName("StepBox"); value.setFont(QFont("Arial", 18, QFont.Bold))
            for btn, direction in [(left, -1), (right, 1)]:
                btn.setMinimumSize(42, 42); btn.setFont(QFont("Arial", 24, QFont.Bold))
                btn.pressed.connect(lambda a=axis, d=direction: self.controller.send(pkt_jog(a, d, 10)))
                btn.released.connect(lambda a=axis: self.controller.send(pkt_stop(a)))
            controls.addWidget(left); controls.addWidget(value); controls.addWidget(right)
            col.addLayout(controls)
            steps = QHBoxLayout()
            for s in ["-", "0.1", "0.5", "1", "5", "10"]:
                small = QPushButton(s); small.setMinimumHeight(30); small.setFont(QFont("Arial", 9, QFont.Bold)); steps.addWidget(small)
            col.addLayout(steps); row.addLayout(col)
        l.addLayout(row)
        return c

    def manual_page(self):
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(18, 14, 18, 14)
        title = QLabel("MANUAL OPERATION"); title.setAlignment(Qt.AlignCenter); title.setFont(QFont("Arial", 23, QFont.Bold)); l.addWidget(title)
        grid = QGridLayout()
        axes = [("FENCE X-AXIS", AXIS_FENCE, "JOG -", "JOG +", 50), ("BLADE HEIGHT", AXIS_HEIGHT, "DOWN", "UP", 10), ("BLADE TILT", AXIS_TILT, "TILT -", "TILT +", 5)]
        for row, (name, axis, neg, pos, speed) in enumerate(axes):
            lab = QLabel(name); lab.setFont(QFont("Arial", 16, QFont.Bold)); grid.addWidget(lab, row, 0)
            for col, (txt, direction) in enumerate([(neg, -1), (pos, 1)], start=1):
                b = QPushButton(txt); b.setMinimumHeight(72); b.setFont(QFont("Arial", 17, QFont.Bold))
                b.pressed.connect(lambda a=axis, d=direction, s=speed: self.controller.send(pkt_jog(a, d, s)))
                b.released.connect(lambda a=axis: self.controller.send(pkt_stop(a)))
                grid.addWidget(b, row, col)
        l.addLayout(grid)
        row2 = QHBoxLayout()
        home = QPushButton("HOME ALL AXES"); stop = QPushButton("STOP ALL"); stop.setObjectName("StopButton")
        for b in [home, stop]:
            b.setMinimumHeight(75); b.setFont(QFont("Arial", 17, QFont.Bold)); row2.addWidget(b)
        home.clicked.connect(lambda: self.controller.send(pkt_home()))
        stop.clicked.connect(lambda: self.controller.send(pkt_stop()))
        l.addLayout(row2)
        return w

    def auto_page(self):
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(18, 14, 18, 14)
        title = QLabel("AUTO POSITIONING"); title.setAlignment(Qt.AlignCenter); title.setFont(QFont("Arial", 23, QFont.Bold)); l.addWidget(title)
        self.in_fence = QLineEdit("1200.00"); self.in_height = QLineEdit("75.0"); self.in_tilt = QLineEdit("90.0")
        grid = QGridLayout()
        for i, (name, edit) in enumerate([("Fence Target mm", self.in_fence), ("Blade Height mm", self.in_height), ("Blade Tilt deg", self.in_tilt)]):
            c = Card(); cl = QVBoxLayout(c); lab = QLabel(name); lab.setFont(QFont("Arial", 15, QFont.Bold))
            edit.setMinimumHeight(70); edit.setFont(QFont("Arial", 24, QFont.Bold))
            cl.addWidget(lab); cl.addWidget(edit); grid.addWidget(c, 0, i)
        l.addLayout(grid)
        move = QPushButton("MOVE TO POSITION"); stop = QPushButton("STOP MOVE"); stop.setObjectName("StopButton")
        for b in [move, stop]:
            b.setMinimumHeight(80); b.setFont(QFont("Arial", 18, QFont.Bold)); l.addWidget(b)
        move.clicked.connect(self.move_auto); stop.clicked.connect(lambda: self.controller.send(pkt_stop()))
        return w

    def programs_page(self):
        return self.info_page("PROGRAMS", "Current Program: Demo Job\nMaterial: MDF 18mm\nCuts queued: 6\n\nNext: editor, search, USB import/export.")

    def io_page(self):
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(18, 14, 18, 14)
        title = QLabel("LIVE I/O MONITOR"); title.setAlignment(Qt.AlignCenter); title.setFont(QFont("Arial", 23, QFont.Bold)); l.addWidget(title)
        self.io_grid = QGridLayout(); l.addLayout(self.io_grid)
        self.io_labels = []
        return w

    def diag_page(self):
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(18, 14, 18, 14)
        title = QLabel("DIAGNOSTICS"); title.setAlignment(Qt.AlignCenter); title.setFont(QFont("Arial", 23, QFont.Bold)); l.addWidget(title)
        self.diag = QLabel(""); self.diag.setObjectName("DiagText"); self.diag.setAlignment(Qt.AlignTop); self.diag.setFont(QFont("Courier New", 14)); l.addWidget(self.diag)
        return w

    def maintenance_page(self):
        return self.info_page("MAINTENANCE", "Blade hours: 0.0\nLubrication: Due in 40 hours\nDust filter: OK\nBackup status: Not configured")

    def alarms_page(self):
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(18, 14, 18, 14)
        title = QLabel("ALARMS"); title.setAlignment(Qt.AlignCenter); title.setFont(QFont("Arial", 23, QFont.Bold)); l.addWidget(title)
        self.alarm_label = QLabel("No active alarms"); self.alarm_label.setAlignment(Qt.AlignCenter); self.alarm_label.setFont(QFont("Arial", 25, QFont.Bold)); l.addWidget(self.alarm_label)
        self.alarm_history = QTextEdit(); self.alarm_history.setReadOnly(True); self.alarm_history.setFont(QFont("Courier New", 13)); l.addWidget(self.alarm_history)
        reset = QPushButton("RESET ALARM"); reset.setMinimumHeight(75); reset.setFont(QFont("Arial", 18, QFont.Bold)); reset.clicked.connect(lambda: self.controller.send(pkt_reset_alarm())); l.addWidget(reset)
        return w

    def settings_page(self):
        return self.info_page("SERVICE SETTINGS", "Access Level: Operator\n\nNext: password login, calibration wizard, RS-485 setup, axis limits, backup/restore.")

    def info_page(self, title, text):
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(18, 14, 18, 14)
        lab = QLabel(title); lab.setAlignment(Qt.AlignCenter); lab.setFont(QFont("Arial", 23, QFont.Bold)); l.addWidget(lab)
        body = QLabel(text); body.setAlignment(Qt.AlignCenter); body.setFont(QFont("Arial", 20, QFont.Bold)); l.addWidget(body)
        return w

    def move_auto(self):
        try:
            self.controller.send(pkt_move_abs(AXIS_FENCE, float(self.in_fence.text()), 80))
            self.controller.send(pkt_move_abs(AXIS_HEIGHT, float(self.in_height.text()), 15))
            self.controller.send(pkt_move_abs(AXIS_TILT, float(self.in_tilt.text()), 8))
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Enter valid numeric values.")

    def bottom_bar(self):
        f = QFrame(); f.setObjectName("BottomBar"); f.setFixedHeight(46)
        l = QHBoxLayout(f); l.setContentsMargins(0, 0, 0, 0)
        self.bottom_alarm = QLabel("✅  No Alarms"); self.bottom_rs485 = QLabel("🔗  RS485 Link: OK"); self.bottom_ctrl = QLabel("▣  Controllers: 4"); self.bottom_io = QLabel("◎  I/O OK"); self.bottom_sd = QLabel("▣  SD Card: OK")
        for x in [self.bottom_alarm, self.bottom_rs485, self.bottom_ctrl, self.bottom_io, self.bottom_sd]:
            x.setObjectName("BottomItem"); x.setAlignment(Qt.AlignCenter); x.setFont(QFont("Arial", 11, QFont.Bold)); l.addWidget(x)
        return f

    def refresh_io_grid(self, s):
        if self.io_labels:
            for lbl in self.io_labels:
                lbl.deleteLater()
            self.io_labels.clear()
        row = 0
        for i, (name, val) in enumerate(s.io.inputs.items()):
            q = QLabel(f"{'🟢' if val else '⚫'} IN {i+1:02d}  {name}")
            q.setFont(QFont("Arial", 14, QFont.Bold))
            self.io_grid.addWidget(q, row, 0)
            self.io_labels.append(q)
            row += 1
        row = 0
        for i, (name, val) in enumerate(s.io.outputs.items()):
            q = QLabel(f"{'🔵' if val else '⚫'} OUT {i+1:02d}  {name}")
            q.setFont(QFont("Arial", 14, QFont.Bold))
            self.io_grid.addWidget(q, row, 1)
            self.io_labels.append(q)
            row += 1

    def refresh(self):
        s = self.controller.status()
        self.clock.setText(datetime.now().strftime("%d/%m/%Y  %H:%M:%S"))
        self.mode_label.setText(s.mode)
        self.ready.setText(s.state)

        self.fence_card.value.setText(f"{s.fence.position:.2f} {s.fence.unit}")
        self.fence_card.target.setText(f"Target: {s.fence.target:.2f} {s.fence.unit}")
        self.height_card.value.setText(f"{s.height.position:.1f} {s.height.unit}")
        self.height_card.target.setText(f"Target: {s.height.target:.1f} {s.height.unit}")
        self.tilt_card.value.setText(f"{s.tilt.position:.1f} {s.tilt.unit}")
        self.tilt_card.target.setText(f"Target: {s.tilt.target:.1f} {s.tilt.unit}")

        self.mimic.set_values(s.fence.position, s.height.position, s.tilt.position)
        self.status_lines.setText(f"Mode:        {s.mode}\nCycle:       {s.cycle}\nProgram:     {s.program}\nOperator:    {s.operator}\nAccess:      {s.access_level}\nRun Time:    {s.runtime}")

        self.alarm_label.setText(s.active_alarm if s.active_alarm else "No active alarms")
        self.alarm_history.setPlainText("\n".join(s.alarm_history) if s.alarm_history else "No alarm history.")

        self.diag.setText(
            f"Machine State       : {s.state}\nMode                : {s.mode}\nCycle               : {s.cycle}\n"
            f"RS-485 Link          : {'OK' if s.rs485_ok else 'FAULT'}\nControllers          : {s.controller_count}\n\n"
            f"Fence Position       : {s.fence.position:8.2f} mm\nFence Target         : {s.fence.target:8.2f} mm\n"
            f"Blade Height         : {s.height.position:8.1f} mm\nBlade Height Target  : {s.height.target:8.1f} mm\n"
            f"Blade Tilt           : {s.tilt.position:8.1f} deg\nBlade Tilt Target    : {s.tilt.target:8.1f} deg\n\n"
            f"E-stop OK            : {s.safety.estop_ok}\nBlade Guard Closed   : {s.safety.blade_guard_closed}\n"
            f"Rear Guard Closed    : {s.safety.rear_guard_closed}\nVacuum OK            : {s.safety.vacuum_ok}\n"
            f"Servo Power OK       : {s.safety.servo_power_ok}\nI/O OK               : {s.io_ok}\n"
            f"SD Card OK           : {s.sd_ok}\nSaw Running          : {s.saw_running}\n"
            f"Panel Count          : {s.panel_count}\nCut Count            : {s.cut_count}\n"
        )

        self.bottom_alarm.setText("✅  No Alarms" if not s.active_alarm else f"⚠️  {s.active_alarm}")
        self.bottom_rs485.setText(f"🔗  RS485 Link: {'OK' if s.rs485_ok else 'FAULT'}")
        self.bottom_ctrl.setText(f"▣  Controllers: {s.controller_count}")
        self.bottom_io.setText(f"◎  I/O {'OK' if s.io_ok else 'FAULT'}")
        self.bottom_sd.setText(f"▣  SD Card: {'OK' if s.sd_ok else 'FAULT'}")

        if self.stack.currentIndex() == 4:
            self.refresh_io_grid(s)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulate", action="store_true")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QWidget { background: #071018; color: #f2f5f7; }
        #TopBar { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #0b1520, stop:1 #060b10); border-bottom: 1px solid #26384a; }
        #Nav { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #071018, stop:1 #0b1c29); border-right: 1px solid #2b4053; }
        #NavButton { background: transparent; color: #f2f5f7; border: none; border-bottom: 1px solid #1e3346; border-radius: 0; text-align: left; padding-left: 10px; }
        #NavButton[active="true"] { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #005ac8, stop:1 #0d73e4); }
        #Card, #AxisCard { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #0c1924, stop:1 #08121a); border: 1px solid #31485e; border-radius: 7px; }
        QPushButton { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #143455, stop:1 #0d263f); color: white; border: 1px solid #2d5a83; border-radius: 6px; padding: 6px; }
        QPushButton:pressed { background: #2f6da2; }
        #StartButton { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #38a526, stop:1 #1f7c16); }
        #StopButton { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #d73528, stop:1 #9d2019); }
        #ResetButton { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #1d5a89, stop:1 #143e61); }
        #ReadyBox { color: #6dff57; border: 1px solid #269d30; border-radius: 5px; background: #102016; }
        #GreenText { color: #6dff57; }
        #StepBox { background: #071018; border: 1px solid #3e5368; border-radius: 4px; color: white; }
        #DiagText { background: #05090d; border: 1px solid #31485e; border-radius: 7px; padding: 14px; }
        #BottomBar { background: #08121a; border-top: 1px solid #26384a; }
        #BottomItem { border-right: 1px solid #26384a; color: #f2f5f7; }
        QLineEdit { background: #05090d; color: #00ff99; border: 1px solid #52677d; border-radius: 6px; padding: 8px; }
        QTextEdit { background: #05090d; color: #f2f5f7; border: 1px solid #31485e; border-radius: 7px; }
    """)

    hmi = IndustrialHMI(simulate=args.simulate)
    hmi.showFullScreen()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
