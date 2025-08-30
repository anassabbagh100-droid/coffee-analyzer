#include <Arduino.h>
#include <Wire.h>
#include <EEPROM.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <WebServer.h>
#include <time.h>
#include <FS.h>
#include <SPIFFS.h>

// --- GUI Library Includes ---
// Assuming TFT_eSPI is used for the display
#include <TFT_eSPI.h>
TFT_eSPI tft = TFT_eSPI();

// --- EEPROM Addresses ---
#define EEPROM_SIZE 512
#define DEVICE_SERIAL_ADDR 0
#define ACTIVATION_KEY_ADDR 64
#define WIFI_SSID_ADDR 128
#define WIFI_PASS_ADDR 192
#define WIFI_CONFIGURED_ADDR 256
#define FIRST_BOOT_ADDR 257
#define FIRST_INTERNET_CONNECT_ADDR 258
#define MEASUREMENT_COUNT_ADDR 260
#define ERROR_COUNT_ADDR 264
#define COFFEE_TYPE_ADDR 268 // New: Address for coffee type
#define COFFEE_ORIGIN_ADDR 269 // New: Address for coffee origin

// --- Server Settings (Local Server) ---
// IMPORTANT: Replace with your local server IP and port
const char* SERVER_IP = "192.168.1.100"; // Example: Your PC\"s local IP
const int SERVER_PORT = 5000;
String SERVER_URL = String("http://") + SERVER_IP + ":" + SERVER_PORT;

// --- NTP Server for Time Synchronization ---
const char* NTP_SERVER = "pool.ntp.org";
const long GMT_OFFSET_SEC = 3 * 3600; // For GMT+3 (e.g., Saudi Arabia, Iraq)
const int DAYLIGHT_OFFSET_SEC = 0; // No daylight saving

// --- Access Point for WiFi Setup ---
const char* AP_SSID = "CoffeeAnalyzer_Setup";
const char* AP_PASS = "12345678";
WebServer server(80);

// --- Operating Modes ---
enum OperatingMode {
  MODE_BASIC = 0,
  MODE_PROFESSIONAL = 1,
  MODE_ADVANCED = 2,
  MODE_CUSTOM = 3,
  MODE_BLEND_PROFILES = 4,
  MODE_ADD_KNOWLEDGE = 5, // New mode for adding knowledge
  MODE_WIFI_SETUP = 6 // New mode for WiFi setup via AP
};

OperatingMode currentMode = MODE_BASIC;

// --- Coffee Types ---
enum CoffeeType {
  COFFEE_GREEN = 0,
  COFFEE_ROASTED = 1,
  COFFEE_GROUND = 2,
  COFFEE_UNKNOWN_TYPE = 3 // For cases where type is not specified
};

CoffeeType currentCoffeeType = COFFEE_UNKNOWN_TYPE; // Default coffee type

// --- Coffee Origins (Simplified for ESP32, full list on server) ---
enum CoffeeOrigin {
  ORIGIN_UNKNOWN = 0,
  ORIGIN_BRAZIL = 1,
  ORIGIN_COLOMBIA = 2,
  ORIGIN_COSTA_RICA = 3,
  ORIGIN_HONDURAS = 4,
  ORIGIN_GUATEMALA = 5,
  ORIGIN_INDIA = 6,
  ORIGIN_INDONESIA = 7,
  ORIGIN_VIETNAM = 8,
  ORIGIN_PERU = 9,
  ORIGIN_TANZANIA = 10,
  ORIGIN_UGANDA = 11,
  ORIGIN_ETHIOPIA = 12,
  ORIGIN_IVORY_COAST = 13,
  ORIGIN_YEMEN = 14,
  ORIGIN_SCA = 15, // For SCA general standards
  ORIGIN_GLOBAL_ARABICA = 16,
  ORIGIN_GLOBAL_ROBUSTA = 17
};

CoffeeOrigin currentCoffeeOrigin = ORIGIN_UNKNOWN; // Default coffee origin

// --- Device Info ---
String deviceSerial = "";
String activationKey = "";
String wifiSSID = "";
String wifiPassword = "";
bool wifiConfigured = false;
bool firstBoot = true;
bool firstInternetConnect = true;
unsigned long measurementCount = 0;
unsigned long errorCount = 0;

// --- Timing Variables ---
unsigned long lastReportTime = 0;
unsigned long lastSyncAttempt = 0;
const unsigned long REPORT_INTERVAL = 300000; // 5 minutes
const unsigned long SYNC_RETRY_INTERVAL = 60000; // 1 minute

