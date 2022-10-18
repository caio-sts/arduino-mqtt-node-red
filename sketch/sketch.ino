#include <WiFiEsp.h>
#include <WiFiEspClient.h>
#include <PubSubClient.h>
#include "SoftwareSerial.h"
#include "DHT.h"

//Colocar aqui os dados do servidor
#define WIFI_AP "CARLOS ADP"
#define WIFI_PASSWORD "12991308"
char server[50] = "192.168.1.113";

WiFiEspClient espClient;
PubSubClient client(espClient);

//Pin2: RX
//Pin3: TX
SoftwareSerial soft(2, 3);

//PinA1: Temperature Sensor
const int lm35_pin = A1;

//PinA2: DHT Sensor
#define DHTPIN A2
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

unsigned long lastSend;
int status = WL_IDLE_STATUS;

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  for (int i=0;i<length;i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();
}

void setup() {
    Serial.begin(9600);
    InitWiFi();
    client.setServer( server, 1883 );
    client.setCallback(callback);
    lastSend = 0;
    dht.begin();

    client.subscribe("receiveDataLed");
}

void loop() {
    status = WiFi.status();
    if(status != WL_CONNECTED) {
        reconnectWifi();
    }
    if(!client.connected() ) {
        reconnectClient();
    }
    if(millis() - lastSend > 2000 ) {
        sendDataTemperature();
        sendDataDHTemperature();
        sendDataDHumidity();
        lastSend = millis();
    }
    client.loop();
}

void sendDataDHTemperature()
{
    float t = dht.readTemperature();

    // JSON String...
    String payload = String(t, 2);

    // Send payload
    char attributes[100];
    payload.toCharArray( attributes, 100 );
    client.publish( "DHTemperature", attributes );
}

void sendDataDHumidity()
{
    float h = dht.readHumidity();

    // JSON String...
    String payload = String(h, 2);

    // Send payload
    char attributes[100];
    payload.toCharArray( attributes, 100 );
    client.publish( "DHumidity", attributes );
}

void sendDataTemperature()
{
    int temp_adc_val;
    float temp_val;
    temp_adc_val = analogRead(lm35_pin);
    temp_val = (temp_adc_val * 4.88);
    temp_val = (temp_val/10);

    // JSON String...
    String payload = String(temp_val, 2);

    // Send payload
    char attributes[100];
    payload.toCharArray( attributes, 100 );
    client.publish( "Temperature", attributes );
}

void InitWiFi()
{
    soft.begin(9600);
    WiFi.init(&soft);
    if (WiFi.status() == WL_NO_SHIELD) {
        Serial.println("Modulo Wifi nao esta funcionando corretamente.");
        while (true);
    }
    reconnectWifi();
}

void reconnectWifi() {
    Serial.println("Iniciando conexao com a rede Wifi");
    while(status != WL_CONNECTED) {
        Serial.print("Tentando efetuar conexao com a rede SSID: ");
        Serial.println(WIFI_AP);
        status = WiFi.begin(WIFI_AP, WIFI_PASSWORD);
        delay(500);
    }
    Serial.println("Conexao efetuado com sucesso.");
}

void reconnectClient() {
    while(!client.connected()) {
        Serial.print("Conectando a: ");
        Serial.println(server);
        String clientId = "ESP8266Client-" + String(random(0xffff), HEX);
        if(client.connect(clientId.c_str())) {
            client.subscribe("receiveDataLed");
            Serial.println("[DONE]");
        } else {
            Serial.print( "[FAILED] [ rc = " );
            Serial.print( client.state() );
            Serial.println( " : retrying in 2 seconds]" );
            delay( 2000 );
        }
    }
}
