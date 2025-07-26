import time
import board
import busio
import analogio
import adafruit_gps
import digitalio
import storage
import adafruit_sdcard

# Cosmic Watch Initialization
cosmic_watch_output = analogio.AnalogIn(board.COSMIC_ANALOG)
counter = 0
SIGNAL_THRESHOLD = 1000 # may need to be tweaked by Pragun


# GPS and pin setup
# pin initialization for UART communication & GPS (uart0 -> proves board | uart1 -> cygnet board)
uart0 = busio.UART(board.TX0, board.RX0, baudrate=9600, timeout=10)


#SD card setup (needs testing)
def Initialize_SDCard():
    global sdcard_mounted
    try:
        cs = digitalio.DigitalInOut(board.GP1)
        spi = busio.SPI(board.GP2, board.GP3, board.GP0)
        sdcard = adafruit_sdcard.SDCard(spi, cs)
        vfs = storage.VfsFat(sdcard)
        storage.mount(vfs, "/sd")
        sdcard_mounted = True
        print("SD card mounted successfully")
        return True
    except Exception as e:
        print(f"SD card initialization failed: {e}")
        sdcard_mounted = False
        return False

def Initialize_GPS():
    global uart0, uart1, gps
    try:
        uart1 = busio.UART(board.TX1, board.RX1, baudrate=9600, timeout=10)
        gps = adafruit_gps.GPS(uart1, debug=True)  # Use UART/pyserial
# Turn on the basic GGA and RMC info (what you typically want)
        gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
        time.sleep(0.1)
# Set update rate to once a second (1hz) which is what you typically want.
        gps.send_command(b"PMTK220,1000")
        time.sleep(0.1)
# ENABLES OUTPUT OF nmea DATA FROM THE MODULE (?)
        gps.send_command(b"PGCMD,33,1")
        time.sleep(0.1)

        print("GPS Initialized successfully")
        return True
    except Exception as e:
        print(f"GPS initialization failed: {e}")
        return False

# function to convert cosmic watch readings (adc values) to voltage 
def get_voltage(raw):
    return (raw * 3.3) / 65536

# function to log data recieved (gps, raw reading, processed reading) to onboard SD
def log_to_sd(raw, volts, gps_obj):
    if not sdcard_mounted:
        print("SD card not available")
        return False
    
    timestamp = time.monotonic()
    filename = '/sd/particle_logs.csv'

    try:

        try:
            with open(filename, 'r') as f:
                pass
        except OSError:
            with open(filename, 'w') as f:
                f.write("timestamp, raw, volts, latitude, longitude, altitude, satellites\n")

# writing GPS data
        if gps_obj and gps.has_fix:
            with open(filename, 'a') as f:
                f.write(f"{timestamp}, {raw}, {volts:.2f},")
                if gps_obj and gps.has_fix:
                    f.write(f"{gps.latitude:.6f},{gps.longitude:.6f},")
                    f.write(f"{gps.altitude_m if gps.altitude_m else 'None'},")
                    f.write(f"{gps.satellites if gps.satellites else 'None'}\n")
                else:
                    f.write("None,None,None,None\n")
            return True
    except Exception as e:
        print(f"SD card logging failed: {e}")
        return False

# function to print GPS data
def print_GPS(gps):
    gps.update()
    if gps is None:
        print("GPS not available")
        return
    try:
        if not gps.has_fix:
            print("No Fix at time of Detection")
            return
    
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
        print("=" * 40)

    except Exception as e:
        print(f"Error printing GPS data: {e}")


# cleanup function to close out program when interrupted

def cleanup():
    print("Program has been interrupted")
    print("============================")
    print(f"Total Particle Counts:{counter}")

    if sdcard_mounted:
        try:
            storage.umount("/sd")
            print("SD card unmounted successfully")
        except Exception as e:
            print(f"Error unmounting SD card: {e}")



# Main loop runs forever, waiting until a particle is found, then printing particle data, and GPS data
print("Cosmic Watch Initialization...")
gps_available = Initialize_GPS()
sd_available = Initialize_SDCard()

if not gps_available:
    print("WARNING: GPS not Available - continuing without GPS")
if not sd_available:
    print("WARNING: SD card not available - continuing without saving logs")

print("Starting particle detection...")

last_gps_update = 0
GPS_UPDATE_INTERVAL = 1.0

Initialize_SDCard()
Initialize_GPS()

try:
    while True:
        current_time = time.monotonic()

        #if gps_available:
        #    gps.update()
        #    last_gps_update = current_time

        raw = cosmic_watch_output.value
        volts = get_voltage(raw)

        #print("raw = {:5d} volts = {:5.2f}".format(raw, volts))
        if cosmic_watch_output.value > SIGNAL_THRESHOLD:
            counter += 1
            print("Particle has been detected!")
            print("raw = {:5d} volts = {:5.2f}".format(raw, volts))

            if uart0:
                try:
                    uart0.write(b"Particle detected\n")
                except Exception as e:
                    print(f"UART communication error: {e}")
            #print_GPS(gps)
            log_to_sd(raw, volts, gps)
                

except KeyboardInterrupt:
    cleanup()
except Exception as e:
    print(f"Unexpected error: {e}")
    cleanup()