// --- Local Storage ---
const char* PENDING_DATA_FILE = "/pending_data.json";
const char* DEVICE_LOG_FILE = "/device_log.txt";
const char* KNOWLEDGE_BASE_FILE = "/knowledge_base.json"; // File for user-added knowledge

// --- Sensor Data ---
// Placeholder for NIR sensor readings (e.g., 11 channels for AS7341)
int nirReadings[11];
float estimatedCO2 = 0.0;
float estimatedProtein = 0.0;
float estimatedAminoAcids = 0.0;
float estimatedMinerals = 0.0; // New field for estimated Minerals
float estimatedFlavorCompounds = 0.0; // New field for estimated Flavor Compounds
float estimatedMoisture = 0.0; // New field for estimated Moisture

// --- Function Prototypes ---
void initGUI();
void drawScreen(const String& title, const String& line1, const String& line2, const String& line3);
void handleTouch();
void setupWiFi();
void setupAccessPoint();
void connectToWiFi();
void syncTime();
String getFormattedDate();
String getFormattedDateTime();
void registerDeviceWithServer();
void checkActivationStatus();
void sendReport();
void syncPendingData();
void readFromEEPROM();
void writeToEEPROM();
void generateDeviceSerial();
void runCurrentMode();
void readSensorData(); // Modified to read NIR and estimate CO2, Protein, Amino Acids, Minerals, Flavor Compounds, Moisture
// Calibration functions will now fetch data from server or use defaults
void getCalibrationData(CoffeeType type, CoffeeOrigin origin, JsonDocument& doc); 
float estimateCO2FromNIR(int* nir_data, const JsonDocument& calibrationData); 
float estimateProteinFromNIR(int* nir_data, const JsonDocument& calibrationData); 
float estimateAminoAcidsFromNIR(int* nir_data, const JsonDocument& calibrationData); 
float estimateMineralsFromNIR(int* nir_data, const JsonDocument& calibrationData); 
float estimateFlavorCompoundsFromNIR(int* nir_data, const JsonDocument& calibrationData); 
float estimateMoistureFromNIR(int* nir_data, const JsonDocument& calibrationData); 
void logEvent(const String& eventType, const String& message);
void saveToLocalStorage(const String& dataType, const JsonDocument& data);
void loadPendingData();
bool isServerAvailable();
void initSPIFFS();
void displayCurrentMode();
void displayMeasurementResults();

// New functions for knowledge base management and owner control
void addKnowledgeBaseEntry(const String& sampleName, const String& chemicalDataJson, const String& sensorDataJson, CoffeeType type, CoffeeOrigin origin);
void saveKnowledgeBaseEntry(const JsonDocument& entry);
void loadKnowledgeBaseEntries(JsonArray& knowledgeArray);
void requestCoffeeTypeAndOriginFromOwner(); // Owner-only function

void setup() {
  Serial.begin(115200);
  EEPROM.begin(EEPROM_SIZE);
  
  // Initialize SPIFFS for local storage
  initSPIFFS();

  // Initialize GUI
  initGUI();
  drawScreen("جهاز تحليل البن", "جاري التهيئة...", "", "");

  readFromEEPROM();

  if (firstBoot) {
    // Generate serial only if it\"s the very first boot
    generateDeviceSerial();
    logEvent("System", "First boot. Generated serial: " + deviceSerial);
    firstBoot = false;
    writeToEEPROM();
  }

  drawScreen("جهاز تحليل البن", "الرقم التسلسلي:", deviceSerial, "جاري الاتصال...");
  delay(2000);

  setupWiFi();

  if (WiFi.status() == WL_CONNECTED) {
    syncTime();
    registerDeviceWithServer();
    checkActivationStatus();
    syncPendingData(); // Sync any pending data from previous sessions
    
    if (firstInternetConnect) {
      logEvent("System", "First internet connection established.");
      firstInternetConnect = false;
      writeToEEPROM();
    }
  }

  // Display initial mode on GUI
  displayCurrentMode();
  delay(3000);
}

void loop() {
  handleTouch(); // Handle touch input for GUI
  server.handleClient(); // Handle web server for WiFi setup

  // Reconnect WiFi if disconnected
  if (WiFi.status() != WL_CONNECTED && wifiConfigured) {
    connectToWiFi();
  }

  // Periodic report sending and sync (if connected)
  if (WiFi.status() == WL_CONNECTED) {
    unsigned long currentTime = millis();
    
    // Send periodic reports
    if (currentTime - lastReportTime > REPORT_INTERVAL) {
      sendReport();
      lastReportTime = currentTime;
    }
    
    // Try to sync pending data
    if (currentTime - lastSyncAttempt > SYNC_RETRY_INTERVAL) {
      syncPendingData();
      lastSyncAttempt = currentTime;
    }
  }

  runCurrentMode();
  delay(100);
}

