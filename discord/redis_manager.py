import bot
from bot import *

import json

import redis

class RedisDB:
    map_list = 0
    bans = 1

#-------------------------------------------------------------------
#-- Баны
#-------------------------------------------------------------------

def add_ban_to_redis(player_name, steam_id, minutes, reason):
    r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=RedisDB.bans)  # Подключение при каждом вызове
    
    try:
        # Создаем объект с информацией о бане
        ban_info = {
            "player_name": player_name,
            "steam_id": steam_id,
            "minutes": minutes,
            "reason": reason
        }
        # Сериализуем объект в JSON и добавляем в общий список "bans"
        r.rpush("bans", json.dumps(ban_info))
        return True
        
    except redis.RedisError as e:
        logging.error(f"Ошибка при добавлении бана в Redis: {e}")
        return False
        
    finally:
        r.close()  # Закрываем соединение. Выполняется даже после return
        
def remove_ban_from_redis(steam_id):
    r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=RedisDB.bans)  # Подключение при каждом вызове
    user_name = None
    
    try:
        # Извлекаем все баны
        bans = r.lrange("bans", 0, -1)
        updated_bans = []

        # Флаг для проверки, был ли удален бан
        ban_removed = False

        for ban in bans:
            # Декодируем байтовую строку в строку
            ban_info = json.loads(ban.decode('utf-8'))  # Декодируем и десериализуем
            if ban_info["steam_id"] == steam_id:
                user_name = ban_info["player_name"]
                ban_removed = True  # Устанавливаем флаг, если бан был найден
                continue  # Пропускаем добавление этого бана в новый список
            updated_bans.append(ban)  # Добавляем бан в новый список, если он не удаляется

        # Если бан был удален, обновляем список в Redis
        if ban_removed:
            r.delete("bans")  # Удаляем старый список
            if updated_bans:  # Проверяем, не пуст ли обновленный список
                r.rpush("bans", *updated_bans)  # Добавляем обновленный список

        return user_name if user_name else False  # Возвращаем имя игрока, если бан был удален, иначе False
        
    except redis.RedisError as e:
        logging.error(f"Ошибка при удалении бана из Redis: {e}")
        return False
        
    finally:
        r.close()  # Закрываем соединение. Выполняется даже после return

        
def get_last_bans_from_redis():
    r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=RedisDB.bans)  # Подключение к Redis
    
    try:
        # Получаем последние 25 записей из общего списка "bans"
        last_bans = r.lrange("bans", -25, -1)
        # Декодируем байты в строки и десериализуем JSON в объекты
        return [json.loads(ban.decode('utf-8')) for ban in last_bans]
        
    except redis.RedisError as e:
        logging.error(f"Ошибка при получении банов из Redis: {e}")
        return []
        
    finally:
        r.close()  # Закрываем соединение. Выполняется даже после return
        
#-------------------------------------------------------------------
#-- Карты
#-------------------------------------------------------------------

# Функция для добавления названия карты
def add_map_to_redis(map_name, active):
    r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=RedisDB.map_list)  # Подключение при каждом вызове
    try:
        if active not in (0, 1):
            return False

        result = r.set(map_name, active, nx=True)
        
        if result:
            return True
        else:
            return False
    finally:
        r.close()  # Закрываем соединение. Выполняется даже после return


def delete_map_from_redis(map_name):
    r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=RedisDB.map_list)  # Подключение при каждом вызове
    try:
        # Удаляем карту по имени
        result = r.delete(map_name)
        
        if result > 0:
            return True
        else:
            return False
    finally:
        r.close()  # Закрываем соединение в любом случае
        
def update_map_value_in_redis(map_name, active):
    r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=RedisDB.map_list)  # Подключение при каждом вызове
    try:
        # Проверяем, что значение active корректно
        if active not in (0, 1):
            return False

        # Обновляем значение карты
        result = r.set(map_name, active)
        
        if result:
            return True
        else:
            return False
    finally:
        r.close()  # Закрываем соединение в любом случае

def load_map_data_from_redis():
    # Подключаемся к Redis
    r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=RedisDB.map_list)

    # Получаем все ключи (названия карт)
    map_names = r.keys()
    
    # Создаем массивы для всех карт и для активных карт
    all_maps = []
    active_maps = []

    for map_name in map_names:
        map_name_decoded = map_name.decode('utf-8')  # Декодируем байтовую строку в строку
        all_maps.append(map_name_decoded)
        
        # Получаем значение для текущей карты
        active = r.get(map_name).decode('utf-8')  # Декодируем значение
        if active == '1':
            active_maps.append(map_name_decoded)
            
    r.close()
		
    return all_maps, active_maps