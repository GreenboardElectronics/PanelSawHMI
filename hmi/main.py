
import argparse
import sys
from pathlib import Path
from datetime import datetime
import json

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPainter, QColor, QPen
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QGridLayout, QLineEdit, QMessageBox,
    QFrame, QTextEdit
)

sys.path.append(str(Path(__file__).resolve().parents[1]))

from protocol.panel_saw_protocol import (
    Simulator, pkt_jog, pkt_move_abs, pkt_stop, pkt_home, pkt_reset_alarm,
    pkt_start_cycle, AXIS_FENCE, AXIS_HEIGHT, AXIS_TILT
)

class Comm:
    def __init__(self, simulate=True):
        self.sim = Simulator()
    def send(self, packet: bytes):
        self.sim.handle_packet(packet)
    def status(self):
        return self.sim.update()

class Card(QFrame):
    def __init__(self, name="Card"):
        super().__init__()
        self.setObjectName(name)

class AxisCard(Card):
    def __init__(self, title, colour):
        super().__init__("AxisCard")
        l = QVBoxLayout(self)
        l.setContentsMargins(10, 8, 10, 8)
        self.title = QLabel(title)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFont(QFont("Arial", 12, QFont.Bold))
        self.value = QLabel("0.0")
        self.value.setAlignment(Qt.AlignCenter)
        self.value.setFont(QFont("Arial", 29, QFont.Bold))
        self.value.setStyleSheet(f"color:{colour};")
        self.target = QLabel("Target: 0.0")
        self.target.setAlignment(Qt.AlignCenter)
        self.target.setFont(QFont("Arial", 10, QFont.Bold))
        l.addWidget(self.title)
        l.addWidget(self.value)
        l.addWidget(self.target)

class SawMimic(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(145)
        self.fence = 1250.0
        self.height = 78.0
        self.tilt = 90.0

    def set_values(self, fence, height, tilt):
        self.fence, self.height, self.tilt = fence, height, tilt
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor("#0b121a"))

        p.setPen(QPen(QColor("#52677a"), 2))
        p.setBrush(QColor("#253442"))
        p.drawRoundedRect(20, 38, int(w*0.64), 42, 4, 4)

        p.setPen(QPen(QColor("#aab6c1"), 4))
        p.drawLine(35, 55, int(w*0.67), 55)
        p.drawLine(35, 70, int(w*0.67), 70)

        p.setBrush(QColor("#d2d7dc"))
        p.setPen(QPen(QColor("#74808c"), 2))
        saw_x = int(w*0.34)
        p.drawEllipse(saw_x, 22, 58, 58)
        p.setPen(QPen(QColor("#1a222c"), 2))
        for i in range(12):
            p.drawLine(saw_x+29, 51, saw_x+55, 51)
            p.translate(saw_x+29, 51)
            p.rotate(30)
            p.translate(-(saw_x+29), -51)
        p.resetTransform()

        p.setBrush(QColor("#c6cbd0"))
        p.setPen(QPen(QColor("#8b949e"), 1))
        p.drawRect(70, 82, 75, 42)
        p.drawRect(int(w*0.56), 82, 75, 42)

        p.setPen(QColor("#f2f5f7"))
        p.setFont(QFont("Arial", 18, QFont.Bold))
        p.drawText(155, 110, "scm")

        fence_x = 35 + int(min(max(self.fence/3200.0, 0), 1) * 180)
        p.setPen(QPen(QColor("#b5c0ca"), 3))
        p.drawLine(fence_x, 25, fence_x, 132)
        p.drawLine(fence_x-30, 42, fence_x+36, 42)
        p.drawRect(fence_x-10, 75, 20, 35)

        p.setPen(QPen(QColor("#31a32a"), 1))
        p.setBrush(QColor("#31a32a"))
        p.drawRect(int(w*0.62), 25, 12, 12)
        p.setBrush(QColor("#c92820"))
        p.drawRect(int(w*0.62), 12, 12, 12)

