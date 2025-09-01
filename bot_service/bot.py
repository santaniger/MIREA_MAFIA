import random
import requests
import telebot
from telebot import types
from types import SimpleNamespace
from config import BOT_TOKEN, BASE_URL, ROLES_CONFIG, TRANSLATE_CONFIG, EMOJI_CONFIG, GROUPES_CONFIG
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
    regisrations_cnt = requests.get(f"{BASE_URL}/game/registrations", json={"player_id": message.from_user.id}).json()["count"]
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

@bot.callback_query_handler(func=lambda call: call.data == "delete_msg")
def delete_msg(call):
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)

@bot.message_handler(commands=["start"])
def start_command(message):
    print("start")
    response = requests.get(f"{BASE_URL}/players/{message.from_user.id}")
    print(message)
    if message.chat.type == "private":
        if (response.status_code // 100 == 2):
            print("OK")
            main_menu(message)
        else:
            bot.send_message(message.chat.id, "Добро пожаловать в клуб мафии МИРЭА! Давайте познакомимся, введите свой игровой ник:")
            bot.register_next_step_handler(message, get_name)
    else:
        if (response.status_code // 100 == 2):
            response = requests.get(f"{BASE_URL}/stat")
            if response.status_code//100 == 2:
                stats_data = response.json()
                def safe_divide(a, b):
                    try:
                        return round(a / b * 100, 1) if b != 0 else float('inf')
                    except:
                        return float('inf')

                def format_ratio(a, b):
                    try:
                        return round(a / b, 1) if b != 0 else float('inf')
                    except:
                        return float('inf')

                msg = "📊 <b>Клубная статистика:</b>\n\n" \
                          "👤 <b>Классические игры:</b>\n" \
                          f"☯ Всего сыграно: {stats_data['classic_games'] + stats_data['extended_games']}\n" \
                          f"🔴 Побед мирных: {stats_data['classic_civilian_wins'] + stats_data['extended_civilian_wins']}\n" \
                          f"⚫ Побед мафии: {stats_data['classic_games'] - stats_data['classic_civilian_wins'] + stats_data['extended_games'] - stats_data['extended_civilian_wins']}\n" \
                          f"🆚 К/Ч: {format_ratio((stats_data['classic_civilian_wins'] + stats_data['extended_civilian_wins']), (stats_data['classic_games'] - stats_data['classic_civilian_wins'] + stats_data['extended_games'] - stats_data['extended_civilian_wins']))}\n\n" \
 \
                          "🤵‍♂️ <b>Классические игры:</b>\n" \
                          f"☯ Всего сыграно: {stats_data['classic_games']}\n" \
                          f"🔴 Побед мирных: {stats_data['classic_civilian_wins']}\n" \
                          f"⚫ Побед мафии: {stats_data['classic_games'] - stats_data['classic_civilian_wins']}\n" \
                          f"🆚 К/Ч: {format_ratio(stats_data['classic_civilian_wins'], (stats_data['classic_games'] - stats_data['classic_civilian_wins']))}\n\n" \
 \
                          "🥷 <b>Городские игры:</b>\n" \
                          f"☯ Всего игр: {stats_data['extended_games']}\n" \
                          f"🔴 Побед мирных: {stats_data['extended_civilian_wins']}\n" \
                          f"⚫ Побед мафии: {stats_data['extended_games'] - stats_data['extended_civilian_wins']}\n" \
                          f"🆚 К/Ч: {format_ratio(stats_data['extended_civilian_wins'], (stats_data['extended_games'] - stats_data['extended_civilian_wins']))}\n\n" \
 \
                          "🎲 <b>Распределение ролей и победы:</b>\n\n" \
                          "<b>Сыграно карт</b>\n" \
                          f"{EMOJI_CONFIG['don']} {TRANSLATE_CONFIG['don']}: {stats_data['roles_distribution']['don']}\n" \
                          f"{EMOJI_CONFIG['mafia']} {TRANSLATE_CONFIG['mafia']}: {stats_data['roles_distribution']['mafia']}\n" \
                          f"{EMOJI_CONFIG['sheriff']} {TRANSLATE_CONFIG['sheriff']}: {stats_data['roles_distribution']['sheriff']}\n" \
                          f"{EMOJI_CONFIG['civilian']} {TRANSLATE_CONFIG['civilian']}: {stats_data['roles_distribution']['civilian']}\n" \
                          f"{EMOJI_CONFIG['doctor']} {TRANSLATE_CONFIG['doctor']}: {stats_data['roles_distribution']['doctor']}\n" \
                          f"{EMOJI_CONFIG['prostitute']} {TRANSLATE_CONFIG['prostitute']}: {stats_data['roles_distribution']['prostitute']}\n" \
                          f"{EMOJI_CONFIG['maniac']} {TRANSLATE_CONFIG['maniac']}: {stats_data['roles_distribution']['maniac']}\n\n" \
                          "<b>Победы по ролям</b>\n" \
                          f"{EMOJI_CONFIG['don']} {TRANSLATE_CONFIG['don']}: {stats_data['roles_wins']['don']}/{stats_data['roles_distribution']['don']} = {safe_divide(stats_data['roles_wins']['don'], stats_data['roles_distribution']['don'])}%\n" \
                          f"{EMOJI_CONFIG['mafia']} {TRANSLATE_CONFIG['mafia']}: {stats_data['roles_wins']['mafia']}/{stats_data['roles_distribution']['mafia']} = {safe_divide(stats_data['roles_wins']['mafia'], stats_data['roles_distribution']['mafia'])}%\n" \
                          f"{EMOJI_CONFIG['sheriff']} {TRANSLATE_CONFIG['sheriff']}: {stats_data['roles_wins']['sheriff']}/{stats_data['roles_distribution']['sheriff']} = {safe_divide(stats_data['roles_wins']['sheriff'], stats_data['roles_distribution']['sheriff'])}%\n" \
                          f"{EMOJI_CONFIG['civilian']} {TRANSLATE_CONFIG['civilian']}: {stats_data['roles_wins']['civilian']}/{stats_data['roles_distribution']['civilian']} = {safe_divide(stats_data['roles_wins']['civilian'], stats_data['roles_distribution']['civilian'])}%\n" \
                          f"{EMOJI_CONFIG['doctor']} {TRANSLATE_CONFIG['doctor']}: {stats_data['roles_wins']['doctor']}/{stats_data['roles_distribution']['doctor']} = {safe_divide(stats_data['roles_wins']['doctor'], stats_data['roles_distribution']['doctor'])}%\n" \
                          f"{EMOJI_CONFIG['prostitute']} {TRANSLATE_CONFIG['prostitute']}: {stats_data['roles_wins']['prostitute']}/{stats_data['roles_distribution']['prostitute']} = {safe_divide(stats_data['roles_wins']['prostitute'], stats_data['roles_distribution']['prostitute'])}%\n" \
                          f"{EMOJI_CONFIG['maniac']} {TRANSLATE_CONFIG['maniac']}: {stats_data['roles_wins']['maniac']}/{stats_data['roles_distribution']['maniac']} = {safe_divide(stats_data['roles_wins']['maniac'], stats_data['roles_distribution']['maniac'])}%\n"

                bot.send_message(
                    chat_id=message.chat.id,
                    text=msg.replace("inf", "∞"),
                    parse_mode='HTML'
                )
        else:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(
                text="Перейти в бота",
                url="https://t.me/MIREA_mafia_bot?start=/start"
            ))
            hello_msgs = ["Ого! Новенький!? Заходи ко мне для регистрации и получай полный доступ к моему функционалу!",
                          "Хмммм... Ты приходишь ко мне и просишь об услуге... Но ты делаешь это без знакомства! Но ты можешь исправить это, заходи и познакомься со мной",
                          "Никто не может сам подойти и представиться кому-то из наших друзей. Их должен познакомить кто-то третий. Заходи ко мне, представься, и перед тобой откроется мир мафии",
                          "Хочешь сыграть? Хорошо, тогда следуй за белым кроликом, представься ему и узнай, на сколько глубока кроличья нора",
                          "Хмммм... Ты хочешь стать частью famiglia? Хорошо, но сначала познакомься со мной, тогда и начнётся твой путь в семье",
                          "В городе ещё более глубокая ночь! Просыпается госпо... Странно, а вас я не припомню! Познакомьтесь со мной, тогда на город опустится ночь!"
                          ]
            bot.send_message(message.chat.id, hello_msgs[random.randint(0, 5)],reply_markup=keyboard)

@bot.message_handler(commands=["stat"])
def club_stat(message):
    response = requests.get(f"{BASE_URL}/players/{message.from_user.id}")
    if (response.status_code // 100 == 2):
        response = requests.get(f"{BASE_URL}/stat")
        if response.status_code // 100 == 2:
            stats_data = response.json()

            def safe_divide(a, b):
                try:
                    return round(a / b * 100, 1) if b != 0 else float('inf')
                except:
                    return float('inf')

            def format_ratio(a, b):
                try:
                    return round(a / b, 1) if b != 0 else float('inf')
                except:
                    return float('inf')

            msg = "📊 <b>Клубная статистика:</b>\n\n" \
                  "👤 <b>Классические игры:</b>\n" \
                  f"☯ Всего сыграно: {stats_data['classic_games'] + stats_data['extended_games']}\n" \
                  f"🔴 Побед мирных: {stats_data['classic_civilian_wins'] + stats_data['extended_civilian_wins']}\n" \
                  f"⚫ Побед мафии: {stats_data['classic_games'] - stats_data['classic_civilian_wins'] + stats_data['extended_games'] - stats_data['extended_civilian_wins']}\n" \
                  f"🆚 К/Ч: {format_ratio((stats_data['classic_civilian_wins'] + stats_data['extended_civilian_wins']), (stats_data['classic_games'] - stats_data['classic_civilian_wins'] + stats_data['extended_games'] - stats_data['extended_civilian_wins']))}\n\n" \
 \
                  "🤵‍♂️ <b>Классические игры:</b>\n" \
                  f"☯ Всего сыграно: {stats_data['classic_games']}\n" \
                  f"🔴 Побед мирных: {stats_data['classic_civilian_wins']}\n" \
                  f"⚫ Побед мафии: {stats_data['classic_games'] - stats_data['classic_civilian_wins']}\n" \
                  f"🆚 К/Ч: {format_ratio(stats_data['classic_civilian_wins'], (stats_data['classic_games'] - stats_data['classic_civilian_wins']))}\n\n" \
 \
                  "🥷 <b>Городские игры:</b>\n" \
                  f"☯ Всего игр: {stats_data['extended_games']}\n" \
                  f"🔴 Побед мирных: {stats_data['extended_civilian_wins']}\n" \
                  f"⚫ Побед мафии: {stats_data['extended_games'] - stats_data['extended_civilian_wins']}\n" \
                  f"🆚 К/Ч: {format_ratio(stats_data['extended_civilian_wins'], (stats_data['extended_games'] - stats_data['extended_civilian_wins']))}\n\n" \
 \
                  "🎲 <b>Распределение ролей и победы:</b>\n\n" \
                  "<b>Сыграно карт</b>\n" \
                  f"{EMOJI_CONFIG['don']} {TRANSLATE_CONFIG['don']}: {stats_data['roles_distribution']['don']}\n" \
                  f"{EMOJI_CONFIG['mafia']} {TRANSLATE_CONFIG['mafia']}: {stats_data['roles_distribution']['mafia']}\n" \
                  f"{EMOJI_CONFIG['sheriff']} {TRANSLATE_CONFIG['sheriff']}: {stats_data['roles_distribution']['sheriff']}\n" \
                  f"{EMOJI_CONFIG['civilian']} {TRANSLATE_CONFIG['civilian']}: {stats_data['roles_distribution']['civilian']}\n" \
                  f"{EMOJI_CONFIG['doctor']} {TRANSLATE_CONFIG['doctor']}: {stats_data['roles_distribution']['doctor']}\n" \
                  f"{EMOJI_CONFIG['prostitute']} {TRANSLATE_CONFIG['prostitute']}: {stats_data['roles_distribution']['prostitute']}\n" \
                  f"{EMOJI_CONFIG['maniac']} {TRANSLATE_CONFIG['maniac']}: {stats_data['roles_distribution']['maniac']}\n\n" \
                  "<b>Победы по ролям</b>\n" \
                  f"{EMOJI_CONFIG['don']} {TRANSLATE_CONFIG['don']}: {stats_data['roles_wins']['don']}/{stats_data['roles_distribution']['don']} = {safe_divide(stats_data['roles_wins']['don'], stats_data['roles_distribution']['don'])}%\n" \
                  f"{EMOJI_CONFIG['mafia']} {TRANSLATE_CONFIG['mafia']}: {stats_data['roles_wins']['mafia']}/{stats_data['roles_distribution']['mafia']} = {safe_divide(stats_data['roles_wins']['mafia'], stats_data['roles_distribution']['mafia'])}%\n" \
                  f"{EMOJI_CONFIG['sheriff']} {TRANSLATE_CONFIG['sheriff']}: {stats_data['roles_wins']['sheriff']}/{stats_data['roles_distribution']['sheriff']} = {safe_divide(stats_data['roles_wins']['sheriff'], stats_data['roles_distribution']['sheriff'])}%\n" \
                  f"{EMOJI_CONFIG['civilian']} {TRANSLATE_CONFIG['civilian']}: {stats_data['roles_wins']['civilian']}/{stats_data['roles_distribution']['civilian']} = {safe_divide(stats_data['roles_wins']['civilian'], stats_data['roles_distribution']['civilian'])}%\n" \
                  f"{EMOJI_CONFIG['doctor']} {TRANSLATE_CONFIG['doctor']}: {stats_data['roles_wins']['doctor']}/{stats_data['roles_distribution']['doctor']} = {safe_divide(stats_data['roles_wins']['doctor'], stats_data['roles_distribution']['doctor'])}%\n" \
                  f"{EMOJI_CONFIG['prostitute']} {TRANSLATE_CONFIG['prostitute']}: {stats_data['roles_wins']['prostitute']}/{stats_data['roles_distribution']['prostitute']} = {safe_divide(stats_data['roles_wins']['prostitute'], stats_data['roles_distribution']['prostitute'])}%\n" \
                  f"{EMOJI_CONFIG['maniac']} {TRANSLATE_CONFIG['maniac']}: {stats_data['roles_wins']['maniac']}/{stats_data['roles_distribution']['maniac']} = {safe_divide(stats_data['roles_wins']['maniac'], stats_data['roles_distribution']['maniac'])}%\n"

            bot.send_message(
                chat_id=message.chat.id,
                text=msg.replace("inf", "∞"),
                parse_mode='HTML'
            )
    else:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            text="Перейти в бота",
            url="https://t.me/MIREA_mafia_bot"
        ))
        hello_msgs = ["Ого! Новенький!? Заходи ко мне для регистрации и получай полный доступ к моему функционалу!",
                      "Хмммм... Ты приходишь ко мне и просишь об услуге... Но ты делаешь это без знакомства! Но ты можешь исправить это, заходи и познакомься со мной",
                      "Никто не может сам подойти и представиться кому-то из наших друзей. Их должен познакомить кто-то третий. Заходи ко мне, представься, и перед тобой откроется мир мафии",
                      "Хочешь сыграть? Хорошо, тогда следуй за белым кроликом, представься ему и узнай, на сколько глубока кроличья нора",
                      "Хмммм... Ты хочешь стать частью famiglia? Хорошо, но сначала познакомься со мной, тогда и начнётся твой путь в семье",
                      "В городе ещё более глубокая ночь! Просыпается госпо... Странно, а вас я не припомню! Познакомьтесь со мной, тогда на город опустится ночь!"
                      ]
        bot.send_message(message.chat.id, hello_msgs[random.randint(0, 5)], reply_markup=keyboard)

