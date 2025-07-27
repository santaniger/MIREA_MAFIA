import random
import requests
import telebot
from telebot import types
from types import SimpleNamespace
from config import BOT_TOKEN, BASE_URL, ROLES_CONFIG, TRANSLATE_CONFIG, EMOJI_CONFIG
from datetime import datetime, timedelta

bot = telebot.TeleBot(BOT_TOKEN)

def format_date(iso_string):
    months = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля",
        5: "мая", 6: "июня", 7: "июля", 8: "августа",
        9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
    }

    # Парсим исходную строку
    dt = datetime.strptime(iso_string, "%Y-%m-%dT%H:%M:%S")

    # Форматируем в нужный вид
    return f"{dt.day} {months[dt.month]} в {dt.strftime('%H:%M')}"

def is_master(id):
    response = requests.get(f"{BASE_URL}/players/{id}")
    return response.json()["is_master"]

@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def call_main_menu(call):
    try:
        main_menu(call.message, 1)
    except telebot.apihelper.ApiTelegramException as e:
        if "message is not modified" in str(e):
            bot.answer_callback_query(callback_query_id=call.id, text="Нет изменений ✅", show_alert=False)
        else:
            bot.answer_callback_query(callback_query_id=call.id, text="Произошла ошибка ⚠️", show_alert=True)

def main_menu(message, is_call=0):
    games_cnt = requests.get(f"{BASE_URL}/game/list").json()["count"]
    regisrations_cnt = requests.get(f"{BASE_URL}/game/registrations", json={"player_id": message.chat.id}).json()["count"]
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="🎲 Игры", callback_data="menu_games"), types.InlineKeyboardButton(text="📊 Статистика", callback_data="stat"))
    keyboard.add(types.InlineKeyboardButton(
        text="🔄 Обновить",
        callback_data="main_menu"
    ))
    if is_call:
        bot.edit_message_text(chat_id=message.chat.id, message_id=message.id, text=f"Доброе утро, город!\nЗапланировано: {games_cnt} игр\nТы зарегистрирован на {regisrations_cnt} игр", reply_markup=keyboard, parse_mode='HTML')
    else:
        bot.send_message(chat_id=message.chat.id, text=f"Доброе утро, город!\nЗапланировано: {games_cnt} игр\nТы зарегистрирован на {regisrations_cnt} игр", reply_markup=keyboard, parse_mode='HTML')

