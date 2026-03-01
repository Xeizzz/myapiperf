from fastapi import FastAPI, Query
import asyncio
import random

app = FastAPI(title="Products API")

# Имитация базы данных
PRODUCTS = [
    {"id": i, "name": f"Product {i}", "price": random.randint(10, 1000)}
    for i in range(100)
]

@app.get("/products")
async def get_products(category: str = None):
    # Имитируем тяжелый запрос к БД
    await asyncio.sleep(random.uniform(0.1, 0.3))
    return PRODUCTS[:10]

@app.get("/search")
async def search(q: str = Query(...)):
    # Поиск работает еще медленнее
    await asyncio.sleep(random.uniform(0.5, 1.0))
    return [p for p in PRODUCTS if q.lower() in p["name"].lower()]

@app.get("/health")
async def health():
    return {"status": "ok"}