@bot.message_handler(commands=["my"])
def my_command(message):
    player = list(filter(lambda x: int(x['ID']) == message.from_user.id,
                         requests.get(f'{BASE_URL}/stats/all/players').json()['stats']))
    if player:
        player = player[0]
        bot.send_message(chat_id=message.chat.id,
                              text=f"Игровой ник: {player['nickname']}\n"
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
                                   f"┖ {EMOJI_CONFIG['prostitute']} {TRANSLATE_CONFIG['prostitute']}: {player['prostitute']['wins']}/{player['prostitute']['games']} = {(player['prostitute']['wins'] / player['prostitute']['games'] * 100) if player['prostitute']['games'] > 0 else 0:.1f}%",
                              )
    else:
        response = requests.get(f'{BASE_URL}/players/{message.from_user.id}')
        print(response.content)
        if (response.status_code // 100 == 2):
            player = response.json()
            bot.send_message(chat_id=message.chat.id,
                              text=f"Игровой ник: {player['nickname']}\n"
                                   f"🥇 Завершите свою первую игру для отображения личной статистики",
                              )
        else:
            start_command(message)

@bot.message_handler(commands=["help"])
def help(message):
    bot.send_message(message.chat.id, "/start - главное меню и перезагрузка\n"
                                      "/stat - клубная статистика\n"
                                      "/my - личная статистика")

def get_name(message, old_group = None, old_name = None):
    if old_group != None:
        bot.send_message(message.chat.id, f"Группа не найдена ({old_group})\nПроверьте написание (XXXX-00-00):")
        bot.register_next_step_handler(message, get_group, old_name)
    else:
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

    headers = {
        "accept": "*/*",
        "accept-language": "ru,en;q=0.9",
        "priority": "u=1, i",
        "referer": "https://schedule-of.mirea.ru/?date=2025-5-16&s=1_5263",
        "sec-ch-ua": '"Chromium";v="136", "YaBrowser";v="25.6", "Not.A/Brand";v="99", "Yowser";v="2.5"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 YaBrowser/25.6.0.0 Safari/537.36"
    }

    cookies = {
        "__ddg1_": "OhFYIEiv93s8E7lksInq",
        "tmr_lvid": "68f0b7cfbff7ad1dc4f49a478b5e8a3f",
        "tmr_lvidTS": "1720817346008",
        "_ym_uid": "1720817346236900417",
        "_ym_d": "1739874555",
        "__ddg9_": "94.29.3.204",
        "_ym_isad": "1",
        "__ddg10_": "1754169100",
        "__ddg8_": "YaxUItBtgkiyQ8Rw"
    }

    base_url = "https://schedule-of.mirea.ru/schedule/api/search"

    response = requests.get(
        base_url,
        headers=headers,
        cookies=cookies,
        params={
            "limit": 28,
            "match": message.text
        },
        timeout=10
    )
    group_name = message.text
    if response.status_code == 200:
        data = response.json()
        print(len(data.get('data')))
        if len(data.get('data')) == 1 and all(len(item.get('fullTitle', '')) >= 8 and item.get('fullTitle', '')[4] == '-' and item.get('fullTitle', '')[7] == '-'for item in data.get('data', [])if item and 'fullTitle' in item):
            print(100)
            group_name = data.get('data')[0]['fullTitle']
            response = requests.post(f"{BASE_URL}/reg", json={
                "ID": message.from_user.id,
                "chat_ID": message.chat.id,
                "nickname": name,
                "username": username,
                "group_name": group_name})
            print(group_name)
            if (response.status_code // 100 == 2):
                main_menu(message)
            else:
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton(text="OK", callback_data="delete_msg"))
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.id,
                                      text=f"Ошибка API: {response.content}\nДля повторной регистрации введите /start",
                                      reply_markup=keyboard)
        elif len(data.get('data')) != 0 and any(len(item.get('fullTitle', '')) >= 8 and item.get('fullTitle', '')[4] == '-' and item.get('fullTitle', '')[7] == '-'for item in data.get('data', [])if item and 'fullTitle' in item):
            print(200)
            keyboard = types.InlineKeyboardMarkup()

            # Фильтруем и добавляем кнопки сразу
            filtered_items = [
                i for i in data.get('data', [])
                if i and 'fullTitle' in i
                   and len(i['fullTitle']) >= 8
                   and i['fullTitle'][4] == '-'
                   and i['fullTitle'][7] == '-'
            ]

            # Создаём кнопки парами
            for i in range(0, len(filtered_items), 2):
                if i + 1 < len(filtered_items):
                    # Две кнопки в ряду
                    btn1 = types.InlineKeyboardButton(
                        text=filtered_items[i]['fullTitle'],
                        callback_data=f"manualReg_{name}_{username}_{filtered_items[i]['fullTitle']}"
                    )
                    btn2 = types.InlineKeyboardButton(
                        text=filtered_items[i + 1]['fullTitle'],
                        callback_data=f"manualReg_{name}_{username}_{filtered_items[i + 1]['fullTitle']}"
                    )
                    keyboard.row(btn1, btn2)
                else:
                    # Одна кнопка в последнем ряду
                    btn = types.InlineKeyboardButton(
                        text=filtered_items[i]['fullTitle'],
                        callback_data=f"manualReg_{name}_{username}_{filtered_items[i]['fullTitle']}"
                    )
                    keyboard.add(btn)
            btn = types.InlineKeyboardButton(
                text="Другая",
                callback_data=f"manualReg_{name}_{username}_{message.text}"
            )
            keyboard.add(btn)
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=loading.id,
                text=f"Выберите свою группу:",
                reply_markup=keyboard
            )
        else:
            print(300)
            get_name(message, old_group=group_name, old_name=name)
    else:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="OK", callback_data="delete_msg"))
        bot.edit_message_text(chat_id=message.chat.id, message_id=loading.id, text=f"Ошибка MIREA_API: {response.content}", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("manualReg"))
