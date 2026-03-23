#!/bin/bash
set -e

# === Проверка поддержки терминала ===
if [ -z "$TERM" ] || [ "$TERM" = "dumb" ]; then
    BLUE="" CYAN="" GREEN="" RED="" YELLOW="" PURPLE="" RESET="" BOLD=""
else
    BLUE="\033[34m"
    CYAN="\033[36m"
    GREEN="\033[32m"
    RED="\033[31m"
    YELLOW="\033[33m"
    PURPLE="\033[35m"
    RESET="\033[0m"
    BOLD="\033[1m"
fi

INSTALL_DIR="$(pwd)"
LOG_FILE="openhost_install.log"
touch "$LOG_FILE"

run_task() {
    "$@" &>> "$LOG_FILE" &
    local pid=$!
    spinner $pid
    wait $pid
    return $?
}

center_title() {
    local title="$1"
    local width=$(tput cols 2>/dev/null || echo 50)
    [ $width -lt $((${#title} + 4)) ] && width=$((${#title} + 4))
    local padding=$(( (width - ${#title}) / 2 ))
    local left=$(printf "%${padding}s" | tr ' ' '-')
    local right=$(printf "%${padding}s" | tr ' ' '-')
    [ $(( (width - ${#title}) % 2 )) -ne 0 ] && right="${right}-"
    echo "${left}${title}${right}"
}

spinner() {
    local pid=$1
    local spinstr='|/-\'
    while kill -0 "$pid" 2>/dev/null; do
        printf " [%c]  " "$spinstr"
        local temp=${spinstr#?}
        spinstr=$temp${spinstr%"$temp"}
        sleep 0.1
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        echo -e "${RED}Запустите скрипт от root (sudo bash install.sh)${RESET}"
        exit 1
    fi
}

install_docker() {
    if command -v docker &>/dev/null; then
        echo -e "${GREEN}Docker уже установлен${RESET}"
        return
    fi

    echo -e "${BLUE}Устанавливаем Docker...${RESET}"
    if [ -f /etc/debian_version ]; then
        run_task bash -c 'apt-get update && apt-get install -y \
            apt-transport-https ca-certificates curl gnupg-agent software-properties-common &&
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add - &&
        add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" &&
        apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io' || { echo -e "${RED}Ошибка установки Docker. Смотри $LOG_FILE${RESET}"; return 1; }
    elif [ -f /etc/arch-release ]; then
        run_task pacman -Syu docker --noconfirm || { echo -e "${RED}Ошибка установки Docker${RESET}"; return 1; }
    elif [ -f /etc/redhat-release ]; then
        run_task bash -c 'yum install -y yum-utils &&
        yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo &&
        yum install -y docker-ce docker-ce-cli containerd.io' || { echo -e "${RED}Ошибка установки Docker${RESET}"; return 1; }
    else
        echo -e "${RED}Неизвестная ОС. Установите Docker вручную.${RESET}"
        return 1
    fi

    systemctl start docker
    systemctl enable docker
    echo -e "${GREEN}Docker установлен!${RESET}"
}

install_openhost_docker() {
    install_docker || return 1

    echo -e "${BLUE}Собираем образ OpenHost...${RESET}"
    if [ ! -d "OpenHost" ]; then
        run_task git clone https://github.com/Holy16rus/OpenHost || { echo -e "${RED}Ошибка клонирования${RESET}"; return 1; }
    fi
    cd OpenHost/Docker
    run_task docker build -t openhost-heroku . || { echo -e "${RED}Ошибка сборки образа. Смотри $LOG_FILE${RESET}"; cd ../..; return 1; }
    cd ../..

    echo -e "${BLUE}Устанавливаем зависимости бота...${RESET}"
    cd OpenHost
    run_task pip3 install -r requirements.txt || { echo -e "${RED}Ошибка установки зависимостей${RESET}"; cd ..; return 1; }
    cd ..

    echo -e "${GREEN}Готово! Для запуска:${RESET}"
    echo -e "${CYAN}  cd OpenHost${RESET}"
    echo -e "${CYAN}  echo 'BotToken=ВАШ_ТОКЕН' > .env${RESET}"
    echo -e "${CYAN}  python3 main.py${RESET}"
}

install_openhost_systemd() {
    echo -e "${BLUE}Устанавливаем зависимости...${RESET}"
    run_task apt-get update
    run_task apt-get install -y git python3 python3-pip python3-venv || { echo -e "${RED}Ошибка установки зависимостей${RESET}"; return 1; }

    if [ ! -d "OpenHost" ]; then
        run_task git clone https://github.com/Holy16rus/OpenHost || { echo -e "${RED}Ошибка клонирования${RESET}"; return 1; }
    fi

    cd OpenHost
    python3 -m venv venv
    source venv/bin/activate
    run_task pip install -r requirements.txt || { echo -e "${RED}Ошибка установки зависимостей${RESET}"; deactivate; cd ..; return 1; }
    deactivate
    cd ..

    # Создаём systemd unit
    local work_dir="${INSTALL_DIR}/OpenHost"
    local run_user="${SUDO_USER:-root}"
    cat > /etc/systemd/system/openhost.service << UNIT
[Unit]
Description=OpenHost Telegram Bot
After=network.target

[Service]
Type=simple
User=${run_user}
WorkingDirectory=${work_dir}
ExecStart=${work_dir}/venv/bin/python3 main.py
Restart=on-failure
RestartSec=5
EnvironmentFile=${work_dir}/.env

[Install]
WantedBy=multi-user.target
UNIT

    systemctl daemon-reload
    systemctl enable openhost

    echo -e "${GREEN}Готово! Для запуска:${RESET}"
    echo -e "${CYAN}  echo 'BotToken=ВАШ_ТОКЕН' > ${work_dir}/.env${RESET}"
    echo -e "${CYAN}  systemctl start openhost${RESET}"
    echo -e "${CYAN}  systemctl status openhost${RESET}"
}

uninstall_openhost() {
    echo -e "${RED}Удаляем OpenHost...${RESET}"

    # Останавливаем systemd если есть
    systemctl stop openhost 2>/dev/null || true
    systemctl disable openhost 2>/dev/null || true
    rm -f /etc/systemd/system/openhost.service
    systemctl daemon-reload 2>/dev/null || true

    # Останавливаем Docker контейнеры если есть
    docker ps -a --filter "name=openhost-" -q | xargs -r docker rm -f 2>/dev/null || true
    docker rmi openhost-heroku 2>/dev/null || true

    rm -rf OpenHost
    echo -e "${GREEN}OpenHost удалён${RESET}"
}

# === Главное меню ===
check_root

while true; do
    clear
    echo -e "${PURPLE}${BOLD}"
    echo "   ___                   _   _           _   "
    echo "  / _ \ _ __   ___ _ __ | | | | ___  ___| |_ "
    echo " | | | | '_ \ / _ \ '_ \| |_| |/ _ \/ __| __|"
    echo " | |_| | |_) |  __/ | | |  _  | (_) \__ \ |_ "
    echo "  \___/| .__/ \___|_| |_|_| |_|\___/|___/\__|"
    echo "       |_|                                    "
    echo -e "${RESET}"
    echo -e "${CYAN}${BOLD}$(center_title ' OpenHost Installer ')${RESET}"
    echo -e "${BLUE}1. Установить с Docker${RESET}"
    echo -e "${BLUE}2. Установить с systemd (venv)${RESET}"
    echo -e "${BLUE}3. Удалить OpenHost${RESET}"
    echo -e "${BLUE}0. Выход${RESET}"
    echo -e "${CYAN}$(center_title '')${RESET}"
    read -p $'\033[33m> \033[0m' choice

    case $choice in
        1)
            install_openhost_docker
            read -p $'\033[33mНажмите Enter...\033[0m'
            ;;
        2)
            install_openhost_systemd
            read -p $'\033[33mНажмите Enter...\033[0m'
            ;;
        3)
            uninstall_openhost
            read -p $'\033[33mНажмите Enter...\033[0m'
            ;;
        0)
            echo -e "${GREEN}Пока!${RESET}"
            exit 0
            ;;
        *)
            echo -e "${RED}Неверный выбор!${RESET}"
            read -p $'\033[33mНажмите Enter...\033[0m'
            ;;
    esac
done
