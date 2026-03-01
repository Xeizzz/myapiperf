from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import random

app = FastAPI(title="Items API")

# Имитация базы данных
ITEMS = [
    {"id": i, "name": f"Item {i}", "price": random.randint(10, 500)}
    for i in range(100)
]

class ItemCreate(BaseModel):
    name: str
    price: float

@app.get("/items")
async def get_items():
    """Получить список всех товаров"""
    await asyncio.sleep(random.uniform(0.05, 0.15))
    return ITEMS[:20]

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    """Получить товар по ID"""
    await asyncio.sleep(random.uniform(0.02, 0.08))
    item = next((i for i in ITEMS if i["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.post("/items")
async def create_item(item: ItemCreate):
    """Создать новый товар"""
    await asyncio.sleep(random.uniform(0.1, 0.3))
    new_item = {
        "id": len(ITEMS) + 1,
        "name": item.name,
        "price": item.price
    }
    ITEMS.append(new_item)
    return new_item

@app.get("/health")
async def health():
    return {"status": "ok"}
