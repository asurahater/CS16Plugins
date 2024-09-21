import bot_web_hooks
from bot_web_hooks import *

import re

#-------------------------------------------------------------------
#-- Utility
#-------------------------------------------------------------------

def is_valid_steam_id(steam_id):
    pattern = r'^(STEAM|VALVE)_[0-9]:[0-9]:[0-9]{1,12}$'
    return bool(re.match(pattern, steam_id))

#-------------------------------------------------------------------
#-- Общие команды
#-------------------------------------------------------------------

#-- /clear
#-- Удаляет сообщения в канале
#-- @params amount (default=0)
@bot.tree.command(name="clear", description="Удаляет сообщения в канале")
@discord.app_commands.describe(amount="Количество сообщений для удаления")
@commands.has_permissions(manage_messages=True) 
async def cmd_clear(interaction: discord.Interaction, amount: int = 0):
    await interaction.response.defer(ephemeral=True, thinking=True)

    channel = interaction.channel
    
    if channel is not None:
        try:
            deleted = await channel.purge(limit=amount)
            await interaction.followup.send(content=f'Удалено {len(deleted)} сообщений.')
        except Exception as e:
            await interaction.followup.send(content=f'Произошла ошибка: {str(e)}')
    else:
        await interaction.followup.send(content='Канал не найден.')

#-- /connect_to_cs
#-- Подключается к серверу.
@bot.tree.command(name="connect_to_cs", description="Подключается к серверу")
@commands.has_permissions(manage_messages=True)  # Проверка прав пользователя
async def cmd_connect_to_cs(interaction: discord.Interaction):
    if srv.is_connected:
		    srv.disconnect()
  
    # Вызываем функцию подключения к серверу
    try:
        await connect_to_cs()
        logging.info(f"Подключился к CS Server")
        await interaction.response.send_message("Успешно подключено к серверу!", ephemeral=True)
    except Exception as e:
        logging.error(f"Ошибка при подключении к CS Server: {e}")
        await interaction.response.send_message('Ошибка при подключении к CS Server. Проверьте логи.', ephemeral=True)

#-------------------------------------------------------------------
#-- Команды для регистрации игроков
#-------------------------------------------------------------------

#-- /reg
#-- Регистрация пользователя с указанием steam_id
#-- @params steam_id
@bot.tree.command(name="reg", description="Регистрация пользователя с указанием steam_id")
async def cmd_reg(interaction: discord.Interaction, steam_id: str):
    user_id = str(interaction.user.id)
    username = interaction.user.name
    ds_username = interaction.user.display_name

    # Проверяем, существует ли запись
    if record_exists(user_id, steam_id):
        await interaction.response.send_message(f'Данные для SteamID {steam_id} или вашего аккаунта уже существуют.', ephemeral=True)
        return
    
    if not is_valid_steam_id(steam_id):
        await interaction.response.send_message(f'Неправильный формат SteamID', ephemeral=True)
        return
    
    save_user(user_id, username, ds_username, steam_id)
    await interaction.response.send_message(f'Данные сохранены: {username}', ephemeral=True)

#-- /unreg
#-- Удаляет данные пользователя по Discord ID
#-- no params
@bot.tree.command(name="unreg", description="Удаляет данные пользователя по Discord ID")
async def cmd_unreg(interaction: discord.Interaction):
    user_id = str(interaction.user.id)

    # Создаем подключение к базе данных
    connection = connect_to_mysql()
    if not connection:
    	await interaction.response.send_message(f'Нет соединения с базой данных', ephemeral=True)
    	return
    
    cursor = connection.cursor()

    # Удаляем запись из базы данных
    query = "DELETE FROM users WHERE discord_id = %s"
    cursor.execute(query, (user_id,))
    connection.commit()

    # Проверяем, сколько строк было удалено
    if cursor.rowcount > 0:
        await interaction.response.send_message(f'Данные для вашего аккаунта успешно удалены.', ephemeral=True)
    else:
        await interaction.response.send_message(f'Данные для вашего аккаунта не найдены.', ephemeral=True)

    cursor.close()
    connection.close()

#-------------------------------------------------------------------
#-- Команды для status
#-------------------------------------------------------------------

#-- /status
#-- Получает информацию о сервере
@bot.tree.command(name="status", description="Получает информацию о сервере")
@commands.has_permissions(manage_messages=True)  # Проверка прав пользователя
async def cmd_status(interaction: discord.Interaction):
    # Отправляем команду на сервер
    try:
        srv.execute("ultrahc_ds_get_info")  # Выполняем команду на сервере
        await interaction.response.send_message('Команда выполнена.', ephemeral=True, delete_after=0)
    except Exception as e:
        logging.error(f"Ошибка при получении статуса CS Server: {e}")
        await interaction.response.send_message('Ошибка при получении статуса сервера. Проверьте логи.', ephemeral=True)

#-------------------------------------------------------------------
#-- Команды для server manager
#-------------------------------------------------------------------

