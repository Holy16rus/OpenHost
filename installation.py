import asyncio
import logging
import os
import re
import shutil
from collections import deque
from typing import Optional, Tuple

from Database.database import db, UserbotStatus

logger = logging.getLogger(__name__)

REPO_URL = "https://github.com/coddrago/Heroku"
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROFILES_DIR = os.path.join(PROJECT_ROOT, "Profile")
VENV_PYTHON = os.path.join(PROJECT_ROOT, ".venv", "bin", "python")
PUBLIC_WEB_URL_RE = re.compile(
    r"https://[^\s]+\.(?:serveousercontent\.com|lhr\.life)",
    re.IGNORECASE,
)


def _service_name(name: str) -> str:
    return f"openhost-{name.lower()}"


def _tunnel_service_name(name: str) -> str:
    return f"openhost-{name.lower()}-serveo"


def _userbot_log_path(name: str) -> str:
    ub = db.get_userbot(name)
    profile_path = ub.get("path") if ub else ""
    if not profile_path:
        profile_path = os.path.join(PROFILES_DIR, name)
    return os.path.join(profile_path, "Heroku", "heroku.log")


def _validate_name(name: str) -> bool:
    return bool(re.match(r"^[a-zA-Z]+$", name)) and len(name) <= 10


def _get_profiles_dir() -> str:
    os.makedirs(PROFILES_DIR, exist_ok=True)
    return PROFILES_DIR


async def _run(cmd: str, timeout: int = 120) -> Tuple[bool, str]:
    try:
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        ok = process.returncode == 0
        out = stdout.decode(errors="ignore").strip()
        err = stderr.decode(errors="ignore").strip()
        return ok, out or err
    except asyncio.TimeoutError:
        return False, "Превышено время выполнения"
    except Exception as e:
        return False, str(e)


