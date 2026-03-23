import asyncio
import logging
import os
import re
import docker

logger = logging.getLogger(__name__)

HEROKU_IMAGE = "openhost-heroku"
HEROKU_REPO = "https://github.com/coddrago/Heroku.git"
CONTAINER_PORT = 8080
DOCKERFILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Docker")

# Хранилище SSH-туннелей: user_id -> asyncio.subprocess.Process
_tunnel_processes: dict[int, asyncio.subprocess.Process] = {}


def get_client() -> docker.DockerClient:
    return docker.from_env()


def is_image_built() -> bool:
    """Проверяет есть ли собранный образ."""
    try:
        client = get_client()
        client.images.get(HEROKU_IMAGE)
        return True
    except docker.errors.ImageNotFound:
        return False
    except docker.errors.DockerException:
        return False


async def build_image(progress_callback=None) -> bool:
    """Собирает Docker-образ. Возвращает True при успехе."""
    client = get_client()

    if progress_callback:
        await progress_callback("Собираем Docker-образ... Это может занять 5-10 минут.")

    try:
        _, logs = await asyncio.to_thread(
            client.images.build,
            path=DOCKERFILE_DIR,
            tag=HEROKU_IMAGE,
            rm=True,
        )
        logger.info("Docker image built successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to build image: {e}")
        return False


def get_user_container_name(user_id: int) -> str:
    return f"openhost-{user_id}"


def get_user_container(user_id: int) -> docker.models.containers.Container | None:
    client = get_client()
    name = get_user_container_name(user_id)
    try:
        return client.containers.get(name)
    except docker.errors.NotFound:
        return None


def is_user_container_running(user_id: int) -> bool:
    container = get_user_container(user_id)
    return container is not None and container.status == "running"


async def create_container(user_id: int) -> tuple[docker.models.containers.Container, int]:
    """Создаёт контейнер с Heroku для пользователя. Возвращает (container, port)."""
    client = get_client()
    name = get_user_container_name(user_id)

    existing = get_user_container(user_id)
    if existing:
        if existing.status == "running":
            bindings = existing.ports.get(f"{CONTAINER_PORT}/tcp") or [{}]
            port = int(bindings[0].get("HostPort", 0))
            return existing, port
        existing.remove(force=True)

    # Docker сам назначит свободный порт (0 = автовыбор)
    container = await asyncio.to_thread(
        client.containers.run,
        HEROKU_IMAGE,
        name=name,
        detach=True,
        restart_policy={"Name": "unless-stopped"},
        ports={f"{CONTAINER_PORT}/tcp": 0},
        volumes={f"openhost-data-{user_id}": {"bind": "/data", "mode": "rw"}},
        mem_limit="512m",
        cpu_period=100000,
        cpu_quota=50000,
        pids_limit=256,
    )

    # Перечитываем контейнер чтобы получить назначенный порт
    container.reload()
    bindings = container.ports.get(f"{CONTAINER_PORT}/tcp") or [{}]
    port = int(bindings[0].get("HostPort", 0))

    return container, port


async def start_tunnel(user_id: int, port: int) -> str | None:
    """Пробрасывает SSH-туннель через serveo.net, fallback на localhost.run.
    Возвращает публичный URL или None."""

    # Убиваем старый туннель если есть
    await stop_tunnel(user_id)

    for cmd in [
        ["ssh", "-o", "StrictHostKeyChecking=no", "-R", f"80:127.0.0.1:{port}", "serveo.net"],
        ["ssh", "-o", "StrictHostKeyChecking=no", "-R", f"80:127.0.0.1:{port}", "nokey@localhost.run"],
    ]:
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            for _ in range(30):
                await asyncio.sleep(0.5)
                if proc.stdout is None:
                    break
                try:
                    line = await asyncio.wait_for(proc.stdout.readline(), timeout=0.5)
                except asyncio.TimeoutError:
                    continue
                decoded = line.decode(errors="ignore")
                match = re.search(r"https?://\S+", decoded)
                if match:
                    _tunnel_processes[user_id] = proc
                    return match.group(0).strip()

            proc.terminate()
            await proc.wait()
        except Exception as e:
            logger.warning(f"Tunnel failed with {cmd}: {e}")
            continue

    return None


async def stop_tunnel(user_id: int):
    """Останавливает SSH-туннель пользователя."""
    proc = _tunnel_processes.pop(user_id, None)
    if proc and proc.returncode is None:
        proc.terminate()
        await proc.wait()


async def stop_container(user_id: int) -> bool:
    """Останавливает контейнер и туннель пользователя."""
    await stop_tunnel(user_id)

    container = get_user_container(user_id)
    if container is None:
        return False
    await asyncio.to_thread(container.stop)
    await asyncio.to_thread(container.remove)
    return True
