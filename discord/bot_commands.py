import bot_web_hooks
from bot_web_hooks import *
from bot_web_hooks import current_players

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
#-- Чистит канал от n сообщений
#-- @params n (default=0)
@bot.tree.command(name="clear", description="Удаляет сообщения в канале.")
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
#-- Подсоединяется к серверу
@bot.tree.command(name="connect_to_cs", description="Подключается к серверу.")
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
#-- Добавляет в БД дискорд айди игрока и связывает его с стим айди
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

#-- /remove
#-- Удаляет из БД данные юзера по дискорд айди
#-- no params
@bot.tree.command(name="unreg", description="Удаляет данные пользователя по Discord ID.")
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
@bot.tree.command(name="status", description="Получает информацию о сервере.")
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

@bot.tree.command(name="rcon", description="Отправляет команду в консоль сервера")
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


#-- /reload_maps
#-- Перезагружает карты
#-- @params: map_name
@bot.tree.command(name="reload_maps", description="Перезагружает список карт")
@commands.has_permissions(manage_messages=True)  
async def cmd_reload_maps(interaction: discord.Interaction):
    # Формируем команду для получения списка карт
    command = "ultrahc_ds_get_map_list"
    
    # Отправляем команду на сервер
    try:
        srv.execute(command)
        
        user_nick = interaction.user.display_name
        nick_color = '\x1b[34m'  # Голубой
        reset_color = '\x1b[0m'
        
        await interaction.response.send_message(f"```ansi\n{nick_color}{user_nick}{reset_color} перезагрузил список карт.```")
    except Exception as e:
        logging.error(f"Ошибка при перезагрузке списка карт: {e}")
        await interaction.response.send_message('Ошибка при перезагрузке списка карт. Проверьте логи.', ephemeral=True)

#-- /change_map
#-- Меняет карту
#-- @params: map_name
@bot.tree.command(name="change_map", description="Меняет карту на удаленном сервере.")
@discord.app_commands.describe(map="Название карты")
@discord.app_commands.autocomplete(map=map_autocomplete)
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


#-- /kick
#-- Кикает игрока с сервера
#-- @params player_nick, reason
@bot.tree.command(name="kick", description="Кикает игрока с сервера.")
@discord.app_commands.describe(player_nick="Ник игрока", reason="Причина кика")
@discord.app_commands.autocomplete(player_nick=kick_autocomplete)
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

#-------------------------------------------------------------------