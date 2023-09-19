import requests


def receive_api_cards():
    url = "http://127.0.0.1:8085/getPlayersCards"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()[:5]
