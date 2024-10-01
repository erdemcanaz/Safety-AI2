#List all the comports available
import serial.tools.list_ports
ports = serial.tools.list_ports.comports()
for index, port in enumerate(ports):
    print(index, port.device)

which_comport = int(input("Enter the index of the comport you want to ping: "))
comport = ports[which_comport].device

import serial
ser = serial.Serial(comport, 9600)
ser.write(b'001780')
print(ser.readline())



