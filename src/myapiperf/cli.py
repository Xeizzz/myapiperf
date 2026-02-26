import typer
from rich.console import Console
from rich.panel import Panel
from .orchestrator import run_load_test
from .reporter import generate_report

# Создаем объект приложения Typer
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
):
    """
    Запуск нагрузочного тестирования и генерация отчёта.
    """
    console.print(Panel.fit(
        f"[bold]Запуск профилирования[/bold]\n"
        f"Модуль: {module}\n"
        f"Длительность: {duration} сек\n"
        f"Пользователи: {users}\n"
        f"Скорость появления: {spawn_rate}/сек",
        title="myapiperf",
        border_style="green"
    ))

    try:
        # Оркестратор сам найдет свободный порт, поэтому host больше не нужен в аргументах
        results = run_load_test(
            module=module,
            duration=duration,
            users=users,
            spawn_rate=spawn_rate
        )
        
        if results["success"]:
            console.print("[bold green]Нагрузка завершена успешно[/bold green]")
            
            report_path = generate_report(
                csv_prefix=results["csv_prefix"],
                output_path=output,
                module=module,
                duration=duration,
                users=users,
                success=True
            )
            
            console.print(f"[bold cyan]Отчёт сохранён: {report_path}[/bold cyan]")
            # Автоматическое открытие отчета в браузере
            typer.launch(report_path)  
        else:
            console.print("[bold red]Ошибка во время нагрузки[/bold red]")
            console.print(results.get("error", "Неизвестная ошибка"))
            
    except Exception as e:
        console.print(f"[bold red]Критическая ошибка: {str(e)}[/bold red]")
        raise typer.Exit(code=1)

# ЭТА ФУНКЦИЯ ДОЛЖНА БЫТЬ ЯВНО ОПРЕДЕЛЕНА ДЛЯ ENTRY POINTS
def main():
    app()

if __name__ == "__main__":
    main()