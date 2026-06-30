
import struct

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
