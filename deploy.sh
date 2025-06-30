#!/bin/bash

# Скрипт деплоя Math IDE на VPS-сервер
# Использование: ./deploy.sh [опции]
# Опции:
#   --env-file PATH    Путь к файлу с переменными окружения
#   --branch BRANCH    Ветка для деплоя (по умолчанию: main)
#   --service-name NAME Имя systemd сервиса (по умолчанию: math-ide)
#   --user USER        Пользователь для запуска сервиса (по умолчанию: $USER)
#   --force            Автоматический режим без запросов пользователя

set -e  # Выход при ошибке

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
ENV_FILE=""
BRANCH="main"
SERVICE_NAME="math-ide"
SERVICE_USER="$USER"
DEPLOY_DIR="/opt/math-ide"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
FORCE_MODE=false

# Парсинг аргументов
while [[ $# -gt 0 ]]; do
    case $1 in
        --env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        --branch)
            BRANCH="$2"
            shift 2
            ;;
        --service-name)
            SERVICE_NAME="$2"
            shift 2
            ;;
        --user)
            SERVICE_USER="$2"
            shift 2
            ;;
        --force)
            FORCE_MODE=true
            shift
            ;;
        --help)
            echo "Использование: $0 [опции]"
            echo "Опции:"
            echo "  --env-file PATH    Путь к файлу с переменными окружения"
            echo "  --branch BRANCH    Ветка для деплоя (по умолчанию: main)"
            echo "  --service-name NAME Имя systemd сервиса (по умолчанию: math-ide)"
            echo "  --user USER        Пользователь для запуска сервиса (по умолчанию: \$USER)"
            echo "  --force            Автоматический режим без запросов пользователя"
            echo "  --help             Показать эту справку"
            exit 0
            ;;
        *)
            log_error "Неизвестная опция: $1"
            exit 1
            ;;
    esac
done

# Проверка наличия uv
check_uv() {
    if ! command -v uv &> /dev/null; then
        log_error "uv не установлен. Установите uv: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
    log_success "uv найден: $(uv --version)"
}

# Проверка наличия git
check_git() {
    if ! command -v git &> /dev/null; then
        log_error "git не установлен"
        exit 1
    fi
    log_success "git найден: $(git --version)"
}

# Создание директории для деплоя
create_deploy_dir() {
    log_info "Создание директории для деплоя: $DEPLOY_DIR"
    if [ ! -d "$DEPLOY_DIR" ]; then
        sudo mkdir -p "$DEPLOY_DIR"
        sudo chown "$SERVICE_USER:$SERVICE_USER" "$DEPLOY_DIR"
        log_success "Директория создана"
    else
        log_info "Директория уже существует: $DEPLOY_DIR"
    fi
}

# Клонирование/обновление репозитория
update_repository() {
    log_info "Обновление репозитория в $DEPLOY_DIR"
    
    if [ -d "$DEPLOY_DIR/.git" ]; then
        log_info "Репозиторий уже существует, обновляем..."
        cd "$DEPLOY_DIR"
        
        # Сохраняем текущую ветку
        CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
        
        # Проверяем, есть ли изменения в рабочей директории
        if ! git diff-index --quiet HEAD -- 2>/dev/null; then
            log_warning "Обнаружены несохраненные изменения в репозитории"
            log_warning "Выполняется stash изменений..."
            git stash push -m "Auto-stash before deployment $(date)"
        fi
        
        # Обновляем репозиторий
        git fetch origin
        git checkout "$BRANCH" 2>/dev/null || git checkout -b "$BRANCH" origin/"$BRANCH"
        git pull origin "$BRANCH"
        
        log_success "Репозиторий обновлен"
    else
        log_info "Клонируем репозиторий..."
        # Проверяем, не пуста ли директория
        if [ "$(ls -A "$DEPLOY_DIR" 2>/dev/null)" ]; then
            log_warning "Директория $DEPLOY_DIR не пуста, но не содержит git репозиторий"
            log_warning "Создаем резервную копию существующих файлов..."
            BACKUP_DIR="/tmp/math-ide-backup-$(date +%Y%m%d-%H%M%S)"
            sudo cp -r "$DEPLOY_DIR" "$BACKUP_DIR"
            log_info "Резервная копия создана: $BACKUP_DIR"
        fi
        
        git clone -b "$BRANCH" https://github.com/your-username/math-ide.git "$DEPLOY_DIR"
        cd "$DEPLOY_DIR"
        log_success "Репозиторий склонирован"
    fi
}

