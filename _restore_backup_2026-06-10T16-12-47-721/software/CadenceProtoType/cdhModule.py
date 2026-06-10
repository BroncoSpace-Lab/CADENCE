class CDH:
    def __init__(self, payloadModule, commsModule, adcsModule, fdirModule):
        self.payload = payloadModule
        self.comms = commsModule
        self.adcs = adcsModule 
        self.fdir = fdirModule

    #     import board
    #     import busio
    #     import adafruit_sdcard
    #     import digitalio
    #     import storage

    #     # Initialize SPI
    #     spi = busio.SPI(board.GP2, MOSI=board.GP3, MISO=board.GP4)
        
    #     # Initialize CS pin
    #     cs = digitalio.DigitalInOut(board.GP5)
        
    #     # Initialize SD card using adafruit_sdcard instead of sdcardio
    #     sdcard = adafruit_sdcard.SDCard(spi, cs)
        
    #     # Mount filesystem
    #     vfs = storage.VfsFat(sdcard)

    #     try:
    #         os.mkdir("\sd\data")
    #     except OSError:
    #         pass
            
    #     storage.mount(vfs, "/sd")

    # def write_to_sd(self, filename,data):
    #     with open(f"/sd/data/{filename}", "a") as f:
    #         f.write(data + "\n")

    def set_polling_rate(self, rate):
        if hasattr(self.payload, 'setPollingRate'):
            if self.payload.setPollingRate(rate):
                ack_data = {
                    'command': 'set_polling_rate',
                    'status': 'success',
                    'new_rate': rate
                }
                packet = self.comms.create_packet('commands', ack_data)
                self.comms.downlink(packet)
                return True
            else:
                ack_data = {
                    'command': 'set_polling_rate',
                    'status': 'failed',
                    'new_rate': rate
                }
                packet = self.comms.create_packet('commands', ack_data)
                self.comms.downlink(packet)
                return False



    def request_data_PAYLOAD(self, raw=False):
        """Get payload data with option for raw transmission"""
        data = self.payload.collectData()
        packet = self.comms.create_packet('payload', data, raw=raw)
        self.comms.downlink(packet)

    def request_data_ADCS(self):
        """Get ADCS data and downlink it"""
        raw_data = self.adcs.getIMUData()
        packet = self.comms.create_packet('adcs', raw_data)
        self.comms.downlink(packet)
    
    def request_data_HEALTH(self, battery_level=None):
        health_data = {
            'status': self.fdir.checkHealth(battery_level),
            'battery': battery_level
        }
        packet = self.comms.create_packet('health', health_data)  # Use create_packet
        self.comms.downlink(packet)