@bot.message_handler(commands=["start"])
def start_command(message):
    print("start")
    response = requests.get(f"{BASE_URL}/players/{message.chat.id}")
    if (response.status_code // 100 == 2):
        print("OK")
        main_menu(message)
    else:
        bot.send_message(message.chat.id, "Добро пожаловать в клуб мафии МИРЭА! Давайте познакомимся, введите свой игровой ник:")
        bot.register_next_step_handler(message, get_name)

def get_name(message):
    bot.send_message(message.chat.id, f"Осталась группа (XXXX-00-00):")
    bot.register_next_step_handler(message, get_group, message.text)

def get_group(message, name):
    loading = bot.send_message(message.chat.id, "Регистрирую...")
    try:
        username = message.from_user.username
    except:
        username = f"random_generaed_{random.randint(1000000, 9999999)}"
    if username == None:
        username = f"random_generaed_{random.randint(1000000, 9999999)}"
    response = requests.post(f"{BASE_URL}/reg", json={
        "ID": message.chat.id,
        "nickname": name,
        "username": username,
        "group_name": message.text})
    if (response.status_code // 100 == 2):
        bot.edit_message_text(chat_id=message.chat.id, message_id=loading.id, text="Критический успех")
        main_menu(message)
    else:
        bot.edit_message_text(chat_id=message.chat.id, message_id=loading.id, text=f"Ошибка API: {response.content}")

@bot.callback_query_handler(func=lambda call: call.data == "menu_games")
def cancel_handler(call):
    response = requests.get(f"{BASE_URL}/game/list")
    msg_str = "ИГРЫ:\n"
    regisrations = [i["game_id"] for i in requests.get(f"{BASE_URL}/game/registrations", json={"player_id": call.message.chat.id}).json()["registrations"]]
    keyboard = types.InlineKeyboardMarkup()
    for i in response.json()["games"]:
        msg_str += f"\nИГРА №{i['game_id']}------------------\nПройдёт {format_date(i['date'].replace(' ', 'T'))}\nТип игры: {'Классическая' if i['type'] == 'classic'  else 'Городская'}\nВедущий: Г-н(жа) {i['master_nickname']}\nАудитория: {i['room']}\nМакс кол-во игроков: {i['slots_cnt']}\nЗарегистрировано: {i['registrations']}\n"
        if (i["game_id"] in regisrations):
            keyboard.add(types.InlineKeyboardButton(text=f"ИГРА №{i['game_id']} (зарегистрирован)", callback_data=f"gameInfo_{i['game_id']}"))
        else:
            keyboard.add(types.InlineKeyboardButton(text=f"ИГРА №{i['game_id']}", callback_data=f"gameInfo_{i['game_id']}"))
    keyboard.add(types.InlineKeyboardButton(
        text="🔄 Обновить",
        callback_data=call.data
    ))
    if (is_master(call.message.chat.id)):
        keyboard.add(types.InlineKeyboardButton(text=f"➕ СОЗДАТЬ", callback_data=f"new_game"))
    keyboard.add(types.InlineKeyboardButton(text=f"🔙", callback_data=f"main_menu"))
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=msg_str, reply_markup=keyboard)
    except:
        bot.answer_callback_query(call.id, "Нет изменений ✅")

@bot.callback_query_handler(func=lambda call: call.data.startswith("gameInfo_"))
def game_info(call, edit=0):
    game_id = int(call.data.split('_')[1])
    regisrations = [i["game_id"] for i in requests.get(f"{BASE_URL}/game/registrations", json={"player_id": call.message.chat.id}).json()["registrations"]]
    i = requests.get(f"{BASE_URL}/game/{game_id}").json()
    msg_text = f"\nИГРА №{i['game_id']}------------------\nПройдёт {format_date(i['date'].replace(' ', 'T'))}\nТип игры: {'Классическая' if i['type'] == 'classic'  else 'Городская'}\nВедущий: Г-н(жа) {i['master_nickname']}\nАудитория: {i['room']}\nМакс кол-во игроков: {i['slots_cnt']}\nЗарегистрировано: {i['players_count']}\n{'Зарегистрированные игроки:' if i['players_count'] else 'Будь первым!'}\n"
    cnt = 0
    for player in sorted(
        i["registered_players"],
        key=lambda x: (1, x['registered_at']) if x['slot'] == 0 else (0, x['slot'])
    ):
        cnt += 1
        slot = player['slot']
        role = TRANSLATE_CONFIG[player['role']] if is_master(call.message.chat.id) else "???"
        msg_text += f"{'' if slot == 0 else f'Слот {slot} | '}Г-н {player['nickname']} | {'В очереди' if cnt > i['slots_cnt'] else '✅' if role == 'None' else f'{role}'}\n"
        if (cnt == i['slots_cnt']):
            msg_text += "---------------\n"
    keyboard = types.InlineKeyboardMarkup()
    if (game_id in regisrations):
        keyboard.add(types.InlineKeyboardButton(text=f"❌ Не смогу :(", callback_data=f"unregOfGame_{game_id}"))
    else:
        keyboard.add(types.InlineKeyboardButton(text=f"✅ Зарегистрироваться", callback_data=f"regToGame_{game_id}"))
    if (is_master(call.message.chat.id)):
        #keyboard.add(types.InlineKeyboardButton(text=f"время", callback_data=f"changeGameTime_{game_id}"), types.InlineKeyboardButton(text=f"аудитория", callback_data=f"changeGameRoom_{game_id}"))
        keyboard.add(types.InlineKeyboardButton(text=f"🔄 Роли", callback_data=f"rolesGame_{game_id}"),
                     types.InlineKeyboardButton(text=f"🔄 Рассадка", callback_data=f"slotsGame_auto_{game_id}"))
        keyboard.add(types.InlineKeyboardButton(text=f"🎴 Отправить", callback_data=f"sendRoles_{game_id}"),
                     types.InlineKeyboardButton(text=f"🪑 Отправить", callback_data=f"sendSlots_{game_id}"))
        keyboard.add(types.InlineKeyboardButton(text=f"🏁 Завершить", callback_data=f"finishGame_{game_id}"))
        keyboard.add(types.InlineKeyboardButton(text=f"🚫 ОТМЕНИТЬ", callback_data=f"cancelGame_{game_id}"))
    keyboard.add(types.InlineKeyboardButton(
        text="🔄 Обновить",
        callback_data=call.data
    ))
    keyboard.add(types.InlineKeyboardButton(text=f"🔙", callback_data=f"menu_games"))
    if edit == 0:
        try:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=msg_text, reply_markup=keyboard)
        except:
            bot.answer_callback_query(call.id, "Нет изменений ✅")
    else:
        bot.send_message(chat_id=call.message.chat.id, text=msg_text, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("slotsGame_auto_"))
