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
    GET_ALLOWED_TOS_ENDPOINT = f"{PARAM_SERVER_URL}/get_allowed_tos"
    user_datas = [["erdem.canaz", "erdem123"], ["akif.tufan.perciner", "akif123"], ["ui.node", "ui123"], ["not_existing","123"]]

    for user_data in user_datas:
        print("\n")
        username, password = user_data[0], user_data[1]    
        print(f"Current user: {username}")    
        print(f"Getting an acces token from {GET_TOKEN_ENDPOINT} with {username}'s credentials")
        acces_token, status_code = get_acces_token(url = GET_TOKEN_ENDPOINT, username=username, password= password)
        print(f"Getting privilages of the user by sending request to {GET_ALLOWED_TOS_ENDPOINT}")
        allowed_tos_data, status_code = get_dummy_data(url = GET_ALLOWED_TOS_ENDPOINT, acces_token=acces_token)
        print(f"{username} is allowed to -> {allowed_tos_data}")


