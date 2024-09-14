import bot_web_hooks
from bot_web_hooks import *

#-------------------------------------------------------------------
#-- Общие команды
#-------------------------------------------------------------------

#-- /clear
#-- Чистит канал от n сообщений
#-- @params n (degault=100)
@bot.tree.command(name="clear", description="Удаляет сообщения в канале.")
@discord.app_commands.describe(amount="Количество сообщений для удаления")
@commands.has_permissions(manage_messages=True) 
async def clear(interaction: discord.Interaction, amount: int = 100):
    channel = interaction.channel
    if channel is not None:
        deleted = await channel.purge(limit=amount)
        await interaction.response.send_message(f'Удалено {len(deleted)} сообщений.', ephemeral=True)
    else:
        await interaction.response.send_message('Канал не найден.', ephemeral=True)

#-- /connect_to_cs
#-- Подсоединяется к серверу
@bot.tree.command(name="connect_to_cs", description="Подключается к серверу.")
@commands.has_permissions(manage_messages=True)  # Проверка прав пользователя
async def connect(interaction: discord.Interaction):
    if srv.is_connected:
		    await interaction.response.send_message('Сервер уже подключен', ephemeral=True)
		    return
		    
    # Вызываем функцию подключения к серверу
    try:
        await connect_to_cs()
        await interaction.response.send_message("Успешно подключено к серверу!", ephemeral=True)
    except Exception as e:
        logging.error(f"Ошибка при подключении к серверу: {e}")
        await interaction.response.send_message('Ошибка при подключении к серверу. Проверьте логи.', ephemeral=True)

#-------------------------------------------------------------------
#-- Команды для регистрации игроков
#-------------------------------------------------------------------

#-- /reg
#-- Добавляет в БД дискорд айди игрока и связывает его с стим айди
#-- @params steam_id
@bot.tree.command(name="reg", description="Регистрация пользователя с указанием steam_id")
async def reg(interaction: discord.Interaction, steam_id: str):
    if interaction.channel.id != config.REG_CHANNEL_ID:
    		return  # Отключаем выполнение команды в других каналах
    
    user_id = str(interaction.user.id)
    username = interaction.user.name
    ds_username = interaction.user.display_name

    # Проверяем, существует ли запись
    if record_exists(user_id, steam_id):
        await interaction.response.send_message(f'Ошибка: Данные для Steam ID {steam_id} или вашего аккаунта уже существуют.', ephemeral=True)
    else:
        # Сохраняем сообщение в базу данных
        save_message(user_id, username, ds_username, steam_id)
        await interaction.response.send_message(f'Данные сохранены: {username}')

#-- /remove
#-- Удаляет из БД данные юзера по дискорд айди
#-- no params
@bot.tree.command(name="remove", description="Удаляет данные пользователя по Discord ID.")
async def remove(interaction: discord.Interaction):
    if interaction.channel.id != config.REG_CHANNEL_ID:
    		return  # Отключаем выполнение команды в других каналах
    
    user_id = str(interaction.user.id)

    # Создаем подключение к базе данных
    connection = create_connection()
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
async def status(interaction: discord.Interaction):
    if interaction.channel.id != config.INFO_CHANNEL_ID:
        return  # Отключаем выполнение команды в других каналах
    
    # Отправляем команду на сервер
    try:
        srv.execute("ultrahc_ds_get_info")  # Выполняем команду на сервере
        await interaction.response.send_message('Команда выполнена.', ephemeral=True, delete_after=0)
    except Exception as e:
        logging.error(f"Ошибка при получении статуса сервера: {e}")
        await interaction.response.send_message('Ошибка при получении статуса сервера. Проверьте логи.', ephemeral=True)

#-------------------------------------------------------------------
#-- Команды для server manager
#-------------------------------------------------------------------

#-- /change_map
#-- Меняет карту
#-- @params: map_name
@bot.tree.command(name="change_map", description="Меняет карту на удаленном сервере.")
@discord.app_commands.describe(map_name="Название карты для смены")
@commands.has_permissions(manage_messages=True)  # Проверка прав пользователя
async def srv_change_map(interaction: discord.Interaction, map_name: str = None):
    if interaction.channel.id != config.SRV_MNGR_CHANNEL_ID:
        return  # Отключаем выполнение команды в других каналах
    
    # Формируем команду для смены карты
    if map_name:
    		command = f"ultrahc_ds_change_map {map_name}"
    else:
    		command = "ultrahc_ds_change_map"
		
    # Отправляем команду на сервер
    try:
        srv.execute(command)
        user_nick = interaction.user.display_name
        nick_color = '\x1b[34m'  # Голубой
        reset_color = '\x1b[0m'
        if map_name:
        	await interaction.response.send_message(f"```ansi\n{nick_color}{user_nick}{reset_color} сменил карту на: {map_name}```")
        else:
        	await interaction.response.send_message(f"```ansi\n{nick_color}{user_nick}{reset_color} перезагрузил карту```")
    except Exception as e:
        logging.error(f"Ошибка при смене карты: {e}")
        await interaction.response.send_message('Ошибка при смене карты. Проверьте логи.', ephemeral=True)

#-- /kick
#-- Кикает игрока с сервера
#-- @params player_nick, reason
@bot.tree.command(name="kick", description="Кикает игрока с сервера.")
@discord.app_commands.describe(player_nick="Ник игрока", reason="Причина кика")
@commands.has_permissions(manage_messages=True)  # Проверка прав пользователя
async def kick(interaction: discord.Interaction, player_nick: str, reason: str):
    if interaction.channel.id != config.SRV_MNGR_CHANNEL_ID:
        return  # Отключаем выполнение команды в других каналах
    
    # Формируем команду для кика игрока
    command = f"ultrahc_ds_kick_player {player_nick} {reason}"
    
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
O
#-------------------------------------------------------------------