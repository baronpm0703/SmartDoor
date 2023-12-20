#include <WebServer.h>
#include <WiFi.h>
#include <esp32cam.h>
#include <Arduino.h>
#include <Firebase_ESP_Client.h>
//Provide the token generation process info.
#include "addons/TokenHelper.h"
//Provide the RTDB payload printing info and other helper functions.
#include "addons/RTDBHelper.h"
#include <ESP32Servo.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
 
const char* WIFI_SSID = "HaXu";
const char* WIFI_PASS = "sonha0203";
//--------------------------------------------------------------------------------------------------
//Pins define
//Pin 0, 16 FAIL
#define ultraTrigPin 12
#define ultraEchoPin 13
#define servoPin 15
#define lcdSdaPin 2
#define lcdSclPin 14
#define buzzerPin 4
// #define ledPin 14
// #define pirPin 14
// #define buttonPin 13

//--------------------------------------------------------------------------------------------------
// Camera
WebServer server(80);

static auto loRes = esp32cam::Resolution::find(320, 240);
static auto midRes = esp32cam::Resolution::find(350, 530);
static auto hiRes = esp32cam::Resolution::find(800, 600);
//--------------------------------------------------------------------------------------------------

//--------------------------------------------------------------------------------------------------
// Firebase
// Insert Firebase project API Key
#define API_KEY "AIzaSyDjFMvE_kklNMo-laMwK6oKAW7HejrhCzk"

// Insert RTDB URLefine the RTDB URL */
#define DATABASE_URL "https://node-69d5e-default-rtdb.asia-southeast1.firebasedatabase.app" 

//Define Firebase Data object
FirebaseData fbdo;
FirebaseAuth auth;
FirebaseConfig config;

unsigned long getDataPrevMillis = 0;
unsigned long sendDataPrevMillis = 0;
String cameraIPPath = "/CameraIP";
String ultraValuePath = "/Sensor/Ultrasonic";
String buzzerRealityPath = "/Warning/Reality";
String buzzerExpectationPath = "/Warning/Expectation";
String doorRealityPath = "/Door/Reality";
String doorExpectationPath = "/Door/Expectation";
String ledExpectationPath = "/Led/Expectation";
String ledRealityPath = "/Led/Reality";
String buttonPath = "/Button/State";
String pirPath = "/Sensor/PIR";
String lcdNameExpectationPath = "/Lcd/nameExpectation";
String lcdNameRealityPath = "/Lcd/nameReality";
String lcdGestureExpectationPath = "/Lcd/gestureExpectation";
String lcdGestureRealityPath = "/Lcd/gestureReality";
String lcdGestureStateExpectationPath = "/Lcd/stateExpectation";
String lcdGestureStateRealityPath = "/Lcd/stateReality";
bool signupOK = false;
//--------------------------------------------------------------------------------------------------

//--------------------------------------------------------------------------------------------------
//Device variable
// Ultrasonic
float ultraValue = 0;
unsigned long sendUltraValuePrevMillis = 0;

//--------------------------------------------------------------------------------------------------
// PIR
bool pirValue = false;
unsigned long sendPirValuePrevMillis = 0;

//--------------------------------------------------------------------------------------------------
// Servo
Servo myservo;
bool doorReality = false;
bool doorExpectation = false;
unsigned long long getDoorValuePrevMillis = 0;
unsigned long long sendDoorValuePrevMillis = 0;
unsigned long long sendDoorExpectationTruePrevMillis = 0;

//--------------------------------------------------------------------------------------------------
// Lcd
// String currentName = "";
unsigned long long getLcdNameValuePrevMillis = 0;
unsigned long long sendLcdNameValuePrevMillis = 0;
unsigned long long getLcdGestureValuePrevMillis = 0;
unsigned long long sendLcdGestureValuePrevMillis = 0;
LiquidCrystal_I2C lcd(0x27, 20, 4);
String lcdNameExpectation = "None";
String lcdNameReality = "None";
String lcdGestureExpectation = "None";
String lcdGestureReality = "None";
String lcdGestureStateExpectation = "None";
String lcdGestureStateReality = "None";

//--------------------------------------------------------------------------------------------------
// Buzzer
unsigned long sendBuzzerValuePrevMillis = 0;
unsigned long getBuzzerValuePrevMillis = 0;
bool buzzerReality = false;
bool buzzerExpectation = false;

//--------------------------------------------------------------------------------------------------
//Led
unsigned long sendLedValuePrevMillis = 0;
unsigned long getLedValuePrevMillis = 0;
bool ledReality = false;
bool ledExpectation = false;

