#!/usr/bin/env python3
import subprocess
import os
import time
import sys
import psutil
import re
import shutil
import venv
import platform
import threading
from itertools import cycle

# --- Конфигурация цветов и стилей ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    GREY = '\033[90m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    
    @staticmethod
    def print_banner():
        os.system('clear' if os.name == 'posix' else 'cls')
        print(f"{Colors.BLUE}")
        print(r"""
    ██╗  ██╗███████╗██████╗  ██████╗ ██╗  ██╗██╗   ██╗
    ██║  ██║██╔════╝██╔══██╗██╔═══██╗██║ ██╔╝██║   ██║
    ███████║█████╗  ██████╔╝██║   ██║█████╔╝ ██║   ██║
    ██╔══██║██╔══╝  ██╔══██╗██║   ██║██╔═██╗ ██║   ██║
    ██║  ██║███████╗██║  ██║╚██████╔╝██║  ██╗╚██████╔╝
    ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝
        """ + Colors.ENDC)
        print(f"{Colors.CYAN}   🚀 ULTIMATE MANAGER | v3.1 (Live Mode){Colors.ENDC}\n")

    @staticmethod
    def box_msg(title, text, color=GREEN):
        # Красивая рамка
        lines = text.split('\n')
        max_len = max(len(line) for line in lines)
        if len(title) > max_len: max_len = len(title)
        
        print(f"\n{color} ╔{'═'*(max_len+2)}╗{Colors.ENDC}")
        print(f"{color} ║ {title.center(max_len)} ║{Colors.ENDC}")
        print(f"{color} ╠{'═'*(max_len+2)}╣{Colors.ENDC}")
        for line in lines:
            print(f"{color} ║ {line.ljust(max_len)} ║{Colors.ENDC}")
        print(f"{color} ╚{'═'*(max_len+2)}╝{Colors.ENDC}\n")

