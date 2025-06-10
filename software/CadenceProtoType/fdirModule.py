class FDIR:
    def checkHealth(self, battery_level):
        if battery_level < 30:
            return "LOW POWER MODE"
        return "NORMAL MODE"