
import time
from hmi.core.state import MachineState
from protocol.panel_saw_protocol import (
    START_BYTE, CMD_MOVE_ABS, CMD_STOP, CMD_HOME, CMD_RESET_ALARM,
    CMD_START_CYCLE, AXIS_FENCE, AXIS_HEIGHT, AXIS_TILT
)
import struct

class MachineController:
    def status(self) -> MachineState:
        raise NotImplementedError
    def send(self, packet: bytes):
        raise NotImplementedError

class SimulatorController(MachineController):
    def __init__(self):
        self._state = MachineState()
        self._last_tick = time.time()

    def status(self):
        now = time.time()
        if now - self._last_tick >= 1:
            self._state.runtime_seconds += int(now - self._last_tick)
            self._last_tick = now
        return self._state

    def send(self, packet: bytes):
        if len(packet) < 4 or packet[0] != START_BYTE:
            return
        cmd = packet[1]
        payload = packet[3:-1]

        if cmd == CMD_MOVE_ABS and len(payload) >= 7:
            axis, target_um, speed = struct.unpack("<BiH", payload)
            value = target_um / 1000.0
            if axis == AXIS_FENCE:
                self._state.fence.target = value
                self._state.fence.position = value
            elif axis == AXIS_HEIGHT:
                self._state.height.target = value
                self._state.height.position = value
            elif axis == AXIS_TILT:
                self._state.tilt.target = value
                self._state.tilt.position = value
            self._state.state = "POSITIONED"
            self._state.cycle = "IDLE"

        elif cmd == CMD_START_CYCLE:
            if self._state.safe_to_run:
                self._state.state = "RUNNING"
                self._state.cycle = "CUTTING"
                self._state.saw_running = True
                self._state.cut_count += 1
                self._state.io.outputs["SAW REQUEST"] = True
                self._state.io.outputs["VACUUM START"] = True
            else:
                self.raise_alarm("Safety chain not ready")

        elif cmd == CMD_STOP:
            self._state.state = "STOPPED"
            self._state.cycle = "STOPPED"
            self._state.saw_running = False
            self._state.io.outputs["SAW REQUEST"] = False

        elif cmd == CMD_HOME:
            self._state.fence.position = 0.0
            self._state.fence.target = 0.0
            self._state.height.position = 0.0
            self._state.height.target = 0.0
            self._state.tilt.position = 90.0
            self._state.tilt.target = 90.0
            self._state.state = "HOMED"

        elif cmd == CMD_RESET_ALARM:
            self._state.active_alarm = ""
            self._state.state = "READY"
            self._state.cycle = "IDLE"
            self._state.io.outputs["ALARM BEACON"] = False
            self._state.io.outputs["BUZZER"] = False

    def raise_alarm(self, text):
        stamp = time.strftime("%d/%m/%Y %H:%M:%S")
        self._state.active_alarm = text
        self._state.alarm_history.insert(0, f"{stamp}  {text}")
        self._state.state = "ALARM"
        self._state.io.outputs["ALARM BEACON"] = True
        self._state.io.outputs["BUZZER"] = True
