import analogio
import board

class PAYLOAD:
    def __init__(self):
        self.sensor = analogio.AnalogIn(board.A0)
        self.polling_rate = 1.0  # Default polling rate in seconds
    
    def collectData(self):
        # raw adc val from gas
        return self.sensor.value

    def setPollingRate(self, rate):
        try:
            rate = float(rate)
            if rate > 0:
                self.polling_rate = rate
                return True
            return False
        except (ValueError, TypeError):
            return False