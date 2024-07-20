import requests

PARAM_SERVER_URL = "http://127.0.0.1:8000"

def get_acces_token(url:str = None, username:str = None, password:str = None):
    payload = {'username': username, 'password': password}
    response = requests.post(url, data=payload)
    acces_token = response.json().get("access_token")
    return acces_token, response.status_code

def get_dummy_data(url:str = None, acces_token:str = None):
    headers = {'Authorization': f'Bearer {acces_token}'}
    response = requests.get(url, headers=headers)
    return response.json(), response.status_code


if __name__ == '__main__':
    GET_TOKEN_ENDPOINT = f"{PARAM_SERVER_URL}/get_token"
    acces_token, status_code = get_acces_token(url = GET_TOKEN_ENDPOINT, username="erdem.canaz", password="erdem123")


    GET_ALLOWED_TOS_ENDPOINT = f"{PARAM_SERVER_URL}/get_allowed_tos"
    allowed_tos_data, status_code = get_dummy_data(url = GET_ALLOWED_TOS_ENDPOINT, acces_token=acces_token)

    print(allowed_tos_data)