class HMI(QMainWindow):
    def __init__(self, simulate=True):
        super().__init__()
        self.comm = Comm(simulate)
        self.setWindowTitle("Greenboard Panel Saw HMI v3.0")
        self.setMinimumSize(1024, 600)
        self.config = self.load_config()

        outer = QWidget()
        self.setCentralWidget(outer)
        main = QVBoxLayout(outer)
        main.setContentsMargins(0,0,0,0)
        main.setSpacing(0)

        main.addWidget(self.top_bar())

        body = QHBoxLayout()
        body.setContentsMargins(0,0,0,0)
        body.setSpacing(0)
        main.addLayout(body)

        body.addWidget(self.nav_bar())
        self.stack = QStackedWidget()
        body.addWidget(self.stack)

        self.stack.addWidget(self.home_page())
        self.stack.addWidget(self.manual_page())
        self.stack.addWidget(self.auto_page())
        self.stack.addWidget(self.programs_page())
        self.stack.addWidget(self.io_page())
        self.stack.addWidget(self.diag_page())
        self.stack.addWidget(self.maintenance_page())
        self.stack.addWidget(self.alarms_page())
        self.stack.addWidget(self.settings_page())

        main.addWidget(self.bottom_bar())

        self.show_page(0)

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(250)
        self.refresh()

    def load_config(self):
        try:
            path = Path(__file__).resolve().parents[1] / "config" / "machine_config.json"
            return json.loads(path.read_text())
        except Exception:
            return {"machine_name":"Panel Saw","brand":"Greenboard Electronics"}

    def top_bar(self):
        f = QFrame(); f.setObjectName("TopBar"); f.setFixedHeight(62)
        l = QHBoxLayout(f); l.setContentsMargins(12,0,12,0)
        menu = QLabel("☰"); menu.setFont(QFont("Arial", 25, QFont.Bold)); menu.setFixedWidth(55)
        self.mode_label = QLabel("AUTO"); self.mode_label.setObjectName("GreenText"); self.mode_label.setFont(QFont("Arial", 13, QFont.Bold)); self.mode_label.setFixedWidth(80)
        title = QLabel("GREENBOARD PANEL SAW CONTROLLER"); title.setAlignment(Qt.AlignCenter); title.setFont(QFont("Arial", 20, QFont.Bold))
        self.clock = QLabel(""); self.clock.setFont(QFont("Arial", 11, QFont.Bold)); self.clock.setAlignment(Qt.AlignRight | Qt.AlignVCenter); self.clock.setFixedWidth(170)
        self.ready = QLabel("READY"); self.ready.setObjectName("ReadyBox"); self.ready.setAlignment(Qt.AlignCenter); self.ready.setFont(QFont("Arial", 12, QFont.Bold)); self.ready.setFixedSize(95,36)
        for x in [menu, self.mode_label, title, self.clock, self.ready]:
            l.addWidget(x, 1 if x is title else 0)
        return f

    def nav_bar(self):
        f = QFrame(); f.setObjectName("Nav"); f.setFixedWidth(162)
        l = QVBoxLayout(f); l.setContentsMargins(0,0,0,0); l.setSpacing(0)
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
        for i,b in enumerate(self.nav_buttons):
            b.setProperty("active", i == idx)
            b.style().unpolish(b); b.style().polish(b)

    def home_page(self):
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(12,12,12,10); l.setSpacing(10)

        axis_row = QHBoxLayout()
        self.fence_card = AxisCard("FENCE POSITION", "#67df4e")
        self.height_card = AxisCard("BLADE HEIGHT", "#59aef7")
        self.tilt_card = AxisCard("BLADE TILT", "#ffd34c")
        for c in [self.fence_card, self.height_card, self.tilt_card]:
            axis_row.addWidget(c)
        l.addLayout(axis_row)

        mid = QHBoxLayout()
        mimic_card = Card()
        ml = QHBoxLayout(mimic_card)
        self.mimic = SawMimic()
        ml.addWidget(self.mimic, 3)
        checks = QVBoxLayout()
        self.check_blade = QLabel("✅  Blade Guard Closed")
        self.check_rear = QLabel("✅  Rear Guard Closed")
        self.check_estop = QLabel("✅  E-Stop OK")
        self.check_vac = QLabel("✅  Vacuum System OK")
        for q in [self.check_blade, self.check_rear, self.check_estop, self.check_vac]:
            q.setFont(QFont("Arial", 12, QFont.Bold)); checks.addWidget(q)
        checks.addStretch(); ml.addLayout(checks, 1)
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
        actions = QVBoxLayout()
        self.start_btn = QPushButton("START CYCLE   ▶"); self.start_btn.setObjectName("StartButton")
        self.stop_btn = QPushButton("STOP CYCLE    ■"); self.stop_btn.setObjectName("StopButton")
        self.reset_btn = QPushButton("RESET         ↻"); self.reset_btn.setObjectName("ResetButton")
        for b in [self.start_btn, self.stop_btn, self.reset_btn]:
            b.setMinimumHeight(58); b.setFont(QFont("Arial", 12, QFont.Bold)); actions.addWidget(b)
        self.start_btn.clicked.connect(lambda: self.comm.send(pkt_start_cycle()))
        self.stop_btn.clicked.connect(lambda: self.comm.send(pkt_stop()))
        self.reset_btn.clicked.connect(lambda: self.comm.send(pkt_reset_alarm()))
        lower.addLayout(actions, 1)
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
            for btn, direction in [(left,-1),(right,1)]:
                btn.setMinimumSize(42,42); btn.setFont(QFont("Arial", 24, QFont.Bold))
                btn.pressed.connect(lambda a=axis,d=direction: self.comm.send(pkt_jog(a,d,10)))
                btn.released.connect(lambda a=axis: self.comm.send(pkt_stop(a)))
            controls.addWidget(left); controls.addWidget(value); controls.addWidget(right)
            col.addLayout(controls)
            steps = QHBoxLayout()
            for s in ["-", "0.1", "0.5", "1", "5", "10"]:
                small = QPushButton(s); small.setMinimumHeight(30); small.setFont(QFont("Arial", 9, QFont.Bold)); steps.addWidget(small)
            col.addLayout(steps); row.addLayout(col)
        l.addLayout(row)
        return c

    def manual_page(self):
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(18,14,18,14)
        title = QLabel("MANUAL OPERATION"); title.setAlignment(Qt.AlignCenter); title.setFont(QFont("Arial", 23, QFont.Bold)); l.addWidget(title)
        grid = QGridLayout()
        axes = [("FENCE X-AXIS", AXIS_FENCE, "JOG -", "JOG +", 50), ("BLADE HEIGHT", AXIS_HEIGHT, "DOWN", "UP", 10), ("BLADE TILT", AXIS_TILT, "TILT -", "TILT +", 5)]
        for row,(name,axis,neg,pos,speed) in enumerate(axes):
            lab=QLabel(name); lab.setFont(QFont("Arial",16,QFont.Bold)); grid.addWidget(lab,row,0)
            for col,(txt,direction) in enumerate([(neg,-1),(pos,1)], start=1):
                b=QPushButton(txt); b.setMinimumHeight(72); b.setFont(QFont("Arial",17,QFont.Bold))
                b.pressed.connect(lambda a=axis,d=direction,s=speed: self.comm.send(pkt_jog(a,d,s)))
                b.released.connect(lambda a=axis: self.comm.send(pkt_stop(a)))
                grid.addWidget(b,row,col)
        l.addLayout(grid)
        row2=QHBoxLayout()
        home=QPushButton("HOME ALL AXES"); stop=QPushButton("STOP ALL"); stop.setObjectName("StopButton")
        for b in [home,stop]:
            b.setMinimumHeight(75); b.setFont(QFont("Arial",17,QFont.Bold)); row2.addWidget(b)
        home.clicked.connect(lambda: self.comm.send(pkt_home())); stop.clicked.connect(lambda: self.comm.send(pkt_stop()))
        l.addLayout(row2)
        return w

    def auto_page(self):
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(18,14,18,14)
        title=QLabel("AUTO POSITIONING"); title.setAlignment(Qt.AlignCenter); title.setFont(QFont("Arial",23,QFont.Bold)); l.addWidget(title)
        self.in_fence=QLineEdit("1200.00"); self.in_height=QLineEdit("75.0"); self.in_tilt=QLineEdit("90.0")
        grid=QGridLayout()
        for i,(name,edit) in enumerate([("Fence Target mm",self.in_fence),("Blade Height mm",self.in_height),("Blade Tilt deg",self.in_tilt)]):
            c=Card(); cl=QVBoxLayout(c); lab=QLabel(name); lab.setFont(QFont("Arial",15,QFont.Bold))
            edit.setMinimumHeight(70); edit.setFont(QFont("Arial",24,QFont.Bold)); cl.addWidget(lab); cl.addWidget(edit); grid.addWidget(c,0,i)
        l.addLayout(grid)
        move=QPushButton("MOVE TO POSITION"); stop=QPushButton("STOP MOVE"); stop.setObjectName("StopButton")
        for b in [move,stop]:
            b.setMinimumHeight(80); b.setFont(QFont("Arial",18,QFont.Bold)); l.addWidget(b)
        move.clicked.connect(self.move_auto); stop.clicked.connect(lambda: self.comm.send(pkt_stop()))
        return w

    def programs_page(self):
        return self.info_page("PROGRAMS", "Current Program: None\n\nNext: cut lists, material database, saved recipes, USB import/export.")

    def io_page(self):
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(18,14,18,14)
        title=QLabel("LIVE I/O MONITOR"); title.setAlignment(Qt.AlignCenter); title.setFont(QFont("Arial",23,QFont.Bold)); l.addWidget(title)
        grid=QGridLayout()
        inputs=["E-STOP OK","GUARD CLOSED","VACUUM OK","SERVO POWER","FENCE HOME","HEIGHT HOME","TILT HOME","START PB"]
        outputs=["SERVO ENABLE","SAW REQUEST","VACUUM START","ALARM BEACON","BUZZER","FENCE BRAKE","HEIGHT BRAKE","TILT BRAKE"]
        for i,name in enumerate(inputs):
            q=QLabel(f"🟢 IN {i+1:02d}  {name}"); q.setFont(QFont("Arial",14,QFont.Bold)); grid.addWidget(q,i,0)
        for i,name in enumerate(outputs):
            q=QLabel(f"🔵 OUT {i+1:02d}  {name}"); q.setFont(QFont("Arial",14,QFont.Bold)); grid.addWidget(q,i,1)
        l.addLayout(grid)
        return w

    def diag_page(self):
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(18,14,18,14)
        title=QLabel("DIAGNOSTICS"); title.setAlignment(Qt.AlignCenter); title.setFont(QFont("Arial",23,QFont.Bold)); l.addWidget(title)
        self.diag=QLabel(""); self.diag.setObjectName("DiagText"); self.diag.setAlignment(Qt.AlignTop); self.diag.setFont(QFont("Courier New",14)); l.addWidget(self.diag)
        return w

    def maintenance_page(self):
        return self.info_page("MAINTENANCE", "Blade hours: 0.0\nLubrication: Due in 40 hours\nDust extraction filter: OK\nBackup status: Not configured")

    def alarms_page(self):
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(18,14,18,14)
        title=QLabel("ALARMS"); title.setAlignment(Qt.AlignCenter); title.setFont(QFont("Arial",23,QFont.Bold)); l.addWidget(title)
        self.alarm_label=QLabel("No active alarms"); self.alarm_label.setAlignment(Qt.AlignCenter); self.alarm_label.setFont(QFont("Arial",25,QFont.Bold)); l.addWidget(self.alarm_label)
        self.alarm_history=QTextEdit(); self.alarm_history.setReadOnly(True); self.alarm_history.setFont(QFont("Courier New",13)); l.addWidget(self.alarm_history)
        reset=QPushButton("RESET ALARM"); reset.setMinimumHeight(75); reset.setFont(QFont("Arial",18,QFont.Bold)); reset.clicked.connect(lambda: self.comm.send(pkt_reset_alarm())); l.addWidget(reset)
        return w

    def settings_page(self):
        return self.info_page("SERVICE SETTINGS", "Access Level: Operator\n\nNext: password login, calibration wizard, RS-485 setup, axis limits, backup/restore.")

    def info_page(self, title, text):
        w=QWidget(); l=QVBoxLayout(w); l.setContentsMargins(18,14,18,14)
        lab=QLabel(title); lab.setAlignment(Qt.AlignCenter); lab.setFont(QFont("Arial",23,QFont.Bold)); l.addWidget(lab)
        body=QLabel(text); body.setAlignment(Qt.AlignCenter); body.setFont(QFont("Arial",20,QFont.Bold)); l.addWidget(body)
        return w

    def move_auto(self):
        try:
            self.comm.send(pkt_move_abs(AXIS_FENCE, float(self.in_fence.text()), 80))
            self.comm.send(pkt_move_abs(AXIS_HEIGHT, float(self.in_height.text()), 15))
            self.comm.send(pkt_move_abs(AXIS_TILT, float(self.in_tilt.text()), 8))
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Enter valid numeric values.")

    def bottom_bar(self):
        f=QFrame(); f.setObjectName("BottomBar"); f.setFixedHeight(46)
        l=QHBoxLayout(f); l.setContentsMargins(0,0,0,0)
        self.bottom_alarm=QLabel("✅  No Alarms"); self.bottom_rs485=QLabel("🔗  RS485 Link: OK"); self.bottom_ctrl=QLabel("▣  Controllers: 4"); self.bottom_io=QLabel("◎  I/O OK"); self.bottom_sd=QLabel("▣  SD Card: OK")
        for x in [self.bottom_alarm,self.bottom_rs485,self.bottom_ctrl,self.bottom_io,self.bottom_sd]:
            x.setObjectName("BottomItem"); x.setAlignment(Qt.AlignCenter); x.setFont(QFont("Arial",11,QFont.Bold)); l.addWidget(x)
        return f

    def refresh(self):
        s = self.comm.status()
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

        self.alarm_label.setText(s.alarm if s.alarm else "No active alarms")
        self.alarm_history.setPlainText("\\n".join(s.alarm_history) if s.alarm_history else "No alarm history.")

        self.diag.setText(
            f"Machine State       : {s.state}\n"
            f"Mode                : {s.mode}\n"
            f"Cycle               : {s.cycle}\n"
            f"RS-485 Link          : {'OK' if s.rs485_ok else 'FAULT'}\n"
            f"Controllers          : {s.controller_count}\n\n"
            f"Fence Position       : {s.fence.position:8.2f} mm\n"
            f"Fence Target         : {s.fence.target:8.2f} mm\n"
            f"Blade Height         : {s.height.position:8.1f} mm\n"
            f"Blade Height Target  : {s.height.target:8.1f} mm\n"
            f"Blade Tilt           : {s.tilt.position:8.1f} deg\n"
            f"Blade Tilt Target    : {s.tilt.target:8.1f} deg\n\n"
            f"E-stop OK            : {s.estop_ok}\n"
            f"Blade Guard Closed   : {s.blade_guard_closed}\n"
            f"Rear Guard Closed    : {s.rear_guard_closed}\n"
            f"Vacuum OK            : {s.vacuum_ok}\n"
            f"I/O OK               : {s.io_ok}\n"
            f"SD Card OK           : {s.sd_ok}\n"
            f"Saw Running          : {s.saw_running}\n"
            f"Panel Count          : {s.panel_count}\n"
            f"Cut Count            : {s.cut_count}\n"
        )

        self.bottom_alarm.setText("✅  No Alarms" if not s.alarm else f"⚠️  {s.alarm}")
        self.bottom_rs485.setText(f"🔗  RS485 Link: {'OK' if s.rs485_ok else 'FAULT'}")
        self.bottom_ctrl.setText(f"▣  Controllers: {s.controller_count}")
        self.bottom_io.setText(f"◎  I/O {'OK' if s.io_ok else 'FAULT'}")
        self.bottom_sd.setText(f"▣  SD Card: {'OK' if s.sd_ok else 'FAULT'}")

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

    hmi = HMI(simulate=args.simulate)
    hmi.showFullScreen()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
