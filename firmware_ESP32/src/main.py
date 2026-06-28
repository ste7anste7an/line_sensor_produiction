from time import sleep, ticks_ms, ticks_diff, sleep_ms
from line_sensor import LineSensorI2C
import lms_esp32
from machine import Pin, UART
from neopixel import NeoPixel

np=NeoPixel(Pin(25),1)
ALL_OK = True
uart=UART(1,rx=lms_esp32.RX_PIN,tx=lms_esp32.TX_PIN,baudrate=115200)
dut = LineSensorI2C(device_addr=0x33, freq=100000)
tu = LineSensorI2C(device_addr=0x34, freq=100000)

N_MEASURE = 10
"""
[*] info
[+] ok
[-] no / removed / skipped
[!] warning
[x] error
[?] question
[>] action
[.] progress
"""

def get_uid():
    uid = dut.get_uid()[:23]
    print("[*] line Sensor UID: ", uid)
    uid = tu.get_uid()[:23]
    print("[*] line Sensor UID: ", uid)

def check_i2c():
    devices = dut.i2c.scan()
    print("[.] check i2c devices")
    print("[*] devices found: ",devices)
    OK = True
    if not 0x33 in devices:
        print("[!] Check I2C connection of DUT")
        OK = False
    if not 0x34 in devices:
        print("[!] Check I2C connection of TU")
        OK = False
    return OK
    
    

def neopixel_test():
    dut.led_mode(dut.LEDS_OFF)
    for i in range(9):
        dut.neopixel(i,30,0,0)
        sleep_ms(50)
    sleep_ms(200)
    for i in range(9):
        dut.neopixel(i,0,30,0)
        sleep_ms(50)
    sleep_ms(200)
    for i in range(9):
        dut.neopixel(i,0,0,30)
        sleep_ms(50)
    sleep_ms(200)
    for i in range(9):
        dut.neopixel(i,0,0,0)
        sleep_ms(30)
    #dut.led_mode(dut.LEDS_VALUES)



def test_gpio_dir(pin_in,pin_out):
    dut.serial_disable()
    dut.gpio_in(pin_in)
    dut.gpio_out(pin_out,0)
    sleep_ms(100)
    in0 = dut.gpio_in(pin_in)
    dut.gpio_out(pin_out,1)
    sleep_ms(100)
    in1 = dut.gpio_in(pin_in)
    dut.serial_enable()
    dut.set_debug(4)
    return (in0,in1)
    
def _gpio_mark(result):
    """
    result should be (low_read, high_read)

    Expected:
        low_read  == 0
        high_read == 1

    Returns:
        O  = OK
        L  = error when LOW was expected
        H  = error when HIGH was expected
        LH = both LOW and HIGH failed
    """
    low_read, high_read = result

    mark = ""

    if low_read != 0:
        mark += "Lo"

    if high_read != 1:
        mark += "Hi"

    if mark == "":
        mark = "OK"

    return mark


def _center(text, width):
    text = str(text)
    if len(text) >= width:
        return text[:width]

    left = (width - len(text)) // 2
    right = width - len(text) - left
    return " " * left + text + " " * right


def _print_pin_box(pin, mark, result):
    width = 13

    print("+" + "-" * width + "+")
    print("|" + _center("PIN {}".format(pin), width) + "|")
    print("|" + _center(mark, width) + "|")
    print("|" + _center(str(result), width) + "|")
    print("+" + "-" * width + "+")


def test_gpio_report():
    """
    Tests both directions.

    test_gpio_dir(1, 0):
        pin 0 is output
        pin 1 is input

    test_gpio_dir(0, 1):
        pin 1 is output
        pin 0 is input
    """

    print("[.] Testing GPIO pins")

    pin0_result = test_gpio_dir(1, 0)   # output pin 0, input pin 1
    pin1_result = test_gpio_dir(0, 1)   # output pin 1, input pin 0

    pin0_mark = _gpio_mark(pin0_result)
    pin1_mark = _gpio_mark(pin1_result)

    print("[*] Expected result per pin: (0, 1)")
    print("[*] O = OK, L = LOW failed, H = HIGH failed, LH = both failed")
    print("")

    _print_pin_box("Rx", pin0_mark, pin0_result)
    print("       ||")
    _print_pin_box("Tx", pin1_mark, pin1_result)

    print("")

    if pin0_mark == "OK" and pin1_mark == "OK":
        print("[+] GPIO test OK")
        return True
    else:
        print("[x] GPIO test failed")
        return False


def vector_add(a, b):
    l=len(a)
    s=[0]*l
    for i in range(l):
        s[i] = a[i] + b[i]
    return s

def vector_div(a, d):
    l=len(a)
    s=[0]*l
    for i in range(l):
        s[i] = a[i]//d
    return s
    

def measure_avg(dev, nr):
    avg = [0]*8
    cnt = 0
    for i in range(nr):
        try:
            val = dev.sensors()
            #print(val)
        except e:
            continue
        cnt += 1
        avg = vector_add(avg, val)
        sleep_ms(20)
    return vector_div(avg, cnt)
    

PASS_LIMIT = 60


def _status_marks(values, limit=PASS_LIMIT):
    # O = OK/pass, * = fail
    return ["O" if v < limit else "*" for v in values]


PASS_LIMIT = 40


