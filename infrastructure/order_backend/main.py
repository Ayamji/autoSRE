import os
import requests
import logging
from fastapi import FastAPI, HTTPException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Order Backend Microservice")
PAYMENT_URL = os.environ.get("PAYMENT_SERVICE_URL", "http://faulty-service:8080/health")

@app.post("/order")
def create_order():
    # Process order
    logger.info("Processing new order...")
    try:
        # Call the payment/inventory service
        resp = requests.get(PAYMENT_URL, timeout=5)
        if resp.status_code != 200:
            logger.error(f"Payment service returned {resp.status_code}")
            raise HTTPException(status_code=502, detail="Payment gateway error")
    except requests.exceptions.RequestException as e:
        logger.error(f"Payment service failed: {e}")
        raise HTTPException(status_code=503, detail="Payment service unavailable")
    
    return {"status": "success", "order_id": "ord_123"}

@app.get("/health")
def health():
    return {"status": "ok", "service": "order-backend"}