def manualReg(call):
    name = call.data.split('_')[1]
    username = call.data.split('_')[2]
    group_name = call.data.split('_')[3]
    response = requests.post(f"{BASE_URL}/reg", json={
        "ID": call.from_user.id,
        "chat_ID": call.message.chat.id,
        "nickname": name,
        "username": username,
        "group_name": group_name})
    print(group_name)
    print({
        "ID": call.from_user.id,
        "chat_ID": call.message.chat.id,
        "nickname": name,
        "username": username,
        "group_name": group_name})
    if (response.status_code // 100 == 2):
        main_menu(call.message)
    else:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="OK", callback_data="delete_msg"))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=f"Ошибка API: {response.content}\nДля повторной регистрации введите /start",
                              reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "menu_games")
def cancel_handler(call):
    response = requests.get(f"{BASE_URL}/game/list")
    msg_str = "ИГРЫ:\n"
    regisrations = [i["game_id"] for i in requests.get(f"{BASE_URL}/game/registrations", json={"player_id": call.from_user.id}).json()["registrations"]]
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
    if (is_master(call.from_user.id)):
        keyboard.add(types.InlineKeyboardButton(text=f"➕ СОЗДАТЬ", callback_data=f"new_game"))
    if (call.message.chat.type == "private"):
        keyboard.add(types.InlineKeyboardButton(text=f"🔙", callback_data=f"main_menu"))
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=msg_str, reply_markup=keyboard)
    except:
        bot.answer_callback_query(call.id, "Нет изменений ✅")

