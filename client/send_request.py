import requests

def send_post_request():
    response = requests.get('http://localhost:5000/')
    print(response.text)


if __name__ == '__main__':
    send_post_request()