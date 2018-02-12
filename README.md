# GPSLogger
GPS Logger

Made to log GPS from a raspberry Pi.

Hardware:

Navspark Mini hardwired to GPIO UART pins, running at baud of 115200.
  (I broke my Serial->USB converter, so I hardwired it)
Arduino Nano clone for TPS input over USB. 
  (Could be a DAC instead, but I might want multiple inputs later for RPM/Brake/Etc)

A separate nano w/ Adafruit's GPS shield logging to an SD card for tagging the cones pre-race.
Then you plug the SD card into the pi, 
