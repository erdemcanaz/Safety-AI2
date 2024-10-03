import serial.tools.list_ports
import serial
import time

# List all available COM ports
ports = serial.tools.list_ports.comports()
if len(ports) == 0:
    print("No COM ports found. Please check your connection.")
    exit()

print("Available COM ports:")
for index, port in enumerate(ports):
    print(f"{index}: {port.device} - {port.description}")

# Ask the user to select the correct COM port
try:
    which_comport = int(input("Enter the index of the COM port you want to use: "))
    comport = ports[which_comport].device
except (ValueError, IndexError):
    print("Invalid selection. Exiting.")
    exit()

# Attempt to open the serial port
try:
    ser = serial.Serial(comport, 9600, timeout=1)  # Ensure baud rate matches your device
    print(f"Opened serial port {comport} successfully.")
except serial.SerialException as e:
    print(f"Failed to open serial port {comport}. Error: {e}")
    exit()

# Wait for the device to be ready, since it resets when the serial connection is opened
print("Please wait for the device to be ready for 5 seconds...")

# Loop for sending data
try:
    while True:
        # Send '001780' as ASCII encoded data
        data_to_send = input("Enter the data you want to send (i.e., 001780). Type 'exit' to close: ")
        if data_to_send.lower() == "exit":
            break
        if not data_to_send:
            print("No data entered. Please try again.")
            continue

        ser.write(data_to_send.encode('ascii'))
        print(f"Sent: {data_to_send}")

except serial.SerialException as e:
    print(f"Error during communication: {e}")
finally:
    # Close the serial connection
    ser.close()
    print(f"Serial connection to {comport} closed.")
