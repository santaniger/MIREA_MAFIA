import sqlite3
from sqlite3 import Error
import random

DATABASE = "mirea_mafia.db"


class APIHandler:
    @staticmethod
    def register_player(data):
        required_fields = ['ID', 'nickname', 'username', 'group_name']
        if not all(field in data for field in required_fields):
            return {"error": "Missing required fields"}, 400

        conn = create_connection(DATABASE)
        if not conn:
            return {"error": "Database connection failed"}, 500

        try:
            c = conn.cursor()
            c.execute("SELECT 1 FROM players WHERE ID = ?", (data['ID'],))
            if c.fetchone():
                return {"error": "Player with this ID already exists"}, 400

            c.execute("SELECT 1 FROM players WHERE nickname = ? OR username = ?",
                      (data['nickname'], data['username']))
            if c.fetchone():
                return {"error": "Nickname or username already taken"}, 400

            c.execute('''INSERT INTO players (ID, username, nickname, group_name)
                         VALUES (?, ?, ?, ?)''',
                      (data['ID'], data['username'], data['nickname'], data['group_name']))

            conn.commit()
            return {"message": "Player registered successfully", "player_id": data['ID']}, 201

        except Error as e:
            return {"error": str(e)}, 500
        finally:
            conn.close()

    @staticmethod
    def change_nickname(data):
        if 'ID' not in data or 'nickname' not in data:
            return {"error": "Missing ID or nickname"}, 400

        conn = create_connection(DATABASE)
        if not conn:
            return {"error": "Database connection failed"}, 500

        try:
            c = conn.cursor()
            c.execute("SELECT 1 FROM players WHERE ID = ?", (data['ID'],))
            if not c.fetchone():
                return {"error": "Player with this ID not found"}, 404

            c.execute("SELECT 1 FROM players WHERE nickname = ? AND ID != ?",
                      (data['nickname'], data['ID']))
            if c.fetchone():
                return {"error": "This nickname is already taken"}, 400

            c.execute("UPDATE players SET nickname = ? WHERE ID = ?",
                      (data['nickname'], data['ID']))

            conn.commit()
            return {
                "message": "Nickname changed successfully",
                "player_id": data['ID'],
                "new_nickname": data['nickname']
            }, 200

        except Error as e:
            return {"error": str(e)}, 500
        finally:
            conn.close()

    @staticmethod
    def change_room(data):
        if 'ID' not in data or 'room' not in data:
            return {"error": "Missing ID or room"}, 400

        conn = create_connection(DATABASE)
        if not conn:
            return {"error": "Database connection failed"}, 500

        try:
            c = conn.cursor()
            c.execute("SELECT 1 FROM games WHERE ID = ?", (data['ID'],))
            if not c.fetchone():
                return {"error": "Game with this ID not found"}, 404

            c.execute("UPDATE games SET room = ? WHERE ID = ?",
                      (data['room'], data['ID']))

            conn.commit()
            return {
                "message": "Game changed successfully",
                "game_id": data['ID'],
                "new_room": data['room']
            }, 200

        except Error as e:
            return {"error": str(e)}, 500
        finally:
            conn.close()

    @staticmethod
    def change_master(data):
        if 'ID' not in data or 'master_ID' not in data:
            return {"error": "Missing ID or master_ID"}, 400

        conn = create_connection(DATABASE)
        if not conn:
            return {"error": "Database connection failed"}, 500

        try:
            c = conn.cursor()
            c.execute("SELECT 1 FROM games WHERE ID = ?", (data['ID'],))
            if not c.fetchone():
                return {"error": "Game with this ID not found"}, 404

            c.execute("UPDATE games SET master_ID = ? WHERE ID = ?",
                      (data['master_ID'], data['ID']))

            conn.commit()
            return {
                "message": "Game changed successfully",
                "game_id": data['ID'],
                "new_master_ID": data['master_ID']
            }, 200

        except Error as e:
            return {"error": str(e)}, 500
        finally:
            conn.close()

    @staticmethod
    def change_date(data):
        if 'ID' not in data or 'date' not in data:
            return {"error": "Missing ID or date"}, 400

        conn = create_connection(DATABASE)
        if not conn:
            return {"error": "Database connection failed"}, 500

        try:
            c = conn.cursor()
            c.execute("SELECT 1 FROM games WHERE ID = ?", (data['ID'],))
            if not c.fetchone():
                return {"error": "Game with this ID not found"}, 404

            c.execute("UPDATE games SET date = ? WHERE ID = ?",
                      (data['date'], data['ID']))

            conn.commit()
            return {
                "message": "Game changed successfully",
                "game_id": data['ID'],
                "new_date": data['date']
            }, 200

        except Error as e:
            return {"error": str(e)}, 500
        finally:
            conn.close()

    @staticmethod
    def change_status(data):
        if 'ID' not in data:
            return {"error": "Missing ID"}, 400

        conn = create_connection(DATABASE)
        if not conn:
            return {"error": "Database connection failed"}, 500

        try:
            c = conn.cursor()
            c.execute("SELECT * FROM players WHERE ID = ?", (data['ID'],))
            player = c.fetchone()
            print("player", player)
            if not player:
                return {"error": "Player with this ID not found"}, 404
            status = not(player[4])
            c.execute("UPDATE players SET is_master = ? WHERE ID = ?",
                      (status, data['ID']))

            conn.commit()
            return {
                "message": "Status changed successfully",
                "player_id": data['ID'],
                "new_status": status
            }, 200

        except Error as e:
            return {"error": str(e)}, 500
        finally:
            conn.close()

    @staticmethod
    def get_players_list():
        conn = create_connection(DATABASE)
        if not conn:
            return {"error": "Database connection failed"}, 500

        try:
            c = conn.cursor()
            c.execute("SELECT ID, username, nickname, group_name, is_master FROM players")
            players = c.fetchall()

            players_list = []
            for player in players:
                players_list.append({
                    "ID": player[0],
                    "username": player[1],
                    "nickname": player[2],
                    "group_name": player[3],
                    "is_master": bool(player[4])
                })

            return {"players": players_list}, 200

        except Error as e:
            return {"error": str(e)}, 500
        finally:
            conn.close()

    # В класс APIHandler добавляем метод
    @staticmethod
    def get_player_info(player_id):
        """
        Получает основную информацию о игроке по его ID
        :param player_id: ID игрока
        :return: (информация о игроке, статус код)
        """
        if not player_id:
            return {"error": "Player ID required"}, 400

        conn = create_connection(DATABASE)
        if not conn:
            return {"error": "Database connection failed"}, 500

        try:
            c = conn.cursor()

            c.execute('''SELECT 
                            ID,
                            username,
                            nickname,
                            group_name,
                            is_master
                        FROM players
                        WHERE ID = ?''', (player_id,))

            player = c.fetchone()

            if not player:
                return {"error": "Player not found"}, 404

            player_info = {
                "ID": player[0],
                "username": player[1],
                "nickname": player[2],
                "group_name": player[3],
                "is_master": bool(player[4])
            }

            return player_info, 200

        except Error as e:
            return {"error": str(e)}, 500
        finally:
            conn.close()

    @staticmethod
    def get_stat():
        conn = create_connection(DATABASE)
        if not conn:
            return {"error": "Database connection failed"}, 500

        try:
            c = conn.cursor()

            c.execute('''SELECT 
                            a.game_ID, 
                            a.player_ID, 
                            p.nickname,
                            p.group_name,
                            a.role, 
                            a.slot, 
                            a.is_winner,
                            g.room,
                            g.type,
                            g.date
                        FROM archive a
                        JOIN players p ON a.player_ID = p.ID
                        JOIN games g ON a.game_ID = g.ID
                        WHERE g.is_archived = 1
                        ORDER BY g.date DESC''')

            archive_data = c.fetchall()
            print('archive_data', archive_data)

            stats = []
            for record in archive_data:
                stats.append({
                    "game_id": record[0],
                    "player_id": record[1],
                    "player_nickname": record[2],
                    "player_group": record[3],
                    "role": record[4],
                    "slot": record[5],
                    "is_winner": bool(record[6]),
                    "room": record[7],
                    "game_type": record[8],
                    "date": record[9]
                })

            return {"stats": stats, "count": len(stats)}, 200

        except Error as e:
            return {"error": str(e)}, 500
        finally:
            conn.close()

    @staticmethod
    def create_game(data):
        required_fields = ['type', 'slots_cnt', 'room', 'masterID']
        if not all(field in data for field in required_fields):
            return {"error": "Missing required fields"}, 400

        conn = create_connection(DATABASE)
        if not conn:
            return {"error": "Database connection failed"}, 500

        try:
            c = conn.cursor()

            c.execute("SELECT 1 FROM players WHERE ID = ? AND is_master = TRUE", (data['masterID'],))
            if not c.fetchone():
                return {"error": "Master with this ID not found or not a master"}, 404

            if 'date' in data:
                c.execute('''INSERT INTO games (type, room, master_ID, slots_cnt, date)
                                             VALUES (?, ?, ?, ?, ?)''',
                          (data['type'], data['room'], data['masterID'], data['slots_cnt'], data['date']))
            else:
                c.execute('''INSERT INTO games (type, room, master_ID, slots_cnt)
                             VALUES (?, ?, ?, ?)''',
                          (data['type'], data['room'], data['masterID'], data['slots_cnt']))

            game_id = c.lastrowid

            conn.commit()

            return {
                "message": "Game created successfully",
                "game_id": game_id,
                "details": {
                    "type": data['type'],
                    "slots_cnt": data['slots_cnt'],
                    "room": data['room'],
                    "masterID": data['masterID']
                }
            }, 201

        except Error as e:
            return {"error": str(e)}, 500
        finally:
            conn.close()

    @staticmethod
    def get_games():
        conn = create_connection(DATABASE)
        if not conn:
            return {"error": "Database connection failed"}, 500

        try:
            c = conn.cursor()

            c.execute('''SELECT 
                            g.ID, 
                            g.room, 
                            g.type, 
                            g.date, 
                            g.master_ID,
                            g.slots_cnt,
                            p.nickname as master_nickname
                        FROM games g
                        LEFT JOIN players p ON g.master_ID = p.ID
                        WHERE g.is_archived = 0
                        ORDER BY g.date DESC''')

            games = c.fetchall()

            games_list = []
            for game in games:
                print(game)
                games_list.append({
                    "game_id": game[0],
                    "room": game[1],
                    "type": game[2],
                    "date": game[3],
                    "master_id": game[4],
                    "slots_cnt": game[5],
                    "master_nickname": game[6] if game[6] else "Unknown"
                })

            return {"games": games_list, "count": len(games_list)}, 200

        except Error as e:
            return {"error": str(e)}, 500
        finally:
            conn.close()

    @staticmethod
    def get_game_by_id(game_id):
        """
        Получает полную информацию об игре по ID
        Параметры:
            - game_id: ID игры

        Возвращает:
            - tuple: (информация об игре в формате словаря, HTTP статус код)
        """
        if not game_id or not isinstance(game_id, int):
            return {"error": "Invalid game ID"}, 400

        conn = create_connection(DATABASE)
        if not conn:
            return {"error": "Database connection failed"}, 500

        try:
            c = conn.cursor()

            # Получаем основную информацию об игре
            c.execute('''SELECT 
                            g.ID, 
                            g.room, 
                            g.type, 
                            g.date, 
                            g.master_ID,
                            g.slots_cnt,
                            p.nickname as master_nickname
                        FROM games g
                        LEFT JOIN players p ON g.master_ID = p.ID
                        WHERE g.ID = ?''', (game_id,))

            game = c.fetchone()

            if not game:
                return {"error": "Game not found"}, 404

            # Получаем список зарегистрированных игроков
            c.execute('''SELECT 
                            p.ID,
                            p.nickname,
                            p.username,
                            p.group_name,
                            r.registration_date,
                            r.slot,
                            r.role
                        FROM registrations r
                        JOIN players p ON r.player_id = p.ID
                        WHERE r.game_id = ?
                        ORDER BY r.registration_date''', (game_id,))

            players = []
            for player in c.fetchall():
                players.append({
                    "player_id": player[0],
                    "nickname": player[1],
                    "username": player[2],
                    "group": player[3],
                    "registered_at": player[4],
                    "slot": player[5],
                    "role": player[6]
                })

            # Формируем полный ответ
            game_info = {
                "game_id": game[0],
                "room": game[1],
                "type": game[2],
                "date": game[3],
                "master_id": game[4],
                "slots_cnt": game[5],
                "master_nickname": game[6] if game[6] else "Unknown",
                "registered_players": players,
                "players_count": len(players),
                "available_slots": game[5] - len(players) if game[5] else None
            }

            return game_info, 200

        except Error as e:
            return {"error": str(e)}, 500
        finally:
            conn.close()

    @staticmethod
    def delete_game(game_id):
        if not game_id or not isinstance(game_id, int):
            return {"error": "Invalid game ID"}, 400

        conn = create_connection(DATABASE)
        if not conn:
            return {"error": "Database connection failed"}, 500

        try:
            c = conn.cursor()

            c.execute("SELECT 1 FROM games WHERE ID = ?", (game_id,))
            if not c.fetchone():
                return {"error": "Game not found"}, 404

            c.execute("DELETE FROM archive WHERE game_ID = ?", (game_id,))

            c.execute("DELETE FROM registrations WHERE game_ID = ?", (game_id,))

            c.execute("DELETE FROM games WHERE ID = ?", (game_id,))

            conn.commit()

            return {"message": f"Game {game_id} deleted successfully"}, 200

        except Error as e:
            conn.rollback()
            return {"error": str(e)}, 500
        finally:
            conn.close()

    @staticmethod
    def get_registrations(setting=None):

        conn = create_connection(DATABASE)
        if not conn:
            return {"error": "Database connection failed"}, 500

        try:
            c = conn.cursor()
            if (setting):
                c.execute(f'''SELECT registration_date, player_id, game_id, slot, role, in_queue FROM registrations WHERE player_id = ?''', (setting,))
            else:
                c.execute(f'''SELECT registration_date, player_id, game_id, slot, role, in_queue FROM registrations''')

            registrations = []
            for row in c.fetchall():
                registrations.append({
                    "game_id": row[2],
                    "player_id": row[1],
                    "registration_date": row[0],
                    "role": row[4],
                    "slot": row[3],
                    "in_queue": row[5]
                })
            return {"registrations": registrations, "count": len(registrations)}, 200

        except Error as e:
            return {"error": str(e)}, 500
        finally:
            conn.close()

    @staticmethod
    def cancel_registration(data):
        required_fields = ['player_id', 'game_id']
        if not all(field in data for field in required_fields):
            return {"error": "Missing required fields"}, 400

        conn = create_connection(DATABASE)
        if not conn:
            return {"error": "Database connection failed"}, 500

        try:
            c = conn.cursor()

            # 1. Получаем данные удаляемой регистрации
            c.execute('''SELECT slot, role, in_queue 
                       FROM registrations 
                       WHERE player_id = ? AND game_id = ?''',
                      (data['player_id'], data['game_id']))
            registration = c.fetchone()

            if not registration:
                return {"error": "Registration not found"}, 404

            slot, role, in_queue = registration

            # 2. Если игрок был не в очереди, ищем замену
            if in_queue == 0:
                # 3. Находим следующего в очереди (самого старого)
                c.execute('''SELECT player_id 
                           FROM registrations 
                           WHERE game_id = ? 
                             AND in_queue = 1 
                           ORDER BY registration_date 
                           LIMIT 1''', (data['game_id'],))
                replacement = c.fetchone()

                if replacement:
                    replacement_id = replacement[0]

                    # 4. Обновляем запись замены
                    c.execute('''UPDATE registrations 
                                SET in_queue = 0,
                                    slot = ?,
                                    role = ?
                                WHERE player_id = ? 
                                  AND game_id = ?''',
                              (slot, role, replacement_id, data['game_id']))

            # 5. Удаляем исходную регистрацию
            c.execute('''DELETE FROM registrations 
                       WHERE player_id = ? AND game_id = ?''',
                      (data['player_id'], data['game_id']))

            conn.commit()

            message = "Registration cancelled successfully"
            if in_queue == 0 and replacement:
                message += f". Player {replacement_id} moved from queue"

            return {"message": message}, 200

        except Error as e:
            conn.rollback()
            return {"error": str(e)}, 500
        finally:
            conn.close()

    @staticmethod
    def register_to_game(data):
        required_fields = ['player_id', 'game_id', 'in_queue']
        if not all(field in data for field in required_fields):
            return {"error": "Missing required fields"}, 400

        conn = create_connection(DATABASE)
        if not conn:
            return {"error": "Database connection failed"}, 500

        try:
            c = conn.cursor()

            # Проверка существования игрока и игры
            c.execute("SELECT 1 FROM players WHERE ID = ?", (data['player_id'],))
            if not c.fetchone():
                return {"error": "Player not found"}, 404

            c.execute("SELECT 1 FROM games WHERE ID = ?", (data['game_id'],))
            if not c.fetchone():
                return {"error": "Game not found"}, 404

            # Проверка дублирования регистрации
            c.execute("SELECT 1 FROM registrations WHERE player_id = ? AND game_id = ?",
                      (data['player_id'], data['game_id']))
            if c.fetchone():
                return {"error": "Player already registered"}, 400

            # Вставка данных
            c.execute('''INSERT INTO registrations 
                        (player_id, game_id, in_queue)
                        VALUES (?, ?, ?)''',
                      (data['player_id'], data['game_id'], data['in_queue']))

            conn.commit()
            return {"message": "Registration successful"}, 201

        except Error as e:
            return {"error": str(e)}, 500
        finally:
            conn.close()

    @staticmethod
    def assign_slots(game_id):
        conn = create_connection(DATABASE)
        if not conn:
            return {"error": "Database connection failed"}, 500

        try:
            c = conn.cursor()

            # Получаем список игроков не в очереди
            c.execute('''SELECT player_id 
                       FROM registrations 
                       WHERE game_id = ? AND in_queue = 0''', (game_id,))
            players = [row[0] for row in c.fetchall()]

            if not players:
                return {"error": "No players to assign slots"}, 400

            # Генерируем случайные уникальные места
            slots = list(range(1, len(players) + 1))
            random.shuffle(slots)

            # Обновляем записи
            for player_id, slot in zip(players, slots):
                c.execute('''UPDATE registrations 
                            SET slot = ? 
                            WHERE game_id = ? AND player_id = ?''',
                          (slot, game_id, player_id))

            conn.commit()
            return {"message": f"Assigned {len(players)} slots",
                    "slots": slots,
                    "players": players}, 200

        except Error as e:
            return {"error": str(e)}, 500
        finally:
            conn.close()

    @staticmethod
    def force_slots(game_id, player_ids):
        """
        Принудительно распределяет места по заданному порядку ID игроков
        :param game_id: ID игры
        :param player_ids: list - массив ID игроков в порядке слотов (0-й элемент = 1-й слот)
        :return: (результат, статус код)
        """
        conn = create_connection(DATABASE)
        if not conn:
            return {"error": "Database connection failed"}, 500

        try:
            c = conn.cursor()

            # 1. Проверяем существование игры
            c.execute("SELECT 1 FROM games WHERE ID = ?", (game_id,))
            if not c.fetchone():
                return {"error": "Game not found"}, 404

            # 2. Получаем текущих игроков (не в очереди)
            c.execute('''SELECT player_id 
                       FROM registrations 
                       WHERE game_id = ? 
                         AND in_queue = 0''', (game_id,))
            db_players = {row[0] for row in c.fetchall()}

            # 3. Проверяем соответствие игроков
            input_players = set(player_ids)

            if len(db_players) != len(player_ids):
                return {"error": "Player count mismatch"}, 400

            if input_players != db_players:
                return {"error": "Player IDs don't match registered players"}, 400

            # 4. Обновляем места
            for slot_idx, player_id in enumerate(player_ids, start=1):
                c.execute('''UPDATE registrations 
                            SET slot = ? 
                            WHERE game_id = ? 
                              AND player_id = ?''',
                          (slot_idx, game_id, player_id))

            conn.commit()
            return {"message": f"Successfully assigned slots to {len(player_ids)} players"}, 200

        except Error as e:
            conn.rollback()
            return {"error": str(e)}, 500
        finally:
            conn.close()

    @staticmethod
    def assign_roles(game_id, roles_config):
        conn = create_connection(DATABASE)
        if not conn:
            return {"error": "Database connection failed"}, 500

        try:
            c = conn.cursor()

            c.execute('''SELECT type FROM games WHERE ID = ?''', (game_id,))
            type = c.fetchone()[0]

            c.execute('''SELECT COUNT(*) 
                       FROM registrations 
                       WHERE game_id = ? AND in_queue = 0''', (game_id,))
            players_count = c.fetchone()[0]
            print(type, players_count)
            roles = roles_config.get(type).get(str(players_count))
            if not roles or len(roles) != players_count:
                return {"error": "Invalid roles configuration"}, 401

            c.execute('''SELECT player_id 
                       FROM registrations 
                       WHERE game_id = ? AND in_queue = 0''', (game_id,))
            players = [row[0] for row in c.fetchall()]
            random.shuffle(players)
            print(players, roles)
            for player_id, role in zip(players, roles):
                c.execute('''UPDATE registrations 
                            SET role = ? 
                            WHERE game_id = ? AND player_id = ?''',
                          (role, game_id, player_id))

            conn.commit()
            return {"message": f"Assigned roles to {len(players)} players",
                    "roles": roles,
                    "players": players}, 200

        except Error as e:
            return {"error": str(e)}, 500
        finally:
            conn.close()

    # В классе APIHandler добавляем метод

    @staticmethod
    def force_roles(game_id, roles):
        """
        Принудительно назначает роли игрокам по слотам
        :param game_id: ID игры
        :param roles: list - массив ролей для слотов (0-й элемент = 1-й слот)
        :return: (результат, статус код)
        """
        conn = create_connection(DATABASE)
        if not conn:
            return {"error": "Database connection failed"}, 500

        try:
            c = conn.cursor()

            c.execute("SELECT 1 FROM games WHERE ID = ?", (game_id,))
            if not c.fetchone():
                return {"error": "Game not found"}, 404

            c.execute('''SELECT slot, player_id 
                       FROM registrations 
                       WHERE game_id = ? 
                         AND in_queue = 0 
                       ORDER BY slot''', (game_id,))

            slots = {row[0]: row[1] for row in c.fetchall()}

            if len(slots) != len(roles):
                return {"error": f"Roles count ({len(roles)}) doesn't match players count ({len(slots)})"}, 400

            for slot_idx, role in enumerate(roles, start=1):
                if slot_idx not in slots:
                    return {"error": f"Slot {slot_idx} not found"}, 400

                c.execute('''UPDATE registrations 
                            SET role = ? 
                            WHERE game_id = ? 
                              AND player_id = ?''',
                          (role, game_id, slots[slot_idx]))

            conn.commit()
            return {"message": f"Successfully assigned roles to {len(roles)} slots"}, 200

        except Error as e:
            conn.rollback()
            return {"error": str(e)}, 500
        finally:
            conn.close()

    @staticmethod
    def finish_game(game_id, civilians_win):
        """
        Завершает игру и переносит данные в архив
        :param game_id: ID завершаемой игры
        :param civilians_win: bool - победа мирных жителей
        :return: (результат, статус код)
        """
        conn = create_connection(DATABASE)
        if not conn:
            return {"error": "Database connection failed"}, 500

        try:
            c = conn.cursor()

            # 1. Проверяем существование игры
            c.execute("SELECT 1 FROM games WHERE ID = ?", (game_id,))
            if not c.fetchone():
                return {"error": "Game not found"}, 404

            # 2. Получаем всех участников (не из очереди)
            c.execute('''SELECT 
                            player_id, role, slot
                        FROM registrations 
                        WHERE game_id = ? 
                          AND in_queue = 0''', (game_id,))
            participants = c.fetchall()

            if not participants:
                return {"error": "No participants found"}, 400

            # 3. Определяем победителей
            peaceful_roles = ["civilian", "sheriff", "doctor"]
            mafia_roles = ["mafia", "don"]

            archive_data = []
            for player_id, role, slot in participants:
                is_winner = 0
                if role:
                    if civilians_win and role in peaceful_roles:
                        is_winner = 1
                    elif not civilians_win and role in mafia_roles:
                        is_winner = 1

                archive_data.append((game_id, player_id, role, slot, is_winner))

            # 4. Переносим в архив
            c.executemany('''INSERT INTO archive 
                            (game_ID, player_ID, role, slot, is_winner)
                            VALUES (?, ?, ?, ?, ?)''', archive_data)

            # 5. Удаляем регистрации
            c.execute('''DELETE FROM registrations 
                       WHERE game_id = ?''', (game_id,))

            c.execute('''UPDATE games 
                                SET is_archived = 1 
                                WHERE ID = ?''', (game_id,))

            conn.commit()
            return {"message": f"Game {game_id} finished successfully",
                    "players_archived": len(archive_data)}, 200

        except Error as e:
            conn.rollback()
            return {"error": str(e)}, 500
        finally:
            conn.close()

    # В класс APIHandler добавляем метод
    @staticmethod
    def get_player_stats(type):
        conn = create_connection(DATABASE)
        if not conn:
            return {"error": "Database connection failed"}, 500

        try:
            c = conn.cursor()
            if (type != "all"):
                # Выполняем сложный SQL-запрос с агрегацией
                c.execute(f'''
                    SELECT 
                        p.ID as player_id,
                        p.nickname,
                        p.group_name,
                        COUNT(a.game_ID) as total_games,
                        SUM(a.is_winner) as total_wins,
                        SUM(CASE WHEN a.role = 'sheriff' THEN 1 ELSE 0 END) as sheriff_games,
                        SUM(CASE WHEN a.role = 'sheriff' THEN a.is_winner ELSE 0 END) as sheriff_wins,
                        SUM(CASE WHEN a.role = 'civilian' THEN 1 ELSE 0 END) as civilian_games,
                        SUM(CASE WHEN a.role = 'civilian' THEN a.is_winner ELSE 0 END) as civilian_wins,
                        SUM(CASE WHEN a.role = 'don' THEN 1 ELSE 0 END) as don_games,
                        SUM(CASE WHEN a.role = 'don' THEN a.is_winner ELSE 0 END) as don_wins,
                        SUM(CASE WHEN a.role = 'mafia' THEN 1 ELSE 0 END) as mafia_games,
                        SUM(CASE WHEN a.role = 'mafia' THEN a.is_winner ELSE 0 END) as mafia_wins,
                        SUM(CASE WHEN a.role = 'doctor' THEN 1 ELSE 0 END) as doctor_games,
                        SUM(CASE WHEN a.role = 'doctor' THEN a.is_winner ELSE 0 END) as doctor_wins
                    FROM archive a
                    JOIN games g ON a.game_ID = g.ID
                    JOIN players p ON a.player_ID = p.ID
                    WHERE g.type = '{type}'
                    AND g.is_archived = 1
                    GROUP BY p.ID
                ''')
            else:
                c.execute(f'''
                                    SELECT 
                                        p.ID as player_id,
                                        p.nickname,
                                        p.group_name,
                                        COUNT(a.game_ID) as total_games,
                                        SUM(a.is_winner) as total_wins,
                                        SUM(CASE WHEN a.role = 'sheriff' THEN 1 ELSE 0 END) as sheriff_games,
                                        SUM(CASE WHEN a.role = 'sheriff' THEN a.is_winner ELSE 0 END) as sheriff_wins,
                                        SUM(CASE WHEN a.role = 'civilian' THEN 1 ELSE 0 END) as civilian_games,
                                        SUM(CASE WHEN a.role = 'civilian' THEN a.is_winner ELSE 0 END) as civilian_wins,
                                        SUM(CASE WHEN a.role = 'don' THEN 1 ELSE 0 END) as don_games,
                                        SUM(CASE WHEN a.role = 'don' THEN a.is_winner ELSE 0 END) as don_wins,
                                        SUM(CASE WHEN a.role = 'mafia' THEN 1 ELSE 0 END) as mafia_games,
                                        SUM(CASE WHEN a.role = 'mafia' THEN a.is_winner ELSE 0 END) as mafia_wins,
                                        SUM(CASE WHEN a.role = 'doctor' THEN 1 ELSE 0 END) as doctor_games,
                                        SUM(CASE WHEN a.role = 'doctor' THEN a.is_winner ELSE 0 END) as doctor_wins
                                    FROM archive a
                                    JOIN games g ON a.game_ID = g.ID
                                    JOIN players p ON a.player_ID = p.ID
                                    WHERE g.is_archived = 1
                                    GROUP BY p.ID
                                ''')
            stats = []
            for row in c.fetchall():
                print('row', row)
                stat = {
                    'ID': row[0],
                    'nickname': row[1],
                    'games': row[3],
                    'wins': row[4],
                    'sheriff': {
                        'games': row[5],
                        'wins': row[6]
                    },
                    'civilian': {
                        'games': row[7],
                        'wins': row[8]
                    },
                    'don': {
                        'games': row[9],
                        'wins': row[10]
                    },
                    'mafia': {
                        'games': row[11],
                        'wins': row[12]
                    },
                    'doctor': {
                        'games': row[13],
                        'wins': row[14]
                    }
                }
                stats.append(stat)

            return {'stats': stats, 'count': len(stats)}, 200

        except Error as e:
            return {"error": str(e)}, 500
        finally:
            conn.close()