#-- /rcon
#-- Отправляет произвольную команду в консоль сервера
#-- @params: command
@bot.tree.command(name="rcon", description="Отправляет произвольную команду в консоль сервера")
@commands.has_permissions(manage_messages=True)
async def cmd_any(interaction: discord.Interaction, command: str):      
  # Отправляем команду на сервер
    try:
        srv.execute(command)
        
        user_nick = interaction.user.display_name
        nick_color = '\x1b[34m'  # Голубой
        reset_color = '\x1b[0m'
        
        await interaction.response.send_message(f"```ansi\n{nick_color}{user_nick}{reset_color} выполнил команду: \"{command}\"```")
    except Exception as e:
        logging.error(f"Ошибка при выполнении команды: {e}")
        await interaction.response.send_message('Ошибка при выполнении команды. Проверьте логи.', ephemeral=True)


#-- /kick
#-- Кикает игрока с сервера
#-- @params player_nick, reason
@bot.tree.command(name="kick", description="Кикает игрока с сервера")
@discord.app_commands.describe(player_nick="Ник игрока, можно вставить steam_id", reason="Причина кика")
@discord.app_commands.autocomplete(player_nick=players_online_autocomplete)
@commands.has_permissions(manage_messages=True)  # Проверка прав пользователя
async def cmd_kick(interaction: discord.Interaction, player_nick: str, reason: str=None):  
    # Формируем команду для кика игрока
    command = f"ultrahc_ds_kick_player \"{player_nick}\" \"{reason}\""
    
    # Отправляем команду на сервер
    try:
        srv.execute(command)
        user_nick = interaction.user.display_name
        nick_color = '\x1b[34m'  # Голубой
        reset_color = '\x1b[0m'
        await interaction.response.send_message(f"```ansi\n{nick_color}{user_nick}{reset_color} кикнул игрока: {nick_color}{player_nick}{reset_color} по причине: {reason}```")
    except Exception as e:
        logging.error(f"Ошибка при кике игрока: {e}")
        await interaction.response.send_message('Ошибка при кике игрока. Проверьте логи.', ephemeral=True)
        
#-- /ban
#-- Банит игрока
@bot.tree.command(name="ban", description="Банит игрока на сервера")
@discord.app_commands.describe(player_nick="Ник игрока(Можно ввести steam_id)", minutes="Минут бана(0 - перманент)", reason="Причина бана")
@discord.app_commands.autocomplete(player_nick=players_online_autocomplete)
@discord.app_commands.autocomplete(minutes=ban_choice_autocomplete)
@commands.has_permissions(manage_messages=True)  # Проверка прав пользователя
async def cmd_ban(interaction: discord.Interaction, player_nick: str, minutes: int, reason: str=None):
    if not reason:
        reason = "Без причины"
		
    command = f"amx_ban \"{player_nick}\" \"{minutes}\" \"{reason}\""
    
    # Отправляем команду на сервер
    try:
        srv.execute(command)
        user_nick = interaction.user.display_name
        nick_color = '\x1b[34m'  # Голубой
        reset_color = '\x1b[0m'
        
        user_steam_id = get_steam_id(player_nick)
        if user_steam_id:
            add_ban_to_redis(player_nick, user_steam_id, minutes, reason)
        else:
            add_ban_to_redis(player_nick, player_nick, minutes, reason)
        
        await interaction.response.send_message(f"```ansi\n{nick_color}{user_nick}{reset_color} забанил игрока: {nick_color}{player_nick}{reset_color} по причине: {reason}```")
    except Exception as e:
        logging.error(f"Ошибка при бане игрока: {e}")
        await interaction.response.send_message('Ошибка при бане игрока. Проверьте логи.', ephemeral=True)
        
#-- /unban
#-- Банит игрока
@bot.tree.command(name="unban", description="Разбанивает игрока")
@discord.app_commands.describe(player_id="steam_id игрока")
@discord.app_commands.autocomplete(player_id=players_banned_autocomplete)
@commands.has_permissions(manage_messages=True)  # Проверка прав пользователя
async def cmd_ban(interaction: discord.Interaction, player_id: str):
		# Формируем команду для кика игрока
		
    command = f"amx_unban \"{player_id}\""
    
    # Отправляем команду на сервер
    try:
        srv.execute(command)
        user_nick = interaction.user.display_name
        nick_color = '\x1b[34m'  # Голубой
        reset_color = '\x1b[0m'
        
        player_name = remove_ban_from_redis(player_id)
        if not player_name:
            await interaction.response.send_message(f"```ansi\n{nick_color}{user_nick}{reset_color} разбанил игрока: {nick_color}{player_id}{reset_color}```")
        else:
            await interaction.response.send_message(f"```ansi\n{nick_color}{user_nick}{reset_color} разбанил игрока: {nick_color}{player_name}{reset_color}```")
    except Exception as e:
        logging.error(f"Ошибка при бане игрока: {e}")
        await interaction.response.send_message('Ошибка при бане игрока. Проверьте логи.', ephemeral=True)

#-------------------------------------------------------------------
#-- Команды для карты (server manager)
#-------------------------------------------------------------------

