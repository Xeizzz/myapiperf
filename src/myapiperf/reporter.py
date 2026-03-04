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
    # Настройка Jinja2
    template_dir = Path("templates")
    template_dir.mkdir(exist_ok=True)
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    
    try:
        template = env.get_template("report.html")
    except Exception as e:
        logger.error(f"Шаблон не найден в {template_dir}/report.html. Ошибка: {e}")
        raise


    stats_file = Path(f"{csv_prefix}_stats.csv")
    if not stats_file.exists():
        raise FileNotFoundError(f"Файл статистики не найден: {stats_file}")

    df_stats = pd.read_csv(stats_file)
    

    agg_mask = df_stats["Name"] == "Aggregated"
    if agg_mask.any():
        agg_row = df_stats[agg_mask].iloc[0]
        kpis = {
            "total_req": int(agg_row.get("Request Count", 0)),
            "avg_rps": round(float(agg_row.get("Requests/s", 0)), 2),
            "fail_rate": round((agg_row.get("Failure Count", 0) / agg_row.get("Request Count", 1) * 100), 2),
            "p95": agg_row.get("95%", 0)
        }
    else:
        kpis = {"total_req": 0, "avg_rps": 0, "fail_rate": 0, "p95": 0}


    df_display = df_stats[df_stats["Name"] != "Aggregated"].copy()
    table_html = df_display.to_html(index=False, classes="table", border=0, justify="left")


    history_file = Path(f"{csv_prefix}_stats_history.csv")
    timeline_json = "{}"
    
    if history_file.exists():
        try:
            df_hist = pd.read_csv(history_file)

            x_axis = range(len(df_hist)) 
            
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=list(x_axis), y=df_hist["Requests/s"],
                name="RPS", line=dict(color='#3498db', width=3)
            ))

            fig.add_trace(go.Scatter(
                x=list(x_axis), y=df_hist["Total Average Response Time"],
                name="Avg Response Time (ms)", yaxis="y2", line=dict(color='#e74c3c', width=2, dash='dot')
            ))

            fig.update_layout(
                title="Динамика производительности во времени",
                template="plotly_white",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                yaxis=dict(title="Requests per Second (RPS)", color="#3498db"),
                yaxis2=dict(title="Response Time (ms)", color="#e74c3c", overlaying="y", side="right"),
                margin=dict(l=50, r=50, t=80, b=50)
            )
            timeline_json = fig.to_json()
        except Exception as e:
            logger.error(f"Ошибка при обработке истории: {e}")

            

    # Рендеринг HTML
    html_content = template.render(
        module=module,
        duration=duration,
        users=users,
        success=success,
        error=error,
        table_html=table_html,
        timeline_plot=timeline_json,
        kpis=kpis
    )

    Path(output_path).write_text(html_content, encoding="utf-8")
    logger.info(f"Отчет успешно создан: {output_path}")
    return output_path