def slotsGameAuto(call):
    game_id = int(call.data.split('_')[2])
    response = requests.put(f'{BASE_URL}/games/{game_id}/slots')
    print(response.json())
    if (response.status_code // 100 == 2):
        game_info(SimpleNamespace(
                    message=SimpleNamespace(
                        chat=SimpleNamespace(id=call.message.chat.id),
                        id=call.message.id
                    ),
                    data=f"hello_{game_id}"
                ), 0
            )
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=f"Ошибка API: {response.content}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("sendSlots_"))
def sendSlots(call):
    game_id = int(call.data.split('_')[1])
    err_str = ""
    response = requests.get(f'{BASE_URL}/game/{game_id}')
    for player in response.json()['registered_players']:
        if int(player["in_queue"]) == 0 and int(player["slot"]) == 0:
            bot.send_message(call.message.chat.id, "Слоты назначены не для всех пользователей!")
            return 0
    for player in response.json()['registered_players']:
        if int(player["in_queue"]) == 0:
            try:
                bot.send_message(player["player_id"], f"ИГРА №{game_id}\nВаше игровое место: {player['slot']}")
            except Exception as e:
                print(e)
                err_str += f"\nОшибка отправки слота пользователю {player['player_id']}: {player['slot']}"
    if err_str:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                              text=f"Ошибка в отправке:{err_str}")
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                              text=f"Слоты успешно отправлены!")
    game_info(SimpleNamespace(
        message=SimpleNamespace(
            chat=SimpleNamespace(id=call.message.chat.id),
            id=call.message.id
        ),
        data=f"hello_{game_id}"
    ), 1
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("rolesGame_auto_"))
def rolesGameAuto(call):
    game_id = int(call.data.split('_')[2])
    response = requests.put(f'{BASE_URL}/games/{game_id}/roles')
    if (response.status_code // 100 == 2):
        game_info(SimpleNamespace(
            message=SimpleNamespace(
                chat=SimpleNamespace(id=call.message.chat.id)
            ),
            data=f"hello_{game_id}"
        ), 1
        )
    elif (response.status_code == 401):
        bot.edit_message_text(chat_id=call.message.chat.id, text=f"Не корректное количество игроков")
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=f"Ошибка API: {response.content}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("sendRoles_"))
def sendRoles(call):
    game_id = int(call.data.split('_')[1])
    err_str = ""
    response = requests.get(f'{BASE_URL}/game/{game_id}')
    game_type = response.json()["type"]
    for player in response.json()['registered_players']:
        if int(player["in_queue"]) == 0 and player["role"] == "None":
            bot.send_message(call.message.chat.id, "Роли назначены не для всех пользователей!")
            return 0
    for player in response.json()['registered_players']:
        if int(player["in_queue"]) == 0:
            try:
                keyboard = telebot.types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton(text="🔂 Перевернуть", callback_data=f"cardShirt_{game_id}_{player['role']}_0_{game_type}"))
                bot.send_photo(player['player_id'], open(f"../resources/{game_type}/card_shirt.jpg", "rb"), caption=f"ИГРА №{game_id}\nВаша карта: ???", reply_markup=keyboard)
            except Exception as e:
                print(e)
                err_str += f"\nОшибка отправки пользователю {player['player_id']}: {TRANSLATE_CONFIG[player['role']]}"
    if err_str:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                              text=f"Ошибка в отправке:{err_str}")
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                              text=f"Роли успешно отправлены!")
    game_info(SimpleNamespace(
        message=SimpleNamespace(
            chat=SimpleNamespace(id=call.message.chat.id),
            id=call.message.id
        ),
        data=f"hello_{game_id}"
    ), 1
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("cardShirt_"))
def cardShirt(call):
    game_id = int(call.data.split('_')[1])
    role = call.data.split('_')[2]
    is_open = int(call.data.split('_')[3])
    game_type = call.data.split('_')[4]
    try:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="🔂 Перевернуть", callback_data=f"cardShirt_{game_id}_{role}_0_{game_type}" if is_open else f"cardShirt_{game_id}_{role}_1_{game_type}"))
        media = types.InputMediaPhoto(
            media=open(f"../resources/{game_type}/card_shirt.jpg" if is_open else f"../resources/{game_type}/{role}.jpg", 'rb'),
            caption=f"ИГРА №{game_id}\nВаша карта: {'???' if is_open else TRANSLATE_CONFIG[role]}"
        )

        bot.edit_message_media(
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            media=media,
            reply_markup=keyboard
        )
    except FileNotFoundError:
        bot.answer_callback_query(
            call.id,
            f"Изображение для роли {role} не найдено",
            show_alert=True
        )
    except Exception as e:
        print(f"Ошибка при обновлении карточки: {e}")
        bot.answer_callback_query(
            call.id,
            "Произошла ошибка при открытии карты",
            show_alert=True
        )

user_sessions = {}

