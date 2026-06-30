
import argparse
import sys
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QGridLayout, QLineEdit, QMessageBox,
    QFrame
)

sys.path.append(str(Path(__file__).resolve().parents[1]))

from protocol.panel_saw_protocol import (
    Simulator, pkt_jog, pkt_move_abs, pkt_stop, pkt_home, pkt_reset_alarm,
    AXIS_FENCE, AXIS_HEIGHT, AXIS_TILT
)

class Comm:
    def __init__(self, simulate=True):
        self.simulate = simulate
        self.sim = Simulator()

    def send(self, packet: bytes):
        if self.simulate:
            self.sim.handle_packet(packet)

    def status(self):
        return self.sim.update()

class Card(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("Card")

class HMI(QMainWindow):
    def __init__(self, simulate=True):
        super().__init__()
        self.comm = Comm(simulate)
        self.setWindowTitle("Panel Saw Controller v2.1")
        self.setMinimumSize(1024, 600)

        outer = QWidget()
        self.setCentralWidget(outer)
        main = QHBoxLayout(outer)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        self.nav_frame = QFrame()
        self.nav_frame.setObjectName("Nav")
        self.nav_frame.setFixedWidth(175)
        nav = QVBoxLayout(self.nav_frame)
        nav.setContentsMargins(8, 10, 8, 10)
        main.addWidget(self.nav_frame)

        logo = QLabel("GREENBOARD\nPANEL SAW")
        logo.setAlignment(Qt.AlignCenter)
        logo.setFont(QFont("Arial", 16, QFont.Bold))
        nav.addWidget(logo)

        self.stack = QStackedWidget()
        main.addWidget(self.stack)

        self.nav_buttons = []
        pages = [("HOME", 0), ("MANUAL", 1), ("AUTO", 2), ("DIAG", 3), ("ALARMS", 4), ("SETTINGS", 5)]
        for text, idx in pages:
            b = QPushButton(text)
            b.setMinimumHeight(62)
            b.setFont(QFont("Arial", 14, QFont.Bold))
            b.clicked.connect(lambda _, i=idx: self.show_page(i))
            nav.addWidget(b)
            self.nav_buttons.append(b)

        nav.addStretch()
        self.footer = QLabel("v2.1\nSimulator")
        self.footer.setAlignment(Qt.AlignCenter)
        nav.addWidget(self.footer)

        self.stack.addWidget(self.home_page())
        self.stack.addWidget(self.manual_page())
        self.stack.addWidget(self.auto_page())
        self.stack.addWidget(self.diag_page())
        self.stack.addWidget(self.alarms_page())
        self.stack.addWidget(self.settings_page())

        self.show_page(0)

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(250)
        self.refresh()

    def show_page(self, idx):
        self.stack.setCurrentIndex(idx)
        for i, b in enumerate(self.nav_buttons):
            b.setProperty("active", i == idx)
            b.style().unpolish(b)
            b.style().polish(b)

    def page(self, title):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(18, 14, 18, 14)

        header = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 23, QFont.Bold))
        header.addWidget(title_label)
        header.addStretch()
        self.clock = QLabel("")
        self.clock.setFont(QFont("Arial", 12, QFont.Bold))
        header.addWidget(self.clock)
        layout.addLayout(header)
        return w, layout

    def metric(self, title, value, color="green"):
        c = Card()
        l = QVBoxLayout(c)
        lab = QLabel(title)
        lab.setFont(QFont("Arial", 12, QFont.Bold))
        val = QLabel(value)
        val.setAlignment(Qt.AlignCenter)
        val.setFont(QFont("Arial", 22, QFont.Bold))
        val.setObjectName("MetricValue")
        val.setProperty("metricColor", color)
        l.addWidget(lab)
        l.addWidget(val)
        return c, val

    def home_page(self):
        w, layout = self.page("PANEL SAW CONTROLLER v2.1")

        grid = QGridLayout()
        self.c_state, self.v_state = self.metric("STATUS", "READY")
        self.c_fence, self.v_fence = self.metric("FENCE POSITION", "0.00 mm")
        self.c_height, self.v_height = self.metric("BLADE HEIGHT", "0.0 mm")
        self.c_tilt, self.v_tilt = self.metric("BLADE TILT", "90.0°")
        self.c_safety, self.v_safety = self.metric("SAFETY", "OK")
        self.c_alarm, self.v_alarm = self.metric("ALARM", "None")

        cards = [self.c_state, self.c_fence, self.c_height, self.c_tilt, self.c_safety, self.c_alarm]
        for i, c in enumerate(cards):
            grid.addWidget(c, i // 2, i % 2)

        layout.addLayout(grid)

        row = QHBoxLayout()
        self.btn_start = QPushButton("START CYCLE")
        self.btn_stop = QPushButton("MACHINE STOP")
        self.btn_reset = QPushButton("RESET")
        for b in [self.btn_start, self.btn_stop, self.btn_reset]:
            b.setMinimumHeight(70)
            b.setFont(QFont("Arial", 16, QFont.Bold))
            row.addWidget(b)
        self.btn_stop.setObjectName("StopButton")
        self.btn_stop.clicked.connect(lambda: self.comm.send(pkt_stop()))
        self.btn_reset.clicked.connect(lambda: self.comm.send(pkt_reset_alarm()))
        layout.addLayout(row)
        return w

    def manual_page(self):
        w, layout = self.page("MANUAL OPERATION")

        grid = QGridLayout()
        axes = [
            ("FENCE X-AXIS", AXIS_FENCE, "JOG -", "JOG +", 50),
            ("BLADE HEIGHT", AXIS_HEIGHT, "DOWN", "UP", 10),
            ("BLADE TILT", AXIS_TILT, "TILT -", "TILT +", 5),
        ]

        for col, (name, axis, neg, pos, speed) in enumerate(axes):
            c = Card()
            l = QVBoxLayout(c)
            lab = QLabel(name)
            lab.setAlignment(Qt.AlignCenter)
            lab.setFont(QFont("Arial", 15, QFont.Bold))
            l.addWidget(lab)

            row = QHBoxLayout()
            for text, direction in [(neg, -1), (pos, 1)]:
                b = QPushButton(text)
                b.setMinimumHeight(82)
                b.setFont(QFont("Arial", 15, QFont.Bold))
                b.pressed.connect(lambda a=axis, d=direction, s=speed: self.comm.send(pkt_jog(a, d, s)))
                b.released.connect(lambda a=axis: self.comm.send(pkt_stop(a)))
                row.addWidget(b)
            l.addLayout(row)
            grid.addWidget(c, 0, col)

        layout.addLayout(grid)

        row2 = QHBoxLayout()
        home = QPushButton("HOME ALL AXES")
        stop = QPushButton("STOP ALL")
        for b in [home, stop]:
            b.setMinimumHeight(75)
            b.setFont(QFont("Arial", 17, QFont.Bold))
            row2.addWidget(b)
        home.clicked.connect(lambda: self.comm.send(pkt_home()))
        stop.setObjectName("StopButton")
        stop.clicked.connect(lambda: self.comm.send(pkt_stop()))
        layout.addLayout(row2)
        return w

    def auto_page(self):
        w, layout = self.page("AUTO POSITIONING")

        self.in_fence = QLineEdit("1200.00")
        self.in_height = QLineEdit("75.0")
        self.in_tilt = QLineEdit("90.0")

        grid = QGridLayout()
        for i, (name, edit) in enumerate([
            ("Fence Target mm", self.in_fence),
            ("Blade Height mm", self.in_height),
            ("Blade Tilt deg", self.in_tilt),
        ]):
            c = Card()
            l = QVBoxLayout(c)
            lab = QLabel(name)
            lab.setFont(QFont("Arial", 15, QFont.Bold))
            edit.setMinimumHeight(70)
            edit.setFont(QFont("Arial", 24, QFont.Bold))
            l.addWidget(lab)
            l.addWidget(edit)
            grid.addWidget(c, 0, i)

        layout.addLayout(grid)

        move = QPushButton("MOVE TO POSITION")
        move.setMinimumHeight(90)
        move.setFont(QFont("Arial", 20, QFont.Bold))
        move.clicked.connect(self.move_auto)
        layout.addWidget(move)

        stop = QPushButton("STOP MOVE")
        stop.setMinimumHeight(70)
        stop.setFont(QFont("Arial", 17, QFont.Bold))
        stop.setObjectName("StopButton")
        stop.clicked.connect(lambda: self.comm.send(pkt_stop()))
        layout.addWidget(stop)
        return w

    def diag_page(self):
        w, layout = self.page("DIAGNOSTICS")
        self.diag = QLabel("")
        self.diag.setObjectName("DiagText")
        self.diag.setAlignment(Qt.AlignTop)
        self.diag.setFont(QFont("Courier New", 15))
        layout.addWidget(self.diag)
        return w

    def alarms_page(self):
        w, layout = self.page("ALARMS")
        self.alarm_label = QLabel("No active alarms")
        self.alarm_label.setAlignment(Qt.AlignCenter)
        self.alarm_label.setFont(QFont("Arial", 28, QFont.Bold))
        layout.addWidget(self.alarm_label)

        reset = QPushButton("RESET ALARM")
        reset.setMinimumHeight(85)
        reset.setFont(QFont("Arial", 18, QFont.Bold))
        reset.clicked.connect(lambda: self.comm.send(pkt_reset_alarm()))
        layout.addWidget(reset)
        return w

    def settings_page(self):
        w, layout = self.page("SETTINGS")
        txt = QLabel("Panel Saw HMI v2.1\n\nNext planned features:\n• Password service mode\n• RS-485 port selection\n• Axis calibration\n• GreenBoard splash screen\n• Autostart on boot")
        txt.setAlignment(Qt.AlignCenter)
        txt.setFont(QFont("Arial", 20, QFont.Bold))
        layout.addWidget(txt)
        return w

    def move_auto(self):
        try:
            self.comm.send(pkt_move_abs(AXIS_FENCE, float(self.in_fence.text()), 80))
            self.comm.send(pkt_move_abs(AXIS_HEIGHT, float(self.in_height.text()), 15))
            self.comm.send(pkt_move_abs(AXIS_TILT, float(self.in_tilt.text()), 8))
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Enter valid numeric values.")

    def refresh(self):
        s = self.comm.status()
        self.clock.setText(datetime.now().strftime("%d/%m/%Y  %H:%M:%S"))

        self.v_state.setText(s.state)
        self.v_fence.setText(f"{s.fence_mm:.2f} mm")
        self.v_height.setText(f"{s.height_mm:.1f} mm")
        self.v_tilt.setText(f"{s.tilt_deg:.1f}°")
        self.v_safety.setText("OK" if s.estop_ok and s.guard_closed and s.servo_power else "NOT SAFE")
        self.v_alarm.setText(s.alarm if s.alarm else "None")
        self.alarm_label.setText(s.alarm if s.alarm else "No active alarms")

        self.diag.setText(
            f"Machine State       : {s.state}\n"
            f"Mode                : {s.mode}\n"
            f"RS-485 Link          : {'OK' if s.rs485_ok else 'FAULT'}\n\n"
            f"Fence Position       : {s.fence_mm:8.2f} mm\n"
            f"Fence Target         : {s.fence_target:8.2f} mm\n"
            f"Blade Height         : {s.height_mm:8.1f} mm\n"
            f"Blade Height Target  : {s.height_target:8.1f} mm\n"
            f"Blade Tilt           : {s.tilt_deg:8.1f} deg\n"
            f"Blade Tilt Target    : {s.tilt_target:8.1f} deg\n\n"
            f"E-stop OK            : {s.estop_ok}\n"
            f"Guard Closed         : {s.guard_closed}\n"
            f"Servo Power OK       : {s.servo_power}\n"
            f"Vacuum OK            : {s.vacuum_ok}\n"
            f"Saw Running          : {s.saw_running}\n"
        )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulate", action="store_true")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QWidget { background: #151a20; color: #f2f5f7; }
        #Nav { background: #0d1117; border-right: 2px solid #303845; }
        QPushButton {
            background: #26384c;
            color: white;
            border: 1px solid #4e6682;
            border-radius: 8px;
            padding: 8px;
        }
        QPushButton[active="true"] { background: #1976d2; }
        QPushButton:pressed { background: #5d789a; }
        #StopButton { background: #b3261e; }
        #Card {
            background: #1d2630;
            border: 2px solid #3b4b5b;
            border-radius: 12px;
            padding: 8px;
        }
        #MetricValue { color: #7CFF7C; }
        QLineEdit {
            background: #090d12;
            color: #00ff99;
            border: 2px solid #61758d;
            border-radius: 8px;
            padding: 8px;
        }
        #DiagText {
            background: #0a0d10;
            border: 2px solid #3b4b5b;
            border-radius: 8px;
            padding: 14px;
        }
    """)

    hmi = HMI(simulate=args.simulate)
    hmi.showFullScreen()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
