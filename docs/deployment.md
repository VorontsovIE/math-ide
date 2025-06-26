# Деплой MathIDE на VPS (Ubuntu)

## Быстрый старт

### Автоматический деплой

1. Склонируйте репозиторий на вашу локальную машину:
   ```bash
   git clone <repository_url>
   cd math-ide
   ```

2. Скопируйте проект на VPS:
   ```bash
   scp -r . user@your-vps-ip:/tmp/math-ide
   ```

3. Подключитесь к VPS и запустите скрипт деплоя:
   ```bash
   ssh user@your-vps-ip
   cd /tmp/math-ide
   ./deploy.sh
   ```

4. Следуйте инструкциям скрипта для настройки `.env` файла.

### Требования к системе

- **ОС**: Ubuntu 20.04 LTS или новее
- **RAM**: минимум 1GB, рекомендуется 2GB+
- **CPU**: 1 ядро минимум
- **Диск**: 5GB свободного места
- **Python**: 3.10 или новее (устанавливается автоматически)

## Ручной деплой

### 1. Подготовка системы

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y python3 python3-pip python3-venv git curl

# Установка uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

### 2. Развертывание приложения

```bash
# Создание директории приложения
sudo mkdir -p /opt/math-ide
sudo chown $USER:$USER /opt/math-ide

# Клонирование репозитория
git clone <repository_url> /opt/math-ide
cd /opt/math-ide

# Установка зависимостей
uv sync --dev

# Настройка конфигурации
cp docs/env.example .env
nano .env  # Отредактируйте необходимые переменные
```

### 3. Настройка systemd сервиса

```bash
# Создание сервиса
sudo tee /etc/systemd/system/math-ide-bot.service > /dev/null <<EOF
[Unit]
Description=MathIDE Telegram Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/math-ide
Environment=PATH=/opt/math-ide/.venv/bin
ExecStart=/opt/math-ide/.venv/bin/python -m interfaces
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Запуск сервиса
sudo systemctl daemon-reload
sudo systemctl enable math-ide-bot
sudo systemctl start math-ide-bot
```

## Конфигурация

### Обязательные переменные окружения

```bash
# Telegram Bot Token (получить у @BotFather)
TELEGRAM_BOT_TOKEN=your_bot_token_here

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# GPT модель (опционально)
GPT_MODEL=gpt-4o-mini

# Уровень логирования (опционально)
LOG_LEVEL=INFO
```

### Дополнительные настройки

```bash
# Таймаут для GPT запросов (секунды)
GPT_TIMEOUT=60

# Максимальное количество попыток при ошибках
MAX_RETRIES=3

# Включение режима предпоказа
PREVIEW_MODE=true
```

## Управление сервисом

### Основные команды

```bash
# Статус сервиса
sudo systemctl status math-ide-bot

# Перезапуск сервиса
sudo systemctl restart math-ide-bot

# Остановка сервиса
sudo systemctl stop math-ide-bot

# Запуск сервиса
sudo systemctl start math-ide-bot

# Отключение автозапуска
sudo systemctl disable math-ide-bot
```

### Просмотр логов

```bash
# Просмотр логов в реальном времени
sudo journalctl -u math-ide-bot -f

# Просмотр последних 100 строк
sudo journalctl -u math-ide-bot -n 100

# Просмотр логов за последний час
sudo journalctl -u math-ide-bot --since "1 hour ago"
```

## Обновление приложения

### Автоматическое обновление

```bash
cd /opt/math-ide
git pull origin main
uv sync
sudo systemctl restart math-ide-bot
```

### Создание скрипта обновления

```bash
# Создание скрипта update.sh
cat > /opt/math-ide/update.sh << 'EOF'
#!/bin/bash
set -e

echo "🔄 Обновление MathIDE..."
cd /opt/math-ide

# Обновление кода
git pull origin main

# Обновление зависимостей
uv sync

# Перезапуск сервиса
sudo systemctl restart math-ide-bot

echo "✅ Обновление завершено!"
EOF

chmod +x /opt/math-ide/update.sh
```

