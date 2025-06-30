#!/bin/bash

# Скрипт для быстрого исправления systemd сервиса
# Решает проблемы с EnvironmentFile и daemon-reload

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции логирования
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Конфигурация
SERVICE_NAME="math-ide"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
DEPLOY_DIR="/opt/math-ide"
SERVICE_USER="ilya"

log_info "Исправление systemd сервиса $SERVICE_NAME"
echo "=========================================="

# Проверяем, что мы в правильной директории
if [ ! -f "deploy.sh" ]; then
    log_error "Скрипт должен запускаться из корня проекта"
    exit 1
fi

# Останавливаем сервис
log_info "Останавливаем сервис..."
sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true

# Пересоздаем сервис с исправленной конфигурацией
log_info "Пересоздаем systemd сервис..."
./deploy.sh --force

# Проверяем результат
log_info "Проверяем статус сервиса..."
sleep 3

if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    log_success "Сервис успешно запущен!"
    log_info "Статус:"
    sudo systemctl status "$SERVICE_NAME" --no-pager -l
else
    log_error "Сервис не запустился"
    log_info "Логи:"
    sudo journalctl -u "$SERVICE_NAME" --no-pager -l -n 10
    exit 1
fi

log_success "Исправление завершено!"
log_info "Для просмотра логов: sudo journalctl -u $SERVICE_NAME -f" 