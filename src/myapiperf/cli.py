import typer
from rich.console import Console
from rich.panel import Panel
from .orchestrator import run_load_test
from .reporter import generate_report

app = typer.Typer(
    name="myapiperf",
    help="Инструмент для нагрузочного тестирования REST API",
    add_completion=False,
)
console = Console()

@app.command()
def profile(
    module: str = typer.Argument(..., help="Путь к FastAPI-приложению (пример: examples.simple_api:app)"),
    duration: int = typer.Option(60, "--duration", "-d", help="Длительность нагрузки в секундах"),
    users: int = typer.Option(20, "--users", "-u", help="Количество виртуальных пользователей"),
    spawn_rate: float = typer.Option(5.0, "--spawn-rate", help="Скорость появления пользователей (пользователей/сек)"),
    output: str = typer.Option("report.html", "--output", "-o", help="Путь к выходному отчёту"),
    max_avg_ms: float = typer.Option(None, "--max-avg-ms", help="SLA: Макс. среднее время ответа в мс"),
    max_fail_rate: float = typer.Option(None, "--max-fail-rate", help="SLA: Максимальный % ошибок (0-100)"),
):
    """
    Запуск нагрузочного тестирования и генерация отчёта.
    """
    

    sla_info = f"SLA: {max_avg_ms}ms / {max_fail_rate}%" if max_avg_ms or max_fail_rate else "SLA: Не задан"

    console.print(Panel.fit(
        f"[bold]Запуск профилирования[/bold]\n"
        f"Модуль: {module}\n"
        f"Длительность: {duration} сек | Пользователи: {users}\n"
        f"Скорость: {spawn_rate}/сек\n"
        f"{sla_info}",
        title="myapiperf",
        border_style="green"
    ))

    try:

        results = run_load_test(
            module=module,
            duration=duration,
            users=users,
            spawn_rate=spawn_rate,
            max_avg_ms=max_avg_ms,
            max_fail_rate=max_fail_rate
        )
        
        if results["success"]:

            sla_passed = results.get("sla_success", True)
            
            if sla_passed:
                console.print("[bold green]✅ Нагрузка завершена. Все критерии SLA соблюдены![/bold green]")
            else:
                console.print("[bold yellow]⚠️ Нагрузка завершена, но SLA НАРУШЕН![/bold yellow]")
                console.print(f"[red]Причина: {results.get('sla_error')}[/red]")
            

            report_path = generate_report(
                csv_prefix=results["csv_prefix"],
                output_path=output,
                module=module,
                duration=duration,
                users=users,
                success=sla_passed,
                error=results.get("sla_error") # Передаем текст ошибки SLA в отчет
            )
            
            console.print(f"[bold cyan]Отчёт сохранён: {report_path}[/bold cyan]")
            typer.launch(report_path) 


            if not sla_passed:
                raise typer.Exit(code=1)
                
        else:
            console.print("[bold red]❌ Ошибка во время нагрузки[/bold red]")
            console.print(results.get("error", "Неизвестная ошибка"))
            raise typer.Exit(code=1)
            
    except Exception as e:
        console.print(f"[bold red]Критическая ошибка: {str(e)}[/bold red]")
        raise typer.Exit(code=1)


def main():
    app()

if __name__ == "__main__":
    main()