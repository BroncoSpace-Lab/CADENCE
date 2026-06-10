import time
import board
import busio
import adafruit_mpu6050  # Fixed import

class ADCS:
    def __init__(self):
        i2c = busio.I2C(scl=board.GP1, sda=board.GP0)
        self.mpu = adafruit_mpu6050.MPU6050(i2c)
    
    def getIMUData(self):  # Renamed from getGPS
        return {
            "acceleration": self.mpu.acceleration,
            "gyro": self.mpu.gyro,
            "temperature": self.mpu.temperature
        }
