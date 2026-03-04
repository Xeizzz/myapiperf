from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import random
import time

app = FastAPI(
    title="Bottleneck Demo API",
    description="API с искусственным ограничением ресурсов для проверки графиков",
    version="0.2.0"
)

# Имитируем пул соединений к базе данных (всего 5 одновременных запросов)
# Это создаст "бутылочное горлышко"
db_semaphore = asyncio.Semaphore(5)

class UserCreate(BaseModel):
    name: str
    email: str | None = None

@app.get("/fast")
async def fast_endpoint():
    # Быстрый эндпоинт, не трогающий "базу"
    return {"status": "ok", "type": "fast"}

@app.get("/slow")
async def slow_endpoint():
    """
    Эндпоинт, имитирующий работу с БД через семафор.
    Если придет 10 человек, 5 будут ждать, пока первые 5 закончат.
    """
    async with db_semaphore:
        # Случайная работа "базы" от 0.1 до 0.5 сек
        delay = random.uniform(0.1, 0.5)
        await asyncio.sleep(delay)
        return {"status": "ok", "waited": f"{delay:.2f}s"}

@app.post("/users")
async def create_user(user: UserCreate):
    # Имитируем тяжелую запись с блокировкой
    async with db_semaphore:
        await asyncio.sleep(0.3)
        if not user.name.strip():
            raise HTTPException(status_code=400, detail="Empty name")
        return {"id": random.randint(1, 100), "name": user.name}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}