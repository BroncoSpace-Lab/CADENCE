import time
import board
import busio
import digitalio
import storage
import adafruit_sdcard
import adafruit_tmp1075
import adafruit_gps
import os

# === TMP1075 - Temperature Sensor (I2C) ===
i2c = busio.I2C(board.I2C1_SCL, board.I2C1_SDA)  # SCL, SDA
tmp = adafruit_tmp1075.TMP1075(i2c)

# === GPS (UART) ===
uart_gps = busio.UART(board.TX1, board.RX1, baudrate=9600, timeout=1)
gps = adafruit_gps.GPS(uart_gps, debug=False)
gps.send_command(b'PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')  # NMEA GGA & RMC
gps.send_command(b'PMTK220,1000')  # 1 Hz update rate

# === SD Card (SPI) ===
spi = busio.SPI(board.GP2, board.GP3, board.GP0)  # SCK, MOSI, MISO
cs = digitalio.DigitalInOut(board.GP1)
sdcard = adafruit_sdcard.SDCard(spi, cs)
vfs = storage.VfsFat(sdcard)
storage.mount(vfs, "/sd")

# === Log File Setup ===
log_file_path = "/sd/log.txt"
with open(log_file_path, "a") as f:
    f.write("Time,TempC,GPS_Fix,Latitude,Longitude\n")

# Setup UART to RP2350
uart_out = busio.UART(board.TX0, board.RX0, baudrate=9600, timeout=0.5)

# Setup trigger signal pin
trigger_pin = digitalio.DigitalInOut(board.GP_)
trigger_pin.direction = digitalio.Direction.INPUT
trigger_pin.pull = digitalio.Pull.DOWN  # or UP

# === Main Loop ===
while True:
    gps.update()
    temperature = tmp.temperature
    time_stamp = time.monotonic()

    # Get GPS info
    if gps.has_fix:
        lat = gps.latitude
        lon = gps.longitude
        fix_status = "1"
    else:
        lat = 0.0
        lon = 0.0
        fix_status = "0"

    # Log raw data
    log_line = "{:.2f},{:.2f},{},{:.6f},{:.6f}\n".format(
        time_stamp, temperature, fix_status, lat, lon
    )
    print("Logging:", log_line.strip())

    try:
        with open(log_file_path, "a") as f:
            f.write(log_line)
    except Exception as e:
        print("SD write error:", e)

    # === Notification Check ===
    if temperature > 40:
        print("ALERT: High temperature!")
    if not gps.has_fix:
        print("WARNING: No GPS fix.")

    # === Send summary only if triggered ===
    if trigger_pin.value:
        if gps.has_fix:
            summary = "OK"
            if temperature > 40:
                summary = "ALERT"
            message = f"{summary},TEMP={temperature:.2f}C,LAT={lat:.6f},LON={lon:.6f}\n"
        else:
            message = "NO_FIX,TEMP={:.2f}C\n".format(temperature)

        uart_out.write(message.encode("utf-8"))
        print("📤 Sent to RP2350:", message.strip())

    time.sleep(2)