//--------------------------------------------------------------------------------------------------
//Button
unsigned long sendButtonValuePrevMillis = 0;
bool buttonValue = false;

void serveJpg()
{
  auto frame = esp32cam::capture();
  if (frame == nullptr) {
    Serial.println("CAPTURE FAIL");
    server.send(503, "", "");
    return;
  }
  Serial.printf("CAPTURE OK %dx%d %db\n", frame->getWidth(), frame->getHeight(),
                static_cast<int>(frame->size()));
 
  server.setContentLength(frame->size());
  server.send(200, "image/jpeg");
  WiFiClient client = server.client();
  frame->writeTo(client);
}
 
void handleJpgLo()
{
  if (!esp32cam::Camera.changeResolution(loRes)) {
    Serial.println("SET-LO-RES FAIL");
  }
  serveJpg();
}
 
void handleJpgHi()
{
  if (!esp32cam::Camera.changeResolution(hiRes)) {
    Serial.println("SET-HI-RES FAIL");
  }
  serveJpg();
}
 
void handleJpgMid()
{
  if (!esp32cam::Camera.changeResolution(midRes)) {
    Serial.println("SET-MID-RES FAIL");
  }
  serveJpg();
}

// //Pattern code
// void getSensorValueRTDB(int interval=15000, bool isPrinted=true) {
//   if (Firebase.ready() && signupOK && (millis() - getDataPrevMillis > interval || getDataPrevMillis == 0)) {
//     getDataPrevMillis = millis();

//     if (Firebase.RTDB.getInt(&fbdo, pirPath)) {
//       if (fbdo.dataType() == "boolean") {
//         pirValue = fbdo.intData();
//         if (isPrinted) {
//           Serial.println(pirValue);
//         }
//       }
//     }
//     else {
//       Serial.println(fbdo.errorReason());
//     }
//   }
// }

// void sendSensorValueRTDB(int interval=15000, bool isPrinted=true) {
//   if (Firebase.ready() && signupOK && (millis() - sendDataPrevMillis > interval || sendDataPrevMillis == 0)) {
//     sendDataPrevMillis = millis();

//     if (Firebase.RTDB.setBool(&fbdo, pirPath, pirValue)) {
//       if (isPrinted) {
//         Serial.println(pirValue);
//       }
//     }
//     else {
//       Serial.println(fbdo.errorReason());
//     }
//   }
// }

//Servo function
void handleDoor(bool isOpen){
  if(isOpen == true)
    myservo.write(95); //Open
  else{
    myservo.write(5); //Close
  }
}

void getDoorValue(int interval=3000, bool isPrinted=true) {
  if (Firebase.ready() && signupOK && (millis() - getDoorValuePrevMillis > interval || getDoorValuePrevMillis == 0)) {
    getDoorValuePrevMillis = millis();

    if (Firebase.RTDB.getInt(&fbdo, doorExpectationPath)) {
      if (fbdo.dataType() == "boolean") {
        doorExpectation = fbdo.intData();
        if (isPrinted) {
          Serial.println(doorExpectation);
        }
      }
    }
    else {
      Serial.println(fbdo.errorReason());
    }
  }
}

void sendDoorValue(int interval=3000, bool isPrinted=true) {
  if (Firebase.ready() && signupOK && (millis() - sendDoorValuePrevMillis > interval || sendDoorValuePrevMillis == 0)) {
    sendDoorValuePrevMillis = millis();

    if (Firebase.RTDB.setBool(&fbdo, doorRealityPath, doorReality)) {
      if (isPrinted) {
        Serial.print("Servo: ");
        Serial.println(doorReality);
      }
    }
    else {
      Serial.println(fbdo.errorReason());
    }
  }
}

void sendDoorExpectationTrue(int interval=3000, bool isPrinted=true) {
  if (Firebase.ready() && signupOK && (millis() - sendDoorExpectationTruePrevMillis > interval || sendDoorExpectationTruePrevMillis == 0)) {
    sendDoorExpectationTruePrevMillis = millis();
    doorExpectation = true;

    if (Firebase.RTDB.setBool(&fbdo, doorExpectationPath, doorExpectation)) {
      if (isPrinted) {
        Serial.println(doorExpectation);
      }
    }
    else {
      Serial.println(fbdo.errorReason());
    }
  }
}

//Lcd function
void getLcdNameValue(int interval=3000, bool isPrinted=true) {
  if (Firebase.ready() && signupOK && (millis() - getLcdNameValuePrevMillis > interval || getLcdNameValuePrevMillis == 0)) {
    getLcdNameValuePrevMillis = millis();

    if (Firebase.RTDB.getString(&fbdo, lcdNameExpectationPath)) {
      lcdNameExpectation = fbdo.stringData();
      if (isPrinted) {
        Serial.print("Lcd_Name: ");
        Serial.println(lcdNameExpectation);
      }
    }
    else {
      Serial.println(fbdo.errorReason());
    }
  }
}