@bot.callback_query_handler(func=lambda call: call.data.startswith("gameInfo_"))
def game_info(call, edit=0):
    game_id = int(call.data.split('_')[1])
    regisrations = [i["game_id"] for i in requests.get(f"{BASE_URL}/game/registrations", json={"player_id": call.from_user.id}).json()["registrations"]]
    response = requests.get(f"{BASE_URL}/game/{game_id}")
    print(response.content)
    if (response.status_code // 100 != 2 and response.json()["is_archived"]):
        print("response.status_code // 100 != 2 and response.json()")
        archivedGame_info(call=SimpleNamespace(
            message=SimpleNamespace(
                chat=SimpleNamespace(id=call.message.chat.id,
                                     type=call.message.chat.type),
                id=call.message.id
            ),
            from_user=call.from_user,
            data=f"archivedGameInfo_{game_id}"
        )
        )
        return 0
    i = response.json()
    msg_text = f"\n<b>ОТКРЫТА РЕГИСТРАЦИЯ НА ИГРУ №{game_id}!</b>\n" \
               f"Пройдёт {format_date(i['date'].replace(' ', 'T'))}\n" \
               f"Тип игры: {'Классическая' if i['type'] == 'classic'  else 'Городская'}\n" \
               f"Ведущий: Г-н(жа) {i['master_nickname']}\n" \
               f"Аудитория: {i['room']}\n" \
               f"Макс кол-во игроков: {i['slots_cnt']}\n" \
               f"Зарегистрировано: {i['players_count']}\n" \
               f"{'Зарегистрированные игроки:' if i['players_count'] else 'Будь первым!'}\n"
    cnt = 0
    for player in sorted(
        i["registered_players"],
        key=lambda x: (1, x['registered_at']) if x['slot'] == 0 else (0, x['slot'])
    ):
        cnt += 1
        slot = player['slot']
        role = TRANSLATE_CONFIG[player['role']] if call.from_user.id == i['master_id'] and call.message.chat.type == "private" else "???"
        msg_text += f"{'' if slot == 0 else f'Слот {slot} | '}Г-н {player['nickname']} | {'В очереди' if cnt > i['slots_cnt'] else '✅' if role == 'None' else f'{role}'}\n"
        if (cnt == i['slots_cnt']):
            msg_text += "---------------\n"
    keyboard = types.InlineKeyboardMarkup()
    if (game_id in regisrations and call.message.chat.type == "private"):
        keyboard.add(types.InlineKeyboardButton(text=f"❌ Не смогу :(", callback_data=f"unregOfGame_{game_id}"))
    else:
        keyboard.add(types.InlineKeyboardButton(text=f"✅ Зарегистрироваться", callback_data=f"regToGame_{game_id}"))
    if (call.from_user.id == i['master_id'] and call.message.chat.type == "private"):
        #keyboard.add(types.InlineKeyboardButton(text=f"время", callback_data=f"changeGameTime_{game_id}"), types.InlineKeyboardButton(text=f"аудитория", callback_data=f"changeGameRoom_{game_id}"))
        keyboard.add(types.InlineKeyboardButton(text=f"🔄 Роли", callback_data=f"rolesGame_{game_id}"),
                     types.InlineKeyboardButton(text=f"🔄 Рассадка", callback_data=f"slotsGame_auto_{game_id}"))
        keyboard.add(types.InlineKeyboardButton(text=f"🎴 Отправить", callback_data=f"sendRoles_{game_id}"),
                     types.InlineKeyboardButton(text=f"🪑 Отправить", callback_data=f"sendSlots_{game_id}"))
        keyboard.add(types.InlineKeyboardButton(text=f"🏁 Завершить", callback_data=f"finishGame_{game_id}"))
        keyboard.add(types.InlineKeyboardButton(text=f"🚫 ОТМЕНИТЬ", callback_data=f"cancelGame_{game_id}"))
    keyboard.add(types.InlineKeyboardButton(
        text="🔄 Обновить",
        callback_data=f"gameInfo_{game_id}"
    ))
    print("Call", call.data)
    if (call.message.chat.type == "private"):
        keyboard.add(types.InlineKeyboardButton(text=f"🔙", callback_data=f"menu_games"))
    if edit == 0:
        try:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=msg_text, reply_markup=keyboard, parse_mode="html")
        except Exception as e:
            print(e)
            bot.answer_callback_query(call.id, "Нет изменений ✅")
    else:
        bot.send_message(chat_id=call.message.chat.id, text=msg_text, reply_markup=keyboard, parse_mode="html")

