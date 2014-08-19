
/***************************************************
  Adafruit CC3000 Breakout/Shield TCP Chat Server
    
  This is a simple chat server which allows clients to connect
  with telnet and exchange messages.  Anything sent by one
  client will be written out to all connected clients.

  See the CC3000 tutorial on Adafruit's learning system
  for more information on setting up and using the
  CC3000:
    http://learn.adafruit.com/adafruit-cc3000-wifi  
    
  Requirements:
  
  This sketch requires the Adafruit CC3000 library.  You can
  download the library from:
    https://github.com/adafruit/Adafruit_CC3000_Library
  
  For information on installing libraries in the Arduino IDE
  see this page:
    http://arduino.cc/en/Guide/Libraries
  
  Usage:
    
  Update the SSID and, if necessary, the CC3000 hardware pin 
  information below, then run the sketch and check the 
  output of the serial port.  After connecting to the 
  wireless network successfully the sketch will output 
  the IP address of the server and start listening for 
  connections.  Once listening for connections, connect
  to the server from your computer  using a telnet client
  on port 23.  
           
  For example on Linux or Mac OSX, if your CC3000 has an
  IP address 192.168.1.100 you would execute in a command
  window:
  
    telnet 192.168.1.100 23
           
  Connect multiple clients and notice that whatever one client
  sends will be echoed to all other clients.  Press ctrl-] and 
  type quit at the prompt to close the telnet session.
           
  On Windows you'll need to download a telnet client.  PuTTY 
  is a good, free GUI client: 
    http://www.chiark.greenend.org.uk/~sgtatham/putty/
  
  License:
 
  This example is copyright (c) 2013 Tony DiCola (tony@tonydicola.com)
  and is released under an open source MIT license.  See details at:
    http://opensource.org/licenses/MIT
  
  This code was adapted from Adafruit CC3000 library example 
  code which has the following license:
  
  Designed specifically to work with the Adafruit WiFi products:
  ----> https://www.adafruit.com/products/1469

  Adafruit invests time and resources providing this open source code, 
  please support Adafruit and open-source hardware by purchasing 
  products from Adafruit!

  Written by Limor Fried & Kevin Townsend for Adafruit Industries.  
  BSD license, all text above must be included in any redistribution      
 ****************************************************/
#include <Adafruit_CC3000.h>
#include <SPI.h>

// These are the interrupt and control pins
#define ADAFRUIT_CC3000_IRQ   1  // MUST be an interrupt pin!
// These can be any two pins
#define ADAFRUIT_CC3000_VBAT  5
#define ADAFRUIT_CC3000_CS    11
// Use hardware SPI for the remaining pins
// On an UNO, SCK = 13, MISO = 12, and MOSI = 11
Adafruit_CC3000 cc3000 = Adafruit_CC3000(ADAFRUIT_CC3000_CS, ADAFRUIT_CC3000_IRQ, ADAFRUIT_CC3000_VBAT,
                                         SPI_CLOCK_DIVIDER); // you can change this clock speed

#define WLAN_SSID       "SSID"           // cannot be longer than 32 characters!
#define WLAN_PASS       "Password"
// Security can be WLAN_SEC_UNSEC, WLAN_SEC_WEP, WLAN_SEC_WPA or WLAN_SEC_WPA2
#define WLAN_SECURITY   WLAN_SEC_WPA2

#define LISTEN_PORT           23    // What TCP port to listen on for connections.

// Used to pulse the connection heartbeat
unsigned long startTime = 0;
#define heartbeat 1000 // Delay between heartbeats

Adafruit_CC3000_Server chatServer(LISTEN_PORT);

// octet of the IP address to display
int octet = 0;

/* Trellis definitions */
#include <Wire.h>
#include "Adafruit_Trellis.h"

Adafruit_Trellis matrix0 = Adafruit_Trellis();
Adafruit_TrellisSet trellis =  Adafruit_TrellisSet(&matrix0);
// set to however many you're working with here, up to 8
#define NUMTRELLIS 1
#define numKeys (NUMTRELLIS * 16)

// This Led is used to indicate if mobo is recording
#define recordPin 1

/* Pots */
#define totalPots 3
const char potLabels[] = "ABC";
const int potPins[totalPots] = {A3, A5, A4};
int lastPotVals[totalPots] = {0, 0, 0};