@bot.callback_query_handler(func=lambda call: call.data.startswith("rolesGame_force_"))
def start_role_distribution(call):
    chat_id = call.message.chat.id
    game_id = int(call.data.split('_')[2])
    print(game_id)
    response = requests.get(f"{BASE_URL}/game/{game_id}")
    if (response.status_code // 100 != 2):
        return bot.send_message(chat_id, response.json()["error"])
    game_type = response.json()["type"]
    slots_cnt = min(response.json()["players_count"], response.json()["slots_cnt"])
    print(slots_cnt)
    config_key = str(slots_cnt)
    if config_key not in ROLES_CONFIG[game_type]:
        return bot.send_message(chat_id, "Недопустимое количество игроков")

    user_sessions[chat_id] = {
        "game_id": game_id,
        "slots_cnt": int(slots_cnt),
        "current_slot": 1,
        "roles": [],
        "remaining_roles": ROLES_CONFIG[game_type][config_key].copy()
    }

    ask_role(chat_id, call.message.id)


def ask_role(chat_id, message_id):
    session = user_sessions.get(chat_id)
    if not session:
        return
    response = requests.get(f"{BASE_URL}/game/{session['game_id']}")
    print(response.json())
    players = sorted(filter(lambda x: x['in_queue'] == 0, response.json()["registered_players"]), key=lambda x: x['slot'])
    keyboard = types.InlineKeyboardMarkup()
    for role in set(session['remaining_roles']):
        count = session['remaining_roles'].count(role)
        keyboard.add(types.InlineKeyboardButton(
            text=f"{TRANSLATE_CONFIG[role]} ({count})",
            callback_data=f"role_select_{role}"
        ))

    bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=f"Выберите роль для слота {session['current_slot']} (Г-н(жа) {players[int(session['current_slot']) - 1]['nickname']}):",
        reply_markup=keyboard
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("role_select_"))
def handle_role_selection(call):
    chat_id = call.message.chat.id
    session = user_sessions.get(chat_id)
    if not session:
        return

    selected_role = call.data.split('_')[2]

    try:
        session['remaining_roles'].remove(selected_role)
    except ValueError:
        return bot.answer_callback_query(call.id, "Роль уже выбрана")

    session['roles'].append(selected_role)
    session['current_slot'] += 1

    if session['current_slot'] > session['slots_cnt']:
        # Отправка данных на сервер
        response = requests.put(
            f"{BASE_URL}/games/{session['game_id']}/force_roles",
            json={"roles": session['roles']}
        )
        print(session['roles'])
        print(response.json())
        if response.status_code // 100 == 2:
            bot.send_message(chat_id, "Роли успешно распределены!")
            game_info(SimpleNamespace(
                message=SimpleNamespace(
                    chat=SimpleNamespace(id=call.message.chat.id)
                ),
                data=f"hello_{session['game_id']}"
            ), 1
            )
        else:
            bot.send_message(chat_id, "Ошибка распределения ролей")
        del user_sessions[chat_id]
    else:
        ask_role(chat_id, call.message.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("rolesGame_"))
def rolesGame(call):
    game_id = int(call.data.split('_')[1])
    print(game_id)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text=f"🦾 Автоматически", callback_data=f"rolesGame_auto_{game_id}"))
    keyboard.add(types.InlineKeyboardButton(text=f"🎛️ Ручной ввод", callback_data=f"rolesGame_force_{game_id}"))
    keyboard.add(types.InlineKeyboardButton(text=f"🔙", callback_data=f"gameInfo_{game_id}"))
    bot.send_message(chat_id=call.message.chat.id, text=f"Автоматическая раздача - всем игрокам придёт уведомление с их ролью\n"
                                                                                         f"Ручной ввод - предпочтительный способ\n---\nСНАЧАЛА НЕОБХОДИМО ВЫПОЛНИТЬ РАССАДКУ!", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("slotsGame_"))
def rolesGame(call):
    game_id = int(call.data.split('_')[1])
    print(game_id)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text=f"🦾 Автоматически", callback_data=f"slotsGame_auto_{game_id}"))
    keyboard.add(types.InlineKeyboardButton(text=f"🎛️ Ручной ввод", callback_data=f"slotsGame_force_{game_id}"))
    keyboard.add(types.InlineKeyboardButton(text=f"🔙", callback_data=f"gameInfo_{game_id}"))
    bot.send_message(chat_id=call.message.chat.id, text=f"Автоматическая рассадка - всем игрокам придёт уведомление с их слотом\n"
                                                                                         f"Ручной ввод - поочерёдный выбор игрока (1, 2 ... n)", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("finishGame_"))
def finishGame(call):
    game_id = int(call.data.split('_')[1])
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text=f"🔴 Победа Мирных", callback_data=f"Win_1_{game_id}"))
    keyboard.add(types.InlineKeyboardButton(text=f"⚫ Победа Мафии", callback_data=f"Win_0_{game_id}"))
    keyboard.add(types.InlineKeyboardButton(text=f"🔙", callback_data=f"gameInfo_{game_id}"))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=f"Укажите победившую команду", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("Win_"))
