# 🔌 Complete Wiring Guide & Verification

## Overview
This robot uses a **hybrid architecture**:
- **Raspberry Pi 5**: IR sensors, camera, YOLO detection
- **Arduino Uno**: Motor control, ultrasonic sensors, relay control
- **Connection**: USB serial (pi ↔ Arduino)

---

## 📋 Part 1: Raspberry Pi GPIO Wiring (BCM Mode)

### IR Line Sensors (3×)
These are **digital input sensors** that detect lines (black/white surfaces).

```
┌─────────────────────────┐
│   IR Sensor Module      │
├─────────────────────────┤
│ OUT  → GPIO 17 (LEFT)   │
│ OUT  → GPIO 27 (CENTER) │
│ OUT  → GPIO 22 (RIGHT)  │
│ VCC  → 3.3V or 5V*      │
│ GND  → Pi GND           │
└─────────────────────────┘

*Check your sensor module specs
```

**Verification:**
```bash
# Test IR sensors are readable
python3 -c "
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup([17, 27, 22], GPIO.IN)
for _ in range(10):
    print(f'LEFT={GPIO.input(17)} CENTER={GPIO.input(27)} RIGHT={GPIO.input(22)}')
    import time; time.sleep(0.1)
GPIO.cleanup()
"
```

---

## 📋 Part 2: Arduino Uno Wiring

### 🔌 Section A: 4× HC-SR04 Ultrasonic Sensors

| Sensor | TRIG Pin | ECHO Pin | VCC | GND |
|--------|----------|----------|-----|-----|
| FRONT  | D12      | A0       | 5V  | GND |
| LEFT   | D11      | A1       | 5V  | GND |
| RIGHT  | A2       | A3       | 5V  | GND |
| BACK   | A4       | A5       | 5V  | GND |

**Wiring Details:**
```
HC-SR04 Sensor:
  VCC ─────► Arduino 5V
  GND ─────► Arduino GND
  TRIG ────► Arduino TRIG pin (see table)
  ECHO ────► Arduino ECHO pin (see table)
```

**Why separate TRIG and ECHO?**
- TRIG: Digital output (triggers 10µs pulse)
- ECHO: Digital input (measures pulse duration = distance)

**Distance Calculation:**
```
Distance (cm) = (ECHO_time_µs × 340 m/s) / 2
            = ECHO_time_µs × 0.0173
```

**Verification:**
```cpp
// Quick test in Arduino IDE Serial Monitor
void testUltrasonic(int trig, int echo) {
  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);
  
  long duration = pulseIn(echo, HIGH, 30000);  // timeout 30ms
  float distance = duration * 0.0173;
  
  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.println(" cm");
}
```

---

### 🔌 Section B: Left Motor Driver (BTS7960 #1)

```
┌──────────────────────────────────────┐
│        BTS7960 Motor Driver #1       │
├──────────────────────────────────────┤
│ RPWM  → Arduino D3  (PWM)            │
│ LPWM  → Arduino D5  (PWM)            │
│ R_EN  → Arduino D2  (Digital)        │
│ L_EN  → Arduino D4  (Digital)        │
│ MOTOR OUT+ ─► Left Motor +           │
│ MOTOR OUT- ─► Left Motor -           │
│ GND   ─► Arduino GND                 │
│ VCC   ─► 12V Power Supply (motor)    │
└──────────────────────────────────────┘

Motor Control Logic:
┌────────────┬────────┬────────┬──────────┐
│ Direction  │ R_EN   │ L_EN   │ PWM Duty │
├────────────┼────────┼────────┼──────────┤
│ FORWARD    │ HIGH   │ LOW    │ RPWM     │
│ BACKWARD   │ LOW    │ HIGH   │ LPWM     │
│ BRAKE      │ HIGH   │ HIGH   │ 0        │
│ FREE COAST │ LOW    │ LOW    │ any      │
└────────────┴────────┴────────┴──────────┘
```

**Speed Control:**
- PWM 0-50: Very slow/stalled
- PWM 50-150: Slow control range
- PWM 150-255: Normal operation

---

### 🔌 Section C: Right Motor Driver (BTS7960 #2)