# Настройка переменных окружения
setup_environment() {
    log_info "Настройка переменных окружения"
    
    # Проверяем, существует ли уже .env файл в директории деплоя
    if [ -f "$DEPLOY_DIR/.env" ]; then
        log_info "Файл .env уже существует в $DEPLOY_DIR"
        
        # Если указан новый файл окружения, обрабатываем его
        if [ -n "$ENV_FILE" ] && [ -f "$ENV_FILE" ]; then
            # Проверяем, не является ли ENV_FILE тем же файлом
            if [ "$(realpath "$ENV_FILE")" = "$(realpath "$DEPLOY_DIR/.env")" ]; then
                log_info "Указанный файл окружения уже находится в директории деплоя"
                log_info "Используется существующий .env файл"
            else
                log_warning "Обнаружен существующий .env файл"
                
                if [ "$FORCE_MODE" = true ]; then
                    log_info "Автоматический режим: создание резервной копии и замена .env"
                    cp "$DEPLOY_DIR/.env" "$DEPLOY_DIR/.env.backup.$(date +%Y%m%d-%H%M%S)"
                    cp "$ENV_FILE" "$DEPLOY_DIR/.env"
                    log_success "Файл окружения обновлен"
                else
                    read -p "Заменить существующий .env файл? (y/N): " -n 1 -r
                    echo
                    if [[ $REPLY =~ ^[Yy]$ ]]; then
                        log_info "Создание резервной копии существующего .env..."
                        cp "$DEPLOY_DIR/.env" "$DEPLOY_DIR/.env.backup.$(date +%Y%m%d-%H%M%S)"
                        cp "$ENV_FILE" "$DEPLOY_DIR/.env"
                        log_success "Файл окружения обновлен"
                    else
                        log_info "Существующий .env файл сохранен"
                    fi
                fi
            fi
        else
            log_info "Используется существующий .env файл"
        fi
    else
        # .env файл не существует, создаем новый
        if [ -n "$ENV_FILE" ] && [ -f "$ENV_FILE" ]; then
            log_info "Копирование файла окружения: $ENV_FILE"
            cp "$ENV_FILE" "$DEPLOY_DIR/.env"
            log_success "Файл окружения скопирован"
        elif [ -f "$DEPLOY_DIR/docs/env.example" ]; then
            log_warning "Файл окружения не указан, копируем пример"
            cp "$DEPLOY_DIR/docs/env.example" "$DEPLOY_DIR/.env"
            log_warning "Не забудьте настроить переменные в $DEPLOY_DIR/.env"
        else
            log_error "Файл окружения не найден и пример недоступен"
            exit 1
        fi
    fi
    
    # Устанавливаем права на файл окружения
    chmod 600 "$DEPLOY_DIR/.env"
    log_success "Права доступа к .env файлу установлены"
}

# Установка зависимостей с uv
install_dependencies() {
    log_info "Установка зависимостей с uv"
    cd "$DEPLOY_DIR"
    
    # Проверяем, существует ли виртуальное окружение
    if [ -d ".venv" ]; then
        log_info "Виртуальное окружение уже существует"
        
        # Проверяем, нужно ли обновить зависимости
        if [ -f "pyproject.toml" ] && [ -f "uv.lock" ]; then
            log_info "Проверяем актуальность зависимостей..."
            uv sync
        else
            log_warning "Файлы pyproject.toml или uv.lock не найдены"
            log_info "Пересоздаем виртуальное окружение..."
            rm -rf .venv
            uv sync
        fi
    else
        log_info "Создаем виртуальное окружение и устанавливаем зависимости"
        uv sync
    fi
    
    log_success "Зависимости установлены"
}

