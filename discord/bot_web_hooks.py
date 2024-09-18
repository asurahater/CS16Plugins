import mysql.connector
from mysql.connector import Error, errorcode

import bot
from bot import *

current_message = None
current_status = None
line_count = 0
MAX_LINES = 50
MAX_CHAR_LIMIT = 2000  # Лимит символов в Discord для одного сообщения
user_message_received = False

@bot.event
async def on_message(message):
    global user_message_received

    if message.author == bot.user:
        return

    if message.channel.id == config.CS_CHAT_CHNL_ID:
        user_message_received = True
        send_msg = message.author.display_name + " " + "\"" + message.content + "\""
        srv.execute(f"ultrahc_ds_send_msg {send_msg}")
				# await message.delete()

    await bot.process_commands(message)

# Функция для проверки API-ключа
def check_api_key(request):
    api_key = request.headers.get('Authorization')  # Извлекаем ключ из заголовка
    if api_key == config.API_KEY:
        return True
    else:
        logging.warning(f"Неверный API-ключ")
        return False

def get_discord_id_by_steam_id(steam_id):
    connection = connect_to_mysql()
    if not connection:
    	return
    
    cursor = connection.cursor()
    query = "SELECT discord_id FROM users WHERE steam_id = %s"
    cursor.execute(query, (steam_id,))
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    
    return result[0] if result else None

# Функция для подключения к MySQL
def connect_to_mysql():
    try:
        conn = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME
        )
        return conn
    except mysql.connector.Error as err:
        # Выводим код ошибки и сообщение
        logging.error(f"Ошибка подключения: {err.errno} - {err.msg}")
        
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logging.error("Неверные данные для подключения к Базе данных")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logging.error("База данных не найдена")
        else:
            logging.error("Ошибка подключения")
        
        return None


# Функция для создания базы данных и таблиц
def setup_database():
    conn = connect_to_mysql()
    if conn is None:
        return
    cursor = conn.cursor()

    try:
        # Создание базы данных, если она не существует
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config.DB_NAME}")
        conn.database = config.DB_NAME
        logging.info(f"База данных '{config.DB_NAME}' проверена или создана.")

        # Создание таблиц, если они не существуют
        create_chat_table = """
        CREATE TABLE IF NOT EXISTS chat (
            id BIGINT UNSIGNED NOT NULL DEFAULT 0,
            server_ip TINYTEXT NOT NULL,
            username TINYTEXT NOT NULL,
            steam_id TINYTEXT NOT NULL,
            team ENUM('A', 'T', 'CT', 'S') NOT NULL DEFAULT 'A',
            datetime DATETIME NOT NULL DEFAULT '2000-05-05 14:13:12',
            channelmsg TINYTEXT NOT NULL COMMENT 'канал, типа (CT)(DEAD)',
            prefix TEXT NOT NULL,
            message TEXT NOT NULL,
            msg_color ENUM('d', 't', 'g') NOT NULL DEFAULT 'd' COMMENT 'default, as team, green',
            UNIQUE KEY `index_1` (id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id INT UNSIGNED NOT NULL AUTO_INCREMENT,
            discord_id TINYTEXT,
            ds_name TINYTEXT,
            ds_display_name TINYTEXT,
            steam_id TINYTEXT,
            date_register TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id) USING BTREE
        ) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4;
        """
        cursor.execute(create_chat_table)
        cursor.execute(create_users_table)
        logging.info("Таблицы 'chat' и 'users' проверены или созданы.")
    except mysql.connector.Error as err:
        logging.error(f"Ошибка при создании базы данных: {err}")
    finally:
        cursor.close()
        conn.close()
    
# Проверка существования записи в базе данных
def record_exists(user_id, steam_id):
    connection = connect_to_mysql()
    if not connection:
    	return
    
    cursor = connection.cursor()
    query = "SELECT COUNT(*) FROM users WHERE discord_id = %s OR steam_id = %s"
    cursor.execute(query, (user_id, steam_id))
    count = cursor.fetchone()[0]
    cursor.close()
    connection.close()
    return count > 0

