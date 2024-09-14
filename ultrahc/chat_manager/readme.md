# ULTRAHC Chat Manager Plugin

### Version: 0.5

### Author: Asura

## Overview

The **ULTRAHC Chat Manager** plugin for AMX Mod X enhances the chat functionality on your Counter-Strike 1.6 server by providing custom prefixes, managing chat visibility, and integrating with SQL. This plugin allows for a highly customizable chat experience, including prefix assignment, message formatting, and team-based chat visibility.

## Features

- **Custom Prefixes**: Assign up to 4 custom prefixes to each player, with support for Steam, name-based, or flag-based prefixes.
- **Chat Management**: Control who can see specific chats, including dead/alive and team chat segregation.
- **SQL Integration**: Save chat logs to a MySQL database for analytics or tracking purposes.
- **Configurable Cvars**: Various configuration options to control prefix format, visibility, and more.

## Installation

1. Ensure AMX Mod X, ReAPI, and SQLx are installed on your Counter-Strike 1.6 server.
2. Place the `.sma` file in the `amxmodx/scripting` folder.
3. Compile the plugin and move the compiled `.amxx` file to the `amxmodx/plugins` folder.
4. Add `ultrahc_chat_manager.amxx` to your `plugins.ini` file.
5. Restart your server or change the map to apply the changes.

## How It Works

- **Prefix System**: Players can have up to 4 custom prefixes, which are displayed in chat messages.
- **SQL Integration**: Chat messages can be saved in a MySQL database for future retrieval.
- **Cvars**: Administrators can configure the behavior of the plugin through Cvars, such as toggling SQL integration, controlling which teams can see which messages, and more.

## Configuration

- **Prefix Configuration**: Modify the prefix file (`ultrahc_prefix.ini`) to define custom prefixes for players based on their name, SteamID, or access flags.
- **Cvars**: Use the following Cvars to configure the plugin:
  - `ultrahc_use_sql` (0/1): Enable or disable SQL logging.
  - `ultrahc_sql_host`, `ultrahc_sql_user`, `ultrahc_sql_pass`, `ultrahc_sql_db`: SQL database connection information.
  - `ultrahc_admin_see_all`: Whether admins can see all chat.
  - `ultrahc_alive_see_deads`: Whether alive players can see dead players' chat.

## Changelog

**v0.5**:
- Initial release with chat management, SQL integration.

## Future Improvements

- Add more flexible options for prefix customization.
- Implement advanced filtering for SQL logs.

---

# Плагин ULTRAHC Chat Manager

### Версия: 0.5

### Автор: Asura

## Описание

**ULTRAHC Chat Manager** — это плагин для AMX Mod X, который улучшает функциональность чата на сервере Counter-Strike 1.6. Он позволяет настраивать пользовательские префиксы, управлять видимостью чата, интегрироваться с базой данных SQL для сохранения чатов. Это обеспечивает высокую кастомизацию чата и контроль за его отображением.

## Особенности

- **Пользовательские префиксы**: Игроки могут иметь до 4 префиксов, основанных на их SteamID, имени или флагах доступа.
- **Управление чатом**: Управление видимостью чатов, разделение на мертвых/живых и чат команды.
- **Интеграция с SQL**: Сохранение логов чатов в базу данных MySQL для аналитики и отслеживания.
- **Настраиваемые Cvars**: Различные опции настройки плагина через переменные Cvar.

## Установка

1. Убедитесь, что на вашем сервере установлены AMX Mod X, ReAPI и SQLx.
2. Поместите файл `.sma` в папку `amxmodx/scripting`.
3. Скомпилируйте плагин и переместите скомпилированный файл `.amxx` в папку `amxmodx/plugins`.
4. Добавьте `ultrahc_chat_manager.amxx` в файл `plugins.ini`.
5. Перезапустите сервер или смените карту для применения изменений.

## Как это работает

- **Система префиксов**: Игроки могут иметь до 4 пользовательских префиксов, которые будут отображаться в их сообщениях в чате.
- **Интеграция с SQL**: Сообщения чата сохраняются в базе данных MySQL для последующего анализа.
- **Cvars**: Администраторы могут настраивать поведение плагина с помощью переменных Cvar, таких как включение/выключение SQL, управление видимостью сообщений и многое другое.

## Настройка

- **Конфигурация префиксов**: Измените файл префиксов (`ultrahc_prefix.ini`), чтобы задать префиксы для игроков на основе их имени, SteamID или флагов доступа.
- **Cvars**: Используйте следующие переменные Cvar для настройки плагина:
  - `ultrahc_use_sql` (0/1): Включить или отключить запись чатов в базу данных SQL.
  - `ultrahc_sql_host`, `ultrahc_sql_user`, `ultrahc_sql_pass`, `ultrahc_sql_db`: Информация для подключения к базе данных SQL.
  - `ultrahc_admin_see_all`: Администраторы могут видеть все сообщения.
  - `ultrahc_alive_see_deads`: Живые игроки могут видеть чат мертвых игроков.

## История изменений

**v0.5**:
- Первоначальный выпуск с управлением чатом, интеграцией SQL.

## Будущие улучшения

- Добавить более гибкие опции настройки префиксов.
- Реализовать расширенные фильтры для логов SQL.