def _pass_off_on(off_value, on_value, limit=PASS_LIMIT):
    """
    Sensor is OK if:
    - without opposite emitter: value is high
    - with opposite emitter: value is low
    """
    return off_value > (255 - limit) and on_value < limit


def print_dut_ascii(
    dut_rx_with_tu_off,
    dut_rx_with_tu_on,
    tu_rx_with_dut_off,
    tu_rx_with_dut_on,
    limit=PASS_LIMIT,
    reverse_tu=False,
):
    """
    Print DUT status as ASCII-art boxes.

    Upper row = DUT emitters.
        O if TU reads high when DUT emitter is OFF
        and TU reads low when DUT emitter is ON.

    Lower row = DUT receivers.
        O if DUT reads high when TU emitter is OFF
        and DUT reads low when TU emitter is ON.

    O = OK
    * = FAIL
    """

    if reverse_tu:
        tu_rx_with_dut_off = list(reversed(tu_rx_with_dut_off))
        tu_rx_with_dut_on = list(reversed(tu_rx_with_dut_on))

    dut_emitter_marks = []
    dut_receiver_marks = []

    for i in range(8):
        emitter_ok = _pass_off_on(
            tu_rx_with_dut_off[i],
            tu_rx_with_dut_on[i],
            limit,
        )

        receiver_ok = _pass_off_on(
            dut_rx_with_tu_off[i],
            dut_rx_with_tu_on[i],
            limit,
        )

        dut_emitter_marks.append("O" if emitter_ok else "*")
        dut_receiver_marks.append("O" if receiver_ok else "*")

    border = "      +" + "---+" * 8

    emitter_row = "EMIT  "
    receiver_row = "RECV  "
    index_row = "       "

    for i in range(8):
        emitter_row += "| {} ".format(dut_emitter_marks[i])
        receiver_row += "| {} ".format(dut_receiver_marks[i])
        index_row += " S{} ".format(i+1)

    emitter_row += "|"
    receiver_row += "|"

    print("\r\n\r\n[*] DUT optical test")
    print("[*] O = OK, * = FAIL")
    print("[*] pass condition: OFF > {}, ON < {}".format(255 - limit, limit))
    print(border)
    print(emitter_row)
    print(border)
    print(receiver_row)
    print(border)
    print(index_row)
    if '*' in dut_emitter_marks or '*' in dut_receiver_marks:
        return False
    else:
        return True

# Check IR sensors
# tu IR off
def test_sensors():
    dut.ir_power(False)
    tu.ir_power(False)
    sleep_ms(50)

    #dut.led_mode(dut.LEDS_VALUES)
    #tu.led_mode(tu.LEDS_VALUES)

    print("[.] Measuring DUT with IR emitter TU off")
    dut_with_tu_off = measure_avg(dut, N_MEASURE)
    print("[*] values DUT: ", dut_with_tu_off)

    tu.ir_power(True)
    sleep_ms(100)

    print("[.] Measuring DUT with IR emitter TU on")
    dut_with_tu_on = measure_avg(dut, N_MEASURE)
    print("[*] values DUT: ", dut_with_tu_on)

    dut.ir_power(False)
    tu.ir_power(False)
    sleep_ms(100)

    print("[.] Measuring TU with IR emitter DUT off")
    tu_with_dut_off = measure_avg(tu, N_MEASURE)
    print("[*] values TU:  ", tu_with_dut_off)

    dut.ir_power(True)
    sleep_ms(100)

    print("[.] Measuring TU with IR emitter DUT on")
    tu_with_dut_on = measure_avg(tu, N_MEASURE)
    print("[*] values TU:  ", tu_with_dut_on)

    dut.ir_power(False)
    tu.ir_power(False)

    OK = print_dut_ascii(
        dut_rx_with_tu_off=dut_with_tu_off,
        dut_rx_with_tu_on=dut_with_tu_on,
        tu_rx_with_dut_off=tu_with_dut_off,
        tu_rx_with_dut_on=tu_with_dut_on,
        limit=PASS_LIMIT,
        reverse_tu=False,
    )
    return OK


OK=True
np[0]=(0,0,0)
np.write()
print("=======================================================\r\n")
print('[*] Test procedure started\r\n')
sleep_ms(100)
tu.led_mode(tu.LEDS_OFF)
if check_i2c():
    neopixel_test()
    print("[*] I2C connections OK\r\n\r\n")
    get_uid()
    dut.neopixel(0,0,40,0)
    print("\r\n\r\n")
    OK = test_gpio_report()
    ALL_OK = ALL_OK & OK
    if OK:
        dut.neopixel(1,0,40,0)
    else:
        dut.neopixel(1,40,0,0)
    print("\r\n\r\n")
    OK = test_sensors()
    ALL_OK = ALL_OK & OK
    #dut.led_mode(dut.LEDS_OFF)
    if OK:
        dut.neopixel(2,0,40,0)
    else:
        dut.neopixel(2,40,0,0)
    if ALL_OK:
        np[0]=(0,50,0)
        np.write()
    else:
        np[0]=(50,0,0)
        np.write()
    print("\r\n=======================================================\r\n")
else:
    print("[!] Test aborted")
    while 1:
        np[0]=(50,0,0)
        np.write()
        sleep_ms(300)
        np[0]=(0,0,0)
        np.write()
        sleep_ms(300)