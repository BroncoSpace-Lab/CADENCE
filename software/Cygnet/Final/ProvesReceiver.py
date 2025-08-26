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
import json


SEND_PING = "ping"
SEND_NOTIFICATION_SINGLE = "send_notification"
SEND_NOTIFICATION_CONTINUOUS = "send_notification_continuous"
SEND_NOTIFICATION_BATCH = "send_notification_batch"
SEND_NOTIFICATION_BATCH_CONTINUOUS = "send_notification_batch_continuous"

RECEIVE_NOTIFICATION_SINGLE = "receive_notification"
RECEIVE_NOTIFICATION_CONTINUOUS = "receive_notification_continuous"
RECEIVE_NOTIFICATION_BATCH = "receive_notification_batch"
RECEIVE_NOTIFICATION_BATCH_CONTINUOUS = "receive_notification_batch_continuous"

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
    log_level = 2,
    colorized=False
)

logger.info(
    "Booting",
    hardware_version=os.uname().version,
    software_version=__version__,
)

watchdog = Watchdog(logger, board.WDT_WDI)
watchdog.pet()



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

sleep_helper = SleepHelper(logger, config, watchdog)

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

def receive_notification_UART_single(timeout):
    buffer = bytearray()
    END_MARKER = b"\n --- \n"  # Message ends with this
    start = time.time()
    
    try:
        while time.time() - start < timeout:
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
                        decoded_msg = full_msg.decode().strip()
                        print(decoded_msg)
                        return decoded_msg
                    except UnicodeError:
                        print("Bad data:", full_msg)
                        return None
            
            time.sleep(0.001)
        
        # Timeout reached without complete message
        print("Timeout: No complete message received")
        return None
        
    except Exception as e:
        print(f"Error: {e}")
        return None
    


def receive_notification_UART_continuous():

    """Continuously receive and print UART messages until interrupted"""
    buffer = bytearray()
    END_MARKER = b"\n --- \n"
    
    try:
        while True:
            data = uart.read(64)  # Read in chunks
            if data:
                buffer.extend(data)
                
                # Process all complete messages in buffer
                while END_MARKER in buffer:
                    # Split at the end marker
                    msg_end = buffer.find(END_MARKER) + len(END_MARKER)
                    full_msg = buffer[:msg_end]  # Extract full message
                    buffer = buffer[msg_end:]    # Remove processed part
                    
                    try:
                        decoded_msg = full_msg.decode().strip()
                        print(decoded_msg)  # Print the complete message
                        uhf_packet_manager.send(full_msg)
                        yield decoded_msg
                    except UnicodeError:
                        print("Bad data:", full_msg)
            
            time.sleep(0.001)  # Small delay to prevent CPU overload
            
    except KeyboardInterrupt:
        print("Stopping...")
    except Exception as e:
        print(f"Error: {e}")

