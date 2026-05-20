/*
 * Robot Pigeon Detection - Arduino Uno Control
 * Controls motors, ultrasonic sensors, and relay via BTS7960 motor driver
 * 
 * Hardware:
 * - BTS7960 Motor Driver (2× for left/right motors)
 * - 4× HC-SR04 Ultrasonic Sensors
 * - Relay on pin 13
 * - Serial communication with Pi 5
 */

// ===================== PIN CONFIGURATION =====================

// Left Motor (BTS7960) - Motor 1
#define L_RPWM 3    // PWM pin for forward
#define L_LPWM 5    // PWM pin for backward
#define L_R_EN 2    // Enable pin
#define L_L_EN 4    // Enable pin

// Right Motor (BTS7960) - Motor 2
#define R_RPWM 9    // PWM pin for forward
#define R_LPWM 10   // PWM pin for backward
#define R_R_EN 7    // Enable pin
#define R_L_EN 8    // Enable pin

// Ultrasonic Sensors (HC-SR04)
#define SR04_FRONT_TRIG 12
#define SR04_FRONT_ECHO A0
#define SR04_LEFT_TRIG 11
#define SR04_LEFT_ECHO A1
#define SR04_RIGHT_TRIG A2
#define SR04_RIGHT_ECHO A3
#define SR04_BACK_TRIG A4
#define SR04_BACK_ECHO A5

// Relay
#define RELAY_PIN 13

// ===================== CONSTANTS =====================

#define MOTOR_MAX_SPEED 255
#define SERIAL_BAUD 115200
#define ULTRASONIC_TIMEOUT 30000  // 30ms timeout
#define SENSOR_UPDATE_INTERVAL 100  // 100ms

// ===================== GLOBAL VARIABLES =====================

unsigned long lastSensorUpdate = 0;

struct Motor {
  int rpwm;
  int lpwm;
  int ren;
  int len;
  int speed;
  int direction;  // 1=forward, -1=backward, 0=stop
};

struct Ultrasonic {
  int trig;
  int echo;
  float distance;
};

Motor leftMotor = {L_RPWM, L_LPWM, L_R_EN, L_L_EN, 0, 0};
Motor rightMotor = {R_RPWM, R_LPWM, R_R_EN, R_L_EN, 0, 0};

Ultrasonic sr04[4] = {
  {SR04_FRONT_TRIG, SR04_FRONT_ECHO, 0},
  {SR04_LEFT_TRIG, SR04_LEFT_ECHO, 0},
  {SR04_RIGHT_TRIG, SR04_RIGHT_ECHO, 0},
  {SR04_BACK_TRIG, SR04_BACK_ECHO, 0}
};

// ===================== SETUP =====================

void setup() {
  Serial.begin(SERIAL_BAUD);
  
  // Motor pins
  pinMode(leftMotor.rpwm, OUTPUT);
  pinMode(leftMotor.lpwm, OUTPUT);
  pinMode(leftMotor.ren, OUTPUT);
  pinMode(leftMotor.len, OUTPUT);
  
  pinMode(rightMotor.rpwm, OUTPUT);
  pinMode(rightMotor.lpwm, OUTPUT);
  pinMode(rightMotor.ren, OUTPUT);
  pinMode(rightMotor.len, OUTPUT);
  
  // Ultrasonic pins
  for (int i = 0; i < 4; i++) {
    pinMode(sr04[i].trig, OUTPUT);
    pinMode(sr04[i].echo, INPUT);
  }
  
  // Relay
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
  
  // Stop motors
  stopMotors();
  
  Serial.println("🤖 Arduino Ready");
  Serial.println("Format: CMD,arg1,arg2");
  Serial.println("Commands: MOV, STOP, RELAY, STATUS");
}

// ===================== MOTOR CONTROL =====================

void setMotorSpeed(Motor *motor, int speed, int direction) {
  motor->speed = constrain(speed, 0, MOTOR_MAX_SPEED);
  motor->direction = direction;
  
  // Enable motor
  digitalWrite(motor->ren, HIGH);
  digitalWrite(motor->len, HIGH);
  
  if (direction == 1) {  // Forward
    analogWrite(motor->rpwm, motor->speed);
    analogWrite(motor->lpwm, 0);
  } 
  else if (direction == -1) {  // Backward
    analogWrite(motor->rpwm, 0);
    analogWrite(motor->lpwm, motor->speed);
  } 
  else {  // Stop
    analogWrite(motor->rpwm, 0);
    analogWrite(motor->lpwm, 0);
  }
}

