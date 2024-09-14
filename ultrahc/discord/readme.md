# ULTRAHC Discord Message Parser

### Version: 1.0

### Author: Asura

## Overview

The **ULTRAHC Discord Message Parser** plugin for AMX Mod X allows your Counter-Strike 1.6 server to receive messages from a Discord bot via RCON and display them in the in-game chat. This functionality bridges communication between Discord and in-game players, making it easier to relay important information or engage with the players in real-time.

## Features

- **Discord to In-Game Messaging**: Receive messages sent by a Discord bot via RCON and display them in the in-game chat.
- **Formatted Messages**: Messages are displayed with a `[DISCORD]` tag, making it clear that the message originated from Discord.
- **Customizable**: Modify the message formatting in the source code to suit your needs.

## Installation

1. Place the `.sma` file in the `amxmodx/scripting` directory.
2. Compile the plugin and move the `.amxx` file to the `amxmodx/plugins` folder.
3. Add `ultrahc_discord_parser.amxx` to your `plugins.ini` file.
4. Restart your server or change the map.

## How It Works

- A Discord bot sends a message via RCON to the server.
- The plugin captures the message, parses it into an author and message format, and prints it to the in-game chat with a Discord tag.
- Players in the game can now see messages sent from Discord.

## Commands

- `ultrahc_ds_send_msg`: This command is executed when a message is sent from Discord to the server. The message is parsed and displayed in the in-game chat in the format `[DISCORD] Author: Message`.

## Changelog

**v1.0**:
- Initial release with Discord message parsing and in-game chat display.

## Future Improvements

- Add support for more advanced message parsing and command handling.

---

# ULTRAHC Парсер сообщений Discord

### Версия: 1.0

### Автор: Asura

## Описание

**ULTRAHC Discord Message Parser** — это плагин для AMX Mod X, который позволяет вашему серверу Counter-Strike 1.6 получать сообщения от бота Discord через RCON и отображать их в игровом чате. Эта функция помогает наладить связь между Discord и игроками на сервере, позволяя передавать важную информацию или просто общаться с ними в реальном времени.

## Особенности

- **Передача сообщений из Discord в игру**: Получайте сообщения, отправленные ботом Discord через RCON, и отображайте их в игровом чате.
- **Форматированные сообщения**: Сообщения отображаются с тегом `[DISCORD]`, чтобы было понятно, что сообщение пришло из Discord.
- **Настраиваемые сообщения**: Формат отображения сообщений можно изменить в исходном коде.

## Установка

1. Поместите файл `.sma` в папку `amxmodx/scripting`.
2. Скомпилируйте плагин и переместите `.amxx` файл в папку `amxmodx/plugins`.
3. Добавьте `ultrahc_discord_parser.amxx` в файл `plugins.ini`.
4. Перезапустите сервер или смените карту.

## Как это работает

- Бот Discord отправляет сообщение на сервер через RCON.
- Плагин перехватывает сообщение, разбирает его на автора и текст сообщения, а затем выводит в игровой чат с тегом Discord.
- Игроки в игре могут видеть сообщения, отправленные из Discord.

## Команды

- `ultrahc_ds_send_msg`: Эта команда выполняется, когда сообщение отправлено из Discord на сервер. Сообщение анализируется и отображается в игровом чате в формате `[DISCORD] Автор: Сообщение`.

## История изменений

**v1.0**:
- Первоначальный выпуск с функцией парсинга сообщений из Discord и их отображения в игровом чате.

## Будущие улучшения

- Добавить поддержку более продвинутого парсинга сообщений и обработки команд.
