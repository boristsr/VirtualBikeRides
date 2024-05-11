// Copyright (C) 2024 Philip Edwards

#ifdef ARDUINO
#include <Arduino.h>
#else
#include <stdio.h>
#endif

#include "lv_conf.h"
#include "lvgl.h"
#include "app_hal.h"

#include "demos/lv_demos.h"

static const lv_font_t * font_small = &lv_font_montserrat_14;
static const lv_font_t * font_large = &lv_font_montserrat_48;

lv_obj_t *cycles_label = nullptr;
lv_obj_t *wifi_label = nullptr;

void setup_gui()
{
    // Create a screen object
    lv_obj_t *scr = lv_scr_act();

    // Create a status bar at the top
    lv_obj_t *status_bar = lv_obj_create(scr);
    lv_obj_set_width(status_bar, lv_pct(100));  // Set width to 100%
    lv_obj_set_height(status_bar, lv_pct(20));  // Set height to 10% of the screen
    lv_obj_align(status_bar, LV_ALIGN_TOP_MID, 0, 0);
    lv_obj_set_scrollbar_mode(status_bar, LV_SCROLLBAR_MODE_OFF);  // Turn off scrollbars

    // Add a label for WiFi status
    wifi_label = lv_label_create(status_bar);
    lv_label_set_text(wifi_label, "WiFi: Connecting...");  // Update with actual WiFi status
    lv_obj_align(wifi_label, LV_ALIGN_LEFT_MID, 0, 0);

    // Create a large label for cycles in the center of the screen
    cycles_label = lv_label_create(scr);
    lv_obj_set_style_text_font(cycles_label, font_large, LV_STATE_DEFAULT);  // Set a large font size
    lv_label_set_text(cycles_label, "12345");  // Example cycles
    lv_obj_align(cycles_label, LV_ALIGN_CENTER, 0, 0);

    // Adjust alignment to ensure it's below the status bar
    lv_obj_align_to(cycles_label, status_bar, LV_ALIGN_OUT_BOTTOM_MID, 0, 30);
}

void setup()
{
    lv_init();

    hal_setup();
    setup_gui();
}

void draw_wifi_status(lv_obj_t * obj) {
    if (!obj) {
        return;
    }
    const int max_length = 50;
    char wifi_status[max_length] = {0};
    sprintf(wifi_status, "%s %s", LV_SYMBOL_WIFI, IsWifiConnected() ? "Connected" : "Disconnected");
    //snprintf(wifi_status, max_length, "%s: Connected", LV_SYMBOL_WIFI);
    lv_label_set_text(obj, wifi_status);
}

void draw_cycles_value(lv_obj_t * obj, int cycles) {
    if (!obj) {
        return;
    }
    const int max_length = 10;
    char cycles_value[max_length];
    snprintf(cycles_value, max_length, "%d", cycles);
    lv_label_set_text(obj, cycles_value);
    lv_obj_align(obj, LV_ALIGN_CENTER, 0, 0);
}

int cycle_count = 0;

int increment_cycles()
{
    return ++cycle_count;
}

int get_cycles()
{
    return cycle_count;
}

void loop()
{
    draw_wifi_status(wifi_label);
    draw_cycles_value(cycles_label, cycle_count);  // Example cycles

    hal_loop();
    lv_task_handler();
}


#ifndef ARDUINO
void startloop() 
{
    while (1)
    {
        loop();
    }
}

int main(void)
{
    setup();
    startloop();
}
#endif