def receive_notification_UART_batch_single(collection_time):
    """Collect UART messages for specified time, then send all at once"""
    buffer = bytearray()
    END_MARKER = b"\n --- \n"
    collected_messages = []
    start_time = time.time()
    
    print(f"Collecting data for {collection_time} seconds...")
    
    try:
        while time.time() - start_time < collection_time:
            data = uart.read(64)  # Read in chunks
            if data:
                buffer.extend(data)
                
                # Process all complete messages in buffer
                while END_MARKER in buffer:
                    # Split at the end marker
                    msg_end = buffer.find(END_MARKER) + len(END_MARKER)
                    full_msg = buffer[:msg_end]  # Extract full message
                    buffer = buffer[msg_end:]    # Remove processed part
                    
                    try:
                        decoded_msg = full_msg.decode().strip()
                        print(f"Collected: {decoded_msg}")  # Show what we're collecting
                        collected_messages.append(decoded_msg)
                    except UnicodeError:
                        print("Bad data:", full_msg)
            
            time.sleep(0.001)  # Small delay to prevent CPU overload
        
        # Collection time is up - now send all messages
        print(f"\nCollection complete! Collected {len(collected_messages)} messages")
        
        if collected_messages:
            # Combine all messages into one batch
            batch_data = "\n".join(collected_messages)
            
            # Print the batch to terminal before sending
            print("\n" + "="*50)
            print("BATCH DATA TO BE SENT:")
            print("="*50)
            print(batch_data)
            print("="*50)
            
            print(f"Sending batch: {len(batch_data)} bytes")
            
            # Send the raw batch data
            uhf_packet_manager.send(batch_data.encode('utf-8'))
            print("Batch sent successfully!")
            
        else:
            print("No messages collected during the time period")

            return batch_data
            
    except KeyboardInterrupt:
        print(f"\nCollection interrupted! Collected {len(collected_messages)} messages so far")
        if collected_messages:
            # Send what we have collected so far
            batch_data = "\n".join(collected_messages)
            
            # Print the partial batch to terminal before sending
            print("\n" + "="*50)
            print("PARTIAL BATCH DATA TO BE SENT:")
            print("="*50)
            print(batch_data)
            print("="*50)
            
            uhf_packet_manager.send(batch_data.encode('utf-8'))
            print("Partial batch sent!")
            return batch_data
    except Exception as e:
        print(f"Error during batch collection: {e}")


def receive_notification_UART_batch_continuous(collection_time):
    """Continuously collect and send batches at specified intervals"""
    batch_number = 1
    
    print(f"Starting continuous batch mode - collecting {collection_time} seconds per batch")
    print("Press Ctrl+C to stop")
    
    try:
        while True:  # Main continuous loop
            print(f"\n{'='*60}")
            print(f"BATCH {batch_number} - Starting collection...")
            print(f"{'='*60}")
            
            # Initialize for this batch
            buffer = bytearray()
            END_MARKER = b"\n --- \n"
            collected_messages = []
            start_time = time.time()
            
            # Collection phase for this batch
            try:
                while time.time() - start_time < collection_time:
                    data = uart.read(64)  # Read in chunks
                    if data:
                        buffer.extend(data)
                        
                        # Process all complete messages in buffer
                        while END_MARKER in buffer:
                            # Split at the end marker
                            msg_end = buffer.find(END_MARKER) + len(END_MARKER)
                            full_msg = buffer[:msg_end]  # Extract full message
                            buffer = buffer[msg_end:]    # Remove processed part
                            
                            try:
                                decoded_msg = full_msg.decode().strip()
                                print(f"Collected: {decoded_msg}")  # Show what we're collecting
                                collected_messages.append(decoded_msg)
                            except UnicodeError:
                                print("Bad data:", full_msg)
                    
                    time.sleep(0.001)  # Small delay to prevent CPU overload
                
                # Send phase for this batch
                print(f"\nBatch {batch_number} collection complete! Collected {len(collected_messages)} messages")
                
                if collected_messages:
                    # Combine all messages into one batch
                    batch_data = "\n".join(collected_messages)
                    
                    # Print the batch to terminal before sending
                    print("\n" + "="*50)
                    print(f"BATCH {batch_number} DATA TO BE SENT:")
                    print("="*50)
                    print(batch_data)
                    print("="*50)
                    
                    print(f"Sending batch {batch_number}: {len(batch_data)} bytes")
                    
                    # Send the raw batch data
                    uhf_packet_manager.send(batch_data.encode('utf-8'))
                    print(f"Batch {batch_number} sent successfully!")
                    yield batch_data
                    
                else:
                    print(f"No messages collected in batch {batch_number}")
                
                batch_number += 1
                print(f"\n Starting batch {batch_number}...")
                time.sleep(0.01)
                
            except Exception as batch_error:
                print(f"Error in batch {batch_number}: {batch_error}")
                # Send partial data if any was collected
                if collected_messages:
                    batch_data = "\n".join(collected_messages)
                    print(f"Sending partial batch {batch_number} due to error")
                    uhf_packet_manager.send(batch_data.encode('utf-8'))
                    yield batch_data
                batch_number += 1
                time.sleep(2)  # Wait before trying next batch
                
    except KeyboardInterrupt:
        print(f"\n\nContinuous batch mode stopped after {batch_number-1} completed batches")
        print("Final batch may be incomplete")
    except Exception as e:
        print(f"Fatal error in continuous batch mode: {e}")


