from flask import Flask, jsonify, request
from config import ROLES_CONFIG
from server_service import database as DB

app = Flask(__name__)
DB.init_db()

@app.route('/reg', methods=['POST'])
def register_player():
    try:
        data = request.get_json()
        print('/reg', data)
        if not data:
            return jsonify({"error": "No data provided"}), 400

        response, status_code = DB.APIHandler.register_player(data)

        return jsonify(response), status_code

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/change_nickname', methods=['POST'])
def change_nickname():
    data = request.get_json()
    response, status_code = DB.APIHandler.change_nickname(data)
    return jsonify(response), status_code

@app.route('/change_room', methods=['POST'])
def change_room():
    data = request.get_json()
    response, status_code = DB.APIHandler.change_room(data)
    return jsonify(response), status_code

@app.route('/change_master', methods=['POST'])
def change_master():
    data = request.get_json()
    response, status_code = DB.APIHandler.change_master(data)
    return jsonify(response), status_code

@app.route('/change_date', methods=['POST'])
def change_date():
    data = request.get_json()
    response, status_code = DB.APIHandler.change_date(data)
    return jsonify(response), status_code

@app.route('/change_status', methods=['POST'])
def change_status():
    data = request.get_json()
    response, status_code = DB.APIHandler.change_status(data)
    return jsonify(response), status_code

@app.route('/players/list', methods=['GET'])
def get_players_list():
    response, status_code = DB.APIHandler.get_players_list()
    return jsonify(response), status_code

@app.route('/players/<int:player_id>', methods=['GET'])
def get_player(player_id):
    try:
        response, status_code = DB.APIHandler.get_player_info(player_id)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stat', methods=['GET'])
def get_stat():
    response, status_code = DB.APIHandler.get_stat()
    print('/stat', response)
    return jsonify(response), status_code

@app.route('/game/create', methods=['POST'])
def create_new_game():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        response, status_code = DB.APIHandler.create_game(data)
        return jsonify(response), status_code

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/game/list', methods=['GET'])
def get_games_list():
    try:
        games_response, games_status_code = DB.APIHandler.get_games()
        registrations_response, registrations_status_code = DB.APIHandler.get_registrations()
        if (registrations_status_code // 100 != 2):
            return jsonify({"error": f"Invalid registrations response: {registrations_status_code, registrations_response}"}), 500
        elif (games_status_code // 100 != 2):
            return jsonify({"error": f"Invalid game response: {games_status_code, games_response}"}), 500
        response = {"count": games_response["count"], "games": []}
        for game in games_response["games"]:
                response["games"].append({
                    "game_id": game['game_id'],
                    "room": game['room'],
                    "type": game['type'],
                    "date": game['date'],
                    "master_id": game['master_id'],
                    "master_nickname": game['master_nickname'] if game['master_nickname'] else "Unknown",
                    "slots_cnt": game['slots_cnt'],
                    "registrations": sum(1 for reg in registrations_response["registrations"] if reg['game_id'] == game['game_id'])
                })
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/game/<int:game_id>', methods=['DELETE'])
def delete_existing_game(game_id):
    try:
        response, status_code = DB.APIHandler.delete_game(game_id)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/game/<int:game_id>', methods=['GET'])
def get_game(game_id):
    try:
        response, status_code = DB.APIHandler.get_game_by_id(game_id)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/game/reg', methods=['POST'])
def register_player_to_game():
    try:
        data = request.get_json()
        response, status_code = DB.APIHandler.get_game_by_id(data["game_id"])
        print('/game/reg', response)
        data["in_queue"] = 1 - int(response["available_slots"] > 0)
        response, status_code = DB.APIHandler.register_to_game(data)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/game/registrations', methods=['GET'])
def get_registrations_list():
    try:
        try:
            data = request.get_json()
            print('/game/registrations', data)
            if ("player_id" in data):
                response, status_code = DB.APIHandler.get_registrations(data["player_id"])
        except:
            response, status_code = DB.APIHandler.get_registrations()
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/game/unreg', methods=['DELETE'])
def cancel_player_registration():
    try:
        data = request.get_json()
        response, status_code = DB.APIHandler.cancel_registration(data)
        print('/game/unreg', response)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/games/<int:game_id>/slots', methods=['PUT'])
def assign_slots_route(game_id):
    """
    Распределение мест для игры
    Пример ответа:
    {"message": "Assigned 5 slots"}
    """
    try:
        # Проверка прав доступа (добавьте при необходимости)
        response, status_code = DB.APIHandler.assign_slots(game_id)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/games/<int:game_id>/roles', methods=['PUT'])
def assign_roles_route(game_id):
    try:
        response, status_code = DB.APIHandler.assign_roles(game_id, ROLES_CONFIG)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/games/<int:game_id>/force_roles', methods=['PUT'])
def force_roles_route(game_id):
    """
    Принудительное назначение ролей по слотам
    Пример тела запроса:
    {
        "roles": ["mafia", "don", "civilian", ...]
    }
    """
    try:
        data = request.get_json()
        if not data or 'roles' not in data:
            return jsonify({"error": "Roles array required"}), 400

        # Здесь можно добавить проверку прав доступа
        # (например, что пользователь - мастер игры)

        response, status_code = DB.APIHandler.force_roles(game_id, data['roles'])
        return jsonify(response), status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/games/<int:game_id>/force_slots', methods=['PUT'])
def force_slots_route(game_id):
    """
    Принудительное распределение мест
    Пример тела запроса:
    {
        "player_ids": [123, 456, 789, ...]
    }
    """
    try:
        data = request.get_json()
        if not data or 'player_ids' not in data:
            return jsonify({"error": "Player IDs array required"}), 400


        response, status_code = DB.APIHandler.force_slots(game_id, data['player_ids'])
        return jsonify(response), status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/games/<int:game_id>/finish', methods=['POST'])
def finish_game_route(game_id):
    try:
        data = request.get_json()
        if data is None or 'civilians_win' not in data:
            return jsonify({"error": "civilians_win field required"}), 400

        response, status_code = DB.APIHandler.finish_game(game_id, data['civilians_win'])
        return jsonify(response), status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stats/<string:game_type>/players', methods=['GET'])
def get_players_stats(game_type):
    try:
        response, status_code = DB.APIHandler.get_player_stats(game_type)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stats/player/<string:player_id>/games', methods=['GET'])
def get_player_games(player_id):
    try:
        response, status_code = DB.APIHandler.get_player_games(player_id, 1)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/registrations/archive/<string:game_id>', methods=['GET'])
def get_archived_registrations(game_id):
    try:
        response, status_code = DB.APIHandler.get_archived_registrations(game_id)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)