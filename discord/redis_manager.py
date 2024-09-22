import bot
from bot import *

import json

import redis

class RedisDB:
    map_list = 0
    bans = 1
    last_players = 2
    
    ban_list = "ban_list"
    offline_players_list = 'offline_players'

#-------------------------------------------------------------------
#-- Игроки
#-------------------------------------------------------------------

def add_player_to_redis(player_name, steam_id):
    r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=RedisDB.last_players)
    
    try:
        # Сохраняем информацию о игроке в Redis
        r.set(steam_id, player_name)  # Сохраняем имя игрока по ключу steam_id
        
        # Удаляем steam_id из списка, если он уже существует
        r.lrem(RedisDB.offline_players_list, 0, steam_id)  # Удаляем все вхождения steam_id из списка
        
        # Добавляем steam_id в конец списка последних игроков
        r.rpush(RedisDB.offline_players_list, steam_id)  # Добавляем в конец списка
        
        return True
        
    except redis.RedisError as e:
        logging.error(f"Ошибка при добавлении игрока в Redis: {e}")
        return False
        
    finally:
        r.close()  # Закрываем соединение. Выполняется даже после return
  
def remove_player_from_redis(steam_id):
    r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=RedisDB.last_players)
    
    try:
        # Удаляем игрока из Redis
        r.delete(steam_id)  # Удаляем имя игрока по ключу steam_id
        
        # Удаляем steam_id из списка последних игроков
        r.lrem(RedisDB.offline_players_list, 0, steam_id)  # Удаляем все вхождения steam_id из списка
        
        return True
        
    except redis.RedisError as e:
        logging.error(f"Ошибка при удалении игрока из Redis: {e}")
        return False
        
    finally:
        r.close()  # Закрываем соединение. Выполняется даже после return


# def get_last_players_from_redis():
#     r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=RedisDB.last_players)
    
#     try:
#         # Получаем все steam_id из списка
#         last_players = r.lrange(RedisDB.offline_players_list, 0, -1)  # Получаем все элементы списка
#         return [steam_id.decode('utf-8') for steam_id in last_players]  # Декодируем байты в строки
        
#     except redis.RedisError as e:
#         logging.error(f"Ошибка при получении последних игроков из Redis: {e}")
#         return []
        
#     finally:
#         r.close()  # Закрываем соединение. Выполняется даже после return

def get_non_current_players(current_players):
    r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=RedisDB.last_players)
    
    try:
        # Получаем последние 58 steam_id из списка последних игроков
        last_players = r.lrange(RedisDB.offline_players_list, -58, -1)  # Получаем последние 58 элементов списка
        last_players_set = {steam_id.decode('utf-8') for steam_id in last_players}  # Декодируем и преобразуем в множество
        
        # Извлекаем steam_id из current_players
        current_players_set = {player['steam_id'] for player in current_players}  # Предполагаем, что steam_id находится в ключе 'steam_id'
        
        # Находим элементы, которые есть в last_players, но отсутствуют в current_players
        non_current_players = list(last_players_set - current_players_set)
        
        # Создаем массив объектов с player_name и steam_id
        result = []
        for steam_id in non_current_players:
            player_name = r.get(steam_id)  # Получаем имя игрока по steam_id
            if player_name:
                player_name = player_name.decode('utf-8')  # Декодируем имя игрока
            else:
                player_name = 'unnamed'  # Если имя отсутствует, устанавливаем 'unnamed'
            
            result.append({
                'steam_id': steam_id,
                'player_name': player_name
            })
        
        logging.info(result)
        return result[:25]  # Возвращаем только первые 25 игроков
        
    except redis.RedisError as e:
        logging.error(f"Ошибка при получении не текущих игроков из Redis: {e}")
        return []
        
    finally:
        r.close()  # Закрываем соединение. Выполняется даже после return

#-------------------------------------------------------------------
#-- Баны
#-------------------------------------------------------------------

def add_ban_to_redis(player_name, steam_id, minutes, reason):
    r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=RedisDB.bans)  # Подключение при каждом вызове
    
    try:
        # Создаем объект с информацией о бане
        ban_info = {
            "player_name": player_name,
            "minutes": minutes,
            "reason": reason
        }
        
        # Перезаписываем информацию о бане
        r.hset(steam_id, mapping=ban_info)
        
        # Удаляем steam_id из списка, если он уже существует
        r.lrem(RedisDB.ban_list, 0, steam_id)  # Удаляем все вхождения steam_id из списка
        
        # Добавляем steam_id в конец списка банов
        r.rpush(RedisDB.ban_list, steam_id)  # Добавляем в конец списка
        
        return True
        
    except redis.RedisError as e:
        logging.error(f"Ошибка при добавлении бана в Redis: {e}")
        return False
        
    finally:
        r.close()  # Закрываем соединение. Выполняется даже после return
        
def remove_ban_from_redis(steam_id):
    r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=RedisDB.bans)  # Подключение при каждом вызове
    
    try:
        # Получаем информацию о бане перед удалением
        ban_info = r.hgetall(steam_id)
        
        if ban_info:
            player_name = ban_info.get(b'player_name')  # Получаем player_name
            # Удаляем запись по steam_id
            r.delete(steam_id)
            r.lrem(RedisDB.ban_list, 1, steam_id)
            return player_name.decode('utf-8') if player_name else None  # Возвращаем player_name в виде строки
        
        return None  # Запись не найдена
        
    except redis.RedisError as e:
        logging.error(f"Ошибка при удалении бана из Redis: {e}")
        return False
        
    finally:
        r.close()  # Закрываем соединение. Выполняется даже после return


        
def get_last_bans_from_redis(limit=25):
    r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=RedisDB.bans)
    
    try:
        # Получаем последние limit записей из ban_list
        last_ids = r.lrange(RedisDB.ban_list, -limit, -1)
        players = []
        
        for steam_id in last_ids:
            player_info = r.hgetall(steam_id)
            if player_info:  # Проверяем, есть ли информация о игроке
                player_name = player_info.get(b'player_name', b'').decode('utf-8')
                minutes = int(player_info.get(b'minutes', 0))
                reason = player_info.get(b'reason', b'').decode('utf-8')
                
                players.append({
                    'steam_id': steam_id.decode('utf-8'),
                    'player_name': player_name,
                    'minutes': minutes,
                    'reason': reason,
                })
        
        return players
    
    except redis.RedisError as e:
        logging.error(f"Ошибка при получении последних банов из Redis: {e}")
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