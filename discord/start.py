import bot_events
from bot_events import *

if __name__ == "__main__":
		try:
		    r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=0)
		    r.ping()  # Проверяем подключение
		    logging.info("Связь с Redis установлена")
		except redis.ConnectionError as e:
		    logging.error(f"Ошибка при подключении к Redis: {e}")
		finally:
		    r.close()
		    
		bot.run(config.BOT_TOKEN)