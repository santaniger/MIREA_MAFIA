BOT_TOKEN = 'BOT_TOKEN'
network_ip = "http://api"
server_port = "5000"
BASE_URL = network_ip + ':' + server_port
ROLES_CONFIG = {
    "classic": {
            "13": ["don", "mafia", "mafia", "mafia", "sheriff", "civilian", "civilian", "civilian", "civilian", "civilian", "civilian", "civilian", "civilian"],
            "12": ["don", "mafia", "mafia", "sheriff", "civilian", "civilian", "civilian", "civilian", "civilian", "civilian", "civilian", "civilian"],
            "11": ["don", "mafia", "mafia", "sheriff", "civilian", "civilian", "civilian", "civilian", "civilian", "civilian", "civilian"],
            "10": ["don", "mafia", "mafia", "sheriff", "civilian", "civilian", "civilian", "civilian", "civilian", "civilian"],
            "9": ["don", "mafia", "mafia", "sheriff", "civilian", "civilian", "civilian", "civilian", "civilian"],
            "8": ["don", "mafia", "sheriff", "civilian", "civilian", "civilian", "civilian", "civilian"],
            "7": ["don", "mafia", "sheriff", "civilian", "civilian", "civilian", "civilian"],
            "6": ["don", "sheriff", "civilian", "civilian", "civilian", "civilian"]
    },
    "extended": {
            "13": ["don", "mafia", "mafia", "sheriff", "doctor", "civilian", "civilian", "civilian", "civilian", "civilian", "civilian", "prostitute", "maniac"],
            "12": ["don", "mafia", "mafia", "sheriff", "civilian", "civilian", "civilian", "civilian", "civilian", "civilian", "doctor", "maniac"],
            "11": ["don", "mafia", "mafia", "sheriff", "civilian", "civilian", "civilian", "civilian", "civilian", "doctor", "maniac"],
            "10": ["don", "mafia", "sheriff", "civilian", "civilian", "civilian", "civilian", "civilian", "doctor", "maniac"],
            "9": ["don", "mafia", "sheriff", "civilian", "civilian", "civilian", "civilian", "prostitute", "maniac"],
            "8": ["don", "mafia", "sheriff", "civilian", "civilian", "civilian", "civilian", "civilian"],
            "7": ["don", "sheriff", "civilian", "civilian", "civilian", "civilian", "civilian"],
            "6": ["mafia", "sheriff", "civilian", "civilian", "civilian", "civilian"]
    },
}
TRANSLATE_CONFIG = {
    "don": "Дон",
    "mafia": "Мафия",
    "sheriff": "Шериф",
    "civilian": "Мирный",
    "prostitute": "Путана",
    "doctor": "Доктор",
    "maniac": "Маньяк",
    "None": "Нет"
}

EMOJI_CONFIG = {
    "don": "🤵🏻",
    "mafia": "♟",
    "sheriff": "⭐",
    "civilian": "🙋🏻‍♂️",
    "prostitute": "🦋",
    "doctor": "💉",
    "maniac": "🔪",
    "None": "Нет"
}