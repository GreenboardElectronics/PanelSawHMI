
from dataclasses import dataclass
import struct

START_BYTE = 0xA5

CMD_JOG = 0x10
CMD_MOVE_ABS = 0x11
CMD_STOP = 0x12
CMD_HOME = 0x13
CMD_RESET_ALARM = 0x14

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

@dataclass
class MachineStatus:
    state: str = "READY"
    mode: str = "MANUAL"
    estop_ok: bool = True
    guard_closed: bool = True
    servo_power: bool = True
    vacuum_ok: bool = True
    rs485_ok: bool = True
    saw_running: bool = False

    fence_mm: float = 1250.25
    fence_target: float = 1250.00
    height_mm: float = 72.0
    height_target: float = 75.0
    tilt_deg: float = 90.0
    tilt_target: float = 90.0

    alarm: str = ""

class Simulator:
    def __init__(self):
        self.status = MachineStatus()

    def update(self):
        return self.status

    def handle_packet(self, packet: bytes):
        if len(packet) < 4 or packet[0] != START_BYTE:
            return
        cmd = packet[1]
        payload = packet[3:-1]

        if cmd == CMD_MOVE_ABS and len(payload) >= 7:
            axis, target_um, speed = struct.unpack("<BiH", payload)
            value = target_um / 1000.0
            if axis == AXIS_FENCE:
                self.status.fence_target = value
                self.status.fence_mm = value
            elif axis == AXIS_HEIGHT:
                self.status.height_target = value
                self.status.height_mm = value
            elif axis == AXIS_TILT:
                self.status.tilt_target = value
                self.status.tilt_deg = value
            self.status.state = "POSITIONED"

        elif cmd == CMD_STOP:
            self.status.state = "STOPPED"

        elif cmd == CMD_HOME:
            self.status.fence_mm = 0.0
            self.status.fence_target = 0.0
            self.status.height_mm = 0.0
            self.status.height_target = 0.0
            self.status.tilt_deg = 90.0
            self.status.tilt_target = 90.0
            self.status.state = "HOMED"

        elif cmd == CMD_RESET_ALARM:
            self.status.alarm = ""
            self.status.state = "READY"