# --- UI Компоненты ---
class Loader:
    def __init__(self, desc="Загрузка..."):
        self.desc = desc
        self.animation = cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
        self.bar_chars = ['▒', '█']

    def animate(self, status_text):
        bar_len = 20
        t = time.time()
        filled = int((t * 5) % bar_len)
        if int((t * 5) // bar_len) % 2 == 0:
            bar = self.bar_chars[1] * filled + self.bar_chars[0] * (bar_len - filled)
        else:
            bar = self.bar_chars[0] * filled + self.bar_chars[1] * (bar_len - filled)
        
        spinner = next(self.animation)
        sys.stdout.write(f"\r{Colors.CYAN} {spinner} [{bar}] {Colors.BOLD}{self.desc}{Colors.ENDC} | {Colors.GREY}{status_text}{Colors.ENDC}   ")
        sys.stdout.flush()

# --- Класс установки и проверки окружения ---
class PanelInstaller:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.venv_path = os.path.join(self.script_dir, "venv")
        self.config_file = os.path.join(self.script_dir, "panel_config.ini")
        self.is_first_run = not os.path.exists(self.config_file)
        
    def check_requirements(self):
        required_tools = ["screen", "git"]
        missing = [t for t in required_tools if shutil.which(t) is None]
        if missing:
            print(f"{Colors.YELLOW}⚠️  Устанавливаю: {', '.join(missing)}...{Colors.ENDC}")
            try:
                subprocess.run(["sudo", "apt-get", "update"], check=False, stderr=subprocess.DEVNULL)
                subprocess.run(["sudo", "apt-get", "install", "-y"] + missing, check=True, stdout=subprocess.DEVNULL)
                return True
            except: return False
        return True
    
    def create_venv(self):
        if not os.path.exists(self.venv_path):
            try: venv.EnvBuilder(with_pip=True).create(self.venv_path)
            except: return False
        return True
    
    def install_requirements(self):
        pip = os.path.join(self.venv_path, "bin", "pip")
        try:
            subprocess.run([pip, "install", "psutil", "requests"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except: return False
    
    def save_config(self):
        with open(self.config_file, "w") as f: f.write(f"installed=true\n")

# --- Класс управления ботами ---
class BotManager:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.venv_path = os.path.join(self.script_dir, "venv")
        self.REPO_URL = "https://github.com/coddrago/Heroku"
        self.BOT_DIR_NAME = "Heroku"
        self.bots_config = []
        
    def get_python(self):
        p = os.path.join(self.venv_path, "bin", "python")
        return p if os.path.exists(p) else sys.executable

    def _get_screen_name(self, name):
        return f"bot_{name.lower()}"

    def discover_bots(self):
        configs = []
        try:
            for name in sorted(os.listdir(self.script_dir)):
                path = os.path.join(self.script_dir, name)
                if (os.path.isdir(path) and 
                    not name.startswith('.') and 
                    name.lower() not in ['venv', '__pycache__', '.git'] and
                    os.path.exists(os.path.join(path, self.BOT_DIR_NAME))):
                    configs.append({"name": name, "path": path})
        except: pass
        return configs

    def create_profile(self):
        print(f"\n{Colors.HEADER}🆕 СОЗДАНИЕ ПРОФИЛЯ{Colors.ENDC}")
        while True:
            name = input(f"{Colors.BOLD}Введите имя (English): {Colors.ENDC}").strip()
            if re.match(r'^[a-zA-Z0-9_]+$', name): break
            print(f"{Colors.RED}❌ Некорректное имя!{Colors.ENDC}")

        profile_path = os.path.join(self.script_dir, name)
        if os.path.exists(profile_path):
            print(f"{Colors.RED}❌ Уже существует{Colors.ENDC}")
            return

        try:
            os.makedirs(profile_path)
            clone_path = os.path.join(profile_path, self.BOT_DIR_NAME)
            
            print(f"{Colors.CYAN}📥 Клонирование...{Colors.ENDC}")
            subprocess.run(["git", "clone", self.REPO_URL, clone_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            print(f"{Colors.CYAN}📦 Библиотеки...{Colors.ENDC}")
            req_file = os.path.join(clone_path, "requirements.txt")
            if os.path.exists(req_file):
                subprocess.run([self.get_python(), "-m", "pip", "install", "-r", req_file], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # ЗАПУСК МОНИТОРИНГА
            self.monitor_activation(name, clone_path, profile_path)
            
        except Exception as e:
            print(f"\n{Colors.RED}❌ Критическая ошибка: {e}{Colors.ENDC}")
            shutil.rmtree(profile_path, ignore_errors=True)

    def monitor_activation(self, name, clone_path, profile_path):
        screen = self._get_screen_name(name)
        log_file = os.path.join(profile_path, "bot_log.txt")
        if os.path.exists(log_file): open(log_file, 'w').close()
        
        cmd = f"cd {clone_path} && {self.get_python()} -u -m heroku --root > {log_file} 2>&1"
        
        loader = Loader(desc="Настройка")
        print() 
        
        # Старт
        self.kill_bot_screen(name)
        subprocess.run(["screen", "-dmS", screen, "bash", "-c", cmd], check=True)
        
        start_time = time.time()
        found_link = None
        restart_count = 0
        
        while True:
            status_msg = "Запуск..."
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', errors='ignore') as f:
                        content = f.read()
                        # Ищем ссылку
                        match = re.search(r'Please visit\s+(https?://\S+)', content)
                        if match:
                            found_link = match.group(1)
                            break 
                        
                        if "Web mode ready" in content: status_msg = "Ожидание ссылки 🕵️"
                        elif "Installing" in content: status_msg = "Установка пакетов 📥"
                        elif "Requirement" in content: status_msg = "Загрузка зависимостей 📥"
                        else: status_msg = "Работа бота ⚙️"
                except: pass

            if not self.get_status(name):
                restart_count += 1
                status_msg = f"Авто-рестарт ({restart_count}) 🔄"
                loader.animate(status_msg)
                subprocess.run(["screen", "-dmS", screen, "bash", "-c", cmd], check=True)
                time.sleep(2)
            
            loader.animate(status_msg)
            time.sleep(0.2)
            
            if time.time() - start_time > 400: # 6+ минут
                break

        sys.stdout.write("\r" + " "*100 + "\r")
        
        if found_link:
            # ВАЖНО: Мы НЕ убиваем бота, он работает!
            Colors.box_msg("✅ ГОТОВО! БОТ АКТИВЕН", f"Ссылка для входа:\n\n   {found_link}   \n\n(Нажмите Ctrl+Click)", Colors.GREEN)
            input(f"{Colors.GREY}[Нажмите Enter, чтобы вернуться в меню...]{Colors.ENDC}")
        else:
            self.kill_bot_screen(name) # Убиваем только при неудаче
            print(f"{Colors.RED}❌ Не удалось получить ссылку. Проверьте: {log_file}{Colors.ENDC}")
            input("Enter...")

    def kill_bot_screen(self, name):
        target = f"bot_{name}"
        try:
            res = subprocess.run(["screen", "-ls"], capture_output=True, text=True)
            for line in res.stdout.splitlines():
                if target.lower() in line.lower() and ("Detached" in line or "Attached" in line):
                    pid = line.strip().split()[0]
                    subprocess.run(["screen", "-XS", pid, "quit"], stderr=subprocess.DEVNULL)
        except: pass

    def manage_bot_state(self, name, action):
        screen_std = self._get_screen_name(name)
        profile = os.path.join(self.script_dir, name)
        bot_dir = os.path.join(profile, self.BOT_DIR_NAME)
        log = os.path.join(profile, "bot_log.txt")
        is_running = self.get_status(name)

        if action == "stop" or action == "restart":
            if is_running:
                self.kill_bot_screen(name)
                if action == "stop": print(f"🛑 {name}: {Colors.RED}Остановлен{Colors.ENDC}")
            elif action == "stop": print(f"⚠️  {name}: Уже стоит")

        if action == "start" or action == "restart":
            if action == "start" and is_running:
                print(f"⚠️  {name}: Уже работает")
                return
            if action == "restart": 
                self.kill_bot_screen(name)
                time.sleep(0.5)

            cmd = f"cd {bot_dir} && {self.get_python()} -u -m heroku --root > {log} 2>&1"
            subprocess.run(["screen", "-dmS", screen_std, "bash", "-c", cmd], check=True)
            print(f"🚀 {name}: {Colors.GREEN}Запущен{Colors.ENDC}")

    def delete_bot(self, name):
        print(f"\n{Colors.RED}🗑️  УДАЛЕНИЕ: {name}{Colors.ENDC}")
        if input(f"Подтвердите 'yes': ").strip().lower() == 'yes':
            self.kill_bot_screen(name)
            try: shutil.rmtree(os.path.join(self.script_dir, name)); print(f"{Colors.GREEN}✅ Удалено{Colors.ENDC}")
            except: print(f"{Colors.RED}Ошибка удаления{Colors.ENDC}")

    def get_status(self, name):
        try:
            res = subprocess.run(["screen", "-ls"], capture_output=True, text=True)
            return bool(re.search(re.escape(f"bot_{name}"), res.stdout, re.IGNORECASE))
        except: return False

    def select_profiles(self, title, allow_all=True):
        if not self.bots_config: return []
        print(f"\n{Colors.CYAN}📋 {title}:{Colors.ENDC}")
        if allow_all: print(f"{Colors.BOLD}[0] 💠 ВСЕ (All){Colors.ENDC}")
        for i, bot in enumerate(self.bots_config, 1):
            st = "🟢" if self.get_status(bot['name']) else "🔴"
            print(f"[{i}] {st} {bot['name']}")
        choice = input(f"\n{Colors.BOLD}>>>{Colors.ENDC} ").strip()
        if allow_all and choice == "0": return [b['name'] for b in self.bots_config]
        if choice.isdigit() and 0 < int(choice) <= len(self.bots_config):
            return [self.bots_config[int(choice)-1]['name']]
        return []

    def show_dashboard(self):
        Colors.print_banner()
        self.bots_config = self.discover_bots()
        if not self.bots_config: Colors.box_msg("ИНФО", "Нет профилей. Создайте первый!", Colors.YELLOW)
        else:
            print(f"   {Colors.BOLD}{'ID':<4} {'СТАТУС':<10} {'ИМЯ':<20}{Colors.ENDC}")
            print(f"   {Colors.GREY}{'─'*35}{Colors.ENDC}")
            for i, bot in enumerate(self.bots_config, 1):
                run = self.get_status(bot['name'])
                st_icon = f"{Colors.GREEN}● ONLINE{Colors.ENDC}" if run else f"{Colors.RED}○ OFFLINE{Colors.ENDC}"
                print(f"   {Colors.BOLD}{i:<4}{Colors.ENDC} {st_icon:<19} {bot['name']}")
        
        print(f"\n{Colors.GREY}┌{'─'*42}┐{Colors.ENDC}")
        print(f"{Colors.GREY}│{Colors.ENDC} 1. {Colors.GREEN}➕ Создать{Colors.ENDC}   3. {Colors.RED}🛑 Стоп{Colors.ENDC}    5. {Colors.BLUE}📜 Логи{Colors.ENDC}   {Colors.GREY}│{Colors.ENDC}")
        print(f"{Colors.GREY}│{Colors.ENDC} 2. {Colors.CYAN}🚀 Запуск{Colors.ENDC}    4. {Colors.YELLOW}🔄 Рестарт{Colors.ENDC} 6. {Colors.GREY}🚪 Выход{Colors.ENDC}  {Colors.GREY}│{Colors.ENDC}")
        print(f"{Colors.GREY}│{Colors.ENDC}              7. {Colors.RED}🗑️  Удалить{Colors.ENDC}              {Colors.GREY}│{Colors.ENDC}")
        print(f"{Colors.GREY}└{'─'*42}┘{Colors.ENDC}")

    def view_logs(self):
        t = self.select_profiles("Логи", False)
        if t:
            log = os.path.join(self.script_dir, t[0], "bot_log.txt")
            print(f"\n{Colors.BLUE}📜 Лог {t[0]}:{Colors.ENDC}")
            os.system(f"tail -n 20 {log}" if os.path.exists(log) else "echo Пусто")
            input("\nEnter...")

def main():
    installer = PanelInstaller()
    if installer.is_first_run:
        Colors.print_banner()
        print("Настройка окружения...")
        if installer.check_requirements() and installer.create_venv():
            installer.install_requirements(); installer.save_config()
    manager = BotManager()
    while True:
        manager.show_dashboard()
        c = input(f"{Colors.BOLD}>>>{Colors.ENDC} ").strip()
        if c == "1": manager.create_profile()
        elif c in ["2", "3", "4"]:
            act = {"2":"start", "3":"stop", "4":"restart"}[c]
            tgts = manager.select_profiles(f"Для {act}")
            if tgts:
                print(); [manager.manage_bot_state(n, act) for n in tgts]; time.sleep(1)
                if len(tgts)>1: input("Enter...")
        elif c == "5": manager.view_logs()
        elif c == "7":
            t = manager.select_profiles("Удаление", False)
            if t: manager.delete_bot(t[0])
        elif c == "6": print("\n👋 Bye!"); break

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print("\n👋")
