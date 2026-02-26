from locust import HttpUser, task, between
import random

class ApiUser(HttpUser):
    """
    Пользователь для нагрузочного тестирования тестового API.
    Имитирует реальных пользователей: чаще быстрые запросы, реже медленные и POST.
    """

    wait_time = between(1, 5)

    @task(6)  # вес 6 — самый частый
    def hit_fast(self):
        """Часто вызываем быстрый эндпоинт"""
        self.client.get("/fast")

    @task(3)
    def hit_slow(self):
        """Реже медленный эндпоинт"""
        self.client.get("/slow")

    @task(2)
    def create_user(self):
        """Создаём пользователя (POST)"""
        payload = {
            "name": f"user_{random.randint(1000, 9999)}",
            "email": f"user{random.randint(1000, 9999)}@example.com"
        }
        self.client.post("/users", json=payload, name="/users (POST)")

    @task(1)
    def health_check(self):
        """Очень редко проверяем здоровье"""
        self.client.get("/health")