void initSPIFFS() {
  if (!SPIFFS.begin(true)) {
    Serial.println("SPIFFS Mount Failed");
    logEvent("Storage", "SPIFFS mount failed");
  } else {
    Serial.println("SPIFFS Mounted Successfully");
    logEvent("Storage", "SPIFFS mounted successfully");
  }
}

void initGUI() {
  // Initialize TFT_eSPI
  tft.init();
  tft.setRotation(1); // Adjust rotation as needed for your display
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.setTextSize(2);
  Serial.println("GUI Initialized");
}

void drawScreen(const String& title, const String& line1, const String& line2, const String& line3) {
  tft.fillScreen(TFT_BLACK);
  tft.setCursor(0, 0);
  tft.setTextSize(2);
  tft.setTextColor(TFT_WHITE);
  tft.println(title);
  tft.setCursor(0, 30);
  tft.println(line1);
  tft.setCursor(0, 60);
  tft.println(line2);
  tft.setCursor(0, 90);
  tft.println(line3);
}

void handleTouch() {
  // This function is now primarily for general GUI navigation and interaction
  // Coffee type selection is handled via server command or owner-specific interface
  // Removed the demo coffee type change logic.
}

void setupWiFi() {
  if (!wifiConfigured) {
    Serial.println("WiFi not configured. Starting Access Point for setup...");
    setupAccessPoint();
  } else {
    Serial.println("WiFi configured. Connecting...");
    connectToWiFi();
  }
}

void setupAccessPoint() {
  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASS);

  IPAddress IP = WiFi.softAPIP();
  Serial.print("AP IP address: ");
  Serial.println(IP);

  server.on("/", HTTP_GET, []() {
    String html = "<!DOCTYPE html><html dir=\'rtl\'><head><meta charset=\'UTF-8\'>";
    html += "<title>إعداد WiFi</title>";
    html += "<style>body{font-family:Arial;text-align:center;padding:50px;}";
    html += "input{padding:10px;margin:10px;width:200px;}";
    html += "button{padding:10px 20px;background:#007cba;color:white;border:none;cursor:pointer;}</style>";
    html += "</head><body>";
    html += "<h1>إعداد اتصال WiFi</h1>";
    html += "<p>الرقم التسلسلي: " + deviceSerial + "</p>";
    html += "<form action=\'/save\' method=\'POST\'>";
    html += "<input type=\'text\' name=\'ssid\' placeholder=\'اسم الشبكة (SSID)\' required><br>";
    html += "<input type=\'password\' name=\'password\' placeholder=\'كلمة المرور\' required><br>";
    html += "<button type=\'submit\'>حفظ والاتصال</button>";
    html += "</form></body></html>";
    server.send(200, "text/html", html);
  });

  server.on("/save", HTTP_POST, []() {
    wifiSSID = server.arg("ssid");
    wifiPassword = server.arg("password");
    wifiConfigured = true;

    writeToEEPROM();

    server.send(200, "text/html",
      "<!DOCTYPE html><html dir=\'rtl\'><head><meta charset=\'UTF-8\'></head><body>"
      "<h1>تم حفظ الإعدادات</h1><p>سيتم إعادة تشغيل الجهاز والاتصال بالشبكة</p></body></html>");

    delay(2000);
    ESP.restart();
  });

  server.begin();
  Serial.println("HTTP server started for WiFi setup");
  drawScreen("إعداد WiFi", "اتصل بشبكة:", AP_SSID, "192.168.4.1");
}

void connectToWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(wifiSSID.c_str(), wifiPassword.c_str());

  int attempts = 0;
  drawScreen("جاري الاتصال", wifiSSID, "", "");
  while (WiFi.status() != WL_CONNECTED && attempts < 40) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    drawScreen("متصل بالإنترنت", "IP:", WiFi.localIP().toString(), "");
    logEvent("WiFi", "Connected to " + wifiSSID + ", IP: " + WiFi.localIP().toString());
  } else {
    Serial.println("\nWiFi connection failed!");
    logEvent("WiFi", "Connection failed to " + wifiSSID);
    drawScreen("فشل الاتصال", "تحقق من الإعدادات", "", "");
    delay(3000);
    setupAccessPoint();
  }
}

