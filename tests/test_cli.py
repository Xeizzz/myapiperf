import pytest
from typer.testing import CliRunner
from myapiperf.cli import app
from unittest.mock import patch

runner = CliRunner()

def test_cli_profile_success():
    """Проверяем запуск без лишнего слова 'profile'."""
    with patch("myapiperf.cli.run_load_test") as mock_run, \
         patch("myapiperf.cli.generate_report") as mock_report:
        
        mock_run.return_value = {
            "success": True, 
            "csv_prefix": "tmp/test", 
            "sla_success": True
        }
        mock_report.return_value = "report.html"


        result = runner.invoke(app, [
            "examples.simple_api:app", 
            "--users", "5", 
            "--duration", "10"
        ])

        if result.exit_code != 0:
            print(result.output)

        assert result.exit_code == 0
        assert "Запуск профилирования" in result.stdout

def test_cli_sla_failure_exit_code():
    """Проверяем выход с кодом 1 при провале SLA."""
    with patch("myapiperf.cli.run_load_test") as mock_run, \
         patch("myapiperf.cli.generate_report") as mock_report:
        
        mock_run.return_value = {
            "success": True, 
            "csv_prefix": "tmp/test", 
            "sla_success": False,
            "sla_error": "Latency too high"
        }
        mock_report.return_value = "report.html"

        result = runner.invoke(app, [
            "examples.simple_api:app", 
            "--max-avg-ms", "100"
        ])

        assert result.exit_code == 1
        assert "SLA НАРУШЕН" in result.stdout