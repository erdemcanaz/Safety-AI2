import os

if os.name == "nt":  # For Windows
    SERVER_IP_ADDRESS = "192.168.0.26"
elif os.name == "posix":  # For Unix-like systems (Linux, macOS, etc.)
    SERVER_IP_ADDRESS = input("Server IP Address: ")

