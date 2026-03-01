from locust import HttpUser, task, between
import random

class ItemsUser(HttpUser):
    """
    Пользователь для нагрузочного тестирования Items API.
    Имитирует реальное поведение: просмотр списка, получение деталей, создание.
    """
    
    wait_time = between(0.5, 2)
    
    @task(5)
    def get_items_list(self):
        """Часто запрашиваем список товаров"""
        self.client.get("/items")
    
    @task(3)
    def get_item_detail(self):
        """Реже - детали конкретного товара"""
        item_id = random.randint(1, 50)
        self.client.get(f"/items/{item_id}")
    
    @task(1)
    def create_item(self):
        """Редко создаём новый товар"""
        payload = {
            "name": f"Test Item {random.randint(1000, 9999)}",
            "price": random.uniform(10, 500)
        }
        self.client.post("/items", json=payload)
