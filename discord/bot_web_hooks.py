import mysql.connector
from mysql.connector import Error, errorcode

import redis_manager
from redis_manager import *

current_message = None
current_status = None
line_count = 0
max_lines = 50
max_char_limit = 2000  # Лимит символов в Discord для одного сообщения
user_message_received = False
current_players = []

# Загружается из БД
all_maps = []
active_maps = []


#-------------------------------------------------------------------
#-- Утильс
#-------------------------------------------------------------------

def get_steam_id(player_name):
    for player in current_players:
        if player["name"] == player_name:
            return player["steam_id"]
    return None  # Если player_name не найден

def update_map_lists(all_maps_, active_maps_):
    global all_maps, active_maps
    all_maps = all_maps_
    active_maps = active_maps_
    
def add_map_to_all(map_name):
    global all_maps
    if map_name not in all_maps:
        all_maps.append(map_name)
        return 1
    return 0

def add_map_to_active(map_name):
    global active_maps
    if map_name not in active_maps:
        active_maps.append(map_name)
        return 1
    return 0

def del_map_from_all(map_name):
    global all_maps
    if map_name in all_maps:
        all_maps.remove(map_name)
        return 1
    return 0

def del_map_from_active(map_name):
    global active_maps
    if map_name in active_maps:
        active_maps.remove(map_name)
        return 1
    return 0

def set_user_message_received(val):
	global user_message_received
	user_message_received = val

# Функция для проверки API-ключа
def check_api_key(request):
    api_key = request.headers.get('Authorization')  # Извлекаем ключ из заголовка
    if api_key == config.API_KEY:
        return True
    else:
        logging.warning(f"Неверный API-ключ")
        return False

#-------------------------------------------------------------------
#-- Работа с БД
#-------------------------------------------------------------------

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
				    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
				    server_ip TINYTEXT NOT NULL,
				    username TINYTEXT NOT NULL,
				    steam_id TINYTEXT NOT NULL,
				    team ENUM('A', 'T', 'CT', 'S') NOT NULL DEFAULT 'A',
				    datetime DATETIME NOT NULL DEFAULT '2000-05-05 14:13:12',
				    channelmsg TINYTEXT NOT NULL COMMENT 'канал, типа (CT)(DEAD)',
				    prefix TEXT NOT NULL,
				    message TEXT NOT NULL,
				    msg_color ENUM('d', 't', 'g') NOT NULL DEFAULT 'd' COMMENT 'default, as team, green',
				    PRIMARY KEY (id)
				) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;
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
        ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;
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
def save_user(user_id, username, ds_username, steam_id):
    connection = connect_to_mysql()
    if not connection:
    	return
    
    cursor = connection.cursor()
    
    query = "INSERT INTO users (discord_id, ds_name, ds_display_name, steam_id) VALUES (%s, %s, %s, %s)"
    
    cursor.execute(query, (user_id, username, ds_username, steam_id))
    connection.commit()
    cursor.close()
    connection.close()
    
# Сохранение Карты в базу данных
def save_map(map_name, activated, min_players, max_players, priority):

    # redis
    add_map_to_redis(map_name, activated)

    connection = connect_to_mysql()
    if not connection:
    	return
    	
    cursor = connection.cursor()
    
    query = """
        INSERT INTO maps (map_name, activated, min_players, max_players, priority) 
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            activated = VALUES(activated),
            min_players = VALUES(min_players),
            max_players = VALUES(max_players),
            priority = VALUES(priority)
    """
    
    cursor.execute(query, (map_name, activated, min_players, max_players, priority))
    connection.commit()
    cursor.close()
    connection.close()
    
def delete_map(map_name):
    # redis
    delete_map_from_redis(map_name)

    connection = connect_to_mysql()
    if not connection:
    	return
    	
    cursor = connection.cursor()
    
    query = "DELETE FROM maps WHERE map_name = %s"
    
    cursor.execute(query, (map_name,))
    connection.commit()
    cursor.close()
    connection.close()

