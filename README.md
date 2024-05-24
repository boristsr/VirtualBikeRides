# Virtual Bike Rides

This is a project add a videoplayer to a mini exercise bike. You can read more about the project on the project page here: [Build Instructions](https://www.gdcorner.com/blog/2024/05/24/VirtualBike.html)

This repository contains 3 main components:

- kicad - The PCB design for the Trip Computer replacement
- TripComputer - The firmware for the Trip Computer
- VirtualBike - The software for the Virtual Bike Rides

## Trip Computer

The Trip Computer is a replacement for the original trip computer on the mini exercise bike. It uses an ESP32 microcontroller to read the wheel speed sensor and display the number of cycles on the screen. It also broadcasts these cycle counts over WiFi for the video player to read.

### Build instructions

The project is build in PlatformIO which makes it easy to build and upload the firmware to the ESP32.

- Configure the WiFi settings in `TripComputer/hal/tdisplay/app_hal.cpp` near the top of the file
- Open the project in PlatformIO
- Build the firmware for the TDisplay board
- PlatformIO will download the required libraries and build the firmware
- The display libraries required some modifications for the TDisplay board. PlatformIO will overwrite these changes when it downloads the libraries. Using git you should see the files that have changed and can revert them back to the correct state. The files are:
  - `TripComputer\.pio\libdeps\tdisplay\lvgl\lv_conf.h`
  - `TripComputer\.pio\libdeps\tdisplay\TFT_eSPI\User_Setup_Select.h`
- Rebuild and upload the firmware to the Trip Computer

## Video Player

The video player is a python program to play videos. It uses the PyGame and OpenCV libraries to display the video.

### Install Requirements and Run

```powershell
# Create virtual environment
python3 -m venv .venv
.venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt

# Run the bike ride app
python VirtualBike.py
```

### Broadcast Simulator

For quicker iteration of the video player without needing to physically pedal the bike you can run the bike_broadcast_simulator.py script. This will broadcast valid packets to the bike ride app.

```powershell
# Run the broadcast simulator
python bike_broadcast_simulator.py
```

### Build standalone exe for Windows

```powershell
pip install pyinstaller
pyinstaller VirtualBike.py
```