def finishGame_Win(call):
    game = call.data.split('_')
    game_id = int(game[2])
    winner = int(game[1])

    response = requests.get(f"{BASE_URL}/game/{game_id}")
    game_data = response.json()

    game_type = game_data['type']
    master = game_data['master_nickname']
    players = sorted(
        filter(lambda x: x['in_queue'] == 0, game_data["registered_players"]),
        key=lambda x: x['slot']
    )

    # Роли по игрокам
    mafia_team = []
    city_team = []

    mafia_roles = {"mafia", "don", "maniac"}

    for player in players:
        slot = player['slot']
        role = player['role']
        nickname = player['nickname']
        line = f"Слот {slot} | Г-н {nickname} | {EMOJI_CONFIG[role]} {TRANSLATE_CONFIG[role]}"
        if role in mafia_roles:
            mafia_team.append(line)
        else:
            city_team.append(line)

    msg_text = f"\n{'Классическая' if game_type == 'classic' else 'Городская'} игра №{game_id} завершена!\n" \
               f"Ведущий: Г-н(жа) {master}\n" \
               f"ПОБЕДА {'МИРНЫХ 🔴' if winner == 1 else 'МАФИИ ⚫'}\n\n"

    msg_text += "КОМАНДА МАФИИ:\n" + "\n".join(mafia_team) if winner == 0 else "КОМАНДА МИРНЫХ:\n" + "\n".join(city_team)
    msg_text += "\n\nКОМАНДА МИРНОГО ГОРОДА:\n" + "\n".join(city_team) if winner == 0 else "\n\nКОМАНДА МАФИИ:\n" + "\n".join(mafia_team)
    err_str = ""
    for player in filter(lambda x: x['in_queue'] == 0, response.json()["registered_players"]):
        try:
            msg = bot.send_message(player["player_id"], msg_text)
            main_menu(msg, 0)
        except Exception as e:
            print(e)
            err_str += f"\nОшибка отправки результата пользователю {player['player_id']}"
    if err_str:
        bot.send_message(chat_id=call.message.chat.id, text=f"Ошибка в отправке:{err_str}")
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                              text=f"Результаты успешно отправлены!")
    response = requests.post(f"{BASE_URL}/games/{int(game[2])}/finish", json={"civilians_win": int(game[1])})
    if (response.status_code // 100 == 2):
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=f"Игра №{int(game[2])} успешно завершена.\nПобеда {'мирных' if bool(game[1]) else 'мафии'}!")
        main_menu(call.message)
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=f"Ошибка API: {response.content}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("cancelGame_"))
def cancelGame(call):
    game_id = int(call.data.split('_')[1])
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text=f"📛 ПОДТВЕРДИТЬ 📛", callback_data=f"forceCancelGame_{game_id}"))
    keyboard.add(types.InlineKeyboardButton(text=f"🔙", callback_data=f"gameInfo_{game_id}"))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=f"Вы уверены, что хотите отменить проведение игры №{game_id}", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("forceCancelGame_"))
def forceCancelGame(call):
    game_id = int(call.data.split('_')[1])
    response = requests.delete(f"{BASE_URL}/game/{game_id}")
    if (response.status_code // 100 == 2):
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=f"Игра №{game_id} успешно отменена")
        main_menu(call.message)
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=f"Ошибка API: {response.content}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("unregOfGame_"))
def regToGame(call):
    game_id = int(call.data.split('_')[1])
    print(game_id)
    response = requests.delete(f"{BASE_URL}/game/unreg", json={
        "player_id": call.message.chat.id,
        "game_id": game_id})
    bot.register_callback_query_handler(call, game_info)
    game_info(call, 0)

@bot.callback_query_handler(func=lambda call: call.data.startswith("regToGame_"))
def regToGame(call):
    game_id = int(call.data.split('_')[1])
    print(game_id)
    response = requests.post(f"{BASE_URL}/game/reg", json={
        "player_id": call.message.chat.id,
        "game_id": game_id})
    bot.register_callback_query_handler(call, game_info)
    game_info(call, 0)

@bot.callback_query_handler(func=lambda call: call.data == "new_game")
def new_game(call):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text=f"🤵 ‍Классические", callback_data=f"new_game_type_classic"))
    keyboard.add(types.InlineKeyboardButton(text=f"🥷 Городские", callback_data=f"new_game_type_extended"))
    keyboard.add(types.InlineKeyboardButton(text=f"🔙", callback_data=f"menu_games"))
    bot.send_message(call.message.chat.id, f"По каким правилам играем?", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("new_game_type_"))
def new_game_type(call):
    game_type = call.data.split('_')[3]
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(text="10", callback_data=f"new_game_cnt_{game_type}_10"),
        types.InlineKeyboardButton(text="без лимита", callback_data=f"new_game_cnt_{game_type}_100")
    )
    keyboard.add(types.InlineKeyboardButton(text="Ввести", callback_data=f"new_game_forceCNT_{game_type}"))
    bot.send_message(call.message.chat.id, "Выберите или введите ограничение по игрокам:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith("new_game_cnt_"))
def handle_predefined_slots(call):
    _, _, _, game_type, slots_cnt = call.data.split('_')
    bot.send_message(call.message.chat.id, "🚪 Введите аудиторию:")
    bot.register_next_step_handler(call.message, process_audience, game_type, slots_cnt)


@bot.callback_query_handler(func=lambda call: call.data.startswith("new_game_forceCNT_"))
def handle_custom_slots_input(call):
    game_type = call.data.split('_')[3]
    bot.send_message(call.message.chat.id, "👥 Введите количество игроков:")
    bot.register_next_step_handler(call.message, process_custom_slots_cnt, game_type)


def process_custom_slots_cnt(message, game_type):
    try:
        slots_cnt = int(message.text)
        bot.send_message(message.chat.id, "🚪 Введите аудиторию:")
        bot.register_next_step_handler(message, process_audience, game_type, slots_cnt)
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите целое число.")
        bot.register_next_step_handler(message, process_custom_slots_cnt, game_type)


def process_audience(message, game_type, slots_cnt):
    chat_id = message.chat.id
    room = message.text
    user_sessions[chat_id] = {
        'game_type': game_type,
        'slots_cnt': slots_cnt,
        'room': room
    }
    show_date_selection(message, chat_id, 0, 0)


def show_date_selection(message, chat_id, offset=0, edit=1):
    start_date = datetime.now() + timedelta(days=offset)
    dates = [start_date + timedelta(days=i) for i in range(7)]

    keyboard = types.InlineKeyboardMarkup(row_width=3)

    # Кнопки навигации
    nav_row = []
    if offset > 0:
        nav_row.append(types.InlineKeyboardButton(
            text="🔙",
            callback_data=f"date_nav_{offset - 7}"
        ))
    if offset < 7:
        nav_row.append(types.InlineKeyboardButton(
            text="🔜",
            callback_data=f"date_nav_{offset + 7}"
        ))
    if nav_row:
        keyboard.add(*nav_row)

    buttons = [
        types.InlineKeyboardButton(
            text=f"{date.strftime('%d.%m')} ({date.strftime('%a')})",
            callback_data=f"select_date_{date.strftime('%Y-%m-%d')}"
        )
        for date in dates
    ]

    keyboard.add(*buttons[:3])
    keyboard.add(*buttons[3:6])
    keyboard.add(buttons[6])

    if edit:
        bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=message.message_id,
            reply_markup=keyboard
        )
    else:
        bot.send_message(
            chat_id,
            "📅 Выберите дату игры:",
            reply_markup=keyboard
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("date_nav_"))
def handle_date_nav(call):
    offset = int(call.data.split('_')[2])
    show_date_selection(call.message, call.message.chat.id, offset)

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_date_"))
def handle_select_date(call):
    chat_id = call.message.chat.id
    date_str = call.data.split('_')[2]
    user_sessions[chat_id]['date'] = datetime.strptime(date_str, "%Y-%m-%d")
    show_time_selection(call.message.chat.id)