# Сохранение сообщения в базу данных
def save_message(user_id, username, ds_username, steam_id):
    connection = connect_to_mysql()
    if not connection:
    	return
    
    cursor = connection.cursor()
    query = "INSERT INTO users (discord_id, ds_name, ds_display_name, steam_id) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (user_id, username, ds_username, steam_id))
    connection.commit()
    cursor.close()
    connection.close()
    
# Функция для создания сообщения с ANSI цветами, включая timestamp и префикс канала
def format_message(nick, message, team, channel_prefix):
    # Получаем текущее время в формате HH:MM:SS
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    # Зеленый цвет для timestamp
    timestamp_color = '\x1b[32m'  # Зеленый
    
    # Определение цвета для ника в зависимости от команды
    if team == 1:
        # Красный цвет для террористов
        nick_color = '\x1b[31m'  # Красный
    elif team == 2:
        # Голубой цвет для контр-террористов
        nick_color = '\x1b[34m'  # Голубой
    else:
        # Белый цвет по умолчанию
        nick_color = '\x1b[37m'  # Белый

    reset_color = '\x1b[0m'

    # Добавляем fпробел только если префикс не пустой
		# prefix_with_space = f"{channel_prefix} " if channel_prefix else ""

    # Форматируем сообщение с timestamp, префиксом канала, ником и его цветом
    return f"{timestamp_color}{timestamp}{reset_color} {channel_prefix} {nick_color}{nick}{reset_color}: {message}\n"
    
#-------------------------------------------------------------------
#-- Форматирование сообщения с информацией о сервере
#-------------------------------------------------------------------
def format_info_message(map_name, current_players, max_players):
    player_count = len(current_players) - 1  # Убираем последний элемент "null"
    team_players = {1: [], 2: [], 3: []}  # Словарь для хранения игроков по командам

    # Группируем игроков по командам
    for player in current_players[:-1]:  # Убираем последний элемент "null"
        player_name = player['name']
        stats = player['stats']
        team = stats[2]
        frags = stats[0]
        deaths = stats[1]

        # Добавляем игрока в соответствующую команду
        if team in team_players:
            team_players[team].append(f"{player_name} - {frags}/{deaths}")

    # Создаем сообщение
    formatted_info = []
    formatted_info.append(f"Название карты: {map_name}")
    formatted_info.append(f"Количество игроков: {player_count} / {max_players}")

    # Форматируем команды с цветами
    formatted_info.append("\n\033[1m\033[31mTerrorists:\033[0m")
    formatted_info.append("\n".join(team_players[1]) if team_players[1] else "Нет игроков")
    # formatted_info.append("\n".join([f"\033[31m{player}\033[0m" for player in team_players[1]]) if team_players[1] else "Нет игроков")
    
    formatted_info.append("\n\033[1m\033[34mCounter-Terrorists:\033[0m")
    formatted_info.append("\n".join(team_players[2]) if team_players[2] else "Нет игроков")
		# formatted_info.append("\n".join([f"\033[34m{player}\033[0m" for player in team_players[2]]) if team_players[2] else "Нет игроков")
    
    formatted_info.append("\n\033[1m\033[37mSpectators:\033[0m")
    formatted_info.append("\n".join(team_players[3]) if team_players[3] else "Нет игроков")
		# formatted_info.append("\n".join([f"\033[37m{player}\033[0m" for player in team_players[3]]) if team_players[3] else "Нет игроков")

    return "\n".join(formatted_info)