## Мониторинг и диагностика

### Проверка работоспособности

```bash
# Проверка статуса сервиса
systemctl is-active math-ide-bot

# Проверка использования ресурсов
sudo systemctl status math-ide-bot

# Проверка открытых портов
sudo netstat -tulpn | grep python
```

### Типичные проблемы и решения

#### Сервис не запускается

1. Проверьте логи:
   ```bash
   sudo journalctl -u math-ide-bot -n 50
   ```

2. Проверьте `.env` файл:
   ```bash
   cat /opt/math-ide/.env
   ```

3. Проверьте права доступа:
   ```bash
   ls -la /opt/math-ide/
   ```

#### Проблемы с API ключами

1. Проверьте валидность токена Telegram:
   ```bash
   curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"
   ```

2. Проверьте OpenAI API ключ:
   ```bash
   curl -s -H "Authorization: Bearer $OPENAI_API_KEY" \
        "https://api.openai.com/v1/models"
   ```

#### Высокое потребление памяти

1. Настройте ограничения в systemd:
   ```bash
   sudo systemctl edit math-ide-bot
   ```
   
   Добавьте:
   ```ini
   [Service]
   MemoryMax=1G
   MemoryHigh=800M
   ```

2. Перезапустите сервис:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart math-ide-bot
   ```

## Резервное копирование

### Создание бэкапа

```bash
# Создание директории для бэкапов
sudo mkdir -p /opt/backups

# Скрипт бэкапа
cat > /opt/math-ide/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="math-ide_backup_$TIMESTAMP.tar.gz"

echo "📦 Создание бэкапа..."
tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
    --exclude='.venv' \
    --exclude='uv.lock' \
    --exclude='.git' \
    /opt/math-ide/

echo "✅ Бэкап создан: $BACKUP_DIR/$BACKUP_FILE"

# Удаление старых бэкапов (старше 30 дней)
find "$BACKUP_DIR" -name "math-ide_backup_*.tar.gz" -mtime +30 -delete
EOF

chmod +x /opt/math-ide/backup.sh
```

### Восстановление из бэкапа

```bash
# Остановка сервиса
sudo systemctl stop math-ide-bot

# Восстановление
sudo tar -xzf /opt/backups/math-ide_backup_TIMESTAMP.tar.gz -C /

# Восстановление зависимостей
cd /opt/math-ide
uv sync

# Запуск сервиса
sudo systemctl start math-ide-bot
```

## Безопасность

### Базовые настройки безопасности

1. **Настройка файрвола**:
   ```bash
   sudo ufw enable
   sudo ufw allow ssh
   sudo ufw allow 443/tcp  # Если планируется HTTPS
   ```

2. **Создание отдельного пользователя**:
   ```bash
   sudo useradd -m -s /bin/bash mathide
   sudo usermod -aG sudo mathide
   ```

3. **Настройка прав доступа**:
   ```bash
   sudo chown -R mathide:mathide /opt/math-ide
   sudo chmod 600 /opt/math-ide/.env
   ```

### Обновление безопасности

```bash
# Автоматические обновления безопасности
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades
```

## Масштабирование

### Запуск нескольких экземпляров

Для высокой нагрузки можно запустить несколько экземпляров бота:

```bash
# Создание дополнительного сервиса
sudo cp /etc/systemd/system/math-ide-bot.service \
       /etc/systemd/system/math-ide-bot-worker2.service

# Редактирование нового сервиса
sudo nano /etc/systemd/system/math-ide-bot-worker2.service
```

### Мониторинг производительности

```bash
# Установка htop для мониторинга
sudo apt install htop

# Просмотр использования ресурсов
htop
```

---

**Примечание**: Этот документ описывает базовую настройку деплоя. Для продакшн-среды рекомендуется дополнительно настроить:
- Reverse proxy (nginx)
- SSL/TLS сертификаты
- Мониторинг (Prometheus, Grafana)
- Централизованное логирование
- Автоматическое масштабирование 