import discord
from discord.ext import commands
from discord.ext import tasks

from aiohttp import web
from datetime import datetime  # Для добавления timestamp

from rehlds.console import Console

import config
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)

srv = Console(host='127.0.0.1', password='12345')

app = web.Application()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)

#-------------------------------------------------------------------

async def run_webserver():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

async def connect_to_cs():
	try:
		await srv.connect()
	except Exception as e:
		logging.error(f"Ошибка при соединении с сервером: {e}")

@bot.event
async def on_ready():
    logging.info(f'Бот {bot.user.name} успешно запущен!')
    bot.loop.create_task(run_webserver())
    bot.loop.create_task(connect_to_cs())
    status_task.start()
    
@tasks.loop(seconds=config.STATUS_INTERVAL)  # Задача будет выполняться каждые 10 секунд
async def status_task():
    if not srv.is_connected:
        return
		
    try:
    		srv.execute("ultrahc_ds_get_info")
    except Exception as e:
    		logging.error(f"Ошибка при соединении с сервером: {e}")
    
@status_task.before_loop
async def before_status_task():
    await bot.wait_until_ready()

# Регистрация команд
@bot.event
async def setup_hook():
    await bot.tree.sync()