void syncTime() {
  configTime(GMT_OFFSET_SEC, DAYLIGHT_OFFSET_SEC, NTP_SERVER);
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    logEvent("Time Sync", "Failed to obtain time");
    return;
  }
  logEvent("Time Sync", "Time synchronized: " + String(asctime(&timeinfo)));
}

String getFormattedDate() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    return "20250101"; // Return default date if time not available
  }
  char dateBuffer[9];
  strftime(dateBuffer, 9, "%Y%m%d", &timeinfo);
  return String(dateBuffer);
}

String getFormattedDateTime() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    return "2025-01-01T00:00:00Z";
  }
  char dateTimeBuffer[25];
  strftime(dateTimeBuffer, 25, "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
  return String(dateTimeBuffer);
}

void registerDeviceWithServer() {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  String url = SERVER_URL + "/api/activation/devices";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  DynamicJsonDocument doc(1024);
  doc["device_serial"] = deviceSerial;
  doc["device_name"] = "جهاز تحليل البن - " + deviceSerial;
  doc["first_boot_date"] = getFormattedDateTime();
  doc["first_internet_date"] = getFormattedDateTime();

  String jsonString;
  serializeJson(doc, jsonString);

  int httpResponseCode = http.POST(jsonString);

  if (httpResponseCode == 200 || httpResponseCode == 201) {
    String response = http.getString();
    DynamicJsonDocument responseDoc(1024);
    deserializeJson(responseDoc, response);
    
    if (responseDoc["success"]) {
      logEvent("Registration", "Device registered successfully with server");
    } else {
      logEvent("Registration", "Server error: " + responseDoc["message"].as<String>());
    }
  } else {
    logEvent("Registration", "Failed to register. HTTP code: " + String(httpResponseCode));
    
    // Save registration data for later sync
    saveToLocalStorage("registration", doc);
  }
  http.end();
}

void checkActivationStatus() {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  String url = SERVER_URL + "/api/activation/devices/" + deviceSerial + "/status";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  int httpResponseCode = http.GET();

  if (httpResponseCode == 200) {
    String response = http.getString();
    DynamicJsonDocument doc(1024);
    deserializeJson(doc, response);

    if (doc["success"]) {
      String level = doc["activation_level"].as<String>();
      String key = doc["activation_key"].as<String>();

      if (key != activationKey) {
        activationKey = key;
        writeToEEPROM();
        logEvent("Activation", "Key updated to: " + key);
      }

      if (level == "basic") {
        currentMode = MODE_BASIC;
      } else if (level == "professional") {
        currentMode = MODE_PROFESSIONAL;
      } else if (level == "advanced") {
        currentMode = MODE_ADVANCED;
      } else if (level == "custom") {
        currentMode = MODE_CUSTOM;
      } else if (level == "blend_profiles") {
        currentMode = MODE_BLEND_PROFILES;
      }
      logEvent("Activation", "Status updated to: " + level);
      displayCurrentMode();
    } else {
      logEvent("Activation", "Server error: " + doc["message"].as<String>());
    }
  } else {
    logEvent("Activation", "Failed to check status. HTTP code: " + String(httpResponseCode));
  }
  http.end();
}

void sendReport() {
  if (WiFi.status() != WL_CONNECTED) {
    // Save report for later sync
    DynamicJsonDocument doc(1024);
    doc["device_serial"] = deviceSerial;
    doc["measurement_count"] = measurementCount;
    doc["error_count"] = errorCount;
    doc["uptime_hours"] = millis() / (1000.0 * 60.0 * 60.0);
    doc["wifi_signal"] = 0; // Not available when offline
    doc["free_heap"] = ESP.getFreeHeap();
    doc["current_mode"] = currentMode;
    doc["timestamp"] = getFormattedDateTime();
    doc["coffee_type"] = currentCoffeeType; // Include coffee type
    doc["coffee_origin"] = currentCoffeeOrigin; // Include coffee origin
    
    saveToLocalStorage("report", doc);
    return;
  }

  HTTPClient http;
  String url = SERVER_URL + "/api/activation/devices/" + deviceSerial + "/report";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  DynamicJsonDocument doc(1024);
  doc["device_serial"] = deviceSerial;
  doc["measurement_count"] = measurementCount;
  doc["error_count"] = errorCount;
  doc["uptime_hours"] = millis() / (1000.0 * 60.0 * 60.0);
  doc["wifi_signal"] = WiFi.RSSI();
  doc["free_heap"] = ESP.getFreeHeap();
  doc["current_mode"] = currentMode;
  doc["coffee_type"] = currentCoffeeType; // Include coffee type
  doc["coffee_origin"] = currentCoffeeOrigin; // Include coffee origin

  String jsonString;
  serializeJson(doc, jsonString);

  int httpResponseCode = http.POST(jsonString);

  if (httpResponseCode == 200) {
    logEvent("Report", "Report sent successfully.");
  } else {
    logEvent("Report", "Failed to send report. HTTP code: " + String(httpResponseCode));
    // Save for later sync
    saveToLocalStorage("report", doc);
  }
  http.end();
}

