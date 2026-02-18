import subprocess
import time
import requests
from pathlib import Path
from typing import Dict, Any
from rich.console import Console  # ← добавь, если используешь rich везде

console = Console()

def run_load_test(
    module: str,
    duration: int,
    users: int,
    spawn_rate: float,
    host: str = "http://localhost:8000"
) -> Dict[str, Any]:
    """
    Запускает uvicorn + locust, ждёт завершения и возвращает пути к CSV.
    """
    tmp_dir = Path("tmp")
    tmp_dir.mkdir(exist_ok=True)
    csv_prefix = tmp_dir / "locust_results"

    try:
        # 1. Запуск uvicorn
        uvicorn_cmd = [
            "uv", "run", "uvicorn",
            module,
            "--host", "0.0.0.0",
            "--port", "8000",
            "--no-access-log",
            "--log-level", "error"
        ]
        console.print("[yellow]Запуск Uvicorn...[/yellow]")
        server_proc = subprocess.Popen(
            uvicorn_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # 2. Ожидание готовности сервера
        ready = False
        console.print("[yellow]Ожидание готовности сервера (до 15 сек)...[/yellow]")
        for _ in range(30):
            try:
                r = requests.get(f"{host}/health", timeout=2)
                if r.status_code == 200:
                    ready = True
                    console.print("[green]Сервер готов[/green]")
                    break
            except:
                time.sleep(0.5)
        
        if not ready:
            server_proc.terminate()
            server_proc.wait(timeout=5)
            return {"success": False, "error": "Сервер не запустился"}

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
        console.print(f"[yellow]Запуск Locust ({users} пользователей, {duration} сек)...[/yellow]")
        locust_proc = subprocess.Popen(
            locust_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # 4. Ожидание завершения Locust
        locust_proc.wait(timeout=duration + 30)
        console.print("[green]Locust завершил работу[/green]")

        # 5. Остановка uvicorn
        console.print("[yellow]Остановка сервера...[/yellow]")
        server_proc.terminate()
        server_proc.wait(timeout=10)

        # Проверка CSV
        if not Path(f"{csv_prefix}_stats.csv").exists():
            return {"success": False, "error": "CSV-файлы не созданы"}

        return {
            "success": True,
            "csv_prefix": str(csv_prefix),
            "error": None
        }

    except Exception as e:
        # Остановка при ошибке
        if 'server_proc' in locals():
            server_proc.terminate()
            server_proc.wait(timeout=5)
        if 'locust_proc' in locals():
            locust_proc.terminate()
            locust_proc.wait(timeout=5)
        
        return {"success": False, "error": str(e)}