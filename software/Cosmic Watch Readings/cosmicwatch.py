import board
import busio
import time
import analogio

cosmic_watch_output = analogio.AnalogIn(board.COSMIC_ANALOG)
counter = 0
SIGNAL_THRESHOLD = 1000

def get_voltage(raw):
    return (raw * 3.3) / 65536

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