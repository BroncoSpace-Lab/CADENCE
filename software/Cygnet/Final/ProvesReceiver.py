import time

import digitalio

try:
    # from board_definitions import proveskit_rp2040_v4 as board
    raise ImportError
except ImportError:
    import board

try:
    from typing import Union
except Exception:
    pass

import os

from lib.adafruit_drv2605 import DRV2605  # This is Hacky V5a Devel Stuff###
from lib.adafruit_mcp230xx.mcp23017 import (
    MCP23017,  # This is Hacky V5a Devel Stuff###
)
from lib.adafruit_mcp9808 import MCP9808  # This is Hacky V5a Devel Stuff###
from lib.adafruit_tca9548a import TCA9548A  # This is Hacky V5a Devel Stuff###
from lib.adafruit_veml7700 import VEML7700  # This is Hacky V5a Devel Stuff###

# from lib.pysquared.Big_Data import AllFaces  ### This is Hacky V5a Devel Stuff###
from lib.pysquared.beacon import Beacon
from lib.pysquared.cdh import CommandDataHandler
from lib.pysquared.config.config import Config
from lib.pysquared.hardware.burnwire.manager.burnwire import BurnwireManager
from lib.pysquared.hardware.busio import _spi_init, initialize_i2c_bus
from lib.pysquared.hardware.digitalio import initialize_pin
from lib.pysquared.hardware.imu.manager.lsm6dsox import LSM6DSOXManager
from lib.pysquared.hardware.magnetometer.manager.lis2mdl import LIS2MDLManager
from lib.pysquared.hardware.power_monitor.manager.ina219 import INA219Manager
from lib.pysquared.hardware.radio.manager.rfm9x import RFM9xManager
from lib.pysquared.hardware.radio.manager.sx1280 import SX1280Manager
from lib.pysquared.hardware.radio.packetizer.packet_manager import PacketManager
from lib.pysquared.logger import Logger
from lib.pysquared.nvm.counter import Counter
from lib.pysquared.protos.power_monitor import PowerMonitorProto
from lib.pysquared.rtc.manager.microcontroller import MicrocontrollerManager
from lib.pysquared.sleep_helper import SleepHelper
from lib.pysquared.watchdog import Watchdog
from version import __version__

import busio

rtc = MicrocontrollerManager()

logger: Logger = Logger(
    error_counter=Counter(0),
    colorized=False,
)

logger.info(
    "Booting",
    hardware_version=os.uname().version,
    software_version=__version__,
)

#watchdog = Watchdog(logger, board.WDT_WDI)
#watchdog.pet()



logger.debug("Initializing Config")
config: Config = Config("config.json")

mux_reset = initialize_pin(logger, board.MUX_RESET, digitalio.Direction.OUTPUT, False)

# TODO(nateinaction): fix spi init
spi0 = _spi_init(
    logger,
    board.SPI0_SCK,
    board.SPI0_MOSI,
    board.SPI0_MISO,
)

spi1 = _spi_init(
    logger,
    board.SPI1_SCK,
    board.SPI1_MOSI,
    board.SPI1_MISO,
)

sband_radio = SX1280Manager(
    logger,
    config.radio,
    spi1,
    initialize_pin(logger, board.SPI1_CS0, digitalio.Direction.OUTPUT, True),
    initialize_pin(logger, board.RF2_RST, digitalio.Direction.OUTPUT, True),
    initialize_pin(logger, board.RF2_IO0, digitalio.Direction.OUTPUT, True),
    2.4,
    initialize_pin(logger, board.RF2_TX_EN, digitalio.Direction.OUTPUT, False),
    initialize_pin(logger, board.RF2_RX_EN, digitalio.Direction.OUTPUT, False),
)

i2c1 = initialize_i2c_bus(
    logger,
    board.SCL1,
    board.SDA1,
    100000,
)

#sleep_helper = SleepHelper(logger, config, watchdog)

uhf_radio = RFM9xManager(
    logger,
    config.radio,
    spi0,
    initialize_pin(logger, board.SPI0_CS0, digitalio.Direction.OUTPUT, True),
    initialize_pin(logger, board.RF1_RST, digitalio.Direction.OUTPUT, True),
)

magnetometer = LIS2MDLManager(logger, i2c1)

imu = LSM6DSOXManager(logger, i2c1, 0x6B)

uhf_packet_manager = PacketManager(
    logger,
    uhf_radio,
    config.radio.license,
    Counter(2),
    0.2,
)

cdh = CommandDataHandler(logger, config, uhf_packet_manager)

beacon = Beacon(
    logger,
    config.cubesat_name,
    uhf_packet_manager,
    time.monotonic(),
    imu,
    magnetometer,
    uhf_radio,
    sband_radio,
)




print("Receiving Cosmic Watch Data...")


try:
    print("About to send radio message...")
    uhf_radio.send("hello")
    print("Radio message sent successfully!")
except Exception as e:
    print(f"Radio failed in main code: {e}")



uart = busio.UART(board.TX, board.RX, baudrate = 9600, timeout = 10)


import time

buffer = bytearray()
END_MARKER = b"\n --- \n"  # Message ends with this

try:
    while True:
        data = uart.read(64)  # Read in chunks
        if data:
            buffer.extend(data)
            
            # Check if a complete message is received
            if END_MARKER in buffer:
                # Split at the end marker
                msg_end = buffer.find(END_MARKER) + len(END_MARKER)
                full_msg = buffer[:msg_end]  # Extract full message
                buffer = buffer[msg_end:]    # Remove processed part
                
                try:
                    print(full_msg.decode().strip())  # Print whole message
                    uhf_radio.send(full_msg)       # Uncomment to send
                except UnicodeError:
                    print("Bad data:", full_msg)
        
        time.sleep(0.001)  # Small delay to prevent CPU overload

except KeyboardInterrupt:
    print("Stopping...")

except Exception as e:
    print(f"Error: {e}")
