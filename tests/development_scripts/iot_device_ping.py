import serial.tools.list_ports
import serial
import time

# List all available COM ports
ports = serial.tools.list_ports.comports()
for index, port in enumerate(ports):
    print(f"{index}: {port.device}")

# Ask the user to select the correct COM port
which_comport = int(input("Enter the index of the COM port you want to use: "))
comport = ports[which_comport].device


# Open the serial port
ser = serial.Serial(comport, 9600)  # Make sure the baud rate matches your device

# Wait for the device to be ready, since it resets when the serial connection is opened
print("Waiting for the device to be ready for 5 seconds...")
time.sleep(5)

# Send '001780' as ASCII encoded data
data_to_send = '001780'
ser.write(data_to_send.encode('ascii'))

# Close the serial connection
ser.close()


