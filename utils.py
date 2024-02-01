import requests

def get_error_message(request: requests.Response):
    status = request.status_code
    if status == 200:
        return None
    elif status == 403:
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