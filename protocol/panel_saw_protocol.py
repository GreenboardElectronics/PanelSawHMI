
from dataclasses import dataclass, field
import struct
import time

START_BYTE = 0xA5

CMD_JOG = 0x10
CMD_MOVE_ABS = 0x11
CMD_STOP = 0x12
CMD_HOME = 0x13
CMD_RESET_ALARM = 0x14
CMD_START_CYCLE = 0x15

AXIS_FENCE = 0
AXIS_HEIGHT = 1
AXIS_TILT = 2

def crc8(data: bytes) -> int:
    crc = 0
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = ((crc << 1) ^ 0x07) & 0xFF if (crc & 0x80) else ((crc << 1) & 0xFF)
    return crc

def make_packet(cmd: int, payload: bytes = b"") -> bytes:
    body = bytes([cmd & 0xFF, len(payload)]) + payload
    return bytes([START_BYTE]) + body + bytes([crc8(body)])

def pkt_jog(axis: int, direction: int, speed_mm_s: float):
    return make_packet(CMD_JOG, struct.pack("<BbH", axis, direction, int(speed_mm_s * 100)))

def pkt_move_abs(axis: int, target_mm: float, speed_mm_s: float):
    return make_packet(CMD_MOVE_ABS, struct.pack("<BiH", axis, int(target_mm * 1000), int(speed_mm_s * 100)))

def pkt_stop(axis: int = 255):
    return make_packet(CMD_STOP, struct.pack("<B", axis))

def pkt_home(axis: int = 255):
    return make_packet(CMD_HOME, struct.pack("<B", axis))

def pkt_reset_alarm():
    return make_packet(CMD_RESET_ALARM)

def pkt_start_cycle():
    return make_packet(CMD_START_CYCLE)

@dataclass
class AxisStatus:
    name: str
    position: float
    target: float
    unit: str
    enabled: bool = True
    homed: bool = True
    fault: bool = False

@dataclass
class MachineStatus:
    state: str = "READY"
    mode: str = "AUTO"
    cycle: str = "IDLE"
    program: str = "None"
    operator: str = "Operator"
    access_level: str = "Operator"
    runtime_seconds: int = 942
    panel_count: int = 0
    cut_count: int = 0

    estop_ok: bool = True
    blade_guard_closed: bool = True
    rear_guard_closed: bool = True
    vacuum_ok: bool = True
    io_ok: bool = True
    sd_ok: bool = True
    rs485_ok: bool = True
    controller_count: int = 4
    saw_running: bool = False
    servo_power_ok: bool = True

    fence: AxisStatus = field(default_factory=lambda: AxisStatus("Fence X", 1250.25, 1250.00, "mm"))
    height: AxisStatus = field(default_factory=lambda: AxisStatus("Blade Height", 78.2, 78.0, "mm"))
    tilt: AxisStatus = field(default_factory=lambda: AxisStatus("Blade Tilt", 90.0, 90.0, "°"))

    alarm: str = ""
    alarm_history: list = field(default_factory=list)

    @property
    def runtime(self):
        h = self.runtime_seconds // 3600
        m = (self.runtime_seconds % 3600) // 60
        s = self.runtime_seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

class Simulator:
    def __init__(self):
        self.status = MachineStatus()
        self.last_tick = time.time()

    def update(self):
        now = time.time()
        if now - self.last_tick >= 1:
            self.status.runtime_seconds += int(now - self.last_tick)
            self.last_tick = now
        return self.status

    def add_alarm(self, text):
        self.status.alarm = text
        self.status.alarm_history.insert(0, f"{time.strftime('%H:%M:%S')} - {text}")

    def handle_packet(self, packet: bytes):
        if len(packet) < 4 or packet[0] != START_BYTE:
            return
        cmd = packet[1]
        payload = packet[3:-1]

        if cmd == CMD_MOVE_ABS and len(payload) >= 7:
            axis, target_um, speed = struct.unpack("<BiH", payload)
            value = target_um / 1000.0
            if axis == AXIS_FENCE:
                self.status.fence.target = value
                self.status.fence.position = value
            elif axis == AXIS_HEIGHT:
                self.status.height.target = value
                self.status.height.position = value
            elif axis == AXIS_TILT:
                self.status.tilt.target = value
                self.status.tilt.position = value
            self.status.state = "POSITIONED"
            self.status.cycle = "IDLE"

        elif cmd == CMD_START_CYCLE:
            self.status.state = "RUNNING"
            self.status.cycle = "CUTTING"
            self.status.saw_running = True
            self.status.cut_count += 1

        elif cmd == CMD_STOP:
            self.status.state = "STOPPED"
            self.status.cycle = "STOPPED"
            self.status.saw_running = False

        elif cmd == CMD_HOME:
            self.status.fence.position = 0.0
            self.status.fence.target = 0.0
            self.status.height.position = 0.0
            self.status.height.target = 0.0
            self.status.tilt.position = 90.0
            self.status.tilt.target = 90.0
            self.status.state = "HOMED"

        elif cmd == CMD_RESET_ALARM:
            self.status.alarm = ""
            self.status.state = "READY"
            self.status.cycle = "IDLE"
            self.status.saw_running = False