def send_notification_single(
        logger,
        uhf_packet_manager,
        sleep_helper,
        config,
        my_callsign = None,
        target_callsigns = None
):
    if my_callsign is None:
        target_callsigns = config.radio.license
    timeout = 5.0
    wait_for_data = True
    notification = receive_notification_UART_single()
    response_message = {
        "current_time": time.monotonic(),
        "callsign": my_callsign,
        "command": RECEIVE_NOTIFICATION_SINGLE,
        "notification": notification
    }

    encoded_response = json.dumps(response_message, separators=(",",":"))

    print(f"sending notification: {encoded_response}")
    sleep_helper.safe_sleep(1)
    uhf_packet_manager.send(encoded_response)
   

def send_notification_continuous(
        logger,
        uhf_packet_manager,
        sleep_helper,
        config,
        my_callsign = None,
        target_callsigns = None
):
    if my_callsign is None:
        target_callsigns = config.radio.license
    timeout = 5.0
    wait_for_data = True
    #notification = receive_notification_UART_continuous()

    for notification in receive_notification_UART_continuous():
        response_message = {
            "current_time": time.monotonic(),
            "callsign": my_callsign,
            "command": RECEIVE_NOTIFICATION_CONTINUOUS,
            "notification": notification
    }

    encoded_response = json.dumps(response_message, separators=(",",":"))

    print(f"sending notification: {encoded_response}")
    sleep_helper.safe_sleep(1)
    uhf_packet_manager.send(encoded_response)


def send_notification_batch_single(
        logger,
        uhf_packet_manager,
        sleep_helper,
        config,
        my_callsign = None,
        target_callsigns = None
):
    if my_callsign is None:
        target_callsigns = config.radio.license
    timeout = 5.0
    wait_for_data = True
    notification = receive_notification_UART_batch_single()
    response_message = {
        "current_time": time.monotonic(),
        "callsign": my_callsign,
        "command": RECEIVE_NOTIFICATION_BATCH,
        "notification": notification
    }

    encoded_response = json.dumps(response_message, separators=(",", ":"))

    print(f"sending notification: {encoded_response}")
    sleep_helper.safe_sleep(1)
    uhf_packet_manager.send(encoded_response)

def send_notification_batch_continuous(
        logger,
        uhf_packet_manager,
        sleep_helper,
        config,
        my_callsign = None,
        target_callsigns = None
):
    if my_callsign is None:
        target_callsigns = config.radio.license
    timeout = 5.0

    for batch_notification in receive_notification_UART_batch_continuous(collection_time):
        if batch_notification:
            response_message = {
                "current_time": time.monotonic(),
                "callsign": my_callsign,
                "command": RECEIVE_NOTIFICATION_BATCH_CONTINUOUS,
                "notification": batch_notification
            }

    encoded_response = json.dumps(response_message, separators=(",", ":"))

    print(f"sending notification: {encoded_response}")
    sleep_helper.safe_sleep(1)
    uhf_packet_manager.send(encoded_response)


