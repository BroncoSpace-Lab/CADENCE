import time
import board
import busio
import analogio
import adafruit_gps
import digitalio
import storage
import adafruit_sdcard

# Global variables
write_to_file = True
sdcard_mounted = False
counter = 0
SIGNAL_THRESHOLD = 1000

# Hardware initialization
cosmic_watch_output = analogio.AnalogIn(board.COSMIC_ANALOG)

def get_voltage(raw):
    return (raw * 3.3) / 65536

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
        uart0 = busio.UART(board.TX0, board.RX0, baudrate=9600, timeout=10)
        gps = adafruit_gps.GPS(uart0, debug=False)
        gps.send_command(b'PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
        gps.send_command(b'PMTK220,1000')
        print("GPS initialized successfully")
        return gps, uart0
    except Exception as e:
        print(f"GPS initialization failed: {e}")
        return None, None

def log_to_sd(raw, volts, latitude=0.0, longitude=0.0):
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
                f.write("timestamp,raw,volts,latitude,longitude,altitude,satellites\n")
        
        # Write data
        if write_to_file:
            with open(filename, 'a') as f:
                f.write(f"{timestamp},{raw},{volts:.2f},{latitude},{longitude},None,None\n")
        return True
        
    except Exception as e:
        print(f"SD card logging failed: {e}")
        return False

def cleanup():
    print("Program has been interrupted")
    print("============================")
    print(f"Total Particle Counts: {counter}")
    if sdcard_mounted:
        try:
            storage.umount("/sd")
            print("SD card unmounted successfully")
        except Exception as e:
            print(f"Error unmounting SD card: {e}")

# Main program
print("Cosmic Watch Initialization...")

# Initialize SD card
sd_available = Initialize_SDCard()
if not sd_available:
    print("WARNING: SD card not available - continuing without saving logs")

# Initialize GPS
gps, uart0 = Initialize_GPS()
if not gps:
    print("WARNING: GPS not available - continuing without GPS data")

print("Starting particle detection...")

try:
    while True:
        current_time = time.monotonic()
        latitude = 0.0
        longitude = 0.0
        
        # Update GPS if available
        if gps:
            gps.update()
            if gps.has_fix:
                latitude = gps.latitude
                longitude = gps.longitude
        
        # Read cosmic watch sensor
        raw = cosmic_watch_output.value
        volts = get_voltage(raw)
        
        # Check for particle detection
        if raw > SIGNAL_THRESHOLD:
            counter += 1
            print("Particle has been detected!")
            print("raw = {:5d} volts = {:5.2f}".format(raw, volts))
            
            # Send UART message if available
            if uart0:
                try:
                    uart0.write(b"Particle detected\n")
                except Exception as e:
                    print(f"UART communication error: {e}")
            
            # Log to SD card
            log_to_sd(raw, volts, latitude, longitude)
        
        
except KeyboardInterrupt:
    cleanup()
except Exception as e:
    print(f"Unexpected error: {e}")
    cleanup()
