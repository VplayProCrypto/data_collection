import os
import time
import subprocess
from orm.initialize_functions import add_all_collections

lock_file = "/tmp/add_collection.lock"

if os.path.exists(lock_file):
    print("Script is already running.")
    exit(1)

open(lock_file, 'w').close()

try:
    print("Script is running...")
    add_all_collections('games.json')
finally:
    os.remove(lock_file)
    print("Script has finished.")

    # Relaunch the script
    subprocess.Popen(["/usr/bin/python3", "/path/to/add_collections.py"])
