import time
import threading
import requests
import random
import logging
import os
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Shop Frontend Microservice")
ORDER_URL = os.environ.get("ORDER_SERVICE_URL", "http://order-backend:8082/order")

def bg_loop():
    while True:
        try:
            # Random traffic simulation
            time.sleep(random.uniform(1.0, 3.0))
            if random.random() < 0.8: # 80% chance to make an order
                resp = requests.post(ORDER_URL, json={"item": "book", "qty": 1}, timeout=5)
                logger.info(f"Placed order, status: {resp.status_code}")
        except Exception as e:
            logger.error(f"Error calling order backend: {e}")

@app.on_event("startup")
def startup():
    threading.Thread(target=bg_loop, daemon=True).start()

@app.get("/health")
def health():
    return {"status": "ok", "service": "shop-frontend"}
