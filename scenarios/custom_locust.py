# scenarios/custom_locust.py
from locust import HttpUser, task, between

class CustomUser(HttpUser):
    wait_time = between(0.5, 2)

    @task
    def get_item(self):
        self.client.get("/items/42")