void sendLcdNameValue(int interval=3000, bool isPrinted=true) {
  if (Firebase.ready() && signupOK && (millis() - sendLcdNameValuePrevMillis > interval || sendLcdNameValuePrevMillis == 0)) {
    sendLcdNameValuePrevMillis = millis();

    if (Firebase.RTDB.setString(&fbdo, lcdNameRealityPath, lcdNameReality)) {
      if (isPrinted) {
        Serial.print("Lcd_Name: ");
        Serial.println(lcdNameReality);
      }
    }
    else {
      Serial.println(fbdo.errorReason());
    }
  }
}

void getLcdGestureValue(int interval=3000, bool isPrinted=true) {
  if (Firebase.ready() && signupOK && (millis() - getLcdGestureValuePrevMillis > interval || getLcdGestureValuePrevMillis == 0)) {
    getLcdGestureValuePrevMillis = millis();

    if (Firebase.RTDB.getString(&fbdo, lcdGestureExpectationPath)) {
      lcdGestureExpectation = fbdo.stringData();
      if (isPrinted) {
        Serial.print("Lcd_gesture_expect: ");
        Serial.println(lcdGestureExpectation);
      }
    }
    else {
      Serial.println(fbdo.errorReason());
    }

    if (Firebase.RTDB.getString(&fbdo, lcdGestureStateExpectationPath)) {
      lcdGestureStateExpectation = fbdo.stringData();
      if (isPrinted) {
        Serial.print("Lcd_gesture_state_expect: ");
        Serial.println(lcdGestureStateExpectation);
      }
    }
    else {
      Serial.println(fbdo.errorReason());
    }
  }
}

void sendLcdGestureValue(int interval=3000, bool isPrinted=true, bool isState=true) {
  if (Firebase.ready() && signupOK && (millis() - sendLcdGestureValuePrevMillis > interval || sendLcdGestureValuePrevMillis == 0)) {
    sendLcdGestureValuePrevMillis = millis();

    if(isState == false){
      if (Firebase.RTDB.setString(&fbdo, lcdGestureRealityPath, lcdGestureReality)) {
        if (isPrinted) {
          Serial.print("Lcd: ");
          Serial.println(lcdGestureReality);
        }
      }
      else {
        Serial.println(fbdo.errorReason());
      }
    }
    else{
      if (Firebase.RTDB.setString(&fbdo, lcdGestureStateRealityPath, lcdGestureStateReality)) {
        if (isPrinted) {
          Serial.print("Lcd: ");
          Serial.println(lcdGestureStateReality);
        }
      }
      else {
        Serial.println(fbdo.errorReason());
      }
    }
  }
}

void handleLcdName(String name){
  lcd.backlight();
  lcd.setCursor(0,0);
  lcd.print("Hello");
  lcd.setCursor(0,1);
  lcd.print(name);
}

void handleLcdGesture(String gesture){
  lcd.backlight();
  lcd.setCursor(0,2);
  lcd.print(gesture);
}

void handleLcdStateGesture(String state){
  lcd.backlight();
  lcd.setCursor(0,3);
  lcd.print(state);
}

void clearLCDLine (int line) {
  lcd.setCursor (0,line);
  for (int n = 0; n < 20; n++) // 20 indicates symbols in line.
    lcd.print (' ');
}

//Buzzer function
void handleBuzzer(bool isOn){
  //buzzerPrevMillis = millis();
  if(isOn){
    tone(buzzerPin, 1000);
  }
  else{
    noTone(buzzerPin);
  }
}

void getBuzzerValue(int interval=3000, bool isPrinted=true) {
  if (Firebase.ready() && signupOK && (millis() - getBuzzerValuePrevMillis > interval || getBuzzerValuePrevMillis == 0)) {
    getBuzzerValuePrevMillis = millis();

    if (Firebase.RTDB.getInt(&fbdo, buzzerExpectationPath)) {
      if (fbdo.dataType() == "boolean") {
        buzzerExpectation = fbdo.intData();
        if (isPrinted) {
          Serial.print("Buzzer: ");
          Serial.println(buzzerExpectation);
        }
      }
    }
    else {
      Serial.println(fbdo.errorReason());
    }
  }
}

