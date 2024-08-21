import requests
import classes
import pprint

def ping_endpoint(endpoint_url:str=None):
    try:
        response = requests.get(endpoint_url)
        if response.status_code == 200:
            print(f"Ping to {endpoint_url} successful!")
        else:
            print(f"Ping to {endpoint_url} failed with status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error pinging {endpoint_url}: {e}")

def correct_request_test():
    violation = classes.ViolationLog()
    violation.set_as_default_correct_dict()

    pprint.pprint(violation.get_violation_log())
    pass



correct_request_test()