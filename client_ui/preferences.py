import os

if os.name == "nt":  # For Windows
    SERVER_IP_ADDRESS = "192.168.0.26"
    PRINT_MOUSE_COORDINATES = True
elif os.name == "posix":  # For Unix-like systems (Linux, macOS, etc.)
    SERVER_IP_ADDRESS = input("Server IP Address: ")
    PRINT_MOUSE_COORDINATES = False