@bot.callback_query_handler(func=lambda call: call.data.startswith("slotsGame_auto_"))
def slotsGameAuto(call):
    game_id = int(call.data.split('_')[2])
    response = requests.put(f'{BASE_URL}/games/{game_id}/slots')
    print(response.json())
    if (response.status_code // 100 == 2):
        game_info(SimpleNamespace(
                    message=SimpleNamespace(
                        chat=SimpleNamespace(id=call.message.chat.id,
                                             type=call.message.chat.type),
                        id=call.message.id
                    ),
                    from_user=call.from_user,
                    data=f"hello_{game_id}"
                ), 0
            )
    else:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="OK", callback_data="delete_msg"))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=f"Ошибка API: {response.content}", reply_markup = keyboard)

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
                err_str += f"\nПользователю {player['player_id']}: {player['slot']}"
    if err_str:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="OK", callback_data="delete_msg"))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                              text=f"Ошибка в отправке:{err_str}", reply_markup = keyboard)
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                              text=f"Слоты успешно отправлены!")
    game_info(SimpleNamespace(
        message=SimpleNamespace(
            chat=SimpleNamespace(id=call.message.chat.id,
                                             type=call.message.chat.type),
            id=call.message.id
        ),
        from_user=call.from_user,
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
                chat=SimpleNamespace(id=call.message.chat.id,
                                             type=call.message.chat.type)
            ),
            from_user=call.from_user,
            data=f"hello_{game_id}"
        ), 1
        )
    elif (response.status_code == 401):
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=f"Не корректное количество игроков")
    else:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="OK", callback_data="delete_msg"))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=f"Ошибка API: {response.content}", reply_markup = keyboard)

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
                err_str += f"\nПользователю {player['player_id']}: {TRANSLATE_CONFIG[player['role']]}"
    if err_str:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="OK", callback_data="delete_msg"))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                              text=f"Ошибка в отправке:{err_str}", reply_markup=keyboard)
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                              text=f"Роли успешно отправлены!")
    game_info(SimpleNamespace(
        message=SimpleNamespace(
            chat=SimpleNamespace(id=call.message.chat.id,
                                             type=call.message.chat.type),
            id=call.message.id
        ),
        from_user=call.from_user,
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

    user_sessions[call.message.from_user] = {
        "game_id": game_id,
        "slots_cnt": int(slots_cnt),
        "current_slot": 1,
        "roles": [],
        "remaining_roles": ROLES_CONFIG[game_type][config_key].copy()
    }

    ask_role(chat_id, call.message.id, call.from_user)


def ask_role(chat_id, message_id, user_id):
    session = user_sessions.get(user_id)
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
                    chat=SimpleNamespace(id=call.message.chat.id,
                                             type=call.message.chat.type)
                ),
                from_user=call.from_user,
                data=f"hello_{session['game_id']}"
            ), 1
            )
        else:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text="OK", callback_data="delete_msg"))
            bot.send_message(chat_id, "Ошибка распределения ролей", reply_markup=keyboard)
        del user_sessions[call.from_user.id]
    else:
        ask_role(chat_id, call.message.id, call.from_user.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("rolesGame_"))
