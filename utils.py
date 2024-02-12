import json
import os
import requests

def get_error_message(request: requests.Response):
    status = request.status_code
    if status == 200:
        return None
    elif status == 403:
        print(status)
        return "Forbidden access"
    elif status == 500:
        return "Internal server error"
    else:
        msg = request.json()['message']
        return msg
    
def del_none_keys(args: dict):
    new_args = args.copy()
    for key in args:
        if args[key] is None:
            del new_args[key]

    return new_args


def append_data_to_file(file_path: str, new_data: any):
    # assert(isinstance(new_data, dict)), "The data to be added should be a dictionary"
    # Check if the file exists and is not empty
    # assert(isinstance(new_data, dict) or isinstance(new_data, list))
    if not isinstance(new_data, list):
        new_data = [new_data]
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        # Open the file in read/write mode
        with open(file_path, 'r+') as file:
            file.seek(0, os.SEEK_END)  # Move to the end of the file
            file.seek(file.tell() - 1, os.SEEK_SET)  # Move back before the closing ']'

            # Write the new data and close the list
            file.write(',' + json.dumps(new_data, indent = 4)[1:-1] + ']')
    else:
        # If file doesn't exist or is empty, create a new file with initial data
        with open(file_path, 'w') as file:
            json.dump(new_data, file, indent=4)

# Example usage
new_data = {'a':'a'} # {"new_key": "new_value"} # Replace with your actual new data
file_path = 'your_data_file.json'
append_data_to_file(file_path, new_data)