#-------------------------------------------------------------------
#-- Обработка вебхука
#-------------------------------------------------------------------
async def handle_message(data):
    global current_message, line_count, user_message_received

    cs_message = data.get('message')
    nick = data.get('nick')
    team = data.get('team')
    channel_prefix = data.get('channel', '')  # Получаем префикс канала
    steam_id = data.get('steam_id', '').strip()  # Получаем steam_id, если он есть

    if cs_message and nick and team is not None:
        # Получаем имя Discord по Steam ID
        discord_id = get_discord_id_by_steam_id(steam_id)

        # Если имя найдено, добавляем его в префикс
        if discord_id:
            guild = bot.get_guild(config.GUILD_ID)
            user = await guild.fetch_member(discord_id)
            display_name = user.display_name
            prefix = f"[{display_name}] "
        else:
            prefix = ""

        formatted_message = format_message(nick, cs_message, team, prefix + channel_prefix)

        can_add_to_current = False

        if current_message and not user_message_received and line_count < MAX_LINES:
            # Убираем закрывающий блок кода, если он есть
            if current_message.content.endswith('```'):
                current_content_without_closing = current_message.content[:-3]
            else:
                current_content_without_closing = current_message.content

            # Формируем новое содержание сообщения
            new_content = current_content_without_closing + formatted_message + '```'

            # Проверяем, не превышает ли новое сообщение лимит символов
            if len(new_content) <= MAX_CHAR_LIMIT:
                can_add_to_current = True

        if can_add_to_current:
            try:
                # Обновляем текущее сообщение, добавляя новое
                current_message = await current_message.edit(content=new_content)
                logging.info("Сообщение успешно обновлено в Discord")
                line_count += 1
            except Exception as e:
                logging.error(f"Ошибка при обновлении сообщения в Discord: {e}")
        else:
            try:
                channel = bot.get_channel(config.CS_CHAT_CHNL_ID)
                if channel is None:
                    logging.error("Канал не найден. Проверьте правильность CS_CHAT_CHNL_ID в config.py.")
                else:
                    # Отправляем новое сообщение
                    current_message = await channel.send(f"```ansi\n{formatted_message}```")
                    line_count = 1  # Сбрасываем счётчик строк
                    user_message_received = False  # Сбрасываем флаг пользователя
            except Exception as e:
                logging.error(f"Ошибка при отправке сообщения в Discord: {e}")

async def handle_notify(data):
    username = data.get('nick')
    notify_message = data.get('message')

    if username and notify_message:
        # Отправляем уведомление в специальный канал для админов
        admin_channel = bot.get_channel(config.ADMIN_CHANNEL_ID)  # Убедитесь, что у вас есть этот ID в config.py
        if admin_channel:
            formatted_notify_message = f"```ansi\nСообщение от \x1b[34m{username}\x1b[0m: {notify_message}```"
            await admin_channel.send(formatted_notify_message)
        else:
            logging.error("Канал для админов не найден. Проверьте правильность ADMIN_CHANNEL_ID в config.py.")

async def handle_info(data):
    global current_status
    
    map_name = data.get('map')
    current_players = data.get('current_players', [])
    
    max_players = data.get('max_players')

    # Форматируем сообщение
    formatted_info = format_info_message(map_name, current_players, max_players)

    # Отправляем сообщение в Discord
    channel = bot.get_channel(config.INFO_CHANNEL_ID)
    if channel:
    		if current_status:
    				new_content = f"```ansi\n{formatted_info}```"
    				current_status = await current_status.edit(content=new_content)
    		else:
       			current_status = await channel.send(f"```ansi\n{formatted_info}```")
    else:
        logging.error("Канал не найден. Проверьте правильность INFO_CHANNEL_ID в config.py.")

async def handle_webhook(request):
    # Проверяем API-ключ перед обработкой запроса
    if not check_api_key(request):
        return web.Response(text='Unauthorized', status=401)

    data = await request.json()
    message_type = data.get('type')  # Получаем тип сообщения

    if message_type == 'message':
        await handle_message(data)
    elif message_type == 'notify':
        await handle_notify(data)
    elif message_type == 'info':
        await handle_info(data)

    return web.Response(text='OK')
    
#-------------------------------------------------------------------

app.router.add_post('/webhook', handle_webhook)