void setup(void)
{
  /* Trellis setup */
  // begin() with the addresses of each panel in order
  trellis.begin(0x70);  // only one
  // light up all the LEDs in order
  for (uint8_t i=0; i<numKeys; i++) {
    trellis.setLED(i);
    trellis.writeDisplay();
    delay(50);
  }
  // then turn them off
  for (uint8_t i=0; i<numKeys; i++) {
    trellis.clrLED(i);
    trellis.writeDisplay();    
    delay(50);
  }
  
  /* Wifi setup: Indicate start of attempting to connect to wifi */
  trellis.setLED(0);
  trellis.writeDisplay();
  
  /* Initialize the module */
  if (!cc3000.begin())
  {
    /* Unable to start the wifi indicate the error */
    trellis.clrLED(0);
    while(1) {
        trellis.setLED(1);
        trellis.writeDisplay();
        delay(100);
        trellis.clrLED(1);
        trellis.writeDisplay();
        delay(100);
    }
  }
  
  /* show the second led to indicate attempting to connect to wifi network */
  trellis.setLED(1);
  trellis.writeDisplay();
  
  //Serial.print(F("\nAttempting to connect to ")); Serial.println(WLAN_SSID);
  if (!cc3000.connectToAP(WLAN_SSID, WLAN_PASS, WLAN_SECURITY)) {
    //Serial.println(F("Failed!"));
    while(1);
  }
   
  /* Show the third led to indicate connection to AP and start of finding ip address by dhcp */
  trellis.setLED(2);
  trellis.writeDisplay();

  while (!cc3000.checkDHCP())
  {
    delay(100); // ToDo: Insert a DHCP timeout!
  }  

  /* Display the IP address DNS, Gateway, etc. */  
  while (! displayConnectionDetails()) {
    delay(1000);
  }

  // Start listening for connections
  chatServer.begin();
  
  /* Turn off the leds so we know we are connected */
  trellis.clrLED(0);
  trellis.clrLED(1);
  trellis.clrLED(2);
  trellis.writeDisplay();
}

void loop(void)
{
  delay(30); // 30ms delay is required(trellis), dont remove me!
  
  // Try to get a client which is connected.
  Adafruit_CC3000_ClientRef client = chatServer.available();
  if (client) {
     // Check if there is data available to read.
     if (client.available() > 0) {
       // Read a byte and write it to all clients.
       uint8_t ch = client.read();
       if (ch == 114) { //r
         trellis.setLED(recordPin);
         trellis.writeDisplay();
       } else if (ch == 115) { //s
         trellis.clrLED(recordPin);
         trellis.writeDisplay();
       }
     }
   }
   /* Check for button presses */
  if (trellis.readSwitches()) {
    for (uint8_t i=0; i<numKeys; i++) {
      // if it was pressed, turn it on
      if (trellis.justPressed(i)) {
        sendButtonIndex(i, true);
      } 
      // if it was released, turn it off
      if (trellis.justReleased(i)) {
        sendButtonIndex(i, false);
      }
    // tell the trellis to set the LEDs we requested
    trellis.writeDisplay();
    }
  }
  
  int potVal;
  for (int i=0; i < totalPots; i++) {
    potVal = potPins[i];
    potVal = analogRead(potPins[i]);
    if (newPotVal(potVal, lastPotVals[i])) {
      // Send p for pot, then pot identifier, then pot value "pb257\r\n"
      chatServer.print("p");
      chatServer.print(potLabels[i]);
      chatServer.println(potVal);
      lastPotVals[i] = potVal;
    }
    delay(10);
  }
  
  /* Pulse the heartbeat so Motion Builder know's its still connected to the remote */
   if (millis() - startTime > heartbeat) {
     chatServer.println("Beat");
     startTime = millis();
   }
}

/* Should probably use a debounce capacitor instead of this function */
#define slop 5
bool newPotVal(int val, int lastVal) {
  return (lastVal < val - slop || val + slop < lastVal);
}

void sendButtonIndex(int index, boolean down) {
  if (down) {
    chatServer.print("dn");
  } else {
    chatServer.print("up");
  }
  if (index < 10) {
    chatServer.print(0);
  }
  // Send button presses, dn or up then button index
  // dn01\r\n, dn12\r\n, up01\r\n, up14\r\n
  chatServer.println(index);
  if (index != recordPin) {
    /* NOTE: Make sure to call trellis.writeDisplay() to update the leds */
    if (down) {
      trellis.setLED(index);
    } else {
      trellis.clrLED(index);
    }
  }
}

/**************************************************************************/
/*!
    @brief  Tries to read the IP address and other connection details
*/
/**************************************************************************/
bool displayConnectionDetails(void)
{
  uint32_t ipAddress, netmask, gateway, dhcpserv, dnsserv;
  
  if(!cc3000.getIPAddress(&ipAddress, &netmask, &gateway, &dhcpserv, &dnsserv))
  {
    //Serial.println(F("Unable to retrieve the IP Address!\r\n"));
    return false;
  }
  else
  {
    trellis.setLED(8);
    while (1) {
      if (trellis.readSwitches()) {
        for (uint8_t i=12; i<16; i++) {
          if (trellis.justPressed(i)) {
            octet = i - 12;
            break;
          }
        }
        if (trellis.justPressed(8)) {
          // Clear display and Exit ip display mode
          displayBinary(0, 0);
          displayBinary(0, 8);
          return true;
        }
      }
      
      for (int i=0; i<4; i++ ) {
        if (i == octet) {
          trellis.setLED(12 + i);
        } else {
          trellis.clrLED(12 + i);
        }
      }
      
      displayBinary(ipAddress >> (8 * octet), 0);
      delay(30);
    }
    return true;
  }
}

/* http://www.multiwingspan.co.uk/arduino.php?page=led5 */
void displayBinary(byte numToShow, int offset) {
  for (int i =0; i<8; i++) {
    if (bitRead(numToShow, i)==1) {
      trellis.setLED(i + offset);
    } else {
      trellis.clrLED(i + offset);
    }
  }
  trellis.writeDisplay();
}