def _make_service(name: str, workdir: str) -> str:
    return f"""[Unit]
Description=OpenHost Userbot - {name}
After=network.target

[Service]
Type=simple
WorkingDirectory={workdir}
ExecStart={VENV_PYTHON} -u -m heroku --root
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""


async def _clone_repo(name: str, clone_path: str) -> Tuple[bool, str]:
    return await _run(f"git clone {REPO_URL} {clone_path}")


async def _install_deps(clone_path: str) -> Tuple[bool, str]:
    req_file = os.path.join(clone_path, "requirements.txt")
    if os.path.exists(req_file):
        return await _run(f"{VENV_PYTHON} -m pip install -r {req_file} 2>&1", timeout=300)
    return True, ""


async def _create_systemd_service(name: str, workdir: str) -> str:
    user_cfg_dir = os.path.expanduser("~/.config/systemd/user")
    os.makedirs(user_cfg_dir, exist_ok=True)
    service_path = os.path.join(user_cfg_dir, f"{_service_name(name)}.service")
    with open(service_path, "w", encoding="utf-8") as f:
        f.write(_make_service(name, workdir))
    return service_path


async def _enable_start_service(name: str) -> Tuple[bool, str]:
    ok, msg = await _run("systemctl --user daemon-reload")
    if not ok:
        return False, msg
    ok, msg = await _run(f"systemctl --user enable --now {_service_name(name)}.service")
    if not ok:
        return False, msg
    await _run("loginctl enable-linger $(whoami) 2>/dev/null")
    return True, ""


def _extract_public_web_url(logs: str) -> Optional[str]:
    matches = PUBLIC_WEB_URL_RE.findall(logs)
    return matches[-1].strip().rstrip('.,);]') if matches else None


async def _wait_for_public_web_url(name: str, attempts: int = 120, delay: float = 0.5) -> Optional[str]:
    for attempt in range(1, attempts + 1):
        ok, logs = await get_logs(name, tail=200)
        if ok:
            url = _extract_public_web_url(logs)
            if url:
                logger.info(f"Юзербот {name}: найдена публичная ссылка {url}")
                return url
        if attempt < attempts:
            await asyncio.sleep(delay)
    return None


async def _remove_legacy_tunnel_service(name: str) -> None:
    tunnel_service = _tunnel_service_name(name)
    await _run(f"systemctl --user disable --now {tunnel_service}.service 2>/dev/null")
    await _run(f"rm -f ~/.config/systemd/user/{tunnel_service}.service")


async def get_registration_url(name: str) -> Tuple[bool, str, Optional[str]]:
    """Получает готовую Serveo-ссылку из heroku.log."""
    if not db.get_userbot(name):
        return False, "Юзербот не найден", None

    await _remove_legacy_tunnel_service(name)
    logger.info(f"Юзербот {name}: ожидание публичной ссылки в {_userbot_log_path(name)}")

    url = await _wait_for_public_web_url(name)
    if not url:
        logger.warning(f"Юзербот {name}: публичная ссылка не найдена в heroku.log")
        return False, f"Публичная ссылка не найдена в Profile/{name}/Heroku/heroku.log", None

    db.update_userbot_registration(name, 0, url)
    return True, "Ссылка регистрации найдена", url


async def create_userbot(name: str, user_id: int, created_by: str) -> Tuple[bool, str]:
    if not _validate_name(name):
        return False, "Некорректное имя. Только латиница, без цифр, макс. 10 символов"

    if db.get_userbot(name):
        return False, f"Юзербот «{name}» уже существует"

    profile_path = os.path.join(_get_profiles_dir(), name)
    clone_path = os.path.join(profile_path, "Heroku")

    if os.path.exists(profile_path):
        return False, f"Папка Profile/{name} уже существует"

    logger.info(f"Юзербот {name}: создание запросил {created_by} ({user_id})")
    db.add_userbot(name, user_id, created_by)

    try:
        os.makedirs(profile_path)
        logger.info(f"Юзербот {name}: создана папка профиля {profile_path}")

        ok, msg = await _clone_repo(name, clone_path)
        if not ok:
            raise RuntimeError(f"Ошибка клонирования: {msg}")
        logger.info(f"Юзербот {name}: репозиторий склонирован")

        ok, msg = await _install_deps(clone_path)
        if not ok:
            logger.warning(f"Ошибка установки зависимостей: {msg}")
        else:
            logger.info(f"Юзербот {name}: зависимости установлены")

        await _create_systemd_service(name, clone_path)
        logger.info(f"Юзербот {name}: systemd-сервис создан")
        ok, msg = await _enable_start_service(name)
        if not ok:
            raise RuntimeError(f"Ошибка запуска сервиса: {msg}")
        logger.info(f"Юзербот {name}: systemd-сервис запущен")

        db.update_userbot_path(name, profile_path)
        db.update_userbot_status(name, UserbotStatus.ON)

        return True, f"Юзербот «{name}» создан и запущен!"
    except Exception as e:
        db.delete_userbot(name)
        shutil.rmtree(profile_path, ignore_errors=True)
        logger.error(f"Ошибка создания юзербота {name}: {e}")
        return False, str(e)


async def start_userbot(name: str) -> Tuple[bool, str]:
    if not db.get_userbot(name):
        return False, "Юзербот не найден"

    ok, msg = await _run(f"systemctl --user start {_service_name(name)}.service")
    if ok:
        db.update_userbot_status(name, UserbotStatus.ON)
        logger.info(f"Юзербот {name}: запущен")
        return True, f"Юзербот «{name}» запущен"
    logger.error(f"Юзербот {name}: ошибка запуска: {msg}")
    return False, f"Ошибка запуска: {msg}"


async def stop_userbot(name: str) -> Tuple[bool, str]:
    if not db.get_userbot(name):
        return False, "Юзербот не найден"

    ok, msg = await _run(f"systemctl --user stop {_service_name(name)}.service")
    if ok:
        db.update_userbot_status(name, UserbotStatus.OFF)
        await _run(f"systemctl --user stop {_tunnel_service_name(name)}.service 2>/dev/null")
        logger.info(f"Юзербот {name}: остановлен")
        return True, f"Юзербот «{name}» остановлен"
    logger.error(f"Юзербот {name}: ошибка остановки: {msg}")
    return False, f"Ошибка остановки: {msg}"


async def restart_userbot(name: str) -> Tuple[bool, str]:
    if not db.get_userbot(name):
        return False, "Юзербот не найден"

    ok, msg = await _run(f"systemctl --user restart {_service_name(name)}.service")
    if ok:
        db.update_userbot_status(name, UserbotStatus.ON)
        logger.info(f"Юзербот {name}: перезапущен")
        return True, f"Юзербот «{name}» перезапущен"
    logger.error(f"Юзербот {name}: ошибка перезапуска: {msg}")
    return False, f"Ошибка перезапуска: {msg}"


async def delete_userbot(name: str) -> Tuple[bool, str]:
    ub = db.get_userbot(name)
    if not ub:
        return False, "Юзербот не найден"

    await _run(f"systemctl --user disable --now {_tunnel_service_name(name)}.service 2>/dev/null")
    await _run(f"rm -f ~/.config/systemd/user/{_tunnel_service_name(name)}.service")
    await _run(f"systemctl --user disable --now {_service_name(name)}.service 2>/dev/null")
    await _run(f"rm -f ~/.config/systemd/user/{_service_name(name)}.service")
    await _run("systemctl --user daemon-reload")

    profile_path = ub.get("path") or os.path.join(PROFILES_DIR, name)
    shutil.rmtree(profile_path, ignore_errors=True)

    db.delete_userbot(name)
    logger.info(f"Юзербот {name}: удалён")
    return True, f"Юзербот «{name}» удалён"


async def get_logs(name: str, tail: int = 50) -> Tuple[bool, str]:
    log_path = _userbot_log_path(name)
    if not os.path.exists(log_path):
        return False, f"Файл логов не найден: {log_path}"

    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = deque(f, maxlen=tail)
    except Exception as e:
        logger.warning(f"Юзербот {name}: ошибка чтения {log_path}: {e}")
        return False, f"Ошибка чтения логов: {e}"

    logs = "".join(lines).strip()
    if logs:
        return True, logs
    return False, "Логи пусты"
