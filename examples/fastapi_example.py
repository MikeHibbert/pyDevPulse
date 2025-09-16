"""Example FastAPI application with DevPulse integration."""

import logging
import random
import time
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

import devpulse
from devpulse.integrations import add_devpulse_middleware

# Initialize DevPulse
devpulse.init(websocket_url="ws://localhost:8000/ws")

# Create FastAPI app
app = FastAPI(title="DevPulse FastAPI Example")

# Add DevPulse middleware
add_devpulse_middleware(app)

# Setup logger
logger = logging.getLogger("example")
logger.setLevel(logging.INFO)


class Item(BaseModel):
    """Example item model."""

    name: str
    price: float
    is_offer: bool = False


@app.get("/")
async def read_root():
    """Root endpoint."""
    logger.info("Root endpoint called")
    return {"Hello": "World"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    """Get an item by ID."""
    logger.info(f"Getting item {item_id}")

    # Simulate random errors for demonstration
    if random.random() < 0.2:
        logger.error(f"Error getting item {item_id}")
        raise HTTPException(status_code=500, detail="Internal server error")

    # Simulate slow response for demonstration
    if random.random() < 0.3:
        time.sleep(2)
        logger.warning(f"Slow response for item {item_id}")

    return {"item_id": item_id, "q": q}


@app.post("/items/")
async def create_item(item: Item):
    """Create a new item."""
    logger.info(f"Creating item {item.name}")

    # Simulate validation error for demonstration
    if item.price < 0:
        logger.error(f"Invalid price for item {item.name}")
        raise HTTPException(status_code=400, detail="Price must be positive")

    return {"item_name": item.name, "price": item.price}


@app.get("/error")
async def trigger_error():
    """Endpoint that always raises an error."""
    logger.info("Error endpoint called")

    # Simulate a division by zero error
    try:
        1 / 0
    except Exception as e:
        logger.exception(f"Division by zero error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)