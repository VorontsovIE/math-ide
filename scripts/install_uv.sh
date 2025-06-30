#!/bin/bash

# Скрипт установки uv на Ubuntu сервере
# Использование: ./scripts/install_uv.sh

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

# Проверка ОС
check_os() {
    if [ ! -f /etc/os-release ]; then
        log_error "Неизвестная операционная система"
        exit 1
    fi

    . /etc/os-release
    if [[ "$ID" != "ubuntu" ]]; then
        log_error "Этот скрипт предназначен только для Ubuntu"
        exit 1
    fi

    log_success "Обнаружена Ubuntu $VERSION_ID"
}

# Обновление системы
update_system() {
    log_info "Обновление системы..."
    sudo apt update
    sudo apt upgrade -y
    log_success "Система обновлена"
}

# Установка необходимых пакетов
install_packages() {
    log_info "Установка необходимых пакетов..."
    sudo apt install -y curl wget git build-essential
    
    log_info "Установка LaTeX-пакетов для рендеринга математических формул..."
    sudo apt-get install -y texlive-latex-extra texlive-fonts-recommended dvipng cm-super
    
    log_success "Пакеты установлены"
}

# Установка uv
install_uv() {
    log_info "Установка uv..."
    
    if command -v uv &> /dev/null; then
        log_warning "uv уже установлен: $(uv --version)"
        return
    fi

    # Устанавливаем uv через официальный скрипт
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Добавляем uv в PATH
    export PATH="$HOME/.local/bin:$PATH"
    
    # Проверяем установку
    if command -v uv &> /dev/null; then
        log_success "uv установлен: $(uv --version)"
    else
        log_error "Ошибка установки uv"
        exit 1
    fi
}

# Настройка PATH
setup_path() {
    log_info "Настройка PATH для uv..."
    
    # Добавляем в .bashrc если еще не добавлено
    if ! grep -q "uv" ~/.bashrc; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        log_success "PATH добавлен в .bashrc"
    fi
    
    # Добавляем в текущую сессию
    export PATH="$HOME/.local/bin:$PATH"
}

# Проверка Python
check_python() {
    log_info "Проверка Python..."
    
    if ! command -v python3 &> /dev/null; then
        log_info "Установка Python 3..."
        sudo apt install -y python3 python3-pip python3-venv
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    log_success "Python $PYTHON_VERSION найден"
    
    # Проверяем версию Python
    if [[ "$(echo "$PYTHON_VERSION >= 3.10" | bc -l 2>/dev/null || echo "0")" != "1" ]]; then
        log_warning "Рекомендуется Python 3.10 или выше. Найден: $PYTHON_VERSION"
    fi
}

# Основная функция
main() {
    log_info "Начинаем установку uv на Ubuntu"
    
    check_os
    update_system
    install_packages
    install_uv
    setup_path
    check_python
    
    log_success "Установка uv завершена успешно!"
    log_info "Для применения изменений PATH перезапустите терминал или выполните: source ~/.bashrc"
    log_info "Проверить установку: uv --version"
}

# Запуск основной функции
main "$@" 