def rolesGame(call):
    game_id = int(call.data.split('_')[1])
    print(game_id)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text=f"🦾 Автоматически", callback_data=f"rolesGame_auto_{game_id}"))
    keyboard.add(types.InlineKeyboardButton(text=f"🎛️ Ручной ввод", callback_data=f"rolesGame_force_{game_id}"))
    if (call.message.chat.type == "private"):
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
    if (call.message.chat.type == "private"):
        keyboard.add(types.InlineKeyboardButton(text=f"🔙", callback_data=f"gameInfo_{game_id}"))
    bot.send_message(chat_id=call.message.chat.id, text=f"Автоматическая рассадка - всем игрокам придёт уведомление с их слотом\n"
                                                                                         f"Ручной ввод - поочерёдный выбор игрока (1, 2 ... n)", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("finishGame_"))
def finishGame(call):
    game_id = int(call.data.split('_')[1])
    response = requests.get(f'{BASE_URL}/game/{game_id}')
    for player in response.json()['registered_players']:
        if int(player["in_queue"]) == 0 and int(player["slot"]) == 0:
            bot.send_message(call.message.chat.id, "Слоты назначены не для всех пользователей!")
            return 0
    for player in response.json()['registered_players']:
        if int(player["in_queue"]) == 0 and player["role"] == "None":
            bot.send_message(call.message.chat.id, "Роли назначены не для всех пользователей!")
            return 0
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text=f"🔴 Победа Мирных", callback_data=f"Win_1_{game_id}"))
    keyboard.add(types.InlineKeyboardButton(text=f"⚫ Победа Мафии", callback_data=f"Win_0_{game_id}"))
    if (call.message.chat.type == "private"):
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
            err_str += f"\nПользователю {player['player_id']}"
    for group in GROUPES_CONFIG:
        try:
            bot.send_message(group, msg_text)
        except Exception as e:
            print(e)
            err_str += f"\nВ группу {group}"
    if err_str:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="OK", callback_data="delete_msg"))
        bot.send_message(chat_id=call.message.chat.id, text=f"Ошибка в отправке:{err_str}", reply_markup = keyboard)
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                              text=f"Результаты успешно отправлены!")
    response = requests.post(f"{BASE_URL}/games/{int(game[2])}/finish", json={"civilians_win": int(game[1])})
    if (response.status_code // 100 == 2):
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=f"Игра №{int(game[2])} успешно завершена.\nПобеда {'мирных' if bool(game[1]) else 'мафии'}!")
        main_menu(call.message)
    else:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="OK", callback_data="delete_msg"))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=f"Ошибка API: {response.content}", reply_markup = keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cancelGame_"))