void syncPendingData() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  File root = SPIFFS.open("/");
  File file = root.openNextFile();
  
  while(file){
    String fileName = file.name();
    if(fileName.startsWith("/pending_") && fileName.endsWith(".json")){
      Serial.print("Syncing pending file: ");
      Serial.println(fileName);
      
      String fileContent = file.readString();
      DynamicJsonDocument doc(fileContent.length() * 2); // Allocate enough memory
      deserializeJson(doc, fileContent);

      String dataType = fileName;
      dataType.replace("/pending_", "");
      dataType.replace(".json", "");

      HTTPClient http;
      String url;
      if(dataType == "report"){
        url = SERVER_URL + "/api/activation/devices/" + deviceSerial + "/report";
      } else if (dataType == "registration"){
        url = SERVER_URL + "/api/activation/devices";
      } else if (dataType == "measurement"){
        url = SERVER_URL + "/api/measurements";
      } else if (dataType == "knowledge"){
        url = SERVER_URL + "/api/knowledge";
      }

      http.begin(url);
      http.addHeader("Content-Type", "application/json");
      String jsonString;
      serializeJson(doc, jsonString);
      int httpResponseCode = http.POST(jsonString);

      if(httpResponseCode == 200 || httpResponseCode == 201){
        Serial.println("Successfully synced and deleting file.");
        SPIFFS.remove(fileName);
      } else {
        Serial.println("Failed to sync. HTTP code: " + String(httpResponseCode));
      }
      http.end();
    }
    file = root.openNextFile();
  }
}

void readFromEEPROM() {
  char buffer[64];
  EEPROM.readBytes(DEVICE_SERIAL_ADDR, buffer, 64);
  deviceSerial = String(buffer);

  EEPROM.readBytes(ACTIVATION_KEY_ADDR, buffer, 64);
  activationKey = String(buffer);

  EEPROM.readBytes(WIFI_SSID_ADDR, buffer, 64);
  wifiSSID = String(buffer);

  EEPROM.readBytes(WIFI_PASS_ADDR, buffer, 64);
  wifiPassword = String(buffer);

  wifiConfigured = EEPROM.readByte(WIFI_CONFIGURED_ADDR);
  firstBoot = EEPROM.readByte(FIRST_BOOT_ADDR);
  firstInternetConnect = EEPROM.readByte(FIRST_INTERNET_CONNECT_ADDR);
  EEPROM.readBytes(MEASUREMENT_COUNT_ADDR, &measurementCount, sizeof(measurementCount));
  EEPROM.readBytes(ERROR_COUNT_ADDR, &errorCount, sizeof(errorCount));
  currentCoffeeType = (CoffeeType)EEPROM.readByte(COFFEE_TYPE_ADDR);
  currentCoffeeOrigin = (CoffeeOrigin)EEPROM.readByte(COFFEE_ORIGIN_ADDR);

  Serial.println("EEPROM Read:");
  Serial.println("Serial: " + deviceSerial);
  Serial.println("WiFi Configured: " + String(wifiConfigured));
  Serial.println("Coffee Type: " + String(currentCoffeeType));
  Serial.println("Coffee Origin: " + String(currentCoffeeOrigin));
}

void writeToEEPROM() {
  EEPROM.writeBytes(DEVICE_SERIAL_ADDR, deviceSerial.c_str(), deviceSerial.length() + 1);
  EEPROM.writeBytes(ACTIVATION_KEY_ADDR, activationKey.c_str(), activationKey.length() + 1);
  EEPROM.writeBytes(WIFI_SSID_ADDR, wifiSSID.c_str(), wifiSSID.length() + 1);
  EEPROM.writeBytes(WIFI_PASS_ADDR, wifiPassword.c_str(), wifiPassword.length() + 1);
  EEPROM.writeByte(WIFI_CONFIGURED_ADDR, wifiConfigured);
  EEPROM.writeByte(FIRST_BOOT_ADDR, firstBoot);
  EEPROM.writeByte(FIRST_INTERNET_CONNECT_ADDR, firstInternetConnect);
  EEPROM.writeBytes(MEASUREMENT_COUNT_ADDR, &measurementCount, sizeof(measurementCount));
  EEPROM.writeBytes(ERROR_COUNT_ADDR, &errorCount, sizeof(errorCount));
  EEPROM.writeByte(COFFEE_TYPE_ADDR, (byte)currentCoffeeType);
  EEPROM.writeByte(COFFEE_ORIGIN_ADDR, (byte)currentCoffeeOrigin);
  EEPROM.commit();
  Serial.println("EEPROM Written.");
}