def show_time_selection(chat_id):
    times = ["9:00", "10:30", "12:40", "14:20", "16:20", "18:00"]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for time in times:
        keyboard.add(types.InlineKeyboardButton(text=time, callback_data=f"select_time_{time}"))
    bot.send_message(chat_id, "🕒 Выберите время игры:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith("select_time_"))
def handle_select_time(call):
    chat_id = call.message.chat.id
    time_str = call.data.split('_')[2]

    try:
        game_data = user_sessions[chat_id]
        date_obj = game_data['date']
        time_obj = datetime.strptime(time_str, "%H:%M").time()
        full_datetime = datetime.combine(date_obj.date(), time_obj)

        response = requests.post(
            f"{BASE_URL}/game/create",
            json={
                "type": game_data['game_type'],
                "slots_cnt": game_data['slots_cnt'],
                "room": game_data['room'],
                "masterID": chat_id,
                "date": full_datetime.isoformat()
            }
        )
        print(response.content)
        bot.send_message(chat_id, f"Игра №{response.json()['game_id']} создана успешно!")
        del user_sessions[chat_id]
        main_menu(call.message)

    except Exception as e:
        bot.send_message(chat_id, f"Ошибка: {str(e)}")
        del user_sessions[chat_id]

@bot.callback_query_handler(func=lambda call: call.data == "stat")
def stat(call):
    player = list(filter(lambda x: int(x['ID']) == call.message.chat.id, requests.get(f'{BASE_URL}/stats/all/players').json()['stats']))
    keyboard = types.InlineKeyboardMarkup()
    if player:
        keyboard.add(types.InlineKeyboardButton(text=f"🗄️ Мои игры", callback_data=f"stat_myGames"))
        keyboard.add(types.InlineKeyboardButton(text=f"👤 Все типы общ", callback_data=f"stat_all"))
        keyboard.add(types.InlineKeyboardButton(text=f"🤵‍♂️ Классика общ", callback_data=f"stat_classic"),
                     types.InlineKeyboardButton(text=f"🥷 Городская общ", callback_data=f"stat_extended"))
        keyboard.add(types.InlineKeyboardButton(text=f"🔙", callback_data=f"main_menu"))
        player = player[0]
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=f"Игровой ник: {player['nickname']}\n"
                                                                                             f"🎮 Всего игр: {player['games']}\n🏆 Побед: {player['wins']}\n➗ Винрейт: {(player['wins'] / player['games'] * 100) if player['games'] > 0 else 0:.1f}%\n"
                                                                                             f"\n⚫ МАФИЯ — {player['don']['wins'] + player['mafia']['wins'] + player['maniac']['wins']}/{player['don']['games'] + player['mafia']['games'] + player['maniac']['games']} = "
                                                                                             f"{((player['don']['wins'] + player['mafia']['wins'] + player['maniac']['wins']) / (player['don']['games'] + player['mafia']['games'] + player['maniac']['games']) * 100) if (player['don']['games'] + player['mafia']['games'] + player['maniac']['games']) > 0 else 0:.1f}%\n"
                                                                                             f"┠ {EMOJI_CONFIG['don']} {TRANSLATE_CONFIG['don']}: {player['don']['games']}/{player['don']['wins']} = {(player['don']['wins'] / player['don']['games'] * 100) if player['don']['games'] > 0 else 0:.1f}%\n"
                                                                                             f"┠ {EMOJI_CONFIG['mafia']} {TRANSLATE_CONFIG['mafia']}: {player['mafia']['games']}/{player['mafia']['wins']} = {(player['mafia']['wins'] / player['mafia']['games'] * 100) if player['mafia']['games'] > 0 else 0:.1f}%\n"
                                                                                             f"┖ {EMOJI_CONFIG['maniac']} {TRANSLATE_CONFIG['maniac']}: {player['maniac']['games']}/{player['maniac']['wins']} = {(player['maniac']['wins'] / player['maniac']['games'] * 100) if player['maniac']['games'] > 0 else 0:.1f}%\n"
                                                                                             f"\n🔴 МИРНЫЕ — {player['sheriff']['wins'] + player['civilian']['wins'] + player['doctor']['wins'] + player['prostitute']['wins']}/{player['sheriff']['games'] + player['civilian']['games'] + player['doctor']['games'] + player['prostitute']['games']}"
                                                                                             f" {((player['sheriff']['wins'] + player['civilian']['wins'] + player['doctor']['wins'] + player['prostitute']['wins']) / (player['sheriff']['games'] + player['civilian']['games'] + player['doctor']['games'] + player['prostitute']['games']) * 100) if player['sheriff']['games'] + player['civilian']['games'] + player['doctor']['games'] + player['prostitute']['games'] > 0 else 0:.1f}%\n"
                                                                                             f"┠ {EMOJI_CONFIG['sheriff']} {TRANSLATE_CONFIG['sheriff']}: {player['sheriff']['wins']}/{player['sheriff']['games']} = {(player['sheriff']['wins'] / player['sheriff']['games'] * 100) if player['sheriff']['games'] > 0 else 0:.1f}%\n"
                                                                                             f"┠ {EMOJI_CONFIG['civilian']} {TRANSLATE_CONFIG['civilian']}: {player['civilian']['wins']}/{player['civilian']['games']} = {(player['civilian']['wins'] / player['civilian']['games'] * 100) if player['civilian']['games'] > 0 else 0:.1f}%\n"
                                                                                             f"┠ {EMOJI_CONFIG['doctor']} {TRANSLATE_CONFIG['doctor']}: {player['doctor']['wins']}/{player['doctor']['games']} = {(player['doctor']['wins'] / player['doctor']['games'] * 100) if player['doctor']['games'] > 0 else 0:.1f}%\n"
                                                                                             f"┖ {EMOJI_CONFIG['prostitute']} {TRANSLATE_CONFIG['prostitute']}: {player['prostitute']['wins']}/{player['prostitute']['games']} = {(player['prostitute']['wins'] / player['prostitute']['games'] * 100) if player['prostitute']['games'] > 0 else 0:.1f}%\n\n👥 Общая статистика:", reply_markup=keyboard)
    else:
        keyboard.add(types.InlineKeyboardButton(text=f"👤 Все типы", callback_data=f"stat_all"))
        keyboard.add(types.InlineKeyboardButton(text=f"🤵‍♂️ Классика", callback_data=f"stat_classic"), types.InlineKeyboardButton(text=f"🥷 Городская", callback_data=f"stat_extended"))
        keyboard.add(types.InlineKeyboardButton(text=f"🔙", callback_data=f"main_menu"))
        player = requests.get(f'{BASE_URL}/players/{call.message.chat.id}').json()
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                              text=f"Игровой ник: {player['nickname']}\n"
                                   f"🥇 Завершите свою первую игру для отображения личной статистики\n\n👥 Другая статистика:",
                              reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "stat_myGames")