def cancelGame(call):
    game_id = int(call.data.split('_')[1])
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text=f"📛 ПОДТВЕРДИТЬ 📛", callback_data=f"forceCancelGame_{game_id}"))
    if (call.message.chat.type == "private"):
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
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="OK", callback_data="delete_msg"))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=f"Ошибка API: {response.content}", reply_markup = keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("unregOfGame_"))
def unregFromGame(call):
    game_id = int(call.data.split('_')[1])
    print(game_id)
    response = requests.delete(f"{BASE_URL}/game/unreg", json={
        "player_id": call.from_user.id,
        "game_id": game_id})
    print(response.content)
    bot.register_callback_query_handler(call, game_info)
    game_info(call, 0)

@bot.callback_query_handler(func=lambda call: call.data.startswith("regToGame_"))
def regToGame(call):
    game_id = int(call.data.split('_')[1])
    print(game_id)
    response = requests.get(f"{BASE_URL}/game/{game_id}")
    if (response.status_code // 100 == 2 and not(response.json()["is_archived"])):
        response = requests.post(f"{BASE_URL}/game/reg", json={
            "player_id": call.from_user.id,
            "game_id": game_id})
        print(1, response.content)
        if (response.status_code // 100 == 2):
            bot.register_callback_query_handler(call, game_info)
            game_info(call, 0)
        elif (response.json()["error"] == "Player already registered"):
            bot.answer_callback_query(call.id, "Нет изменений ✅")
        else:
            start_command(call.message)
    elif (response.status_code // 100 == 2):
        try:
            archivedGame_info(call=SimpleNamespace(
            message=SimpleNamespace(
                chat=SimpleNamespace(id=call.message.chat.id,
                                     type=call.message.chat.type),
                id=call.message.id
            ),
            from_user=call.from_user,
            data=f"archivedGameInfo_{game_id}"
            )
            )
        except:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text="Игра завершена")
    else:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="OK", callback_data="delete_msg"))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text="Ошибка регистрации", reply_markup = keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "new_game")
