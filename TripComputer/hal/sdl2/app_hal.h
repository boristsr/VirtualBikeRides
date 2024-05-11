#ifndef DRIVER_H
#define DRIVER_H

#ifdef __cplusplus
extern "C" {
#endif


void hal_setup(void);
void hal_loop(void);

bool IsWifiConnected();
void ConnectWifi();
void broadcast_update();
void broadcast_reset();


#ifdef __cplusplus
} /* extern "C" */
#endif

#endif /*DRIVER_H*/
