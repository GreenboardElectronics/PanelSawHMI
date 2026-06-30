
from dataclasses import dataclass, field
import time

@dataclass
class AxisState:
    label: str
    position: float
    target: float
    unit: str
    enabled: bool = True
    homed: bool = True
    fault: bool = False

@dataclass
class SafetyState:
    estop_ok: bool = True
    blade_guard_closed: bool = True
    rear_guard_closed: bool = True
    vacuum_ok: bool = True
    servo_power_ok: bool = True

@dataclass
class IOState:
    inputs: dict = field(default_factory=lambda: {
        "E-STOP OK": True,
        "GUARD CLOSED": True,
        "REAR GUARD": True,
        "VACUUM OK": True,
        "SERVO POWER": True,
        "FENCE HOME": False,
        "HEIGHT HOME": False,
        "TILT HOME": True,
    })
    outputs: dict = field(default_factory=lambda: {
        "SERVO ENABLE": True,
        "SAW REQUEST": False,
        "VACUUM START": False,
        "ALARM BEACON": False,
        "BUZZER": False,
        "FENCE BRAKE": False,
        "HEIGHT BRAKE": False,
        "TILT BRAKE": False,
    })

@dataclass
class MachineState:
    mode: str = "AUTO"
    state: str = "READY"
    cycle: str = "IDLE"
    program: str = "None"
    operator: str = "Operator"
    access_level: str = "Operator"
    runtime_seconds: int = 955
    panel_count: int = 0
    cut_count: int = 0
    rs485_ok: bool = True
    io_ok: bool = True
    sd_ok: bool = True
    controller_count: int = 4
    saw_running: bool = False

    fence: AxisState = field(default_factory=lambda: AxisState("Fence Position", 1250.25, 1250.00, "mm"))
    height: AxisState = field(default_factory=lambda: AxisState("Blade Height", 78.2, 78.0, "mm"))
    tilt: AxisState = field(default_factory=lambda: AxisState("Blade Tilt", 90.0, 90.0, "°"))
    safety: SafetyState = field(default_factory=SafetyState)
    io: IOState = field(default_factory=IOState)

    active_alarm: str = ""
    alarm_history: list = field(default_factory=list)

    @property
    def runtime(self):
        h = self.runtime_seconds // 3600
        m = (self.runtime_seconds % 3600) // 60
        s = self.runtime_seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    @property
    def safe_to_run(self):
        return (
            self.safety.estop_ok and
            self.safety.blade_guard_closed and
            self.safety.rear_guard_closed and
            self.safety.vacuum_ok and
            self.safety.servo_power_ok
        )
