import subprocess
import time
import requests
import socket
from pathlib import Path
from typing import Dict, Any
from rich.console import Console 

console = Console()

def find_free_port() -> int:
    """Находит любой свободный порт в системе."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

def run_load_test(
    module: str,
    duration: int,
    users: int,
    spawn_rate: float,
) -> Dict[str, Any]:
    tmp_dir = Path("tmp")
    tmp_dir.mkdir(exist_ok=True)
    # Уникальный префикс для CSV, чтобы не было конфликтов
    timestamp = int(time.time())
    csv_prefix = tmp_dir / f"result_{timestamp}"
    
    port = find_free_port()
    host = f"http://127.0.0.1:{port}"
    
    server_proc = None

    try:
        # 1. Запуск Uvicorn на найденном порту
        uvicorn_cmd = [
            "uv", "run", "uvicorn", module,
            "--host", "127.0.0.1",
            "--port", str(port),
            "--no-access-log",
            "--log-level", "error"
        ]
        console.print(f"[yellow]🚀 Запуск сервера на порту {port}...[/yellow]")
        server_proc = subprocess.Popen(uvicorn_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 2. Ожидание готовности
        ready = False
        for _ in range(30):
            try:
                if requests.get(f"{host}/health", timeout=1).status_code == 200:
                    ready = True
                    break
            except:
                pass
            time.sleep(0.5)
        
        if not ready:
            raise Exception(f"Сервер не ответил на {host}/health")

        # 3. Запуск Locust
        locust_cmd = [
            "uv", "run", "locust",
            "-f", "scenarios/basic_locust.py",
            "--headless",
            "--host", host,
            "--users", str(users),
            "--spawn-rate", str(spawn_rate),
            "--run-time", f"{duration}s",
            "--csv", str(csv_prefix)
        ]
        
        console.print(f"[green]🔥 Нагружаем {users} пользователей (порт {port})...[/green]")
        subprocess.run(locust_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 4. Завершение
        server_proc.terminate()
        server_proc.wait(timeout=5)

        return {
            "success": True,
            "csv_prefix": str(csv_prefix),
            "port": port
        }

    except Exception as e:
        if server_proc: server_proc.terminate()
        return {"success": False, "error": str(e)}