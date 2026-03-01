import socket
import os
from myapiperf.orchestrator import find_free_port
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

def test_find_free_port_returns_valid_integer():
    """Проверяем, что порт — это число в допустимом диапазоне."""
    port = find_free_port()
    assert isinstance(port, int)
    assert 1024 <= port <= 65535

def test_find_free_port_is_actually_free():
    """Проверяем, что на полученном порту можно открыть соединение."""
    port = find_free_port()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Если порт занят, bind выкинет ошибку OSError
        s.bind(('', port)) 

def test_sequential_ports_are_different():
    """Проверяем, что два вызова подряд дают разные порты (обычно ОС их чередует)."""
    p1 = find_free_port()
    p2 = find_free_port()
    assert p1 != p2

def test_run_load_test_sla_failure(tmp_path, mocker):
    """
    Тестируем SLA failure, меняя рабочую директорию на временную.
    """
    # 1. Запоминаем текущую директорию, чтобы вернуться в неё потом
    old_cwd = os.getcwd()
    
    try:
        # Переходим во временную папку pytest
        os.chdir(tmp_path)
        
        # 2. Готовим данные
        timestamp = 12345
        mock_tmp_dir = Path("tmp")
        mock_tmp_dir.mkdir()
        
        # Префикс будет 'tmp/result_12345'
        csv_prefix = mock_tmp_dir / f"result_{timestamp}"
        stats_file = Path(f"{csv_prefix}_stats.csv")
        
        # Записываем плохие данные (500ms > 200ms)
        df = pd.DataFrame({
            "Name": ["Aggregated"],
            "Average Response Time": [500.0],
            "Request Count": [100],
            "Failure Count": [0]
        })
        df.to_csv(stats_file, index=False)

        # 3. Мокаем системные вызовы
        mocker.patch("subprocess.Popen")
        mocker.patch("subprocess.run")
        mocker.patch("requests.get").return_value.status_code = 200
        mocker.patch("time.time", return_value=timestamp)
        
        # Импортируем и запускаем
        from myapiperf.orchestrator import run_load_test
        
        results = run_load_test(
            module="examples.simple_api:app",
            duration=1,
            users=1,
            spawn_rate=1,
            max_avg_ms=200.0
        )

        # 4. Проверяем
        assert results["success"] is True, f"Ошибка: {results.get('error')}"
        assert results["sla_success"] is False, "SLA должен был провалиться (500 > 200)"
        assert "Latency" in results["sla_error"]

    finally:
        # Возвращаемся в исходную директорию в любом случае
        os.chdir(old_cwd)