```
┌──────────────────────────────────────┐
│        BTS7960 Motor Driver #2       │
├──────────────────────────────────────┤
│ RPWM  → Arduino D9  (PWM)            │
│ LPWM  → Arduino D10 (PWM)            │
│ R_EN  → Arduino D7  (Digital)        │
│ L_EN  → Arduino D8  (Digital)        │
│ MOTOR OUT+ ─► Right Motor +          │
│ MOTOR OUT- ─► Right Motor -          │
│ GND   ─► Arduino GND                 │
│ VCC   ─► 12V Power Supply (motor)    │
└──────────────────────────────────────┘

Note: Pin D7, D8, D9, D10 for RIGHT motor
      Pin D2, D3, D4, D5 for LEFT motor
```

**Motor Testing:**
```cpp
// Forward: both motors 200/255 speed
digitalWrite(L_R_EN, HIGH); digitalWrite(L_L_EN, LOW);
digitalWrite(R_R_EN, HIGH); digitalWrite(R_L_EN, LOW);
analogWrite(L_RPWM, 200);
analogWrite(R_RPWM, 200);
delay(2000);

// Stop
analogWrite(L_RPWM, 0);
analogWrite(R_RPWM, 0);
```

---

### 🔌 Section D: Relay (D13)

```
┌─────────────────────────┐
│   5V Relay Module       │
├─────────────────────────┤
│ IN   → Arduino D13      │
│ VCC  → 5V (Arduino)     │
│ GND  → GND              │
│                         │
│ COM ─ (Common contact)  │
│ NO  ─ (Normally Open)   │
│ NC  ─ (Normally Closed) │
│                         │
│ Load wired through      │
│ COM/NO or COM/NC        │
└─────────────────────────┘
```

**Relay Logic:**
```cpp
// Relay ON (energized, load connected to COM-NO)
digitalWrite(RELAY_PIN, HIGH);

// Relay OFF (de-energized, load connected to COM-NC)
digitalWrite(RELAY_PIN, LOW);
```

---

## 🔋 Power Distribution

```
                    ┌─────────────────┐
                    │  Power Supply   │
                    │  (Typical: 12V) │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
      ┌───▼────┐      ┌──────▼──────┐      ┌──▼────┐
      │ Motor  │      │ Arduino VIN │      │ Pi    │
      │Driver  │      │ (12V input) │      │ (5V)  │
      │VCC     │      │             │      │ USB   │
      │(12V)   │      │ GND ─────┐  │      │Power  │
      └────────┘      └──────────┼──┘      └───────┘
                                 │
                            ┌────▼────┐
                            │ Common   │
                            │ Ground   │
                            └──────────┘
```

**Best Practices:**
- Use **separate 12V supply** for motors (not Pi USB power!)
- Pi draws ~3-5A, motors draw ~2-5A each
- Connect GND between Pi and Arduino
- Use capacitor (100µF) across motor power for noise filtering

---

## ✅ Wiring Checklist

### Before Powering On:
```
□ All motor driver RPWM/LPWM pins use PWM-capable pins (3,5,9,10)
□ All ultrasonic TRIG pins in OUTPUT mode
□ All ultrasonic ECHO pins in INPUT mode
□ IR sensors wired to GPIO 17, 27, 22 (BCM)
□ Common GND between Pi, Arduino, and motor drivers
□ Motor supply voltage correct (12V nominal)
□ Pi USB power separate from motor power
□ No loose connections or exposed wires
□ RELAY_PIN set to D13 (HIGH/LOW logic correct)
```

---

## 🧪 Testing Procedures

### Test 1: Verify Arduino-Pi Connection
```bash
# Check if Arduino appears
ls -la /dev/ttyUSB* /dev/ttyACM*

# Test serial communication
python3 << 'EOF'
import serial
import time

try:
    ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
    time.sleep(2)  # Wait for Arduino reset
    ser.write(b'PING\n')
    response = ser.readline().decode()
    print(f"✅ Arduino responds: {response}")
    ser.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
EOF
```

### Test 2: IR Sensors
```bash
python3 hardware_test.py  # Select IR sensor test
```

### Test 3: Ultrasonic Sensors (Arduino)
```cpp
// Upload this sketch to Arduino IDE to test ultrasonic
void setup() {
  Serial.begin(115200);
}

void loop() {
  // Test front sensor
  digitalWrite(12, HIGH);
  delayMicroseconds(10);
  digitalWrite(12, LOW);
  
  long duration = pulseIn(A0, HIGH, 30000);
  float distance = duration * 0.0173;
  
  Serial.print("FRONT: ");
  Serial.print(distance);
  Serial.println(" cm");
  
  delay(500);
}
```

