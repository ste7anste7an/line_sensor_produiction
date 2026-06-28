# Firmware for Line Sensor Modules

## DUT (Device under test)

This is the production firmware to be flashed on every new module. this firmware listens to I2C address 0x33.

## TU (Test unit)
This is the firmware to be flashed on the Test Unit (TU). It is identical to the firmware for the DUT, but only listenes to address 0x34 on I2C.