void generateDeviceSerial() {
  String chipId = String((uint32_t)ESP.getEfuseMac(), HEX);
  deviceSerial = "ESP32-" + chipId.substring(chipId.length() - 6);
}

void runCurrentMode() {
  // This function simulates the main loop of the device based on its mode.
  // In a real scenario, this would involve sensor readings, data processing, and display updates.
  
  // For demonstration, we'll just read sensor data and display results.
  readSensorData();
  displayMeasurementResults();
  delay(5000); // Simulate measurement interval
}

void readSensorData() {
  // Simulate reading from NIR sensor (replace with actual sensor code)
  for (int i = 0; i < 11; i++) {
    nirReadings[i] = analogRead(A0 + i); // Placeholder: read from analog pins
  }

  // Fetch calibration data from server based on current coffee type and origin
  DynamicJsonDocument calibrationData(2048); // Increased size for calibration data
  getCalibrationData(currentCoffeeType, currentCoffeeOrigin, calibrationData);

  // Estimate chemical components using calibration data
  estimatedCO2 = estimateCO2FromNIR(nirReadings, calibrationData);
  estimatedProtein = estimateProteinFromNIR(nirReadings, calibrationData);
  estimatedAminoAcids = estimateAminoAcidsFromNIR(nirReadings, calibrationData);
  estimatedMinerals = estimateMineralsFromNIR(nirReadings, calibrationData);
  estimatedFlavorCompounds = estimateFlavorCompoundsFromNIR(nirReadings, calibrationData);
  estimatedMoisture = estimateMoistureFromNIR(nirReadings, calibrationData);

  measurementCount++;

  // Send measurement data to server
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = SERVER_URL + "/api/measurements";
    http.begin(url);
    http.addHeader("Content-Type", "application/json");

    DynamicJsonDocument doc(1024);
    doc["device_serial"] = deviceSerial;
    doc["timestamp"] = getFormattedDateTime();
    doc["coffee_type"] = currentCoffeeType; // Send as integer enum value
    doc["coffee_origin"] = currentCoffeeOrigin; // Send as integer enum value
    JsonArray nirArray = doc.createNestedArray("nir_readings");
    for (int i = 0; i < 11; i++) {
      nirArray.add(nirReadings[i]);
    }
    doc["estimated_co2"] = estimatedCO2;
    doc["estimated_protein"] = estimatedProtein;
    doc["estimated_amino_acids"] = estimatedAminoAcids;
    doc["estimated_minerals"] = estimatedMinerals;
    doc["estimated_flavor_compounds"] = estimatedFlavorCompounds;
    doc["estimated_moisture"] = estimatedMoisture;

    String jsonString;
    serializeJson(doc, jsonString);

    int httpResponseCode = http.POST(jsonString);

    if (httpResponseCode == 200 || httpResponseCode == 201) {
      logEvent("Measurement", "Measurement sent successfully.");
    } else {
      logEvent("Measurement", "Failed to send measurement. HTTP code: " + String(httpResponseCode));
      errorCount++;
      saveToLocalStorage("measurement", doc);
    }
    http.end();
  }
}

void getCalibrationData(CoffeeType type, CoffeeOrigin origin, JsonDocument& doc) {
  if (WiFi.status() != WL_CONNECTED) {
    // Fallback to default or cached calibration data if offline
    Serial.println("Offline: Using default/cached calibration data.");
    // Populate doc with some default values or load from SPIFFS if cached
    doc["co2_coeff"] = 0.1; 
    doc["protein_coeff"] = 0.05;
    doc["amino_acids_coeff"] = 0.02;
    doc["minerals_coeff"] = 0.01;
    doc["flavor_compounds_coeff"] = 0.03;
    doc["moisture_coeff"] = 0.08;
    return;
  }

  HTTPClient http;
  String url = SERVER_URL + "/api/calibration_data?coffee_type=" + String(type) + "&coffee_origin=" + String(origin);
  http.begin(url);
  int httpResponseCode = http.GET();

  if (httpResponseCode == 200) {
    String response = http.getString();
    deserializeJson(doc, response);
    logEvent("Calibration", "Calibration data fetched successfully.");
  } else {
    logEvent("Calibration", "Failed to fetch calibration data. HTTP code: " + String(httpResponseCode));
    // Fallback to default if server call fails
    doc["co2_coeff"] = 0.1; 
    doc["protein_coeff"] = 0.05;
    doc["amino_acids_coeff"] = 0.02;
    doc["minerals_coeff"] = 0.01;
    doc["flavor_compounds_coeff"] = 0.03;
    doc["moisture_coeff"] = 0.08;
  }
  http.end();
}