### Test 4: Motor Control
```bash
python3 test_hardware.py  # Or run robot_main.py briefly
```

### Test 5: All Systems Together
```bash
# Final full system test
python3 robot_main.py

# Monitor logs
tail -f logs/robot.log
```

---

## 🐛 Troubleshooting

### Issue: Arduino Not Detected
```bash
# Solution 1: Check permissions
sudo usermod -a -G dialout $USER
groups $USER  # Should show 'dialout'

# Solution 2: Try different port
ls /dev/tty*  # Look for ttyUSB0, ttyACM0, etc.
# Update ARDUINO_PORT in config.py

# Solution 3: Reset Arduino
# Press RST button on Arduino or add reset circuit
```

### Issue: IR Sensors Always Return 1
```
Problem: Sensor reads "no line" all the time
Solution:
  1. Check VCC (should be 3.3V or 5V per module)
  2. Place sensor on black line
  3. Adjust potentiometer on sensor module
  4. Verify GPIO pins in config.py
  5. Run: python3 calibrate.py → option 1
```

### Issue: Ultrasonic Returns 0 or 999999
```
Problem: Distance measurement fails
Solution:
  1. Verify TRIG and ECHO pin connections
  2. Ensure TRIG is OUTPUT, ECHO is INPUT
  3. Check timeout value (ULTRASONIC_TIMEOUT = 30000µs)
  4. Test sensor separately with simple Arduino sketch
  5. Check sensor wiring (VCC/GND polarity)
```

### Issue: Motors Don't Spin
```
Problem: Motors receive PWM but don't move
Solution:
  1. Verify motor power supply (12V, 2+ amps)
  2. Check R_EN and L_EN pins connected to D2,D4,D7,D8
  3. Ensure PWM frequency is correct (1kHz typical)
  4. Test with simple digitalWrite HIGH/LOW first
  5. Swap motor polarity if spinning wrong direction
```

### Issue: Arduino Sketch Upload Fails
```
Problem: "Serial port not found" in Arduino IDE
Solution:
  1. Install CH340 driver (common on Arduino clones)
  2. Select correct board: "Arduino Uno"
  3. Select correct port: /dev/ttyUSB0 (Linux/Mac)
  4. Check USB cable (must be data cable, not charge-only)
```

---

## 📊 Pin Summary Table

| Component | Pin(s) | Type | Purpose |
|-----------|--------|------|---------|
| **Ultrasonic FRONT** | D12, A0 | Digital OUT/IN | Distance sensor |
| **Ultrasonic LEFT** | D11, A1 | Digital OUT/IN | Distance sensor |
| **Ultrasonic RIGHT** | A2, A3 | Digital OUT/IN | Distance sensor |
| **Ultrasonic BACK** | A4, A5 | Digital OUT/IN | Distance sensor |
| **Left Motor RPWM** | D3 | PWM | Forward speed |
| **Left Motor LPWM** | D5 | PWM | Backward speed |
| **Left Motor R_EN** | D2 | Digital | Forward enable |
| **Left Motor L_EN** | D4 | Digital | Backward enable |
| **Right Motor RPWM** | D9 | PWM | Forward speed |
| **Right Motor LPWM** | D10 | PWM | Backward speed |
| **Right Motor R_EN** | D7 | Digital | Forward enable |
| **Right Motor L_EN** | D8 | Digital | Backward enable |
| **Relay** | D13 | Digital | Relay control |
| **Camera** | CSI Ribbon | Serial | Image capture |
| **IR LEFT** | GPIO 17 (BCM) | Digital | Line detect |
| **IR CENTER** | GPIO 27 (BCM) | Digital | Line detect |
| **IR RIGHT** | GPIO 22 (BCM) | Digital | Line detect |

---

## 📖 References

- **HC-SR04 Datasheet**: Time-of-flight ultrasonic sensor
- **BTS7960 Datasheet**: H-bridge motor driver
- **Arduino Uno Pin Map**: https://www.arduino.cc/en/uploads/Main/ArduinoUno_R3_Front_450px_RoHS.pdf
- **RPi GPIO BCM Reference**: https://pinout.xyz/

---

**Last Updated:** 2026-05-20  
**Version:** 1.0 - Complete Wiring Guide
