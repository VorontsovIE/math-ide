# Деплой Math IDE на VPS-сервер

Этот документ описывает процесс деплоя Math IDE на Ubuntu VPS-сервер с использованием uv и systemd.

## Предварительные требования

- Ubuntu 20.04+ VPS-сервер
- SSH-доступ с sudo-привилегиями
- GitHub-репозиторий с кодом проекта
- Telegram Bot Token (получить у @BotFather)
- OpenAI API Key

## Быстрый старт

### 1. Подготовка сервера

Подключитесь к серверу по SSH и выполните:

```bash
# Клонируйте репозиторий
git clone https://github.com/your-username/math-ide.git
cd math-ide

# Установите uv
chmod +x scripts/install_uv.sh
./scripts/install_uv.sh

# Перезапустите терминал или выполните
source ~/.bashrc
```

### 2. Настройка переменных окружения

Создайте файл `.env` с вашими настройками:

```bash
# Скопируйте пример
cp docs/env.example .env

# Отредактируйте файл
nano .env
```

Содержимое `.env`:
```env
# Токен Telegram-бота (получить у @BotFather)
TELEGRAM_BOT_TOKEN=your_bot_token_here

# API-ключ OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Модель GPT для использования (опционально)
GPT_MODEL=gpt-4-turbo-preview
```

### 3. Деплой

```bash
# Запустите деплой
chmod +x deploy.sh
./deploy.sh --env-file .env
```

## Детальное описание

### Структура скриптов

- `deploy.sh` - Основной скрипт деплоя
- `scripts/install_uv.sh` - Установка uv на сервере
- `scripts/service_manager.sh` - Управление systemd сервисом

### Опции деплоя

```bash
./deploy.sh [опции]

Опции:
  --env-file PATH    Путь к файлу с переменными окружения
  --branch BRANCH    Ветка для деплоя (по умолчанию: main)
  --service-name NAME Имя systemd сервиса (по умолчанию: math-ide)
  --user USER        Пользователь для запуска сервиса (по умолчанию: $USER)
  --help             Показать справку
```

### Управление сервисом

После деплоя используйте скрипт управления сервисом:

```bash
# Запуск сервиса
./scripts/service_manager.sh start

# Остановка сервиса
./scripts/service_manager.sh stop

# Перезапуск сервиса
./scripts/service_manager.sh restart

# Просмотр статуса
./scripts/service_manager.sh status

# Просмотр логов
./scripts/service_manager.sh logs

# Обновление кода и перезапуск
./scripts/service_manager.sh update
```

## Архитектура деплоя

### Директории

- `/opt/math-ide/` - Основная директория приложения
- `/etc/systemd/system/math-ide.service` - Конфигурация systemd сервиса

### Systemd сервис

Сервис настроен с:
- Автоматическим перезапуском при сбоях
- Логированием в systemd journal
- Ограничениями безопасности
- Загрузкой переменных окружения из `.env`

### Виртуальное окружение

Проект использует uv для управления зависимостями:
- Автоматическое создание виртуального окружения
- Установка зависимостей из `pyproject.toml`
- Изоляция зависимостей проекта

## Мониторинг и логи

### Просмотр логов

```bash
# Логи в реальном времени
sudo journalctl -u math-ide -f

# Последние 100 строк логов
sudo journalctl -u math-ide -n 100

# Логи с определенной даты
sudo journalctl -u math-ide --since "2024-01-01"
```

### Статус сервиса

```bash
# Подробный статус
sudo systemctl status math-ide

# Проверка активности
sudo systemctl is-active math-ide

# Проверка автозапуска
sudo systemctl is-enabled math-ide
```

## Обновление

### Автоматическое обновление

```bash
./scripts/service_manager.sh update
```

Этот скрипт:
1. Останавливает сервис
2. Обновляет код из репозитория
3. Обновляет зависимости
4. Запускает сервис

### Ручное обновление

```bash
# Остановите сервис
sudo systemctl stop math-ide

# Обновите код
cd /opt/math-ide
git pull origin main

# Обновите зависимости
uv sync

# Запустите сервис
sudo systemctl start math-ide
```

## Устранение неполадок

### Сервис не запускается

1. Проверьте логи:
```bash
sudo journalctl -u math-ide -n 50
```

2. Проверьте переменные окружения:
```bash
sudo systemctl show math-ide --property=Environment
```

3. Проверьте права доступа:
```bash
ls -la /opt/math-ide/.env
```

### Проблемы с зависимостями

1. Пересоздайте виртуальное окружение:
```bash
cd /opt/math-ide
rm -rf .venv
uv sync
```

2. Проверьте версию Python:
```bash
python3 --version
```

### Проблемы с Telegram ботом

1. Проверьте токен бота в `.env`
2. Убедитесь, что бот не заблокирован
3. Проверьте логи на наличие ошибок API

## Безопасность

### Рекомендации

1. Используйте отдельного пользователя для запуска сервиса
2. Ограничьте права доступа к файлам конфигурации
3. Регулярно обновляйте систему и зависимости
4. Используйте firewall для ограничения доступа
5. Настройте SSL/TLS для HTTPS (если используется веб-интерфейс)

### Ограничения systemd

Сервис настроен с ограничениями безопасности:
- `NoNewPrivileges=true` - Запрет получения новых привилегий
- `PrivateTmp=true` - Изолированная временная директория
- `ProtectSystem=strict` - Защита системных файлов
- `ProtectHome=true` - Защита домашних директорий

## Резервное копирование

### Конфигурация

```bash
# Создание резервной копии конфигурации
sudo cp /opt/math-ide/.env /opt/math-ide/.env.backup

# Восстановление конфигурации
sudo cp /opt/math-ide/.env.backup /opt/math-ide/.env
```

### Полное резервное копирование

```bash
# Создание архива
tar -czf math-ide-backup-$(date +%Y%m%d).tar.gz /opt/math-ide

# Восстановление
sudo tar -xzf math-ide-backup-YYYYMMDD.tar.gz -C /
``` 