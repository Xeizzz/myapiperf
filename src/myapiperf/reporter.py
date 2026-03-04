import pandas as pd
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import plotly.graph_objects as go
import json
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def generate_report(
    csv_prefix: str,
    output_path: str = "report.html",
    module: str = "unknown",
    duration: int = 0,
    users: int = 0,
    success: bool = True,
    error: str = None
) -> str:
    template_dir = Path("templates")
    template_dir.mkdir(exist_ok=True)
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    
    try:
        template = env.get_template("report.html")
    except Exception as e:
        logger.error(f"Шаблон не найден: {e}")
        raise

    # 1. Загрузка статистики
    stats_file = Path(f"{csv_prefix}_stats.csv")
    if not stats_file.exists():
        raise FileNotFoundError(f"Файл статистики не найден: {stats_file}")

    df_stats = pd.read_csv(stats_file)
    agg_row = df_stats[df_stats["Name"] == "Aggregated"].iloc[0]
    
    kpis = {
        "total_req": int(agg_row.get("Request Count", 0)),
        "avg_rps": round(float(agg_row.get("Requests/s", 0)), 2),
        "fail_rate": round((agg_row.get("Failure Count", 0) / agg_row.get("Request Count", 1) * 100), 2),
        "p95": agg_row.get("95%", 0)
    }

    df_display = df_stats[df_stats["Name"] != "Aggregated"].copy()
    table_html = df_display.to_html(index=False, classes="table", border=0)

    # 2. Построение графика с контекстом
    history_file = Path(f"{csv_prefix}_stats_history.csv")
    timeline_json = "{}"
    
    if history_file.exists():
        try:
            df_hist = pd.read_csv(history_file)
            x_axis = range(len(df_hist)) 
            
            fig = go.Figure()

            # ФОН: Пользователи (User Count)
            fig.add_trace(go.Scatter(
                x=list(x_axis), y=df_hist["User Count"],
                name="Юзеры", fill='tozeroy',
                fillcolor='rgba(226, 232, 240, 0.4)',
                line=dict(width=0), yaxis="y3"
            ))

            # ЛИНИЯ 1: RPS
            fig.add_trace(go.Scatter(
                x=list(x_axis), y=df_hist["Requests/s"],
                name="RPS", line=dict(color='#3b82f6', width=3, shape='spline')
            ))

            # ЛИНИЯ 2: Средняя задержка
            fig.add_trace(go.Scatter(
                x=list(x_axis), y=df_hist["Total Average Response Time"],
                name="Avg Latency (ms)", yaxis="y2",
                line=dict(color='#10b981', width=2)
            ))

            # ЛИНИЯ 3: Максимальная задержка (Пики)
            if "Total Max Response Time" in df_hist.columns:
                fig.add_trace(go.Scatter(
                    x=list(x_axis), y=df_hist["Total Max Response Time"],
                    name="Max Latency", yaxis="y2",
                    line=dict(color='#ef4444', width=1, dash='dot'),
                    opacity=0.5
                ))

            fig.update_layout(
                template="plotly_white",
                hovermode="x unified",
                margin=dict(l=0, r=0, t=40, b=0),
                legend=dict(orientation="h", y=1.15, x=0.5, xanchor="center"),
                xaxis=dict(title="Время (интервалы)", gridcolor='#f1f5f9'),
                yaxis=dict(title="RPS", color="#3b82f6", side="left", rangemode="tozero"),
                yaxis2=dict(title="Latency (ms)", color="#10b981", overlaying="y", side="right", showgrid=False, rangemode="tozero"),
                yaxis3=dict(overlaying="y", visible=False, range=[0, df_hist["User Count"].max() * 1.5])
            )
            timeline_json = fig.to_json()
        except Exception as e:
            logger.error(f"Ошибка при обработке истории: {e}")

    html_content = template.render(
        module=module, duration=duration, users=users,
        success=success, error=error, table_html=table_html,
        timeline_plot=timeline_json, kpis=kpis
    )

    Path(output_path).write_text(html_content, encoding="utf-8")
    return output_path