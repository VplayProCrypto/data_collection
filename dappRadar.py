import json
import os
import requests
import argparse
from utils import get_error_message, del_none_keys

api_key = 'InrjMd9Bxc6geuaIus7lm2wIDHqjwr3575qt6hYk'

def append_data_to_file(file_path, new_data):
    # Check if the file exists and is not empty
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        # Open the file in read/write mode
        with open(file_path, 'r+') as file:
            file.seek(0, os.SEEK_END)  # Move to the end of the file
            file.seek(file.tell() - 1, os.SEEK_SET)  # Move back before the closing ']'

            if file.read(1) != '[':
                file.seek(file.tell() - 1, os.SEEK_SET)  # Move back before the closing ']'
                file.write(',')  # Write a comma if the list is not empty

            # Write the new data and close the list
            file.write(json.dumps(new_data)[1:-1] + ']')
    else:
        # If file doesn't exist or is empty, create a new file with initial data
        with open(file_path, 'w') as file:
            json.dump(new_data, file, indent=4)

# Example usage
new_data = [{"new_key": "new_value"}]  # Replace with your actual new data
file_path = 'your_data_file.json'
append_data_to_file(file_path, new_data)


def get_last_page():
    try: 
        with open('last_page.txt') as page:
            last_page_num = int(page.read())
    except FileNotFoundError:
        with open('last_page.txt', 'w') as page:
            page.write('1')
            last_page_num = 1
    # except ValueError:
    #     print("invlaid number")

    return last_page_num

def update_last_page(page_num):
    with open('last_page.txt') as f:
        f.write(str(page_num))

def store_daaps_data(file_path, results_per_page = 50, number_of_pages = 10, chain = 'ethereum'):
    base_endpoint = 'https://apis.dappradar.com/v2/dapps'

    headers = {
        'accept': 'application/json',
        'x-api-key': api_key
    }


    for i in range(number_of_pages):
        last_page_num = get_last_page()
        print(last_page_num)
        params = {
            'chain': chain,
            'page': last_page_num,
            'resultsPerPage': results_per_page
        }
        r = requests.get(base_endpoint, params = params)
        print(r)
        msg = get_error_message(r)
        if msg:
            raise ConnectionError(msg)
        
        new_data = r.json()['results']
        append_data_to_file(file_path = file_path, new_data = json.dumps(new_data))
        update_last_page(last_page_num + i)
        print("Appended")
    
    print("Done")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_path', help = 'file path to store the data to')
    parser.add_argument('--chain', help = 'chain to search')
    parser.add_argument('--res_page', help = 'results per page')
    parser.add_argument('--num_pages', help = 'number of pages to request')
    args = parser.parse_args().__dict__

    try:
        file_path = args['file_path']
    except KeyError:
        raise('Please add a file path')
    
    args = del_none_keys(args)
    if 'chain' in args:
        chain = args['chain']
    else:
        chain = 'ethereum'
    
    if 'num_pages' in args:
        number_of_pages = args['num_pages']
    else:
        number_of_pages = 1
    
    if 'res_page' in args:
        results_per_page = args['res_page']
    else:
        results_per_page = 50

    store_daaps_data(file_path = file_path, results_per_page = results_per_page, number_of_pages = number_of_pages, chain = chain)

if __name__ == "__main__":
    main()