# Обновляет карту в базе данных
def update_map(map_name, activated, min_players, max_players, priority):
    global all_maps, active_maps
    if map_name not in all_maps:
        return 0
    
    # Обновление в Redis перед попыткой соединения с БД
    update_map_value_in_redis(map_name, activated)

    connection = connect_to_mysql()
    if not connection:
        return 1  # Возвращаем 1, так как обновление в Redis прошло успешно

    cursor = connection.cursor()
    
    # Формируем запрос и параметры
    updates = []
    params = []

    if activated is not None:
        updates.append("activated = %s")
        params.append(activated)
        
    if min_players is not None:
        updates.append("min_players = %s")
        params.append(min_players)
        
    if max_players is not None:
        updates.append("max_players = %s")
        params.append(max_players)
        
    if priority is not None:
        updates.append("priority = %s")
        params.append(priority)

    if not updates:
        cursor.close()
        connection.close()
        return 0

    query = f"UPDATE maps SET {', '.join(updates)} WHERE map_name = %s"
    params.append(map_name)

    cursor.execute(query, params)
    connection.commit()
    cursor.close()
    connection.close()
    
    return 1
      
def sync_redis_with_db():
    global all_maps, active_maps
    r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=0)

    connection = connect_to_mysql()
    if not connection:
        return 0
        
    cursor = connection.cursor()
    
    # Получаем данные из базы данных
    cursor.execute("SELECT map_name, activated FROM maps")
    results = cursor.fetchall()  # Получаем все результаты
    
    # Очищаем Redis перед синхронизацией
    r.flushdb()

    for name, activated in results:
        # Сохраняем данные в Redis
        r.set(name, activated)
        
    cursor.close()
    connection.close()
    
    all_maps, active_maps = load_map_data_from_redis()
    
    r.bgsave()
    r.close()
    
    return 1
    
#-------------------------------------------------------------------
#-- Форматирование сообщения с информацией о сервере
#-------------------------------------------------------------------

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

def format_info_message(map_name, current_players, max_players):
    player_count = len(current_players)  # Убираем последний элемент "null"
    team_players = {1: [], 2: [], 3: []}  # Словарь для хранения игроков по командам

    # Группируем игроков по командам
    for player in current_players:  # Убираем последний элемент "null"
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
    global current_message, line_count, max_lines, user_message_received, max_char_limit

    cs_message = data.get('message')
    nick = data.get('nick')
    team = data.get('team')
    channel_prefix = data.get('channel', '')  # Получаем префикс канала
    steam_id = data.get('steam_id', '').strip()  # Получаем steam_id, если он есть

    if not (cs_message and nick and team is not None):
        return  # Ранний выход, если нет сообщения, ника или команды

    # Получаем имя Discord по Steam ID
    discord_id = get_discord_id_by_steam_id(steam_id)
    prefix = ""

    if discord_id:
        guild = bot.get_guild(config.GUILD_ID)
        user = await guild.fetch_member(discord_id)
        prefix = f"[{user.display_name}] "

    formatted_message = format_message(nick, cs_message, team, prefix + channel_prefix)

    if current_message and not user_message_received and (line_count < max_lines):
        try:
            current_message_new = await current_message.channel.fetch_message(current_message.id)
            can_add_to_current = False

            # Убираем закрывающий блок кода, если он есть
            current_content_without_closing = current_message_new.content[:-3] if current_message_new.content.endswith('```') else current_message_new.content

            # Формируем новое содержание сообщения
            new_content = current_content_without_closing + formatted_message + '```'

            # Проверяем, не превышает ли новое сообщение лимит символов
            if len(new_content) <= max_char_limit:
                can_add_to_current = True

            if can_add_to_current:
                current_message = await current_message_new.edit(content=new_content)
                logging.info("Сообщение успешно обновлено в Discord")
                line_count += 1
                return  # Ранний выход после успешного обновления
        except discord.NotFound:
            logging.warning("Текущее сообщение не найдено, создаем новое.")
        except Exception as e:
            logging.error(f"Ошибка при обновлении сообщения в Discord: {e}")


    channel = bot.get_channel(config.CS_CHAT_CHNL_ID)
    if channel is None:
        logging.error("Канал не найден. Проверьте правильность CS_CHAT_CHNL_ID в config.py.")
        return

    try:
        # Отправляем новое сообщение
        current_message = await channel.send(f"```ansi\n{formatted_message}```")
        line_count = 1  # Сбрасываем счётчик строк
        user_message_received = False  # Сбрасываем флаг пользователя
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения в Discord: {e}")

