# Line tracking sensor test protocol

## Objective

The tests confirm that these components are properlyworking:

- USB connector
- 2× Qwiic connectors
- 2×3 UART connector
- 9 RGB LEDs
- 2 buttons
- 8 IR sensors
  - emitters
  - detectors

## General overview test
The test will be performed by a firmware residing on the LMS-ESP32v2. The ESP32 communicates through I2C with two Line Sensor boards. One Line Sensor board, called the Test Unit (**TU**), will be used in all tests and has I2C address 0x34. 
Each test is performed on a Device Under Test (DUT) which is first flash with the production firmware and is then connected with one QWIIC port to the TU and with the other QWIIC port to the LMS-ESP32. 
By mounting the two Line Sensor boards (DUT and TU) in opposite directions, the emitters of the TU can be used to test the IR sensors of the DUT and the IR sensors of the TU will be used to test the IR emitters of the DUT.

## Preparation (set up once)

1. Download [WCHIPTool](https://www.wch-ic.com/downloads/WCHISPTool_Setup_exe.html)
2. Download firmware from this repository: `CH32_TU_line_sensor_i2c_0x34.bin` and `CH32_production_line_sensor_i2c.bin`
1. Flash **TU** (test unit — one line-sensor board used for all tests) with `CH32_TU_line_sensor_i2c_0x34.bin`
  a. connect TU board with USB to PC
  b. Start WCHISPtool and open  `CH32_TU_line_sensor_i2c_0x34.bin`
  c. While holding BOOT/CAL button press RESET button on TU
  d. The USB device should show up in WCHISPtool
  e. Download the firmware
3. Flash LMS-ESP32 with `ESP32_line_sensor_test.bin` starting at `0x0` using esptool.
4. Prepare a 10kOhm resistor connected to two female DuPont cables

  <img width="401" height="530" alt="image" src="https://github.com/user-attachments/assets/d179f15f-a026-424d-b28e-f8d7c65d0a45" />

## Test procedure for each DUT (device under test)

### USB + buttons

1. Connect DUT with USB to PC
2. Start WCHIPTool
3. Keep BOOT button pressed while pressing RESET button
4. USB device should appear in WCHIPTool (buttons and USB work)
5. Flash firmware `CH32_production_line_sensor_i2c.bin`
6. Check first 8 RGB LEDs scanning 3 times in different collors (confirms RGB blue LEDs work)
7. Press BOOT/CAL button — CALIBRATE LED (9th) should start flashing BLUE and turns GREEN after a few seconds
8. Use a voltage meter to measure the coltage betweenGND and 3V3 on the 2x3 header. The voltage should be 3V3. (voltage regulator and pins 2x3 header work) 
9. Disconnect USB


### Test setup

Once both Line Sensor boards are flashed with the DUT and UT firmware, mount both boards mirrored to each other with the sensors pointing towards each other. 
Use spacers to keep the distance at approx 10mm.



<img width="399" height="719" alt="image" src="https://github.com/user-attachments/assets/719b527f-22d9-48b5-b40f-0e8fd8cc6fba" />

Connect the 10kOhm restister between the TX and RX pins of the 2x3 header\

<p>>
<img width="388" height="366" alt="image" src="https://github.com/user-attachments/assets/02d6a105-3075-4814-98e7-9d9b0a2f02b1" />
</p>

<p>
<img width="388" height="708" alt="image" src="https://github.com/user-attachments/assets/d0b1b04b-ba82-4627-b37a-5666063c32f0" />
</p>

### Sensor testing + Qwiic connectors

1. Connect one QWIIC port of DUT to LMS-ESP32 using Qwiic cable
2. Connect other QWIIC port of DUT to TU using Qwiic cable
3. Mount DUT mirror opposite to TU as indicated in the picture above
4. Connect LMS-ESP32 with USB to serial monitor
5. Press RESET on LMS-ESP32 and log serial output (115200 kbit/s)
6. LED S1: Green -> QWIIC cables OK
7. LED S2: Green -> TX and RX pins OK on 2x3 header
8. LED S3: Green -> IR sensors and IR emitter OK for DUT
  
