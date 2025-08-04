import time
import board
import busio
import analogio
import adafruit_gps
import digitalio
import storage
import adafruit_sdcard
import math

# UART 1 -> GPS
# UART 0 -> proves 


# Global variables
write_to_file = True
sdcard_mounted = False
counter = 0
SIGNAL_THRESHOLD = 1000

cal = [-9.085681659276021e-27, 4.6790804314609205e-23, -1.0317125207013292e-19,
  1.2741066484319192e-16, -9.684460759517656e-14, 4.6937937442284284e-11, -1.4553498837275352e-08,
   2.8216624998078298e-06, -0.000323032620672037, 0.019538631135788468, -0.3774384056850066, 12.324891083404246]

# Hardware initialization
cosmic_watch_output = analogio.AnalogIn(board.COSMIC_ANALOG)

uart1 = busio.UART(board.TX1, board.RX1, baudrate=9600, timeout=0)
uart0 = busio.UART(board.TX0, board.RX0, baudrate=9600, timeout=10)


def get_sipm_voltage(raw):
    voltage = 0.0
    cal_length = len(cal)

    for i in range (cal_length):
        voltage += cal[i] * math.pow(raw, (cal_length - i - 1))

    return voltage


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
    try:
        gps = adafruit_gps.GPS(uart1, debug=False)
        gps.send_command(b'PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
        gps.send_command(b'PMTK220,1000')
        print("GPS initialized successfully")
        return gps
    except Exception as e:
        print(f"GPS initialization failed: {e}")
        return None, None

def log_to_sd(raw, volts, latitude=0.0, longitude=0.0, altitude = 0.0, satellites = 0 ):
    global filename
    if not sdcard_mounted:
        print("SD card not available")
        return False
        
    timestamp = time.monotonic()
    filename = '/sd/particle_logs.csv'
    
    try:
        # Check if file exists, create header if not
        try:
            with open(filename, 'r') as f:
                pass
        except OSError:
            with open(filename, 'w') as f:
                f.write("time since boot (s) | ADC | volts | latitude | longitude | altitude | satellites\n")
        
        # Write data
        if write_to_file:
            with open(filename, 'a') as f:
                f.write(f"{timestamp} , {raw} , {volts:.2f} , {latitude} , {longitude}, {altitude} , {satellites}\n")
        return True
        
    except Exception as e:
        print(f"SD card logging failed: {e}")
        return False

def cleanup():
    print("Program has been interrupted")
    print("============================")
    print(f"Total Particle Counts: {counter}")

    clearSD = (input("Clear SD? (test function) - y/n:  "))

    if clearSD == 'y':
        with open(filename, 'w') as f:
            f.write("time since boot (s) | ADC | volts | latitude | longitude | altitude | satellites\n")
        print("SD file cleared")
    elif clearSD == 'n':
        print("SD file not cleared")

    

    if sdcard_mounted:
        try:
            storage.umount("/sd")
            print("SD card unmounted successfully")
        except Exception as e:
            print(f"Error unmounting SD card: {e}")

    try:
        uart0.deinit()
        uart1.deinit()
        print("UART connections closed")
    except:
        pass
    



# Main program
print("Cosmic Watch Initialization...")

# Initialize SD card
sd_available = Initialize_SDCard()
if not sd_available:
    print("WARNING: SD card not available - continuing without saving logs")

# Initialize GPS
gps = Initialize_GPS()
if not gps:
    print("WARNING: GPS not available - continuing without GPS data")


# uncomment to bypass GPS and auto fill with fake information

#gps_working = input("use simulated gps data? (y/n): ").strip().lower()
#use_simulated_gps = gps_working in ['y', 'yes']

#if use_simulated_gps:
#    simulated_latitude = 40.77
#    simulated_longitude = -111.9
#else:
#    print("continuing with normal GPS")


print("Starting particle detection...")

gps_fix_status = False
last_fix_status = False

try:
    while True:

        current_time = time.monotonic()
        latitude = 0.0
        longitude = 0.0
        altitude = 0.0
        satellites = 0.0
        gps_status = ""
        
# uncomment to bypass GPS and auto fill with fake information

 #       if use_simulated_gps:
 #           latitude = simulated_latitude
 #           longitude = simulated_longitude
 #           gps_status = "Simulated GPS"
 #       else:
        # Update GPS if available
        if gps:
            gps.update()
            gps_fix_status = gps.has_fix

            if gps_fix_status != last_fix_status:
                if gps_fix_status:
                    print("GPS fix acquired")
                    print(f"Satellites: {gps.satellites}")
                    print(f"Location: {gps.latitude}, {gps.longitude}")
                    print("=" * 40)
                else:
                    print("GPS fix lost")
                    print("=" * 40)
                last_fix_status = gps_fix_status
            if gps_fix_status:
                latitude = gps.latitude
                longitude = gps.longitude
                altitude = gps.altitude_m
                satellites = gps.satellites
                gps_status = f"GPS fixed: ({gps.satellites} sats)"
            else:
                latitude = 0.0
                longitude = 0.0
                gps_status = "Searching for GPS..."
        else: gps_status = "GPS not available"


        
        # Read cosmic watch sensor
        raw = cosmic_watch_output.value
        volts = get_sipm_voltage(raw)
        
        # Check for particle detection
        if raw > SIGNAL_THRESHOLD:
            counter += 1
            print(f"({counter}) -  Particle detected!")
            print("Data     | ADC value:{:5d} volts ={:5.2f}".format(raw,volts))                
            print(f"GPS Data | Latitude: {latitude}, Longitude: {longitude}\n")
            
            # Send UART message if available
            if uart0:
                    try:
                        # Combine all data into one message
                        complete_message = f"({counter}) - particle detected!\nData | ADC:{raw:5d} V:{volts:5.2f}\nGPS| LAT: {latitude}, LONG: {longitude}, ALT: {altitude}, SAT: {satellites}\n --- \n"
                        uart0.write(complete_message.encode())
                    except Exception as e:
                        print(f"UART communication error: {e}")
            
            # Log to SD card
            log_to_sd(raw, volts, latitude, longitude, altitude, satellites)
        
        
except KeyboardInterrupt:
    cleanup()
except Exception as e:
    print(f"Unexpected error: {e}")
    cleanup()
