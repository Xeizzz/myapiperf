import pandas as pd
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import plotly.express as px
import plotly.io as pio
from typing import Dict, Any

def generate_report(
    csv_prefix: str,
    output_path: str = "report.html",
    module: str = "unknown",
    duration: int = 0,
    users: int = 0,
    success: bool = True,
    error: str = None
) -> str:
    """
    Генерирует красивый HTML-отчёт на основе CSV от Locust.
    """
    env = Environment(loader=FileSystemLoader("templates"))
    try:
        template = env.get_template("report.html")
    except Exception as e:
        raise RuntimeError(f"Не удалось загрузить шаблон report.html: {e}")

    # Основной файл — stats
    stats_file = Path(f"{csv_prefix}_stats.csv")
    if not stats_file.exists():
        raise FileNotFoundError(f"Основной CSV не найден: {stats_file}")

    try:
        df = pd.read_csv(stats_file)
    except Exception as e:
        raise RuntimeError(f"Ошибка чтения CSV: {e}")

    # Нормализация колонок (Locust может менять названия в разных версиях)
    column_map = {
        "Name": "Endpoint",
        "Request Count": "Count",
        "# requests": "Count",
        "Failures": "Failures",
        "Failure Count": "Failures",
        "Median response time": "Median (ms)",
        "50%": "Median (ms)",
        "Average response time": "Avg (ms)",
        "Min response time": "Min (ms)",
        "Max response time": "Max (ms)",
        "Requests/s": "RPS",
        "Requests /s": "RPS"
    }

    df = df.rename(columns={k: v for k, v in column_map.items() if k in df.columns})

    # Убираем строку Aggregated
    df = df[df["Endpoint"] != "Aggregated"].copy()

    # Таблица
    table_html = df.to_html(
        index=False,
        classes="table",
        float_format="%.2f",
        border=0,
        escape=False
    )

    # График RPS (если колонка есть)
    if "RPS" in df.columns and "Endpoint" in df.columns:
        fig = px.bar(
            df,
            x="Endpoint",
            y="RPS",
            title="Requests per Second по эндпоинтам",
            labels={"RPS": "Запросов в секунду"},
            color="Endpoint",
            height=500
        )
        fig.update_layout(showlegend=False, xaxis_tickangle=-45)
        rps_plot = fig.to_json()
    else:
        rps_plot = "{}"  # пустой график

    # Рендеринг
    html_content = template.render(
        module=module,
        duration=duration,
        users=users,
        success=success,
        error=error,
        table_html=table_html,
        rps_plot=rps_plot
    )

    Path(output_path).write_text(html_content, encoding="utf-8")
    return output_path