import subprocess
import time
import requests
import socket
import pandas as pd  # Добавили для анализа SLA
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
    max_avg_ms: float = None,  
    max_fail_rate: float = None 
) -> Dict[str, Any]:
    tmp_dir = Path("tmp")
    tmp_dir.mkdir(exist_ok=True)
    timestamp = int(time.time())
    csv_prefix = tmp_dir / f"result_{timestamp}"
    
    port = find_free_port()
    host = f"http://127.0.0.1:{port}"
    server_proc = None

    try:
        # 1. Запуск Uvicorn
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
        
        # 4. Завершение серверного процесса
        if server_proc:
            server_proc.terminate()
            server_proc.wait(timeout=5)

        # --- НОВОЕ: Логика проверки SLA ---
        sla_success = True
        sla_error = None
        
        stats_path = Path(f"{csv_prefix}_stats.csv")
        if stats_path.exists():
            df = pd.read_csv(stats_path)
            # Берем строку Aggregated (итог всего теста)
            agg = df[df["Name"] == "Aggregated"].iloc[0]
            
            avg_ms = agg.get("Average Response Time", 0)
            req_count = agg.get("Request Count", 1)
            fail_count = agg.get("Failure Count", 0)
            fail_rate = (fail_count / req_count) * 100

            errors = []
            if max_avg_ms and avg_ms > max_avg_ms:
                errors.append(f"Latency: {avg_ms:.2f}ms > {max_avg_ms}ms")
            if max_fail_rate is not None and fail_rate > max_fail_rate:
                errors.append(f"Fail Rate: {fail_rate:.2f}% > {max_fail_rate}%")
            
            if errors:
                sla_success = False
                sla_error = " | ".join(errors)

        return {
            "success": True,
            "csv_prefix": str(csv_prefix),
            "port": port,
            "sla_success": sla_success,
            "sla_error": sla_error
        }

    except Exception as e:
        if server_proc: 
            server_proc.terminate()
        return {"success": False, "error": str(e)}