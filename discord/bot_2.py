import discord
from discord.ext import commands
from aiohttp import web
import logging
import config  # Импортируем файл config.py
from datetime import datetime  # Для добавления timestamp
from rHLDS import Console

srv = Console(host='127.0.0.1', password='12345')
srv.connect()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

current_message = None
line_count = 0
MAX_LINES = 50
MAX_CHAR_LIMIT = 2000  # Лимит символов в Discord для одного сообщения
user_message_received = False

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

    # Добавляем пробел только если префикс не пустой
    prefix_with_space = f"{channel_prefix} " if channel_prefix else ""

    # Форматируем сообщение с timestamp, префиксом канала, ником и его цветом
    return f"{timestamp_color}{timestamp}{reset_color} {prefix_with_space}{nick_color}{nick}{reset_color}: {message}\n"

# Функция для проверки API-ключа
def check_api_key(request):
    api_key = request.headers.get('Authorization')  # Извлекаем ключ из заголовка
    if api_key == config.API_KEY:
        return True
    else:
        logging.warning("Неверный API-ключ")
        return False

# Обработчик вебхуков с проверкой API-ключа
async def handle_webhook(request):
    global current_message, line_count, user_message_received

    # Проверяем API-ключ перед обработкой запроса
    if not check_api_key(request):
        return web.Response(text='Unauthorized', status=401)

    logging.info("Получен вебхук")

    data = await request.json()
    cs_message = data.get('message')
    nick = data.get('nick')
    team = data.get('team')
    channel_prefix = data.get('channel', '')  # Получаем префикс канала

    if cs_message and nick and team is not None:
        formatted_message = format_message(nick, cs_message, team, channel_prefix)
        logging.info(f"Сообщение из CS: {formatted_message}")

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
                channel = bot.get_channel(config.CHANNEL_ID)
                if channel is None:
                    logging.error("Канал не найден. Проверьте правильность CHANNEL_ID в config.py.")
                else:
                    # Отправляем новое сообщение
                    current_message = await channel.send(f"```ansi\n{formatted_message}```")
                    logging.info("Новое сообщение отправлено в Discord")
                    line_count = 1  # Сбрасываем счётчик строк
                    user_message_received = False  # Сбрасываем флаг пользователя
            except Exception as e:
                logging.error(f"Ошибка при отправке сообщения в Discord: {e}")

    return web.Response(text='OK')

app = web.Application()
app.router.add_post('/webhook', handle_webhook)

@bot.event
async def on_message(message):
    global user_message_received

    if message.author == bot.user:
        return

    if message.channel.id == config.CHANNEL_ID:
        logging.info("Получено сообщение от пользователя")
        user_message_received = True
        send_msg = message.author.display_name + " " + "\"" + message.content + "\""
        srv.execute(f"ultrahc_ds_send_msg {send_msg}")
				# await message.delete()

    await bot.process_commands(message)

async def run_webserver():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

@bot.event
async def on_ready():
    logging.info(f'Бот {bot.user.name} успешно запущен!')
    bot.loop.create_task(run_webserver())

bot.run(config.BOT_TOKEN)