def create_connection(db_file):
    try:
        return sqlite3.connect(db_file)
    except Error as e:
        print(e)
        return None


def init_db():
    conn = create_connection(DATABASE)
    if conn is None:
        return False

    try:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS players
                     (ID INTEGER PRIMARY KEY,
                      username TEXT NOT NULL UNIQUE,
                      nickname TEXT NOT NULL UNIQUE,
                      group_name TEXT,
                      is_master BOOLEAN DEFAULT FALSE)''')

        c.execute('''CREATE TABLE IF NOT EXISTS games
                     (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                      room TEXT NOT NULL,
                      type TEXT NOT NULL,
                      date DATETIME DEFAULT CURRENT_TIMESTAMP,
                      master_ID INTEGER,
                      slots_cnt INTEGER,
                      is_archived BOOLEAN DEFAULT 0,
                      FOREIGN KEY (master_ID) REFERENCES players(ID))''')

        c.execute('''CREATE TABLE IF NOT EXISTS archive
                     (game_ID INTEGER NOT NULL,
                      player_ID INTEGER NOT NULL,
                      role TEXT,
                      slot INTEGER DEFAULT -1,
                      is_winner BOOLEAN DEFAULT 0,
                      PRIMARY KEY (game_ID, player_ID),
                      FOREIGN KEY (game_ID) REFERENCES games(ID),
                      FOREIGN KEY (player_ID) REFERENCES players(ID))''')

        c.execute('''CREATE TABLE IF NOT EXISTS registrations
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      player_id INTEGER NOT NULL,
                      game_id INTEGER NOT NULL,
                      registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                      slot INTEGER DEFAULT 0,
                      role TEXT DEFAULT None,
                      in_queue BOOLEAN DEFAULT 0,
                      FOREIGN KEY (player_id) REFERENCES players(ID),
                      FOREIGN KEY (game_id) REFERENCES games(ID),
                      UNIQUE(player_id, game_id))''')

        conn.commit()
        return True
    except Error as e:
        print(e)
        return False
    finally:
        conn.close()