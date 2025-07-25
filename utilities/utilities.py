import requests
import random
from bot_service.config import BASE_URL
from datetime import datetime, timedelta

def new_game(master_id):
    response = requests.post(BASE_URL + "/game/create", json = {
        'type': "classic",
        'slots_cnt': 10,
        'room': "A-204",
        'masterID': master_id
    })
    print(response.text)

def reg_bots(game_id, n):
    for i in range(1, n + 1):
        response = requests.post(f"{BASE_URL}/reg", json={
            "ID": i,
            "nickname": f"Utopia-{i}",
            "username": f"Username-{i}",
            "group_name": f"ИКБО-{i}-25"})
        print(response.content)

def reg_bot_to_game(game_id, bot_id):
    response = requests.post(f"{BASE_URL}/game/reg", json={
        "player_id": bot_id,
        "game_id": game_id})
    print(response.content)

def reg_bots_to_game(game_id, n):
    for i in range(1, n + 1):
        reg_bot_to_game(game_id, i)

def unreg_bot_from_game(game_id, bot_id):
    response = requests.delete(f"{BASE_URL}/game/unreg", json={
        "player_id": bot_id,
        "game_id": game_id})
    print(response.content)

def unreg_bots_from_game(game_id, n):
    for i in range(1, n + 1):
        unreg_bot_from_game(game_id, i)

if __name__ == "__main__":
    #reg_bots(2, 13)
    reg_bots_to_game(4, 12)
    unreg_bots_from_game(4, 4)
    #new_game(1040117682)