// Placeholder estimation functions - these would use actual NIR models
float estimateCO2FromNIR(int* nir_data, const JsonDocument& calibrationData) {
  float coeff = calibrationData["co2_coeff"] | 0.1; // Default if not found
  return (nir_data[0] * coeff + nir_data[1] * (coeff/2)); // Example calculation
}

float estimateProteinFromNIR(int* nir_data, const JsonDocument& calibrationData) {
  float coeff = calibrationData["protein_coeff"] | 0.05;
  return (nir_data[2] * coeff + nir_data[3] * (coeff/2));
}

float estimateAminoAcidsFromNIR(int* nir_data, const JsonDocument& calibrationData) {
  float coeff = calibrationData["amino_acids_coeff"] | 0.02;
  return (nir_data[4] * coeff + nir_data[5] * (coeff/2));
}

float estimateMineralsFromNIR(int* nir_data, const JsonDocument& calibrationData) {
  float coeff = calibrationData["minerals_coeff"] | 0.01;
  return (nir_data[6] * coeff + nir_data[7] * (coeff/2));
}

float estimateFlavorCompoundsFromNIR(int* nir_data, const JsonDocument& calibrationData) {
  float coeff = calibrationData["flavor_compounds_coeff"] | 0.03;
  return (nir_data[8] * coeff + nir_data[9] * (coeff/2));
}

float estimateMoistureFromNIR(int* nir_data, const JsonDocument& calibrationData) {
  float coeff = calibrationData["moisture_coeff"] | 0.08;
  return (nir_data[10] * coeff + nir_data[0] * (coeff/2));
}

void logEvent(const String& eventType, const String& message) {
  Serial.print("LOG [" + eventType + "]: ");
  Serial.println(message);

  File file = SPIFFS.open(DEVICE_LOG_FILE, FILE_APPEND);
  if (!file) {
    Serial.println("Failed to open log file for appending");
    return;
  }
  file.print(getFormattedDateTime());
  file.print(" [" + eventType + "]: ");
  file.println(message);
  file.close();
}

void saveToLocalStorage(const String& dataType, const JsonDocument& data) {
  String filePath = "/pending_" + dataType + "_" + String(millis()) + ".json";
  File file = SPIFFS.open(filePath, FILE_WRITE);
  if (!file) {
    Serial.println("Failed to open file for writing: " + filePath);
    return;
  }
  serializeJson(data, file);
  file.close();
  Serial.println("Saved to local storage: " + filePath);
}

void loadPendingData() {
  // This function is called at boot to attempt syncing any previously failed data.
  // Actual syncing logic is in syncPendingData().
}

bool isServerAvailable() {
  // Simple check if server is reachable
  HTTPClient http;
  http.begin(SERVER_URL + "/health"); // Assuming a health check endpoint
  int httpResponseCode = http.GET();
  http.end();
  return (httpResponseCode == 200);
}

void displayCurrentMode() {
  String modeString;
  switch (currentMode) {
    case MODE_BASIC: modeString = "أساسي"; break;
    case MODE_PROFESSIONAL: modeString = "احترافي"; break;
    case MODE_ADVANCED: modeString = "متقدم"; break;
    case MODE_CUSTOM: modeString = "مخصص"; break;
    case MODE_BLEND_PROFILES: modeString = "ملفات خلطات"; break;
    case MODE_ADD_KNOWLEDGE: modeString = "إضافة معرفة"; break;
    case MODE_WIFI_SETUP: modeString = "إعداد WiFi"; break;
    default: modeString = "غير معروف"; break;
  }
  drawScreen("الوضع الحالي:", modeString, "", "");
}

