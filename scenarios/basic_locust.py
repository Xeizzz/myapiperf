from locust import HttpUser, task, between
import random

class ApiUser(HttpUser):
    """
    Оптимизированный сценарий для выявления узких мест.
    """

    # Уменьшаем паузу, чтобы создать реальное давление на Semaphore(5)
    wait_time = between(0.1, 1.0)

    @task(4)
    def hit_fast(self):
        """Быстрые запросы создают 'фон' RPS"""
        self.client.get("/fast")

    @task(10) # Увеличиваем вес, чтобы целенаправленно забить "пул соединений"
    def hit_slow(self):
        """Медленные запросы, которые будут вставать в очередь"""
        self.client.get("/slow")

    @task(2)
    def create_user(self):
        payload = {
            "name": f"user_{random.randint(1000, 9999)}",
            "email": f"user{random.randint(1000, 9999)}@example.com"
        }
        # name="..." помогает группировать статистику в отчете, если URL меняются
        self.client.post("/users", json=payload, name="/users")

    @task(1)
    def health_check(self):
        self.client.get("/health")