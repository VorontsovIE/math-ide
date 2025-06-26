#!/bin/bash
set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Логирование
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

# Проверка запуска от root
if [[ $EUID -eq 0 ]]; then
   error "Не запускайте этот скрипт от имени root!"
   exit 1
fi

# Проверка ОС
if [ ! -f /etc/os-release ]; then
    error "Неизвестная операционная система"
    exit 1
fi

. /etc/os-release
if [[ "$ID" != "ubuntu" ]]; then
    error "Этот скрипт предназначен только для Ubuntu"
    exit 1
fi

log "🚀 Начинаю деплой MathIDE на Ubuntu VPS"

# Обновление системы
log "📦 Обновление системы..."
sudo apt update && sudo apt upgrade -y

# Установка Python 3.10+
log "🐍 Проверка и установка Python..."
if ! command -v python3 &> /dev/null; then
    sudo apt install -y python3 python3-pip python3-venv
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [[ "$(echo "$PYTHON_VERSION >= 3.10" | bc -l)" != "1" ]]; then
    error "Требуется Python 3.10 или выше. Найден: $PYTHON_VERSION"
    exit 1
fi

# Установка uv
log "⚡ Установка uv..."
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.local/bin/env
fi

# Создание директории для приложения
APP_DIR="/opt/math-ide"
log "📁 Создание директории приложения: $APP_DIR"
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Клонирование или обновление репозитория
if [ -d "$APP_DIR/.git" ]; then
    log "🔄 Обновление существующего репозитория..."
    cd $APP_DIR
    git pull origin main
else
    log "📥 Клонирование репозитория..."
    # Предполагаем, что репозиторий уже склонирован локально
    cp -r . $APP_DIR/
    cd $APP_DIR
fi

# Установка зависимостей
log "📦 Установка зависимостей..."
uv sync --dev

# Создание .env файла если он не существует
if [ ! -f "$APP_DIR/.env" ]; then
    log "⚙️ Создание файла конфигурации..."
    cp docs/env.example .env
    warn "⚠️ Пожалуйста, отредактируйте файл .env и добавьте необходимые API ключи:"
    warn "   - TELEGRAM_BOT_TOKEN"
    warn "   - OPENAI_API_KEY"
    echo
    read -p "Нажмите Enter после редактирования .env файла..."
fi

# Создание systemd сервиса для Telegram бота
log "🔧 Создание systemd сервиса..."
sudo tee /etc/systemd/system/math-ide-bot.service > /dev/null <<EOF
[Unit]
Description=MathIDE Telegram Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/.venv/bin
ExecStart=$APP_DIR/.venv/bin/python -m interfaces
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Перезагрузка systemd и запуск сервиса
log "🚀 Запуск сервиса..."
sudo systemctl daemon-reload
sudo systemctl enable math-ide-bot
sudo systemctl start math-ide-bot

# Проверка статуса
log "✅ Проверка статуса сервиса..."
if sudo systemctl is-active --quiet math-ide-bot; then
    log "🎉 MathIDE успешно развернут и запущен!"
    log "📊 Статус сервиса: $(sudo systemctl is-active math-ide-bot)"
    log "📝 Логи: sudo journalctl -u math-ide-bot -f"
else
    error "❌ Сервис не запустился. Проверьте логи: sudo journalctl -u math-ide-bot -f"
    exit 1
fi

log "🔧 Полезные команды:"
echo "  • Статус: sudo systemctl status math-ide-bot"
echo "  • Перезапуск: sudo systemctl restart math-ide-bot"
echo "  • Остановка: sudo systemctl stop math-ide-bot"
echo "  • Логи: sudo journalctl -u math-ide-bot -f"
echo "  • Обновление: cd $APP_DIR && git pull && uv sync && sudo systemctl restart math-ide-bot"

log "✨ Деплой завершен!" 