void sendBuzzerValue(int interval=3000, bool isPrinted=true) {
  if (Firebase.ready() && signupOK && (millis() - sendBuzzerValuePrevMillis > interval || sendBuzzerValuePrevMillis == 0)) {
    sendBuzzerValuePrevMillis = millis();

    if (Firebase.RTDB.setBool(&fbdo, buzzerRealityPath, buzzerReality)) {
      if (isPrinted) {
        Serial.print("Buzzer: ");
        Serial.println(buzzerReality);
      }
    }
    else {
      Serial.println(fbdo.errorReason());
    }
  }
}

// //Pir function
// void sendPirValue(int interval=3000, bool isPrinted=true) {
//   if (Firebase.ready() && signupOK && (millis() - sendPirValuePrevMillis > interval || sendPirValuePrevMillis == 0)) {
//     sendPirValuePrevMillis = millis();

//     if (Firebase.RTDB.setBool(&fbdo, pirPath, pirValue)) {
//       if (isPrinted) {
//         Serial.println("-------------------------"); //For test
//         Serial.println(pirValue);
//       }
//     }
//     else {
//       Serial.println(fbdo.errorReason());
//     }
//   }
// }

// //Led function
// void getLedValue(int interval=3000, bool isPrinted=true) {
//   if (Firebase.ready() && signupOK && (millis() - getLedValuePrevMillis > interval || getLedValuePrevMillis == 0)) {
//     getLedValuePrevMillis = millis();

//     if (Firebase.RTDB.getInt(&fbdo, ledExpectationPath)) {
//       if (fbdo.dataType() == "boolean") {
//         ledExpectation = fbdo.intData();
//         if (isPrinted) {
//           Serial.println(ledExpectation);
//         }
//       }
//     }
//     else {
//       Serial.println(fbdo.errorReason());
//     }
//   }
// }

// void sendLedValue(int interval=3000, bool isPrinted=true) {
//   if (Firebase.ready() && signupOK && (millis() - sendLedValuePrevMillis > interval || sendLedValuePrevMillis == 0)) {
//     sendLedValuePrevMillis = millis();

//     if (Firebase.RTDB.setBool(&fbdo, ledRealityPath, ledReality)) {
//       if (isPrinted) {
//         Serial.println(ledReality);
//       }
//     }
//     else {
//       Serial.println(fbdo.errorReason());
//     }
//   }
// }

// void handleLed(bool isOn){
//   if(isOn){
//     digitalWrite(ledPin, HIGH);
//   }
//   else{
//     digitalWrite(ledPin, LOW);
//   }
// }