def stat_myGames(call):
    try:
        response = requests.get(f"{BASE_URL}/stats/player/{call.message.chat.id}/games")
        message_text = "🗄️ Архив игр:\n"
        keyboard = types.InlineKeyboardMarkup()
        for game in response.json()['games']:
            message_text += f"\n— {format_date(game['date'].replace(' ', 'T'))}\n{'Классическая' if game['type'] == 'classic' else 'Городская'} игра №{game['game_ID']}\nРоль: {EMOJI_CONFIG[game['role']]} {TRANSLATE_CONFIG[game['role']]} ({game['slot']} слот)"
            message_text += "\n🏆 ПОБЕДА 🏆\n" if game['is_winner'] else "\n💀 ПОРАЖЕНИЕ 💀\n"
            keyboard.add(types.InlineKeyboardButton(text=f"ИГРА №{game['game_ID']}", callback_data=f"archivedGameInfo_{game['game_ID']}"))
        keyboard.add(types.InlineKeyboardButton(text=f"🔙", callback_data=f"stat"))
        bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=message_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
    except requests.exceptions.RequestException as e:
        error_text = f"🚫 Ошибка получения данных: {str(e)}"
        bot.answer_callback_query(call.id, error_text, show_alert=True)
    except Exception as e:
        error_text = "⚠️ Произошла непредвиденная ошибка"
        print(e)
        bot.answer_callback_query(call.id, error_text, show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("archivedGameInfo_"))
