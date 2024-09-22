import random
from pathlib import Path
import sys

# Local imports
API_SERVER_DIRECTORY = Path(__file__).resolve().parent
SAFETY_AI2_DIRECTORY = API_SERVER_DIRECTORY.parent
print(f"API_SERVER_DIRECTORY: {API_SERVER_DIRECTORY}")
print(f"SAFETY_AI2_DIRECTORY: {SAFETY_AI2_DIRECTORY}")
sys.path.append(str(SAFETY_AI2_DIRECTORY)) # Add the modules directory to the system path so that below imports work

import PREFERENCES
import sql_module



#================================================================================================
print("\n ADMIN CONSOLE \n")
tasks = {
    "0": "Delete database",
}
for key, value in tasks.items():
    print(key, value)

desired_task = input("Enter the task you want to perform: ")
if desired_task == "0":
    random_number = random.randint(100000, 1000000)
    entered_number = input(f"Enter the number {random_number} to confirm the deletion of the database: ")
    if entered_number == str(random_number):
        print("Please ensure that server is not running.")
        is_server_running = input("Is the server running? (yes/no): ")
        if is_server_running != "no":
            print("Please stop the server and try again.")
            sys.exit(0)
        sql_module.SQLManager.delete_database()
        print("Database deleted successfully.")
    else:
        print("Entered number is incorrect. Database deletion cancelled.")