# Создание systemd сервиса
create_systemd_service() {
    log_info "Создание systemd сервиса: $SERVICE_NAME"
    
    # Проверяем, существует ли уже сервис
    if [ -f "$SERVICE_FILE" ]; then
        log_info "Systemd сервис уже существует: $SERVICE_FILE"
        
        # Создаем резервную копию
        BACKUP_SERVICE="$SERVICE_FILE.backup.$(date +%Y%m%d-%H%M%S)"
        sudo cp "$SERVICE_FILE" "$BACKUP_SERVICE"
        log_info "Создана резервная копия сервиса: $BACKUP_SERVICE"
        
        if [ "$FORCE_MODE" = true ]; then
            log_info "Автоматический режим: замена существующего сервиса"
        else
            # Спрашиваем пользователя о замене
            read -p "Заменить существующий systemd сервис? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_info "Существующий сервис сохранен"
                return
            fi
        fi
    fi
    
    # Создаем новый файл сервиса
    cat > /tmp/"$SERVICE_NAME".service << EOF
[Unit]
Description=Math IDE Telegram Bot
After=network.target
Wants=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$DEPLOY_DIR
Environment=PATH=$DEPLOY_DIR/.venv/bin
ExecStart=$DEPLOY_DIR/.venv/bin/python -m interfaces.telegram_bot
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Переменные окружения
EnvironmentFile=$DEPLOY_DIR/.env

# Ограничения безопасности
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$DEPLOY_DIR

[Install]
WantedBy=multi-user.target
EOF

    # Копируем файл сервиса
    sudo cp /tmp/"$SERVICE_NAME".service "$SERVICE_FILE"
    rm /tmp/"$SERVICE_NAME".service
    
    # Перезагружаем systemd и включаем сервис
    sudo systemctl daemon-reload
    
    # Включаем сервис только если он еще не включен
    if ! sudo systemctl is-enabled "$SERVICE_NAME" >/dev/null 2>&1; then
        sudo systemctl enable "$SERVICE_NAME"
        log_success "Systemd сервис включен"
    else
        log_info "Systemd сервис уже включен"
    fi
    
    log_success "Systemd сервис создан"
}

# Запуск сервиса
start_service() {
    log_info "Запуск сервиса $SERVICE_NAME"
    
    # Проверяем, запущен ли уже сервис
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        log_info "Сервис уже запущен, перезапускаем..."
        sudo systemctl restart "$SERVICE_NAME"
    else
        sudo systemctl start "$SERVICE_NAME"
    fi
    
    # Проверяем статус
    sleep 2
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        log_success "Сервис успешно запущен"
        log_info "Статус сервиса:"
        sudo systemctl status "$SERVICE_NAME" --no-pager -l
    else
        log_error "Ошибка запуска сервиса"
        log_info "Логи сервиса:"
        sudo journalctl -u "$SERVICE_NAME" --no-pager -l -n 20
        exit 1
    fi
}

# Основная функция деплоя
main() {
    log_info "Начинаем деплой Math IDE"
    log_info "Ветка: $BRANCH"
    log_info "Сервис: $SERVICE_NAME"
    log_info "Пользователь: $SERVICE_USER"
    log_info "Директория: $DEPLOY_DIR"
    
    # Проверки
    check_uv
    check_git
    
    # Выполнение деплоя
    create_deploy_dir
    update_repository
    setup_environment
    install_dependencies
    create_systemd_service
    start_service
    
    log_success "Деплой завершен успешно!"
    log_info "Для просмотра логов используйте: sudo journalctl -u $SERVICE_NAME -f"
    log_info "Для перезапуска сервиса: sudo systemctl restart $SERVICE_NAME"
    log_info "Для остановки сервиса: sudo systemctl stop $SERVICE_NAME"
}

# Запуск основной функции
main "$@" 