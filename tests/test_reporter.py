import pytest
import pandas as pd
from pathlib import Path
from myapiperf.reporter import generate_report

def test_generate_report_success(tmp_path):
    """
    Проверяем успешную генерацию отчета при наличии всех файлов.
    """
    # 1. Подготовка фейковых данных
    csv_prefix = tmp_path / "test_perf"
    stats_file = Path(f"{csv_prefix}_stats.csv")
    history_file = Path(f"{csv_prefix}_stats_history.csv")
    output_html = tmp_path / "report.html"

    # Создаем основной отчет
    stats_df = pd.DataFrame({
        "Name": ["/test", "Aggregated"],
        "Request Count": [100, 100],
        "Requests/s": [10.5, 10.5],
        "Failure Count": [0, 0],
        "95%": [150, 150],
        "Average Response Time": [80, 80]
    })
    stats_df.to_csv(stats_file, index=False)

    # Создаем историю для графика
    history_df = pd.DataFrame({
        "Requests/s": [5, 10, 15],
        "Total Average Response Time": [70, 80, 90],
        "Total Max Response Time": [100, 110, 120]
    })
    history_df.to_csv(history_file, index=False)

    # 2. Вызов функции (убедись, что папка templates доступна)
    # Если запуск из корня, Jinja2 найдет templates/report.html
    report_path = generate_report(
        csv_prefix=str(csv_prefix),
        output_path=str(output_html),
        module="my_app:app",
        duration=30,
        users=5,
        success=True
    )

    # 3. Проверки
    assert Path(report_path).exists()
    content = Path(report_path).read_text()
    assert "my_app:app" in content
    assert "10.5" in content  # Проверка RPS в тексте
    assert 'id="timeline-plot"' in content # Проверка, что блок графика на месте

def test_generate_report_no_history(tmp_path):
    """
    Проверяем, что репортер не падает, если файла истории нет (короткий тест).
    """
    csv_prefix = tmp_path / "no_history"
    stats_file = Path(f"{csv_prefix}_stats.csv")
    output_html = tmp_path / "report_no_hist.html"

    stats_df = pd.DataFrame({
        "Name": ["Aggregated"],
        "Request Count": [10],
        "Requests/s": [1.0],
        "Failure Count": [0],
        "95%": [100],
        "Average Response Time": [50]
    })
    stats_df.to_csv(stats_file, index=False)

    # Файл _stats_history.csv НЕ создаем

    report_path = generate_report(
        csv_prefix=str(csv_prefix),
        output_path=str(output_html),
        module="test:app",
        duration=5,
        users=1,
        success=True
    )

    assert Path(report_path).exists()
    content = Path(report_path).read_text()
    assert "Данные истории недоступны" in content or "timeline-plot" in content