// Ultrasonic function
long getDistance(){
  digitalWrite(ultraTrigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(ultraTrigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(ultraTrigPin, LOW);
  
  long duration = pulseIn(ultraEchoPin, HIGH);
  
  long distanceCm = duration * 0.034 / 2;
  
  return distanceCm;
}

void sendUltraValue(int interval=3000, bool isPrinted=true) {
  if (Firebase.ready() && signupOK && (millis() - sendUltraValuePrevMillis > interval || sendUltraValuePrevMillis == 0)) {
    sendUltraValuePrevMillis = millis();

    if (Firebase.RTDB.setFloat(&fbdo, ultraValuePath, ultraValue)) {
      if (isPrinted) {
        Serial.print("Ultra: ");
        Serial.println(ultraValue);
      }
    }
    else {
      Serial.println(fbdo.errorReason());
    }
  }
}

// //Button function
// void sendButtonValue(int interval=3000, bool isPrinted=true) {
//   if (Firebase.ready() && signupOK && (millis() - sendButtonValuePrevMillis > interval || sendButtonValuePrevMillis == 0)) {
//     sendButtonValuePrevMillis = millis();

//     if (Firebase.RTDB.setBool(&fbdo, buttonPath, buttonValue)) {
//       if (isPrinted) {
//          Serial.print("Button: ");
//         Serial.println(buttonValue);
//       }
//     }
//     else {
//       Serial.println(fbdo.errorReason());
//     }
//   }
// }
 
void setup(){
  Serial.begin(115200);
  Serial.println();
  {
    using namespace esp32cam;
    Config cfg;
    cfg.setPins(pins::AiThinker);
    cfg.setResolution(hiRes);
    cfg.setBufferCount(2);
    cfg.setJpeg(80);
 
    bool ok = Camera.begin(cfg);
    Serial.println(ok ? "CAMERA OK" : "CAMERA FAIL");
  }
  WiFi.persistent(false);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
  auto cameraIP = WiFi.localIP();
  String ipStr = "http://" + String(cameraIP[0]) + "." + String(cameraIP[1]) + "." + String(cameraIP[2]) + "." + String(cameraIP[3]);
  Serial.println(ipStr);
  Serial.println("  /cam-lo.jpg");
  Serial.println("  /cam-hi.jpg");
  Serial.println("  /cam-mid.jpg");
 
  server.on("/cam-lo.jpg", handleJpgLo);
  server.on("/cam-hi.jpg", handleJpgHi);
  server.on("/cam-mid.jpg", handleJpgMid);
 
  server.begin();

  // Firebase
  /* Assign the api key (required) */
  config.api_key = API_KEY;

  /* Assign the RTDB URL (required) */
  config.database_url = DATABASE_URL;

  /* Sign up */
  if (Firebase.signUp(&config, &auth, "", "")) {
    Serial.println("ok");
    signupOK = true;
  }
  else {
    Serial.printf("%s\n", config.signer.signupError.message.c_str());
  }

  /* Assign the callback function for the long running token generation task */
  config.token_status_callback = tokenStatusCallback; //see addons/TokenHelper.h

  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);
  //Send IP to Firebase

  if (!Firebase.RTDB.setString(&fbdo, cameraIPPath, ipStr)) {
    Serial.println(fbdo.errorReason());
  }
  //Servo
  myservo.attach(servoPin);
  handleDoor(false);
  sendDoorValue(0, false);

  //Lcd
  Wire.begin(lcdSdaPin, lcdSclPin);
  lcd.begin(20,4);
  lcd.backlight();
  lcd.clear();
  sendLcdNameValue(0, true);
  sendLcdGestureValue(0, true, false);
  sendLcdGestureValue(0, true, true);

  //Buzzer
  pinMode(buzzerPin, OUTPUT);
  handleBuzzer(false);
  sendBuzzerValue(0,false);

  //Ultrasonic
  pinMode(ultraTrigPin, OUTPUT);
  pinMode(ultraEchoPin, INPUT);

  //Pir
  // pinMode(pirPin, INPUT);

  // //Led
  // pinMode(ledPin, OUTPUT);
  // handleLed(false);
  // sendLedValue(0,false);

  // //Button
  // pinMode(buttonPin, INPUT);
}

bool isRunning = true;

void loop()
{
  server.handleClient();

  Serial.println("Running");

  if(isRunning == true){
    lcd.setCursor(17,0);
    lcd.print("  ");
    lcd.setCursor(17,0);
    lcd.print(".");
    isRunning = false;
  }
  else{
    lcd.setCursor(17,0);
    lcd.print("  ");
    lcd.setCursor(17,0);
    lcd.print("..");
    isRunning = true;
  }

  //Servo code
  getDoorValue(5000, false);
  if(doorReality != doorExpectation){
    handleDoor(doorExpectation);
    doorReality = doorExpectation;
    sendDoorValue(0, true);
  }

  //Ultra
  ultraValue = getDistance();
  sendUltraValue(5000, true);

  //Buzzer
  getBuzzerValue(5000, false);
  if(buzzerReality != buzzerExpectation){
    handleBuzzer(buzzerExpectation);
    buzzerReality = buzzerExpectation;
    sendBuzzerValue(0, true);
  }

  //Lcd
  getLcdNameValue(5000, true);
  if(lcdNameExpectation != lcdNameReality){
    clearLCDLine(0);
    clearLCDLine(1);
    if(lcdNameExpectation != "None"){
      handleLcdName(lcdNameExpectation);
    }
    lcdNameReality = lcdNameExpectation;
    sendLcdNameValue(0, true);
  }

  getLcdGestureValue(5000, true);
  if(lcdGestureExpectation != lcdGestureReality){
    clearLCDLine(2);
    if(lcdGestureExpectation != "None"){
      handleLcdGesture(lcdGestureExpectation);
    }
    lcdGestureReality = lcdGestureExpectation;
    sendLcdGestureValue(0, true, false);
  }

  if(lcdGestureStateExpectation != lcdGestureStateReality){
    clearLCDLine(3);
    if(lcdGestureStateExpectation != "None"){
      handleLcdStateGesture(lcdGestureStateExpectation);
    }
    lcdGestureStateReality = lcdGestureStateExpectation;
    sendLcdGestureValue(0, true, true);
  }

  // //Pir
  // pirValue = digitalRead(pirPin);
  // Serial.println(pirValue);
  // sendPirValue(1000, true);

  // //Led
  // getLedValue(1000, false);
  // if(ledReality != ledExpectation){
  //   handleLed(ledExpectation);
  //   ledReality = ledExpectation;
  //   sendLedValue(0, false);
  // }

  // //Button
  // buttonValue = digitalRead(buttonPin);
  // if(buttonValue == true){
  //   sendDoorExpectationTrue(1000, false);
  // }
  // sendButtonValue(1000, false);
}