def archivedGame_info(call, edit=0):
    game_id = int(call.data.split('_')[1])
    i = requests.get(f"{BASE_URL}/game/{game_id}").json()
    archived = requests.get(f"{BASE_URL}/registrations/archive/{game_id}").json()
    msg_text = f"\nИГРА №{i['game_id']}------------------\nПрошла {format_date(i['date'].replace(' ', 'T'))}\nТип игры: {'Классическая' if i['type'] == 'classic'  else 'Городская'}\nВедущий: Г-н(жа) {i['master_nickname']}\nАудитория: {i['room']}\nКол-во игроков: {len(archived['players'])}\n"
    players = sorted(archived["players"], key=lambda x: x['slot'])

    mafia_team = []
    city_team = []

    mafia_roles = {"mafia", "don", "maniac"}
    civilian_win = 0
    for player in players:
        if player['role'] == "civilian" and player['is_winner']:
            civilian_win = 1
        slot = player['slot']
        role = player['role']
        nickname = player['nickname']
        if __name__ == '__main__':
            line = f"<b>Слот {slot} | Г-н {nickname} | {EMOJI_CONFIG[role]} {TRANSLATE_CONFIG[role]}</b>" if player['player_ID'] == call.message.chat.id else f"Слот {slot} | Г-н {nickname} | {EMOJI_CONFIG[role]} {TRANSLATE_CONFIG[role]}"
        if role in mafia_roles:
            mafia_team.append(line)
        else:
            city_team.append(line)
    msg_text += f"\nПОБЕДА {'МИРНЫХ 🔴' if civilian_win else 'МАФИИ ⚫'}\n\n"

    msg_text += "КОМАНДА МАФИИ:\n" + "\n".join(mafia_team) if civilian_win == 0 else "КОМАНДА МИРНЫХ:\n" + "\n".join(
        city_team)
    msg_text += "\n\nКОМАНДА МИРНОГО ГОРОДА:\n" + "\n".join(
        city_team) if civilian_win == 0 else "\n\nКОМАНДА МАФИИ:\n" + "\n".join(mafia_team)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text=f"🔙", callback_data=f"stat_myGames"))
    if edit == 0:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=msg_text, reply_markup=keyboard, parse_mode="html")
    else:
        bot.send_message(chat_id=call.message.chat.id, text=msg_text, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("stat_"))
def stat_for(call):
    try:
        type = call.data.split('_')[1]
        response = requests.get(f'{BASE_URL}/stats/{type}/players')
        response.raise_for_status()
        data = response.json()

        sorted_stats = sorted(data['stats'],
                              key=lambda x: (-x['games'],
                                             -x['wins'] / x['games'] if x['games'] > 0 else 0))

        message_text = f"📊 Статистика игроков ({'Классика' if type == 'classic' else 'Городская' if type == 'extended' else 'Все игры'}) побед из ообщего числа игр | винрейт\n\n"

        for idx, player in enumerate(sorted_stats, 1):
            total_winrate = (player['wins'] / player['games'] * 100) if player['games'] > 0 else 0

            roles_text = "\n".join([
                f"👤 Мирный: {player['civilian']['wins']} из {player['civilian']['games']} | {(player['civilian']['wins'] / player['civilian']['games'] * 100) if player['civilian']['games'] > 0 else 0:.1f}%",
                f"🕵️ Шериф: {player['sheriff']['wins']} из {player['sheriff']['games']} | {(player['sheriff']['wins'] / player['sheriff']['games'] * 100) if player['sheriff']['games'] > 0 else 0:.1f}%",
                f"🔫 Мафия: {player['mafia']['wins']} из {player['mafia']['games']} | {(player['mafia']['wins'] / player['mafia']['games'] * 100) if player['mafia']['games'] > 0 else 0:.1f}%",
                f"👑 Дон: {player['don']['wins']} из {player['don']['games']} | {(player['don']['wins'] / player['don']['games'] * 100) if player['don']['games'] > 0 else 0:.1f}%"
            ])
            if type != 'classic':
                roles_text += f"\n💉 Доктор: {player['doctor']['wins']} из {player['doctor']['games']} | {(player['doctor']['wins'] / player['doctor']['games'] * 100) if player['doctor']['games'] > 0 else 0:.1f}%"

            message_text += (
                f"👤 Г-н (Г-жа) {player['nickname']}\n"
                f"🎮 Всего игр: {player['games']}\n"
                f"📈 Винрейт: {total_winrate:.1f}%\n"
                f"{roles_text}\n"
                f"────────────────────\n"
            )

        keyboard = types.InlineKeyboardMarkup()
        refresh_btn = types.InlineKeyboardButton(
            text="🔄 Обновить статистику",
            callback_data=call.data
        )
        keyboard.add(refresh_btn)
        keyboard.add(types.InlineKeyboardButton(text=f"🔙", callback_data=f"stat"))
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=message_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        except:
            bot.answer_callback_query(call.id, "Нет изменений ✅")

    except requests.exceptions.RequestException as e:
        error_text = f"🚫 Ошибка получения данных: {str(e)}"
        bot.answer_callback_query(call.id, error_text, show_alert=True)
    except Exception as e:
        error_text = "⚠️ Произошла непредвиденная ошибка"
        print(e)
        bot.answer_callback_query(call.id, error_text, show_alert=True)

if __name__ == "__main__":
    bot.infinity_polling()