def listener_nominal_power_loop(
    logger, uhf_packet_manager, sleep_helper, config, my_callsign=None
):
    if my_callsign is None:
        my_callsign = config.radio.license

    received_message = uhf_packet_manager.listen(5)
    if received_message:
        try:
            decoded_message = json.loads(received_message.decode("utf-8"))
            logger.info(f"Received message: {decoded_message}")
            sender_callsign = decoded_message.get("callsign")
            if sender_callsign == my_callsign or sender_callsign == "any":
                logger.info(f"Received message: its for me! {my_callsign}")
                command = decoded_message.get("command")
                if command == SEND_PING:
                    logger.info(f"Received ping from {sender_callsign}")
                    response_message = {
                        "current_time": time.monotonic(),
                        "callsign": my_callsign,
                        "command": "pong",
                    }
                    encoded_response = json.dumps(
                        response_message, separators=(",", ":")
                    ).encode("utf-8")
                    sleep_helper.safe_sleep(1)
                    uhf_packet_manager.send(encoded_response)
                elif command == SEND_NOTIFICATION_SINGLE:
                    send_notification_single(
                        sleep_helper, uhf_packet_manager, config, my_callsign
                    )
                elif command == SEND_NOTIFICATION_CONTINUOUS:
                    send_notification_continuous(
                        sleep_helper, uhf_packet_manager, config, my_callsign
                    )
                elif command == SEND_NOTIFICATION_BATCH:
                    send_notification_batch_single(
                        sleep_helper, uhf_packet_manager, config, my_callsign
                    )
                elif command == SEND_NOTIFICATION_BATCH_CONTINUOUS:
                    send_notification_batch_continuous(
                        sleep_helper, uhf_packet_manager, config, my_callsign
                    )

        except ValueError:
            logger.error("Failed to decode message")


try:
    print("radio test -- sending message")
    uhf_packet_manager.send("Hello World")
    print("Radio message sent successfully! - continuing....")
except Exception as e:
    print(f"Radio failed in main code: {e}")


print("Receiving Cosmic Watch Data...\n")


uart = busio.UART(board.TX, board.RX, baudrate = 9600, timeout = 10)


import time
collection_time = 10
buffer = bytearray()
END_MARKER = b"\n --- \n"  # Message ends with this

method = 0
method = input("Sending options:\n"+
                "(1) Call/Response mode\n"+
                "(2) send singular Particle\n"+
                "(3) send continuous data\n"+
                f"(4) send one batch after {collection_time} seconds \n"+
                f"(5) continuously send batches every {collection_time} seconds ")

try:
    if method == '1':
        print("Initiating Ground Station Call/Response")
        while True:
            listener_nominal_power_loop(
                logger, uhf_packet_manager, sleep_helper, config, my_callsign=None)
            
    if method == '2':
        print("Initiating singular particle collection")
        receive_notification_UART_single(timeout = 20)
        
    
    elif method == '3':
        print("Initiating constant data beacon")

        for msg in receive_notification_UART_continuous():
            response_message = {
                "current_time": time.monotonic(),
                "callsign": config.radio.license,
                "command": RECEIVE_NOTIFICATION_CONTINUOUS,
                "notification": msg
            }

            encoded_response = json.dumps(response_message, separators=(",", ":"))
            print(f"sending notification: {encoded_response}")
            sleep_helper.safe_sleep(1)
            uhf_packet_manager.send(encoded_response.encode("utf-8"))

    elif method =='4':
        print("Initiating singular batch collection")
        receive_notification_UART_batch_single(collection_time)
    elif method == '5':
        print("Initiating continuous batch collection")

        for batch_notification in receive_notification_UART_batch_continuous(collection_time):
            if batch_notification:
                response_message = {
                    "current_time": time.monotonic(),
                    "callsign": config.radio.license,
                    "command": RECEIVE_NOTIFICATION_BATCH_CONTINUOUS,
                    "notification": batch_notification
                }

                encoded_response = json.dumps(response_message, separators=(",", ":"))
                print(f"sending batch notification: {encoded_response}")
                sleep_helper.safe_sleep(1)
                uhf_packet_manager.send(encoded_response.encode("utf-8"))
            else:
                print("No batch data to send this round.")

    
    else:
        print("Invalid option. Please choose (1-5)")

except KeyboardInterrupt:
    print("Stopping...")
except Exception as e:
    print(f"Error: {e}")
