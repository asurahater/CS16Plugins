
# ULTRAHC Damager Plugin

### Version: 0.1

### Author: Asura

## Overview

The **ULTRAHC Damager** plugin for AMX Mod X tracks the total damage dealt by a player within the last 3 seconds and displays it in the player's HUD. This plugin uses ReGameDLL (ReAPI) to hook into damage events and provide real-time feedback.

## Features

- **Damage Accumulation**: Tracks the damage a player deals within 3 seconds.
- **HUD Display**: Shows cumulative damage in real-time in a red HUD message.
- **HUD Clearing**: Clears old HUD messages before updating with new damage numbers.
- **Efficient Hooking**: Uses ReAPI hook chains to intercept damage events accurately.

## Installation

1. Install AMX Mod X and ReAPI on your Counter-Strike 1.6 server.
2. Place the `.sma` source file into `amxmodx/scripting`.
3. Compile the plugin and move the `.amxx` file into `amxmodx/plugins`.
4. Add the plugin's name to `plugins.ini`.
5. Restart the server or change the map.

## How It Works

- The plugin hooks into the `CBasePlayer::TakeDamage` function using ReAPI hook chains.
- Damage dealt by the player is accumulated over 3 seconds and displayed on the HUD.
- If no damage is dealt within 3 seconds, the counter resets.

## Dependencies

- **AMX Mod X 1.10+**
- **ReAPI (ReGameDLL)**

## Changelog

**v0.1**:
- Initial release with damage accumulation and HUD display features.

## Future Improvements

- Add customization options for reset time and HUD formats.
- Add sound notifications alongside HUD damage display.

---

# Плагин ULTRAHC Damager

### Версия: 0.1

### Автор: Asura

## Описание

**ULTRAHC Damager** — это плагин для AMX Mod X, который отслеживает суммарный урон, нанесённый игроком за последние 3 секунды, и отображает его на экране HUD. Плагин использует ReGameDLL (ReAPI) для перехвата событий нанесения урона и предоставляет игрокам обратную связь в режиме реального времени.

## Особенности

- **Накопление урона**: Отслеживает нанесённый урон игроком за 3 секунды.
- **Отображение на HUD**: Показывает суммарный урон в режиме реального времени в красном сообщении HUD.
- **Очистка HUD**: Очищает старые сообщения HUD перед обновлением информации.
- **Эффективное перехватывание**: Использует цепочки хуков ReAPI для точного перехвата событий нанесения урона.

## Установка

1. Установите AMX Mod X и ReAPI на сервер Counter-Strike 1.6.
2. Поместите исходный файл `.sma` в папку `amxmodx/scripting`.
3. Скомпилируйте плагин и переместите `.amxx` файл в папку `amxmodx/plugins`.
4. Добавьте название плагина в файл `plugins.ini`.
5. Перезапустите сервер или смените карту.

## Как это работает

- Плагин перехватывает функцию `CBasePlayer::TakeDamage`, используя цепочки хуков ReAPI.
- Нанесённый урон суммируется в течение 3 секунд и отображается на экране HUD.
- Если в течение 3 секунд урон не был нанесён, счётчик сбрасывается.

## Зависимости

- **AMX Mod X 1.10+**
- **ReAPI (ReGameDLL)**

## История изменений

**v0.1**:
- Первый выпуск с функциями накопления урона и отображения на HUD.

## Будущие улучшения

- Добавление опций настройки времени сброса и форматов HUD.
- Внедрение звуковых уведомлений при отображении урона.

