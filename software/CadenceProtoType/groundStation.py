class GROUND:
    def __init__(self, cdh):
        self.cdh = cdh
    # send command
    def send_command(self, command_type, *args):

    # PAYLOAD
        if command_type == "payload":
            raw_mode = args[0] if args else False
            print(f"\n{'RAW' if raw_mode else 'PROCESSED'} payload data requested...")
            self.cdh.request_data_PAYLOAD(raw=raw_mode)
            return "Payload data request acknowledged"
    # ADCS
        elif command_type == "adcs":
            print(f"\nADCS data requested . . .")
            self.cdh.request_data_ADCS()
            return (f"\ndata request acknowledged")
    # HEALTH
        elif command_type == "health":
            battery = args[0] if args else None
            (f"\nhealth data requested")
            self.cdh.request_data_HEALTH(battery)
            return (f"\ndata request acknowledged")
    # POLLING RATE        
        elif command_type == "rate":
            print("\nPolling rate change requested")
            self.cdh.set_polling_rate(args[0])
            return "Change request acknowledged"