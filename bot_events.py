import bot_commands
from bot_commands import *

#-------------------------------------------------------------------
#-- События
#-------------------------------------------------------------------

@bot.event
async def on_ready():
    logging.info(f'Бот {bot.user.name} v{config._VERSION_} успешно запущен!')
    
    # Подготовка базы данных при запуске
    setup_database()
    
    # Запуск веб-сервера и подключение к CS
    try:
        bot.loop.create_task(run_webserver())
        bot.loop.create_task(connect_to_cs())
        
        channel = bot.get_channel(config.INFO_CHANNEL_ID)
        await channel.purge(limit=10)
        
    except Exception as e:
        logging.error(f"Ошибка при запуске задач: {e}")
    
    status_task.start()

# Регистрация команд
@bot.event
async def setup_hook():
    guild = bot.get_guild(config.GUILD_ID)
    await bot.tree.sync(guild=guild)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.id == config.CS_CHAT_CHNL_ID:
        set_user_message_received(True)
        send_msg = "\"" + message.author.display_name + "\"" + " " + "\"" + message.content + "\""
        srv.execute(f"ultrahc_ds_send_msg {send_msg}")

    await bot.process_commands(message)

@bot.event
async def on_member_update(before, after):
    if before.display_name == after.display_name:
        return

    try:
        connection = connect_to_mysql()
        if not connection:
            return
        
        cursor = connection.cursor()
        query = "UPDATE users SET ds_display_name = %s WHERE discord_id = %s"
        cursor.execute(query, (after.display_name, str(after.id)))
        connection.commit()
    except Exception as e:
        logging.error(f"Ошибка при обновлении ds_display_name: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
