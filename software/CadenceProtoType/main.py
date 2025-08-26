from cdhModule import CDH
from payloadModule import PAYLOAD
from commsModule import COMMS
from adcsModule import ADCS
from fdirModule import FDIR
from groundStation import GROUND
import time

# Initialize systems
cdh = CDH(PAYLOAD(), COMMS(), ADCS(), FDIR())
ground = GROUND(cdh)
batt = 10

# Command menu
while True:
    print("\n1. Get processed gas data\n2. Get raw gas data\n3. Get ADCS data\n4. Check health\n5. Set rate\nq. Quit")   
    choice = input("\nSelect: ").strip()
    
    if choice == '1':
        print(ground.send_command("payload", False))
    
    elif choice == '2':
        print(ground.send_command("payload", True))

    elif choice == '3':
        print(ground.send_command("adcs"))

    elif choice == '4':
        print(ground.send_command("health", int(batt)) if batt else ground.send_command("health"))

    elif choice == '5':
        rate = float(input("Polling rate (s): "))
        print(ground.send_command("rate", rate))

    elif choice.lower() == 'q':
        break
    else:
        print("\nInvalid choice")

    loop = input("\n input another command?: (y/n)")

    if loop == 'n':
      break
    elif loop =='y':
      print("repeating command options. . .")

    
