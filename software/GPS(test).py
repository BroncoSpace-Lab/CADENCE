import board
import busio
import time

uart = busio.UART(board.TX1, board.RX1, baudrate=9600, receiver_buffer_size=512)

line_buffer = ""

def parse_lat_lon(lat_raw, lat_dir, lon_raw, lon_dir):
    try:
        lat_deg = float(lat_raw[:2])
        lat_min = float(lat_raw[2:])
        latitude = lat_deg + (lat_min / 60.0)
        if lat_dir == "S":
            latitude = -latitude

        lon_deg = float(lon_raw[:3])
        lon_min = float(lon_raw[3:])
        longitude = lon_deg + (lon_min / 60.0)
        if lon_dir == "W":
            longitude = -longitude

        return latitude, longitude
    except (ValueError, IndexError):
        return None, None

def format_gps_time(timestr):
    try:
        # timestr: 'hhmmss' or 'hhmmss.sss'
        hour = int(timestr[0:2])
        minute = int(timestr[2:4])
        second = int(timestr[4:6])
        return "{:02}:{:02}:{:02} UTC".format(hour, minute, second)
    except:
        return "Invalid Time"

while True:
    try:
        data = uart.read(64)
        if data:
            line_buffer += data.decode("utf-8", errors="ignore")

            while "\n" in line_buffer:
                line, line_buffer = line_buffer.split("\n", 1)
                line = line.strip()

                if line.startswith("$GPGGA") or line.startswith("$GNGGA"):
                    parts = line.split(",")

                    if len(parts) > 5 and parts[2] and parts[4]:
                        gps_time = parts[1]
                        lat_raw = parts[2]
                        lat_dir = parts[3]
                        lon_raw = parts[4]
                        lon_dir = parts[5]

                        lat, lon = parse_lat_lon(lat_raw, lat_dir, lon_raw, lon_dir)
                        if lat is not None:
                            timestamp = format_gps_time(gps_time)
                            print("[{}] Latitude: {:.6f}, Longitude: {:.6f}".format(timestamp, lat, lon))
                        else:
                            print("Invalid lat/lon data.")
                    else:
                        print("Waiting for GPS fix...")

        time.sleep(0.5)

    except Exception as e:
        print("Error:", e)
        time.sleep(1)
