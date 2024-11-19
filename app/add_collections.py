import os
import time
from orm.initialize_functions import add_all_collections

lock_file = "/tmp/add_collection.lock"

while True:
    if os.path.exists(lock_file):
        print("Script is already running. Waiting for the current instance to complete...")
        time.sleep(10)  # Wait for 10 seconds before checking again
        continue

    try:
        # Create the lock file to indicate the script is running
        open(lock_file, 'w').close()
        print("Script is running...")

        # Run the main function to add all collections
        add_all_collections('games.json')

    except Exception as e:
        print(f"An error occurred during the execution: {e}")

    finally:
        # Ensure that the lock file is removed after the operation
        if os.path.exists(lock_file):
            os.remove(lock_file)
        print("Script has finished.")

    # Optional: Add a delay before restarting the function to control the frequency of execution
    time.sleep(10)  # Wait for 10 seconds before the next iteration

