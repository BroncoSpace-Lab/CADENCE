import time
import board
import busio
import analogio
import adafruit_gps

cosmic_watch_output = analogio.AnalogIn(board.COSMIC_ANALOG)
counter = 0
SIGNAL_THRESHOLD = 1000

def get_voltage(raw):
    return (raw * 3.3) / 65536

uart0 = busio.UART(board.TX0, board.RX0, baudrate=9600, timeout=10)

uart1 = busio.UART(board.TX1, board.RX1, baudrate=9600, timeout=10)


gps = adafruit_gps.GPS(uart1, debug=True)  # Use UART/pyserial


# Turn on the basic GGA and RMC info (what you typically want)
gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")


# Set update rate to once a second (1hz) which is what you typically want.
gps.send_command(b"PMTK220,1000")


# Main loop runs forever printing the location, etc. every second.
last_print = time.monotonic()

try:
    while True:
        raw = cosmic_watch_output.value
        volts = get_voltage(raw)
        #print("raw = {:5d} volts = {:5.2f}".format(raw, volts))
        if cosmic_watch_output.value > SIGNAL_THRESHOLD:
            counter += 1
            print("raw = {:5d} volts = {:5.2f}".format(raw, volts))
            print("Particle has been detected!")
            uart0.write(b"Particle detected!\n")

            gps.send_command(b"PGCMD,33,1")
            gps.update()
            current = time.monotonic()
            if current - last_print >= 1.0:
                last_print = current
                if not gps.has_fix:
                    print("Waiting for fix...")
                    continue
                print("=" * 40)  
                print(
                    "Fix timestamp: {}/{}/{} {:02}:{:02}:{:02}".format(  # noqa: UP032
                        gps.timestamp_utc.tm_mon,  
                        gps.timestamp_utc.tm_mday,  
                        gps.timestamp_utc.tm_year,  
                        gps.timestamp_utc.tm_hour,  
                        gps.timestamp_utc.tm_min,  
                        gps.timestamp_utc.tm_sec,
                    )
                )
                print(f"Latitude: {gps.latitude:.6f} degrees")
                print(f"Longitude: {gps.longitude:.6f} degrees")
                print(f"Precise Latitude: {gps.latitude_degrees} degs, {gps.latitude_minutes:2.4f} mins")
                print(f"Precise Longitude: {gps.longitude_degrees} degs, {gps.longitude_minutes:2.4f} mins")
                print(f"Fix quality: {gps.fix_quality}")


                if gps.satellites is not None:
                    print(f"# satellites: {gps.satellites}")
                if gps.altitude_m is not None:
                    print(f"Altitude: {gps.altitude_m} meters")
                if gps.speed_knots is not None:
                    print(f"Speed: {gps.speed_knots} knots")
                if gps.speed_kmh is not None:
                    print(f"Speed: {gps.speed_kmh} km/h")
                if gps.track_angle_deg is not None:
                    print(f"Track angle: {gps.track_angle_deg} degrees")
                if gps.horizontal_dilution is not None:
                    print(f"Horizontal dilution: {gps.horizontal_dilution}")
                if gps.height_geoid is not None:
                    print(f"Height geoid: {gps.height_geoid} meters")



except KeyboardInterrupt:
    print("Program has been interrupted")
    print("============================")
    print(f"Total Particle Counts:{counter}")