#-- /sync_maps
#-- Перезагружает список карт
#-- @params: none
@bot.tree.command(name="sync_maps", description="Синхронизирует список карт между MySQL, redis и сервером(MySQL главный)")
@commands.has_permissions(manage_messages=True)  
async def cmd_sync_maps(interaction: discord.Interaction):
    # Формируем команду для перезагрузки списка карт
    command = "ultrahc_ds_reload_map_list"
    
    if not sync_redis_with_db():
         await interaction.response.send_message(f"```Нет связи с БД```")
         return
    
    # Отправляем команду на сервер
    try:
        srv.execute(command)
        
        user_nick = interaction.user.display_name
        nick_color = '\x1b[34m'  # Голубой
        reset_color = '\x1b[0m'
        
        await interaction.response.send_message(f"```Успешно```", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message('Нет связи с CS server', ephemeral=True)

#-- /change_map
#-- Меняет карту
#-- @params: map
@bot.tree.command(name="change_map", description="Меняет карту")
@discord.app_commands.describe(map="Название карты")
@discord.app_commands.autocomplete(map=active_map_autocomplete)
@commands.has_permissions(manage_messages=True)
async def cmd_change_map(interaction: discord.Interaction, map: str):  
    # Формируем команду для смены карты
    command = f"ultrahc_ds_change_map {map}"
    
    # Отправляем команду на сервер
    try:
        srv.execute(command)
        
        user_nick = interaction.user.display_name
        nick_color = '\x1b[34m'  # Голубой
        reset_color = '\x1b[0m'
        
        await interaction.response.send_message(f"```ansi\n{nick_color}{user_nick}{reset_color} сменил карту на: {map}```")
    except Exception as e:
        logging.error(f"Ошибка при смене карты: {e}")
        await interaction.response.send_message('Ошибка при смене карты. Проверьте логи.', ephemeral=True)

#-- /add_map
#-- Добавляет карту в БД
#-- @params map_name, activated(1), min_players(0), max_players(32), priority(100)
@bot.tree.command(name="add_map", description="Добавляет карту в БД")
@discord.app_commands.describe(map_name="Название карты", activated="Активна ли карта(в маппуле)", min_players="Минимум игроков", max_players="Максимум игроков", priority="Приоритет")
@commands.has_permissions(manage_messages=True)  # Проверка прав пользователя
async def cmd_kick(interaction: discord.Interaction, map_name: str, activated: int=1, min_players: int=0, max_players: int=32, priority: int=100):
    if not map_name.strip():
    	await interaction.response.send_message('Введите название карты', ephemeral=True)
    	return
    	
    
    if not add_map_to_all(map_name):
        await interaction.response.send_message(f'Карта {map_name} уже есть в списке', ephemeral=True)
        return
    
    save_map(map_name, activated, min_players, max_players, priority) # to db
    if activated:
        add_map_to_active(map_name)
        
    await interaction.response.send_message(f'Карта {map_name} добавлена', ephemeral=True)
    
#-- /delete_map
#-- Удаляет карту из БД
#-- @params map_name
@bot.tree.command(name="delete_map", description="Удаляет карту из БД")
@discord.app_commands.describe(map_name="Название карты")
@discord.app_commands.autocomplete(map_name=all_map_autocomplete)
@commands.has_permissions(manage_messages=True)  # Проверка прав пользователя
async def cmd_kick(interaction: discord.Interaction, map_name: str):
    if not map_name.strip():
    	await interaction.response.send_message('Введите название карты', ephemeral=True)
    	return
    	
    
    if not del_map_from_all(map_name):
        await interaction.response.send_message(f'Карты {map_name} нет в списке', ephemeral=True)
        return
        
    del_map_from_active(map_name)
    delete_map(map_name) # from db
    
    await interaction.response.send_message(f'Карта {map_name} удалена', ephemeral=True)

#-- /update_map
#-- Обновляет карту новыми данными
#-- @params map_name, activated, min_players, max_players, priority
@bot.tree.command(name="update_map", description="Обновляет карту новыми данными")
@discord.app_commands.describe(map_name="Название карты", activated="Активна ли карта(в маппуле)", min_players="Минимум игроков", max_players="Максимум игроков", priority="Приоритет")
@discord.app_commands.autocomplete(map_name=all_map_autocomplete)
@commands.has_permissions(manage_messages=True)  # Проверка прав пользователя
async def cmd_kick(interaction: discord.Interaction, map_name: str, activated: int=None, min_players: int=None, max_players: int=None, priority: int=None):
    if not map_name.strip():
    	await interaction.response.send_message('Введите название карты', ephemeral=True)
    	return
    	
    if not update_map(map_name, activated, min_players, max_players, priority):
        await interaction.response.send_message(f'Не удалось обновить карту: {map_name}', ephemeral=True)
        return
    
    if activated:
        add_map_to_active(map_name)
    else:
    		del_map_from_active(map_name)
    
    await interaction.response.send_message(f'Карта {map_name} обновлена', ephemeral=True)

#-------------------------------------------------------------------