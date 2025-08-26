# commsModule.py
import json
import time

class COMMS:
    def __init__(self):
        self.packet_counter = 0
        self.apids = {
            'adcs': 0x020,      # ADCS data
            'payload': 0x030,    # Processed payload data
            'payload_raw': 0x031, # Raw payload data
            'health': 0x040,      # health status (battery)
            'commands' : 0x050,    #command acknowledgments
        }
    
    def _create_header(self, apid, data_length):
        """Create CCSDS-like packet header"""
        self.packet_counter = (self.packet_counter + 1) % 65536
        return {
            'version': 0,          # CCSDS version
            'type': 0,              # 0=Telemetry, 1=Command
            'apid': apid,           # Application Process ID
            'seq_count': self.packet_counter,
            'length': data_length,  # Data length
            'timestamp': time.time()
        }
    
    def _crc16_ccitt(self, data):
        """Pure Python CRC-16-CCITT implementation for CircuitPython"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        crc = 0xFFFF
        for byte in data:
            crc ^= byte << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc = crc << 1
                crc &= 0xFFFF  # Ensure 16-bit
        return crc
    
    def create_packet(self, data_type, data, raw=False):
        """Create a complete packet with header, data, and CRC"""
        apid = self.apids['payload_raw'] if (data_type == 'payload' and raw) else self.apids[data_type]
        
        # Format the data
        if data_type == 'adcs':
            binary_data = self.format_adcs(data)
        elif data_type == 'health':
            binary_data = self.format_health(data)
        elif data_type == 'commands':
            binary_data = data
        else:
            binary_data = self.format_payload(data, raw)
        
        header = self._create_header(apid, len(str(binary_data)))
        full_packet = {
            'header': header,
            'data': binary_data
        }
        
        # Calculate CRC
        packet_bytes = json.dumps(full_packet).encode('utf-8')
        full_packet['crc'] = self._crc16_ccitt(packet_bytes)
        
        return full_packet
    
    def format_adcs(self, data):
        """Format ADCS data for transmission"""
        return {
            'accel_x': data['acceleration'][0],
            'accel_y': data['acceleration'][1],
            'accel_z': data['acceleration'][2],
            'gyro_x': data['gyro'][0],
            'gyro_y': data['gyro'][1],
            'gyro_z': data['gyro'][2],
            'temp': data['temperature']
        }
    
    def format_payload(self, data, raw):
        """Format payload data with option for raw transmission"""
        if raw:
            return {'raw_value': data}
        else:
            return {'data (processed)': data * 0.1}  # Example conversion

    def format_health(self,data):
        return {
            'status': data.get('status'),
            'battery': data.get('battery')
        }
    
    def downlink(self, packet):
        """Simulate downlinking a packet with formatted output"""
        print("\nDOWNLINKING PACKET:")
        print(f"APID: 0x{packet['header']['apid']:03X}")
        print(f"Counter: {packet['header']['seq_count']}")
        print(f"Timestamp: {packet['header']['timestamp']}")
        
        # Format the data display
        print("\nDATA:")
        if packet['header']['apid'] == 0x020:  # ADCS data
            data = packet['data']
            # Define display order, field names, and units
            fields = [
                ("Accel X", "accel_x", "m/s²"),
                ("Accel Y", "accel_y", "m/s²"),
                ("Accel Z", "accel_z", "m/s²"),
                ("Gyro X", "gyro_x", "rad/s"),
                ("Gyro Y", "gyro_y", "rad/s"),
                ("Gyro Z", "gyro_z", "rad/s"),
                ("Temp", "temp", "°C")
            ]
            
            # Print each field with fixed-width formatting
            for label, key, unit in fields:
                value = data.get(key, 'N/A')
                # CircuitPython-compatible formatting
                label_str = "{:<8}".format(label)  # Left-align, 8 chars wide
                value_str = "{:8.4f}".format(value) if isinstance(value, (int, float)) else str(value)
                print("{}: {}{}".format(label_str, value_str, unit))

        elif packet['header']['apid'] == 0x040:
            data = packet['data']
            print(f"Status: {data.get('status', 'N/A')}")
            if 'battery' in data and data['battery'] is not None:
                print(f"Battery: {data['battery']}%")
        elif packet['header']['apid'] == 0x050:
            print("\nCOMMAND ACKNOWLEDGMENT:")
            data = packet['data']
            print(f"Command: {data.get('command', 'N/A')}")
            print(f"Status: {data.get('status', 'N/A')}")
            if 'new_rate' in data:
                print(f"New polling rate: {data['new_rate']} seconds")
            if 'message' in data:
                print(f"Message: {data['message']}")
        
        else:  # payload_raw (0x031) or payload (0x030)
            for key, value in packet['data'].items():
                print(f"{key}: {value}")
    
        print(f"\nCRC: 0x{packet['crc']:04X}")
        
        # Verify CRC
        verify_bytes = json.dumps({'header': packet['header'], 'data': packet['data']}).encode('utf-8')
        calculated_crc = self._crc16_ccitt(verify_bytes)
        if calculated_crc == packet['crc']:
            print("CRC VERIFIED: Packet intact")
        else:
            print(f"CRC ERROR: Expected 0x{calculated_crc:04X}")

  