void moveRobot(int leftSpeed, int rightSpeed, int direction) {
  // direction: 1=forward, -1=backward, 0=stop
  setMotorSpeed(&leftMotor, leftSpeed, direction);
  setMotorSpeed(&rightMotor, rightSpeed, direction);
}

void stopMotors() {
  setMotorSpeed(&leftMotor, 0, 0);
  setMotorSpeed(&rightMotor, 0, 0);
}

void turnLeft(int speed) {
  setMotorSpeed(&leftMotor, speed, -1);   // Left backward
  setMotorSpeed(&rightMotor, speed, 1);   // Right forward
}

void turnRight(int speed) {
  setMotorSpeed(&leftMotor, speed, 1);    // Left forward
  setMotorSpeed(&rightMotor, speed, -1);  // Right backward
}

// ===================== ULTRASONIC SENSOR =====================

float measureDistance(Ultrasonic *sensor) {
  // Send 10µs pulse
  digitalWrite(sensor->trig, LOW);
  delayMicroseconds(2);
  digitalWrite(sensor->trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(sensor->trig, LOW);
  
  // Measure echo pulse
  unsigned long pulseTime = pulseIn(sensor->echo, HIGH, ULTRASONIC_TIMEOUT);
  
  if (pulseTime == 0) {
    return -1.0;  // Timeout
  }
  
  // Distance = (time × speed of sound) / 2
  // Speed of sound = 343 m/s = 0.0343 cm/µs
  float distance = (pulseTime * 0.0343) / 2.0;
  
  return distance;
}

void updateSensors() {
  if (millis() - lastSensorUpdate < SENSOR_UPDATE_INTERVAL) {
    return;
  }
  lastSensorUpdate = millis();
  
  for (int i = 0; i < 4; i++) {
    sr04[i].distance = measureDistance(&sr04[i]);
  }
}

void printSensorStatus() {
  Serial.print("SENSORS,");
  for (int i = 0; i < 4; i++) {
    Serial.print(sr04[i].distance, 2);
    if (i < 3) Serial.print(",");
  }
  Serial.println();
}

// ===================== RELAY CONTROL =====================

void setRelay(boolean state) {
  digitalWrite(RELAY_PIN, state ? HIGH : LOW);
  Serial.print("RELAY,");
  Serial.println(state ? "ON" : "OFF");
}

// ===================== SERIAL COMMUNICATION =====================

void processCommand(String cmd) {
  int commaIndex = cmd.indexOf(',');
  String command = cmd.substring(0, commaIndex);
  String args = cmd.substring(commaIndex + 1);
  
  if (command == "MOV") {
    // MOV,leftSpeed,rightSpeed,direction (1=forward, -1=backward)
    int comma1 = args.indexOf(',');
    int comma2 = args.indexOf(',', comma1 + 1);
    
    int leftSpeed = args.substring(0, comma1).toInt();
    int rightSpeed = args.substring(comma1 + 1, comma2).toInt();
    int direction = args.substring(comma2 + 1).toInt();
    
    moveRobot(leftSpeed, rightSpeed, direction);
    Serial.print("MOV,");
    Serial.print(leftSpeed);
    Serial.print(",");
    Serial.print(rightSpeed);
    Serial.print(",");
    Serial.println(direction);
  }
  
  else if (command == "TURN") {
    // TURN,speed,direction (1=right, -1=left)
    int comma = args.indexOf(',');
    int speed = args.substring(0, comma).toInt();
    int dir = args.substring(comma + 1).toInt();
    
    if (dir == 1) {
      turnRight(speed);
      Serial.println("TURN,RIGHT");
    } else {
      turnLeft(speed);
      Serial.println("TURN,LEFT");
    }
  }
  
  else if (command == "STOP") {
    stopMotors();
    Serial.println("STOP,OK");
  }
  
  else if (command == "RELAY") {
    // RELAY,1 or RELAY,0
    boolean state = args.toInt();
    setRelay(state);
  }
  
  else if (command == "STATUS") {
    Serial.print("STATUS,LEFT:");
    Serial.print(leftMotor.speed);
    Serial.print(",RIGHT:");
    Serial.print(rightMotor.speed);
    Serial.println();
  }
  
  else if (command == "SENSORS") {
    printSensorStatus();
  }
  
  else {
    Serial.println("ERROR,Unknown command");
  }
}

// ===================== MAIN LOOP =====================

void loop() {
  // Update sensors periodically
  updateSensors();
  
  // Check for serial commands
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command.length() > 0) {
      processCommand(command);
    }
  }
}
