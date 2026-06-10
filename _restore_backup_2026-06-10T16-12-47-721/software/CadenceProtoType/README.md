# Cadence software prototype using WOKWI (unfinished)
---
## Description
prelim system I used to familiarize myself with circuitpython + help plan out the final system that will be writting in F Prime. It's not finished and it'll probably never be because I'll be pivoting to an F' system

## Features

### Basic Structure
- All command handling/data sending/module comms is handled through the CDH module, which acts as a central node connecting all the modules. CDH holds the functions to request data from any of the other modules 
- The Comms module handles packetization of requested data before "downlink", which in this case is just printing to the console
- GroundStation holds the commands that may be sent from ground during a real mission, simulating a ask/response flow
- Other Modules (ADCS, Payload, FDIR) handle their respective hardware, recording data from them when requested

- From main, a command is called from ground, for example, requesting payload data. This command then goes to CDH, which identifies the command and links to the Payload module. Data is read and sent back to the CDH module,
 which proceeds to send it to COMMS where it will be packetized and given an ID. COMMS then "downlinks" this package, presenting the data in the packetized format, as well as the verification if
 the data is intact


### Commands

1. Get processed gas data -> reads data from simulated gas sensor and multiplies it by some number ("processing" lol), then sends data
2. Get raw gas data -> reads data from simulated gas sensor and sends raw value
3. Get ADCS data -> reads data from the simulated IMU; Returns acceleration x,y,z, Gyro x,y,z, and Temperature
4. Check health -> returns output based on battery level (which is hard coded atm), if level <30 outputs low power mode, if >30 outputs normal mode
5. Set rate -> fake function to set polling rate of gas sensor, input value and it says it updated it (the number doesn't do anything)
q. Quit -> quit

### File Organization
- each file represents a system that will be in the final system architecture (CDH, ADCS, Payload, FDIR, COMMS), which are controlled from main
- GroundStation.py simulates commands being sent from ground station, not a planned module in final architecture (I don't think)
- diagram.json is for circuitpython so it knows the setup in the simulated hardware 
- everything else (requirements, adafruit_sd.py, init_sd.py, SD card - all hold library dependancies and driver code for the simulated hardware 

***!!! none of the SD card code does anything, it is all commented out because it doesnt work !!!***

### How to clone
1. go to https://wokwi.com/ and start a new project on a Raspberry Pi Pico board, using the CircuitPython template
2. upload all the files into the project
3. Wokwi should be able to simulate the hardware via the diagram.json, and the dependancies will be settled by the imports and requirements file, so thats it


