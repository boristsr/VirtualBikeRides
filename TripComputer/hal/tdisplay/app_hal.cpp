// Copyright (C) 2024 Philip Edwards

#include <TFT_eSPI.h>
#include "lvgl.h"
#include "app_hal.h"
#include <Arduino.h>
#include <WiFi.h>
#include "main.h"

const int BROADCAST_UDP_PORT = 20203;
int sensorPin = 21; // Pin21 is the magenetic switch

const char* wifi_ssid = "YOUR SSID HERE";
const char* wifi_password = "YOUR WIFI PASSWORD HERE";

TFT_eSPI tft = TFT_eSPI();

//Some boiler plate code to init LVGL from here: https://daumemo.com/how-to-use-lvgl-library-on-arduino-with-an-esp-32-and-spi-lcd/
const int LV_HOR_RES_MAX = 240;
//static lv_disp_buf_t disp_buf;
static lv_disp_draw_buf_t disp_buf;
static lv_color_t buf[LV_HOR_RES_MAX * 10];
lv_disp_drv_t disp_drv;

lv_obj_t *btn1;
lv_obj_t *btn2;
lv_obj_t *screenMain;
lv_obj_t *label;

void flush_display(lv_disp_drv_t *disp, const lv_area_t *area, lv_color_t *color_p)
{
    uint32_t w = (area->x2 - area->x1 + 1);
    uint32_t h = (area->y2 - area->y1 + 1);
    uint32_t wh = w*h;

    tft.startWrite();
    tft.setAddrWindow(area->x1, area->y1, w, h);
    //not using adafruit display lib, so comment out this
    //while (wh--) tft.pushColor(color_p++->full);
    //and add this
    tft.pushColors(&color_p->full, w * h, true);
    tft.endWrite();

    lv_disp_flush_ready(disp);
}

void setup_lvgl_tft_screen()
{
    tft.begin();

    tft.setRotation(1);
    tft.fillScreen(TFT_BLACK);
    /*Initialize the display*/
    lv_init();
    lv_disp_draw_buf_init(&disp_buf, buf, NULL, LV_HOR_RES_MAX * 10);
    lv_disp_drv_init(&disp_drv);
    disp_drv.hor_res = 240;
    disp_drv.ver_res = 135;
    disp_drv.flush_cb = flush_display;
    disp_drv.draw_buf = &disp_buf;
    //disp_drv.buffer = &disp_buf;
    lv_disp_drv_register(&disp_drv);
}

void ConnectWifi()
{
    WiFi.mode(WIFI_STA);
    WiFi.begin(wifi_ssid, wifi_password);
    Serial.println("\nConnecting to WiFi Network ..");
}

bool IsWifiConnected()
{
    return WiFi.status() == WL_CONNECTED;
}

IPAddress GetBroadcastAddress()
{
    IPAddress broadcastIP = WiFi.localIP();
    broadcastIP[3] = 255;
    return broadcastIP;
}


IPAddress BroadcastIP;
bool countIsDirty = false;
unsigned int packet_idx = 0;
unsigned long last_cycle_time = 0;
unsigned long last_broadcast_time = millis();
unsigned long debounce_time = 300;
unsigned long broadcast_heartbeat_time = 1000;

void hal_setup(void)
{
    Serial.begin(9600);
    ConnectWifi();
    pinMode(sensorPin, INPUT_PULLUP);
    //set an interrupt for the button on sensorPin
    attachInterrupt(digitalPinToInterrupt(sensorPin), [](){
        if(millis() > last_cycle_time + debounce_time)
        {
            increment_cycles();
            countIsDirty = true;
            last_cycle_time = millis();
        }
    }, FALLING);

    setup_lvgl_tft_screen();
    //tick lvgl once to get the screen to show up
    lv_task_handler();
}

void broadcast_update()
{
    countIsDirty = false;
    packet_idx++;
    char message[100];
    sprintf(message, "VBC:%d,%d", packet_idx, get_cycles());
    uint8_t broadcast_message_buffer[100];
    memcpy(broadcast_message_buffer, message, 100);
    broadcast_message_buffer[99] = '\0';
    //broadcast the message to the broadcast IP
    if(IsWifiConnected())
    {
        WiFiUDP udp;
        udp.beginPacket(BroadcastIP, BROADCAST_UDP_PORT);
        udp.write(broadcast_message_buffer, strnlen(message, 100));
        udp.endPacket();
        last_broadcast_time = millis();
    }
    Serial.println(message);
    Serial.println(BroadcastIP.toString());
}

void broadcast_reset()
{
    countIsDirty = false;
    packet_idx++;
    char message[100];
    sprintf(message, "VBR:%d,%d", packet_idx, get_cycles());
    uint8_t broadcast_message_buffer[100];
    memcpy(broadcast_message_buffer, message, 100);
    broadcast_message_buffer[99] = '\0';
    //broadcast the message to the broadcast IP
    if(IsWifiConnected())
    {
        WiFiUDP udp;
        udp.beginPacket(BroadcastIP, BROADCAST_UDP_PORT);
        udp.write(broadcast_message_buffer, strnlen(message, 100));
        udp.endPacket();
        last_broadcast_time = millis();
    }
    Serial.println(message);
    Serial.println(BroadcastIP.toString());
}


bool was_wifi_connected = false;
void hal_loop(void)
{
    if(IsWifiConnected() && was_wifi_connected == false)
    {
        BroadcastIP = GetBroadcastAddress();
        was_wifi_connected = true;
        broadcast_reset();
    }
    if(millis() > last_broadcast_time + broadcast_heartbeat_time)
    {
        broadcast_update();
    }
    if(countIsDirty)
    {
        broadcast_update();
    }
}
