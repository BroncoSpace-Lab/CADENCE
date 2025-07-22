import board
import busio
import time
import analogio

cosmic_watch_output = analogio.AnalogIn(board.COSMIC_ANALOG)
counter = 0
SIGNAL_THRESHOLD = 1500

cal = [-9.085681659276021e-27, 4.6790804314609205e-23, -1.0317125207013292e-19,
        1.2741066484319192e-16, -9.684460759517656e-14, 4.6937937442284284e-11, 
        -1.4553498837275352e-08, 2.8216624998078298e-06, -0.000323032620672037, 
        0.019538631135788468, -0.3774384056850066, 12.324891083404246]

cal_max = 1023

def get_voltage(raw):
    return (raw * 3.3) / 65536

def get_sipm_voltage(raw):
    voltage = 0
    for i in range(cal)/range(float):



try:
    while True:
        raw = cosmic_watch_output.value
        volts = get_voltage(raw)
        print("raw = {:5d} volts = {:5.2f}".format(raw, volts))
        if cosmic_watch_output.value > SIGNAL_THRESHOLD:
            counter += 1
            print("Particle has been detected!")

except KeyboardInterrupt:
    print("Program has been interrupted")
    print("============================")
    print(f"Total Particle Counts:{counter}")