void displayMeasurementResults() {
  String typeStr;
  switch(currentCoffeeType) {
    case COFFEE_GREEN: typeStr = "أخضر"; break;
    case COFFEE_ROASTED: typeStr = "محمص"; break;
    case COFFEE_GROUND: typeStr = "مطحون"; break;
    case COFFEE_UNKNOWN_TYPE: typeStr = "غير محدد"; break;
  }

  String originStr;
  switch(currentCoffeeOrigin) {
    case ORIGIN_BRAZIL: originStr = "البرازيل"; break;
    case ORIGIN_COLOMBIA: originStr = "كولومبيا"; break;
    case ORIGIN_COSTA_RICA: originStr = "كوستاريكا"; break;
    case ORIGIN_HONDURAS: originStr = "هندوراس"; break;
    case ORIGIN_GUATEMALA: originStr = "غواتيمالا"; break;
    case ORIGIN_INDIA: originStr = "الهند"; break;
    case ORIGIN_INDONESIA: originStr = "إندونيسيا"; break;
    case ORIGIN_VIETNAM: originStr = "فيتنام"; break;
    case ORIGIN_PERU: originStr = "بيرو"; break;
    case ORIGIN_TANZANIA: originStr = "تنزانيا"; break;
    case ORIGIN_UGANDA: originStr = "أوغندا"; break;
    case ORIGIN_ETHIOPIA: originStr = "إثيوبيا"; break;
    case ORIGIN_IVORY_COAST: originStr = "ساحل العاج"; break;
    case ORIGIN_YEMEN: originStr = "اليمن"; break;
    case ORIGIN_SCA: originStr = "SCA"; break;
    case ORIGIN_GLOBAL_ARABICA: originStr = "أرابيكا عام"; break;
    case ORIGIN_GLOBAL_ROBUSTA: originStr = "روبوستا عام"; break;
    case ORIGIN_UNKNOWN: originStr = "غير محدد"; break;
  }

  drawScreen("نتائج القياس:",
             "النوع: " + typeStr + "، الأصل: " + originStr,
             "CO2: " + String(estimatedCO2, 2) + "%, رطوبة: " + String(estimatedMoisture, 2) + "%",
             "بروتين: " + String(estimatedProtein, 2) + "%, معادن: " + String(estimatedMinerals, 2) + "%");
}

void addKnowledgeBaseEntry(const String& sampleName, const String& chemicalDataJson, const String& sensorDataJson, CoffeeType type, CoffeeOrigin origin) {
  if (WiFi.status() != WL_CONNECTED) {
    logEvent("Knowledge Base", "Cannot add knowledge entry offline.");
    return;
  }

  HTTPClient http;
  String url = SERVER_URL + "/api/knowledge";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  DynamicJsonDocument doc(1024);
  doc["device_serial"] = deviceSerial;
  doc["sample_name"] = sampleName;
  doc["chemical_data"] = serialized(chemicalDataJson); // Assuming chemicalDataJson is a valid JSON string
  doc["sensor_data"] = serialized(sensorDataJson); // Assuming sensorDataJson is a valid JSON string
  doc["coffee_type"] = type;
  doc["coffee_origin"] = origin;
  doc["status"] = "pending_owner_approval"; // New entries require owner approval

  String jsonString;
  serializeJson(doc, jsonString);

  int httpResponseCode = http.POST(jsonString);

  if (httpResponseCode == 200 || httpResponseCode == 201) {
    logEvent("Knowledge Base", "Knowledge entry sent for approval.");
  } else {
    logEvent("Knowledge Base", "Failed to send knowledge entry. HTTP code: " + String(httpResponseCode));
    saveToLocalStorage("knowledge", doc);
  }
  http.end();
}

void saveKnowledgeBaseEntry(const JsonDocument& entry) {
  // This function is primarily for local caching if needed, but main storage is server-side.
  // For now, it just logs.
  logEvent("Knowledge Base", "Attempted to save knowledge entry locally.");
}

void loadKnowledgeBaseEntries(JsonArray& knowledgeArray) {
  // This function would load cached knowledge entries if any, but main source is server.
  logEvent("Knowledge Base", "Attempted to load knowledge entries locally.");
}

void requestCoffeeTypeAndOriginFromOwner() {
  // This function would trigger a notification on the owner's interface (e.g., web dashboard)
  // to prompt them to select the coffee type and origin for the current measurement.
  // For ESP32, it means waiting for a server command.
  drawScreen("تحديد نوع البن", "الرجاء تحديد النوع والأصل", "عبر واجهة المالك", "");
  logEvent("Owner Control", "Requested coffee type and origin from owner.");
  // In a real system, this would block or periodically check a server endpoint for the owner's input.
  // For now, it's a placeholder.
}


