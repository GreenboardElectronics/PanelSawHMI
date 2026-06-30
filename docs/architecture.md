# Production Architecture

## Layers

- hmi/main.py: application shell and screen navigation
- hmi/core/state.py: machine state model
- hmi/core/controller.py: simulator/hardware backend interface
- hmi/widgets/: reusable display widgets
- protocol/: wire protocol packet creation
- config/: machine-specific settings
- data/: programs and alarm history

## Next hardware step

Add a SerialController class beside SimulatorController. This will communicate to the dsPIC controller through isolated RS-485.
