from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import time
import random

app = FastAPI(
    title="Test API for myapiperf",
    description="Простое приложение для тестирования нагрузочного инструмента",
    version="0.1.0"
)

class UserCreate(BaseModel):
    name: str
    email: str | None = None

@app.get("/fast")
async def fast_endpoint():
    return {"status": "ok", "message": "Это быстрый ответ"}

@app.get("/slow")
async def slow_endpoint():
    delay = random.uniform(0.5, 1.5)
    time.sleep(delay)
    return {"status": "ok", "message": f"Медленный ответ после {delay:.2f} сек"}

@app.post("/users")
async def create_user(user: UserCreate):
    time.sleep(0.3)
    if not user.name.strip():
        raise HTTPException(status_code=400, detail="Имя не может быть пустым")
    return {
        "id": random.randint(1000, 9999),
        "name": user.name,
        "email": user.email,
        "message": "Пользователь создан"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}