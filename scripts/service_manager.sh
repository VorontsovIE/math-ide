#!/bin/bash

# Скрипт управления systemd сервисом Math IDE
# Использование: ./scripts/service_manager.sh [команда]
# Команды:
#   start     - Запустить сервис
#   stop      - Остановить сервис
#   restart   - Перезапустить сервис
#   status    - Показать статус сервиса
#   logs      - Показать логи сервиса
#   enable    - Включить автозапуск сервиса
#   disable   - Отключить автозапуск сервиса
#   update    - Обновить код и перезапустить сервис

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
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

# Параметры по умолчанию
SERVICE_NAME="math-ide"
DEPLOY_DIR="/opt/math-ide"

# Парсинг аргументов
COMMAND="$1"

if [ -z "$COMMAND" ]; then
    echo "Использование: $0 [команда]"
    echo "Команды:"
    echo "  start     - Запустить сервис"
    echo "  stop      - Остановить сервис"
    echo "  restart   - Перезапустить сервис"
    echo "  status    - Показать статус сервиса"
    echo "  logs      - Показать логи сервиса"
    echo "  enable    - Включить автозапуск сервиса"
    echo "  disable   - Отключить автозапуск сервиса"
    echo "  update    - Обновить код и перезапустить сервис"
    exit 1
fi

# Функции управления сервисом
start_service() {
    log_info "Запуск сервиса $SERVICE_NAME..."
    sudo systemctl start "$SERVICE_NAME"
    
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        log_success "Сервис успешно запущен"
    else
        log_error "Ошибка запуска сервиса"
        exit 1
    fi
}

stop_service() {
    log_info "Остановка сервиса $SERVICE_NAME..."
    sudo systemctl stop "$SERVICE_NAME"
    log_success "Сервис остановлен"
}

restart_service() {
    log_info "Перезапуск сервиса $SERVICE_NAME..."
    sudo systemctl restart "$SERVICE_NAME"
    
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        log_success "Сервис успешно перезапущен"
    else
        log_error "Ошибка перезапуска сервиса"
        exit 1
    fi
}

show_status() {
    log_info "Статус сервиса $SERVICE_NAME:"
    sudo systemctl status "$SERVICE_NAME" --no-pager -l
}

show_logs() {
    log_info "Логи сервиса $SERVICE_NAME:"
    sudo journalctl -u "$SERVICE_NAME" --no-pager -l -f
}

enable_service() {
    log_info "Включение автозапуска сервиса $SERVICE_NAME..."
    sudo systemctl enable "$SERVICE_NAME"
    log_success "Автозапуск включен"
}

disable_service() {
    log_info "Отключение автозапуска сервиса $SERVICE_NAME..."
    sudo systemctl disable "$SERVICE_NAME"
    log_success "Автозапуск отключен"
}

update_service() {
    log_info "Обновление кода и перезапуск сервиса..."
    
    if [ ! -d "$DEPLOY_DIR" ]; then
        log_error "Директория деплоя не найдена: $DEPLOY_DIR"
        exit 1
    fi
    
    # Останавливаем сервис
    stop_service
    
    # Обновляем код
    log_info "Обновление кода из репозитория..."
    cd "$DEPLOY_DIR"
    
    if [ -d ".git" ]; then
        git fetch origin
        git pull origin main
        log_success "Код обновлен"
    else
        log_error "Репозиторий git не найден в $DEPLOY_DIR"
        exit 1
    fi
    
    # Обновляем зависимости
    log_info "Обновление зависимостей..."
    uv sync
    log_success "Зависимости обновлены"
    
    # Запускаем сервис
    start_service
    
    log_success "Обновление завершено"
}

# Основная логика
case "$COMMAND" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    enable)
        enable_service
        ;;
    disable)
        disable_service
        ;;
    update)
        update_service
        ;;
    *)
        log_error "Неизвестная команда: $COMMAND"
        echo "Используйте --help для справки"
        exit 1
        ;;
esac 