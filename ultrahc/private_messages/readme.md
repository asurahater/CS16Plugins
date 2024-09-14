# ULTRAHC Private Messages Plugin

### Version: 0.1

### Author: Asura

## Overview

The **ULTRAHC Private Messages** plugin for AMX Mod X allows players on a Counter-Strike 1.6 server to send private messages to each other. The plugin provides a menu-based system for selecting a recipient, and it includes a similarity-based search for finding player names quickly. It also supports saving private messages to a database if configured.

## Features

- **Private Messaging**: Players can send private messages to others on the server.
- **Menu System**: A menu interface helps players select recipients for their private messages.
- **Name Similarity Search**: A search system based on the Dice-Sørensen coefficient helps players find recipients based on partial name matches.
- **Database Logging**: Optionally save private messages to a database for future reference or moderation purposes.

## Installation

1. Place the `.sma` file in the `amxmodx/scripting` directory.
2. Compile the plugin and move the `.amxx` file to the `amxmodx/plugins` folder.
3. Add `ultrahc_private_messages.amxx` to your `plugins.ini` file.
4. Restart your server or change the map.

## How It Works

- **Private Message Mode**: Players type `/pm` in the chat to open the private messaging menu. They can either choose a recipient from a full list of players or search for a specific player by name.
- **Name Matching**: If a partial name is provided, the plugin uses the Dice-Sørensen coefficient to suggest players whose names closely match the input.
- **Database Saving**: If enabled, the plugin will save all private messages to a MySQL database, using the `ultrahc_chat_manager` for SQL interaction.

## Configuration

- **Cvars**:
  - `ultrahc_private_save_db` (0/1): Enable or disable saving private messages to the database.
  - `ultrahc_private_name_coeff` (0.0 to 1.0): The coefficient used for name similarity in the player search menu.

## Changelog

**v0.1**:
- Initial release with private messaging, menu selection, name similarity search, and optional database saving.

## Future Improvements

- Allow for customization of message formatting and additional recipient search options.

---

# Плагин ULTRAHC Личные Сообщения

### Версия: 0.1

### Автор: Asura

## Описание

**ULTRAHC Private Messages** — это плагин для AMX Mod X, который позволяет игрокам на сервере Counter-Strike 1.6 отправлять личные сообщения друг другу. Плагин предоставляет систему меню для выбора получателя, а также использует систему поиска по частичному совпадению имен. Он также поддерживает сохранение личных сообщений в базу данных, если это настроено.

## Особенности

- **Личные сообщения**: Игроки могут отправлять личные сообщения другим игрокам на сервере.
- **Система меню**: Интерфейс меню помогает игрокам выбирать получателей для личных сообщений.
- **Поиск по частичному совпадению имен**: Система поиска, основанная на коэффициенте сходства Дайса-Сёренсена, помогает игрокам находить получателей по частичному совпадению имен.
- **Сохранение в базе данных**: По желанию можно сохранять личные сообщения в базу данных для последующего анализа или модерации.

## Установка

1. Поместите файл `.sma` в папку `amxmodx/scripting`.
2. Скомпилируйте плагин и переместите `.amxx` файл в папку `amxmodx/plugins`.
3. Добавьте `ultrahc_private_messages.amxx` в файл `plugins.ini`.
4. Перезапустите сервер или смените карту.

## Как это работает

- **Режим личных сообщений**: Игроки вводят команду `/pm` в чате, чтобы открыть меню личных сообщений. Они могут либо выбрать получателя из списка всех игроков, либо искать конкретного игрока по имени.
- **Совпадение имен**: Если введено частичное имя, плагин использует коэффициент Дайса-Сёренсена для предложений игроков, чьи имена наиболее близки к введенному.
- **Сохранение в базе данных**: Если включено, плагин сохранит все личные сообщения в базу данных MySQL, используя взаимодействие с `ultrahc_chat_manager` для работы с SQL.

## Настройка

- **Cvars**:
  - `ultrahc_private_save_db` (0/1): Включить или отключить сохранение личных сообщений в базу данных.
  - `ultrahc_private_name_coeff` (0.0 до 1.0): Коэффициент, используемый для поиска по совпадению имен в меню.

## История изменений

**v0.1**:
- Первый выпуск с функциями личных сообщений, меню для выбора игроков, поиска по совпадению имен и сохранением в базу данных.

## Будущие улучшения

- Добавить возможности кастомизации формата сообщений и улучшить поиск получателей.
