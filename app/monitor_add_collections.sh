#!/bin/bash

while true
do
    # Check if the script is running
    if ! pgrep -f add_collection.py > /dev/null
    then
        # Start the script if it's not running
        /usr/bin/python3 /path/to/add_collection.py &
    fi
    # Wait for 1 minute before checking again
    sleep 60
done
