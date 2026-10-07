# Project Notes and Variant Guide

These notes reconcile the implementation variants and documentation already in this repository. They are intended to be read with `README.md`, `SETUP-PI.md`, `DEPLOYMENT.md`, and `WIRING_GUIDE.md`.

## Current status

The repository is an experimental robot-control prototype, not a validated production system. It contains two materially different control architectures, and the existing guides do not consistently select the same one. Choose one architecture, wiring plan, entry point, and dependency set before applying power.

## Two control architectures

### 1. Hybrid Raspberry Pi + Arduino

This is the architecture described by `WIRING_GUIDE.md` and used by `robot_pi.py`:

```text
Camera -> Raspberry Pi 5 -> YOLO
                     |
              USB serial, 115200
                     |
                Arduino Uno
              /      |       \
        BTS7960s  4 x HC-SR04  relay

Pi GPIO17/27/22 -> three IR line sensors (documented wiring only;
                                      robot_pi.py does not read them)
```

Relevant files:

- `robot_pi.py` - vision-driven controller;
- `camera_handler.py` - DroidCam/local camera handling;
- `arduino_interface.py` - Pi serial client;
- `arduino_uno/robot_control.ino` - Uno motor, ultrasonic, and relay firmware;
- `requirements-pi.txt` - includes `pyserial` and Pi-oriented dependencies;
- `SETUP-PI.md` and `WIRING_GUIDE.md` - closest documentation match.

### 2. Pi-direct GPIO

`robot_main.py` directly configures IR, motor-driver, ultrasonic, and buzzer GPIO on the Pi. It does not use `arduino_interface.py` or the Uno sketch.

This path is inconsistent with the current hybrid wiring guide: several values in `config.py` are explicitly documented as Arduino pins but are reused as BCM GPIO numbers by `robot_main.py`. The top-level README and `DEPLOYMENT.md` refer to this entry point, while `SETUP-PI.md` refers to `robot_pi.py`. Do not connect hardware using one guide and execute the other architecture.

For the checked-in hybrid wiring, `robot_pi.py` is the logically matching entry point. That does not mean it is safe to deploy without addressing the gaps below.

Despite the hybrid wiring guide assigning three IR sensors to Pi GPIO17/27/22, `robot_pi.py` does not import a GPIO module or read those sensors. Its motion decisions come from camera/YOLO detections and serial commands. The wired IR inputs therefore provide no line-following or safety behavior in this entry point.

## Configuration that must be reviewed

`config.py` currently defaults to:

| Setting | Value |
| --- | --- |
| Camera type | `droidcam` |
| DroidCam URL | `http://192.168.1.47:4747/video` |
| Arduino port | `/dev/ttyACM1` |
| Arduino rate | 115200 baud |
| Pi IR pins, BCM | 17, 27, 22 |
| Pi buzzer pin, BCM | 26 |
| Model path | `models/best.pt` |
| Base motor speed | 200 on a 0-255 scale |
| Obstacle threshold | 20 cm |
| Detection confidence | 0.5 |

Email addresses and password are placeholders, and email alerts are disabled. Do not commit real credentials; load secrets from the environment or a file excluded from version control if email is implemented.

## Model location and interpretation

A `best.pt` file is committed at the repository root. The configured path, however, is `models/best.pt`. No tracked model exists at that configured location. Because `config.py` creates an empty `models` directory at import time, a fresh run still fails to load the checked-in model unless the path or file placement is reconciled.

Choose one explicit approach before running:

- update `MODEL_PATH` to `PROJECT_DIR / "best.pt"`; or
- place the intended model at `models/best.pt` and document how it is obtained.

The model's dataset, class map, training procedure, validation results, checksum, and license are not documented. Inspect those before trusting the artifact.

`robot_pi.py` assigns `detection_class = 14` in its constructor but never uses that value to filter predictions. Its detection loop accepts every bounding box above the confidence threshold as a pigeon. This only behaves as intended for a verified single-class model. A generic COCO model or another multiclass model requires explicit class-ID/name filtering.

`DEPLOYMENT.md` also gives a `best_int8.tflite` example, while the active configuration and committed artifact use PyTorch `.pt`. Treat that as an older alternative, not the checked-in default, and validate loader compatibility before selecting it.

## Hybrid serial protocol

`arduino_interface.py` and `arduino_uno/robot_control.ino` use newline-terminated, comma-separated ASCII:

| Pi command | Uno action |
| --- | --- |
| `MOV,leftSpeed,rightSpeed,direction` | Drive both motors; direction is `1`, `-1`, or `0` |
| `TURN,speed,direction` | Pivot right for `1` or left otherwise |
| `STOP` | Stop both motors |
| `RELAY,1` / `RELAY,0` | Turn the relay on/off |
| `SENSORS` | Return `SENSORS,front,left,right,back` |
| `STATUS` | Return motor-speed status |

The Uno also emits acknowledgements such as `MOV,...`, `TURN,RIGHT`, `STOP,OK`, `RELAY,ON`, and `ERROR,Unknown command`. Both ends must remain at 115200 baud.

