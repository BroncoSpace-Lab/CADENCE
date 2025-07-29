import board
import busio
import digitalio
import storage
import adafruit_sdcard

def display_csv_contents():
    # Mount SD card
    try:
        cs = digitalio.DigitalInOut(board.GP1)
        spi = busio.SPI(board.GP2, board.GP3, board.GP0)
        sdcard = adafruit_sdcard.SDCard(spi, cs)
        vfs = storage.VfsFat(sdcard)
        storage.mount(vfs, "/sd")
        print("SD card mounted successfully")
    except Exception as e:
        print(f"SD card mount failed: {e}")
        return

    # Read and display CSV file
    filename = '/sd/particle_logs.csv'
    
    try:
        with open(filename, 'r') as f:
            print(f"\n--- Contents of {filename} ---")
            print("-" * 50)
            
            line_count = 0
            for line in f:
                line_count += 1
                print(f"{line_count:3d}: {line.strip()}")
            
            print("-" * 50)
            print(f"Total lines: {line_count}")
            
    except OSError:
        print(f"File {filename} not found")
        
        # List all files in SD root to help debug
        try:
            files = storage.listdir("/sd")
            print(f"\nFiles found on SD card:")
            for file in files:
                print(f"  - {file}")
        except:
            print("Could not list SD card contents")
            
    except Exception as e:
        print(f"Error reading file: {e}")
    
    finally:
        # Unmount SD card
        try:
            storage.umount("/sd")
            print("\nSD card unmounted")
        except:
            pass

# Run the function
display_csv_contents()