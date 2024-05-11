// Copyright (C) 2024 Philip Edwards

#pragma once

bool IsWifiConnected();
void ConnectWifi();
void broadcast_update();
void broadcast_reset();

void hal_setup(void);
void hal_loop(void);
