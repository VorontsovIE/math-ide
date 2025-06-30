#!/bin/bash

# Скрипт диагностики systemd сервиса Math IDE
# Использование: ./scripts/debug_service.sh [service_name]

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
SERVICE_NAME="${1:-math-ide}"
DEPLOY_DIR="/opt/math-ide"

# Проверка существования сервиса
check_service_exists() {
    log_info "Проверка существования сервиса: $SERVICE_NAME"
    
    if ! systemctl list-unit-files | grep -q "^$SERVICE_NAME.service"; then
        log_error "Сервис $SERVICE_NAME не найден в systemd"
        return 1
    fi
    
    log_success "Сервис $SERVICE_NAME найден"
    return 0
}

# Проверка конфигурации сервиса
check_service_config() {
    log_info "Проверка конфигурации сервиса"
    
    if [ -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
        log_info "Конфигурация сервиса:"
        cat "/etc/systemd/system/$SERVICE_NAME.service"
        echo
    else
        log_error "Файл конфигурации сервиса не найден"
        return 1
    fi
}

# Проверка статуса сервиса
check_service_status() {
    log_info "Проверка статуса сервиса"
    
    echo "=== Статус сервиса ==="
    systemctl status "$SERVICE_NAME" --no-pager -l || true
    echo
    
    echo "=== Активность сервиса ==="
    systemctl is-active "$SERVICE_NAME" || echo "Неактивен"
    echo
    
    echo "=== Автозапуск ==="
    systemctl is-enabled "$SERVICE_NAME" || echo "Не включен"
    echo
}

# Проверка логов сервиса
check_service_logs() {
    log_info "Проверка логов сервиса"
    
    echo "=== Последние 50 строк логов ==="
    journalctl -u "$SERVICE_NAME" --no-pager -l -n 50 || true
    echo
    
    echo "=== Логи с ошибками ==="
    journalctl -u "$SERVICE_NAME" --no-pager -l -p err -n 20 || true
    echo
}

# Проверка файлов и директорий
check_files_and_dirs() {
    log_info "Проверка файлов и директорий"
    
    echo "=== Проверка директории деплоя ==="
    if [ -d "$DEPLOY_DIR" ]; then
        log_success "Директория $DEPLOY_DIR существует"
        ls -la "$DEPLOY_DIR"
    else
        log_error "Директория $DEPLOY_DIR не существует"
    fi
    echo
    
    echo "=== Проверка .env файла ==="
    if [ -f "$DEPLOY_DIR/.env" ]; then
        log_success ".env файл существует"
        echo "Размер: $(stat -c%s "$DEPLOY_DIR/.env") байт"
        echo "Права: $(stat -c%a "$DEPLOY_DIR/.env")"
        echo "Владелец: $(stat -c%U "$DEPLOY_DIR/.env")"
    else
        log_error ".env файл не найден"
    fi
    echo
    
    echo "=== Проверка виртуального окружения ==="
    if [ -d "$DEPLOY_DIR/.venv" ]; then
        log_success "Виртуальное окружение существует"
        if [ -f "$DEPLOY_DIR/.venv/bin/python" ]; then
            log_success "Python найден в виртуальном окружении"
            echo "Версия Python: $($DEPLOY_DIR/.venv/bin/python --version)"
        else
            log_error "Python не найден в виртуальном окружении"
        fi
    else
        log_error "Виртуальное окружение не найдено"
    fi
    echo
}

# Проверка переменных окружения
check_environment() {
    log_info "Проверка переменных окружения"
    
    echo "=== Переменные окружения сервиса ==="
    systemctl show "$SERVICE_NAME" --property=Environment --property=EnvironmentFile || true
    echo
    
    echo "=== Содержимое .env файла (без секретов) ==="
    if [ -f "$DEPLOY_DIR/.env" ]; then
        # Показываем только ключи, без значений
        grep -E '^[A-Z_]+=' "$DEPLOY_DIR/.env" | sed 's/=.*/=***/' || true
    fi
    echo
}

# Тестовый запуск команды
test_command() {
    log_info "Тестовый запуск команды"
    
    echo "=== Тест запуска Python модуля ==="
    if [ -f "$DEPLOY_DIR/.venv/bin/python" ]; then
        cd "$DEPLOY_DIR"
        echo "Рабочая директория: $(pwd)"
        echo "Команда: $DEPLOY_DIR/.venv/bin/python -m interfaces.telegram_bot --help"
        
        # Запускаем с таймаутом для теста
        timeout 10s "$DEPLOY_DIR/.venv/bin/python" -m interfaces.telegram_bot --help 2>&1 || true
    else
        log_error "Python не найден для тестирования"
    fi
    echo
}

# Проверка прав доступа
check_permissions() {
    log_info "Проверка прав доступа"
    
    echo "=== Права на директорию ==="
    ls -ld "$DEPLOY_DIR" || true
    echo
    
    echo "=== Права на файлы ==="
    ls -la "$DEPLOY_DIR" | head -10 || true
    echo
    
    echo "=== Права пользователя сервиса ==="
    id "$SERVICE_USER" || true
    echo
}

# Основная функция диагностики
main() {
    log_info "Начинаем диагностику сервиса $SERVICE_NAME"
    echo "========================================"
    
    check_service_exists || exit 1
    check_service_config
    check_service_status
    check_service_logs
    check_files_and_dirs
    check_environment
    check_permissions
    test_command
    
    echo "========================================"
    log_info "Диагностика завершена"
    
    echo
    log_info "Полезные команды для дальнейшей диагностики:"
    echo "  • Подробные логи: sudo journalctl -u $SERVICE_NAME -f"
    echo "  • Логи с ошибками: sudo journalctl -u $SERVICE_NAME -p err"
    echo "  • Перезапуск сервиса: sudo systemctl restart $SERVICE_NAME"
    echo "  • Проверка конфигурации: sudo systemctl cat $SERVICE_NAME"
}

# Запуск основной функции
main "$@" 