def new_game(call):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text=f"🤵 ‍Классические", callback_data=f"new_game_type_classic"))
    keyboard.add(types.InlineKeyboardButton(text=f"🥷 Городские", callback_data=f"new_game_type_extended"))
    if (call.message.chat.type == "private"):
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
    user_sessions[message.from_user.id] = {
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
    user_sessions[call.from_user.id]['date'] = datetime.strptime(date_str, "%Y-%m-%d")
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
        game_data = user_sessions[call.from_user.id]
        date_obj = game_data['date']
        time_obj = datetime.strptime(time_str, "%H:%M").time()
        full_datetime = datetime.combine(date_obj.date(), time_obj)

        response = requests.post(
            f"{BASE_URL}/game/create",
            json={
                "type": game_data['game_type'],
                "slots_cnt": game_data['slots_cnt'],
                "room": game_data['room'],
                "masterID": call.from_user.id,
                "date": full_datetime.isoformat()
            }
        )
        print(response.content)
        game_ID = response.json()['game_id']
        bot.send_message(chat_id, f"Игра №{game_ID} создана успешно!")
        del user_sessions[call.from_user.id]
        response = requests.get(f"{BASE_URL}/players/{call.from_user.id}").json()
        for group in GROUPES_CONFIG:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text=f"✅ Зарегистрироваться", callback_data=f"regToGame_{game_ID}"))
            keyboard.add(types.InlineKeyboardButton(
                text="🔄 Обновить",
                callback_data=f"gameInfo_{game_ID}"
            ))
            bot.send_message(group, f"<b>ОТКРЫТА РЕГИСТРАЦИЯ НА ИГРУ №{game_ID}!</b>\n"
                                    f"Пройдёт {format_date(full_datetime.isoformat().replace(' ', 'T'))}\n"
                                    f"Тип игры: {'Классическая' if game_data['game_type'] == 'classic'  else 'Городская'}\n"
                                    f"Ведущий: Г-н(жа) {response['nickname']}\n"
                                    f"Аудитория: {game_data['room']}\n"
                                    f"Макс кол-во игроков: {game_data['slots_cnt']}\n", reply_markup=keyboard, parse_mode="html")
        main_menu(call.message)

    except Exception as e:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="OK", callback_data="delete_msg"))
        bot.send_message(chat_id, f"Ошибка: {str(e)}", reply_markup = keyboard)
        del user_sessions[call.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "stat")
def stat(call):
    player = list(filter(lambda x: int(x['ID']) == call.from_user.id, requests.get(f'{BASE_URL}/stats/all/players').json()['stats']))
    keyboard = types.InlineKeyboardMarkup()
    if player:
        keyboard.add(types.InlineKeyboardButton(text=f"🗄️ Мои игры", callback_data=f"stat_myGames"))
        keyboard.add(types.InlineKeyboardButton(text=f"👤 Все типы", callback_data=f"stat_all"))
        keyboard.add(types.InlineKeyboardButton(text=f"🤵‍♂️ Классика", callback_data=f"stat_classic"),
                     types.InlineKeyboardButton(text=f"🥷 Городская", callback_data=f"stat_extended"))
        if (call.message.chat.type == "private"):
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
        if (call.message.chat.type == "private"):
            keyboard.add(types.InlineKeyboardButton(text=f"🔙", callback_data=f"main_menu"))
        player = requests.get(f'{BASE_URL}/players/{call.from_user.id}').json()
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                              text=f"Игровой ник: {player['nickname']}\n"
                                   f"🥇 Завершите свою первую игру для отображения личной статистики\n\n👥 Другая статистика:",
                              reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "stat_myGames")
def stat_myGames(call):
    try:
        response = requests.get(f"{BASE_URL}/stats/player/{call.from_user.id}/games")
        message_text = "🗄️ Архив игр:\n"
        keyboard = types.InlineKeyboardMarkup()
        for game in response.json()['games']:
            message_text += f"\n— {format_date(game['date'].replace(' ', 'T'))}\n{'Классическая' if game['type'] == 'classic' else 'Городская'} игра №{game['game_ID']}\nРоль: {EMOJI_CONFIG[game['role']]} {TRANSLATE_CONFIG[game['role']]} ({game['slot']} слот)"
            message_text += "\n🏆 ПОБЕДА 🏆\n" if game['is_winner'] else "\n💀 ПОРАЖЕНИЕ 💀\n"
            keyboard.add(types.InlineKeyboardButton(text=f"ИГРА №{game['game_ID']}", callback_data=f"archivedGameInfo_{game['game_ID']}"))
        if (call.message.chat.type == "private"):
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
            line = f"<b>Слот {slot} | Г-н {nickname} | {EMOJI_CONFIG[role]} {TRANSLATE_CONFIG[role]}</b>" if player['player_ID'] == call.from_user.id else f"Слот {slot} | Г-н {nickname} | {EMOJI_CONFIG[role]} {TRANSLATE_CONFIG[role]}"
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
    if (call.message.chat.type == "private"):
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
                #f"{roles_text}\n"
                f"────────────────────\n"
            )

        keyboard = types.InlineKeyboardMarkup()
        refresh_btn = types.InlineKeyboardButton(
            text="🔄 Обновить статистику",
            callback_data=call.data
        )
        keyboard.add(refresh_btn)
        if (call.message.chat.type == "private"):
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