async def handle_notify(data):
    username = data.get('nick')
    notify_message = data.get('message')

    if not (username and notify_message):
        return  # Ранний выход, если нет имени пользователя или сообщения

    # Отправляем уведомление в специальный канал для админов
    admin_channel = bot.get_channel(config.ADMIN_CHANNEL_ID)
    if not admin_channel:
        logging.error("Канал для админов не найден. Проверьте правильность ADMIN_CHANNEL_ID в config.py.")
        return

    formatted_notify_message = f"```ansi\nСообщение от \x1b[34m{username}\x1b[0m: {notify_message}```"
    await admin_channel.send(formatted_notify_message)

async def handle_info(data):
    global current_status, current_players
    
    map_name = data.get('map')
    current_players = data.get('current_players', [])
    max_players = data.get('max_players')

    for player in current_players:
        add_player_to_redis(player['name'], player['steam_id'])

    # Форматируем сообщение
    formatted_info = format_info_message(map_name, current_players, max_players)

    # Отправляем сообщение в Discord
    channel = bot.get_channel(config.INFO_CHANNEL_ID)
    if not channel:
        logging.error("Канал не найден. Проверьте правильность INFO_CHANNEL_ID в config.py.")
        return

    if current_status:
        try:
            # Проверяем, существует ли сообщение
            current_status_message = await channel.fetch_message(current_status.id)
            
            new_content = f"```ansi\n{formatted_info}```"
            current_status = await current_status_message.edit(content=new_content)
            return
        except discord.Forbidden:
            logging.error("У меня нет прав на редактирование этого сообщения.")
            return
        except discord.NotFound:
            logging.warning("Сообщение не найдено, создаем новое.")
        except discord.HTTPException as e:
            logging.error(f"Ошибка при редактировании сообщения: {e}")
            return

    # Если current_status не существует или сообщение не найдено, создаем новое
    current_status = await channel.send(f"```ansi\n{formatted_info}```")

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

#-------------------------------------------------------------------
#-- Autocompletions
#-------------------------------------------------------------------

async def all_map_autocomplete(interaction: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    filter_maps = [map_name for map_name in all_maps if current.lower() in map_name.lower()][:25]
    return [discord.app_commands.Choice(name=map, value=map) for map in filter_maps]

async def active_map_autocomplete(interaction: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    filter_maps = [map_name for map_name in active_maps if current.lower() in map_name.lower()][:25]
    return [discord.app_commands.Choice(name=map, value=map) for map in filter_maps]

async def players_online_autocomplete(interaction: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    global current_players
    filter_players = [player['name'] for player in current_players if current.lower() in player['name'].lower()][:25]
    return [discord.app_commands.Choice(name=player, value=player) for player in filter_players]

async def players_offline_autocomplete(interaction: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    global current_players
    filter_players = get_non_current_players(current_players);
    choices = [
        discord.app_commands.Choice(name=f"{player['player_name']} ({player['steam_id']})", value=player["steam_id"])
        for player in filter_players
    ][:25]
    
    return choices

async def players_banned_autocomplete(interaction: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    ban_list = get_last_bans_from_redis() # последние 25

    filter_players = [ban for ban in ban_list if current.lower() in ban['player_name'].lower()][:25]
    return [discord.app_commands.Choice(name=f"{player['player_name']} ({player['steam_id']})", value=player['steam_id']) for player in filter_players]

async def ban_choice_autocomplete(interaction: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    return [
						discord.app_commands.Choice(name="5 минут", value=5),
						discord.app_commands.Choice(name="30 минут", value=30),
						discord.app_commands.Choice(name="60 минут", value=60),
						discord.app_commands.Choice(name="1 день", value=1440),
						discord.app_commands.Choice(name="1 неделя", value=10080),
						discord.app_commands.Choice(name="Навсегда", value=0)
					]