## Safety-critical gaps in the hybrid path

These behaviors follow from the checked-in source and should be resolved before a mobile test:

1. **No serial motor watchdog.** The Uno keeps applying the last motor state if Pi commands stop. A Pi crash, USB disconnect, or blocked process can therefore leave the robot moving. Add a firmware command timeout that forces both motors and, where appropriate, the relay to a safe state.
2. **Obstacle data is not actively polled by `robot_pi.py`.** The Uno updates internal HC-SR04 readings, but only transmits them after a `SENSORS` command. The Pi interface initializes all cached distances to `0.0`, and `robot_pi.py` does not call `read_sensors()`. As written, `check_obstacles()` can operate on stale/default data, so the documented obstacle stop must not be assumed to work.
3. **Detection is not class-filtered.** Every model detection above the threshold can command motion toward the box.
4. **Camera loss does not stop motion.** `robot_pi.py` logs a warning if initial camera connection fails and proceeds to Arduino setup. During the normal loop, a failed frame read sleeps and continues without sending `STOP`. Combined with the Uno's missing motor watchdog, the last motor command can persist indefinitely after the stream is lost.
5. **Motor control has no local obstacle interlock.** The Uno firmware measures distance but does not independently block motor commands based on it; avoidance depends on the Pi receiving and acting on sensor data.
6. **Relay safety is application-dependent.** Confirm active-high/active-low behavior and define a safe power-on, disconnect, exception, and shutdown state for the actual load.
7. **Configured watchdog/runtime values are inactive.** `config.py` declares `ENABLE_WATCHDOG`, `WATCHDOG_TIMEOUT`, and `MAX_RUNTIME`, but `robot_pi.py` does not use them. They provide no protection in the hybrid runtime.

Software checks are not a substitute for a physical emergency cutoff, current limiting, fusing, guarded moving parts, and a clear test area.

## Dependency and guide differences

- `requirements.txt` supports the older Pi-direct path and does not list `pyserial`.
- `requirements-pi.txt` includes `pyserial` for the hybrid path, but pins a different OpenCV/Torch combination.
- `README.md` and `DEPLOYMENT.md` launch `robot_main.py`.
- `SETUP-PI.md` launches `robot_pi.py`.
- `WIRING_GUIDE.md` describes the hybrid Pi/Uno wiring but some examples still tell the user to run `robot_main.py`.
- Camera setup instructions mix legacy Raspberry Pi camera commands with HTTP DroidCam use.

Create and test one environment for the selected architecture rather than installing both requirement files indiscriminately.

## Hybrid commissioning sequence

1. Keep the motor supply and relay load disconnected.
2. Upload `arduino_uno/robot_control.ino` to the Uno.
3. Verify each HC-SR04, each BTS7960 input, and relay polarity separately.
4. Confirm a common signal ground and use a motor supply separate from Pi logic power.
5. Check which `/dev/ttyACM*` device belongs to the Uno and update `ARDUINO_PORT`.
6. Reconcile `MODEL_PATH`, inspect the model's class names, and add class filtering.
7. Fix sensor polling and camera-loss stopping, then add an Arduino motor watchdog.
8. Validate the DroidCam URL from the Pi and keep the stream on a trusted network.
9. Run protocol tests with motors disconnected.
10. Secure the chassis with wheels raised; test stop, forward, reverse, turning, process termination, USB removal, missing camera frames, invalid ultrasonic readings, and relay shutdown.
11. Perform the first floor test at a reduced speed with a physical power cutoff in reach.

## Pin ownership for the hybrid build

Under the hybrid wiring guide, the Pi is assigned the three IR inputs plus camera/network/USB functions. The current `robot_pi.py` runtime ignores those IR inputs. The Uno owns the BTS7960 inputs, four HC-SR04 interfaces, and relay:

- left BTS7960: D3, D5, D2, D4;
- right BTS7960: D9, D10, D7, D8;
- front HC-SR04: D12/A0;
- left HC-SR04: D11/A1;
- right HC-SR04: A2/A3;
- back HC-SR04: A4/A5;
- relay: D13.

Refer to `WIRING_GUIDE.md` for the complete table, but verify the actual module logic levels and power requirements against their datasheets.

## Documentation and release gaps

- Hardware behavior has not been demonstrated by automated or hardware-in-the-loop tests in this repository.
- The tests and calibration utilities span both architectures and should not be assumed interchangeable.
- Logs and runtime-created directories are not a substitute for a reproducible test report.
- Model provenance and evaluation evidence are absent.
- The README says “MIT License,” but no `LICENSE` file is present. Do not assume redistribution or reuse terms until the author adds the actual license text; the model may require separate terms.
- “Production-ready” claims in existing documentation are not supported by the unresolved path, protocol, and safety issues above.

Before a release, select and document a canonical architecture, remove or archive conflicting instructions, add a fail-safe firmware watchdog, add model metadata, run loss-of-communication and stopping-distance tests, and publish the exact supported software/hardware versions.
