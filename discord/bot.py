import discord
from discord.ext import commands, tasks
from aiohttp import web
from datetime import datetime  # Для добавления timestamp
from rehlds.console import Console
import config
import logging
import mysql.connector
from mysql.connector import errorcode

# Настройка логирования
logging.basicConfig(level=logging.INFO)

srv = Console(host=config.CS_HOST, password=config.CS_RCON_PASSWORD)

app = web.Application()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)

# Запуск веб-сервера
async def run_webserver():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, config.WEB_HOST_ADDRESS, config.WEB_SERVER_PORT)
    await site.start()
    logging.info(f"Web server started at {config.WEB_HOST_ADDRESS}:{config.WEB_SERVER_PORT}")

# Подключение к серверу CS
async def connect_to_cs():
    try:
        await srv.connect()
        logging.info("Successfully connected to CS server.")
    except Exception as e:
        logging.error(f"Ошибка при соединении с сервером: {e}")

# Периодическое задание для обновления статуса
@tasks.loop(seconds=config.STATUS_INTERVAL)  # Задача будет выполняться каждые 10 секунд
async def status_task():
    if not srv.is_connected:
        return
    try:
        srv.execute("ultrahc_ds_get_info")
    except Exception as e:
        logging.error(f"Ошибка при получении данных с сервера: {e}")

@status_task.before_loop
async def before_status_task():
    await bot.wait_until_ready()