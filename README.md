# Line Sensor Test Protocol

## Summary

### One-time setup

Perform these steps once before testing a batch of DUTs:

* Flash `CH32_TU_line_sensor_i2c_0x34.bin` to the **Test Unit (TU)**.
* Flash `ESP32_line_sensor_test.bin` to the **LMS-ESP32v2**.
* Prepare a **10 kΩ resistor** with two female DuPont connectors.
* Connect the TU to the LMS-ESP32v2 test setup.
* Connect the LMS-ESP32v2 to a PC via USB and open a serial terminal.

### For each DUT

Repeat the following steps for every new Device Under Test (DUT):

1. Flash `CH32_production_line_sensor_i2c.bin` to the DUT.
2. Verify USB operation, buttons, RGB LEDs, and the 3.3 V supply.
3. Mount the DUT opposite the TU with the IR sensors facing each other (approximately 10 mm spacing).
4. Connect one Qwiic connector of the DUT to the LMS-ESP32v2.
5. Connect the second Qwiic connector of the DUT to the TU.
6. Connect the **10 kΩ resistor** between the DUT **TX** and **RX** pins.
7. Press **RESET** on the LMS-ESP32v2.
8. Verify that the DUT LEDs perform a red, green, and blue scan.
9. Verify that status LEDs **S1**, **S2**, and **S3** all turn green.
10. If any status LED turns red, the DUT has failed. Begin troubleshooting.
11. Disconnect the DUT and continue with the next board.


---

## Objective

This test verifies the correct operation of the following components:

* USB connector
* Two Qwiic connectors
* 2×3 UART header
* Nine RGB LEDs
* Two push buttons
* Eight IR sensors

  * IR emitters
  * IR detectors

---

## General Overview

The LMS-ESP32v2 communicates over I²C with two Line Sensor boards:

* A permanent **Test Unit (TU)** with I²C address **0x34**
* The **Device Under Test (DUT)**

The DUT is first flashed with the production firmware and connected to both the TU and the LMS-ESP32v2 via its two Qwiic connectors.

During testing, the TU and DUT are mounted facing each other. This allows:

* The TU IR emitters to test the DUT IR receivers.
* The DUT IR emitters to test the TU IR receivers.

This verifies the complete IR sensing system without requiring external test equipment.

---

# Preparation (performed once)

1. Download **WCHISPTool**:
   https://www.wch-ic.com/downloads/WCHISPTool_Setup_exe.html

2. Download the following firmware files from this repository:

   * `CH32_TU_line_sensor_i2c_0x34.bin`
   * `CH32_production_line_sensor_i2c.bin`
   * `ESP32_line_sensor_test.bin`

3. Flash the **Test Unit (TU)**.

   a. Connect the TU to the PC using USB.

   b. Start **WCHISPTool** and open:

   `CH32_TU_line_sensor_i2c_0x34.bin`

   c. While holding the **BOOT/CAL** button, press **RESET**.

   d. Verify that the USB device appears in WCHISPTool.

   e. Program the firmware.

4. Flash the LMS-ESP32v2 with:

   `ESP32_line_sensor_test.bin`

   at flash address **0x0** using **esptool**.

5. Prepare a **10 kΩ resistor** fitted with two female DuPont connectors.

*(Insert resistor image here.)*

---

# Test Procedure for Each DUT

## 1. USB and Button Test

1. Connect the DUT to the PC via USB.

2. Start WCHISPTool.

3. Hold the **BOOT** button while pressing **RESET**.

4. Verify that the USB device appears in WCHISPTool. This confirms correct USB operation and button functionality.

5. Flash:

   `CH32_production_line_sensor_i2c.bin`

6. Verify that the first eight RGB LEDs perform three complete color-scanning cycles.

7. Press the **BOOT/CAL** button.

8. Verify that the **CALIBRATE** LED (LED 9) flashes blue and turns green after a few seconds.

9. Measure the voltage between **3V3** and **GND** on the 2×3 header. The measured voltage should be approximately **3.3 V**.

10. Disconnect the USB cable.

---

## 2. Test Setup

After both boards have been programmed:

* Mount the DUT opposite the TU with the IR sensors facing each other.
* Maintain a spacing of approximately **10 mm** using spacers.

*(Insert mounting image here.)*

Connect the **10 kΩ resistor** between the **TX** and **RX** pins on the DUT 2×3 header.

*(Insert resistor connection images here.)*

---

## 3. Sensor Test and Qwiic Connectors

1. Connect one Qwiic connector of the DUT to the LMS-ESP32v2.
2. Connect the second Qwiic connector of the DUT to the TU.
3. Verify that the DUT is mounted opposite the TU.
4. Connect the LMS-ESP32v2 to a PC via USB.
5. Open a serial terminal at **115200 baud**.
6. Press **RESET** on the LMS-ESP32v2.
7. Observe the serial output.

Expected results:

| Status LED   | Meaning                          |
| ------------ | -------------------------------- |
| **S1 Green** | Qwiic communication passed       |
| **S2 Green** | UART TX/RX loopback passed       |
| **S3 Green** | IR emitters and receivers passed |

If any status LED turns red, the corresponding test has failed and the DUT should be investigated.
