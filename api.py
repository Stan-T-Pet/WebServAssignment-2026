import os
import requests
from typing import Annotated
from fastapi import FastAPI, HTTPException, Path, Query
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from prometheus_fastapi_instrumentator import Instrumentator

# Initialize FastAPI app and Prometheus instrumentation
app = FastAPI()
Instrumentator().instrument(app).expose(app)


# MongoDB connection
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
mongo_db_name = os.getenv("MONGO_DB", "inventory_db")

client = MongoClient(mongo_uri)
db = client[mongo_db_name]
collection = db["products"]

# Helper function to remove MongoDB's _id field from documents
# This ensures that the API responses do not include the internal MongoDB identifier.
def _strip_mongo_id(doc):
    if doc is None:
        return None
    if isinstance(doc, list):
        for item in doc:
            if isinstance(item, dict):
                item.pop("_id", None)
        return doc
    if isinstance(doc, dict):
        doc.pop("_id", None)
        return doc
    return doc


@app.get("/")
def home():
    return {
        "message": "Inventory API is running",
        "endpoints": [
            "/getSingleProduct/{product_id}",
            "/getAll",
            "/addNew",
            "/deleteOne/{product_id}",
            "/startsWith/{letter}",
            "/paginate/{start_id}/{end_id}",
            "/convert/{product_id}"
        ]
    }


@app.get("/getSingleProduct/{product_id}")
def get_single_product(product_id: str):
    try:
        product = collection.find_one({"ProductID": str(product_id)}, {"_id": 0})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return _strip_mongo_id(product)
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/getAll")
def get_all():
    try:
        products = list(collection.find({}, {"_id": 0}))
        return _strip_mongo_id(products)
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/addNew")
def add_new(
    ProductID: Annotated[str, Query(min_length=1)],
    Name: Annotated[str, Query(min_length=1)],
    UnitPrice: Annotated[float, Query(gt=0)],
    StockQuantity: Annotated[int, Query(ge=0)],
    Description: Annotated[str, Query(min_length=1)]
):
    try:
        existing = collection.find_one({"ProductID": str(ProductID)})
        if existing:
            raise HTTPException(status_code=400, detail="ProductID already exists")

        new_product = {
            "ProductID": str(ProductID),
            "Name": Name,
            "UnitPrice": str(UnitPrice),
            "StockQuantity": str(StockQuantity),
            "Description": Description
        }

        collection.insert_one(new_product)
        return {"message": "Product added successfully", "product": new_product}

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.delete("/deleteOne/{product_id}")
def delete_one(product_id: str):
    try:
        result = collection.delete_one({"ProductID": str(product_id)})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Product not found")

        return {"message": f"Product {product_id} deleted successfully"}

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/startsWith/{letter}")
def starts_with(letter: Annotated[str, Path(min_length=1, max_length=1)]):
    try:
        regex_pattern = f"^{letter}"
        products = list(
            collection.find(
                {"Name": {"$regex": regex_pattern, "$options": "i"}},
                {"_id": 0}
            )
        )
        return _strip_mongo_id(products)
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/paginate/{start_id}/{end_id}")
def paginate(start_id: str, end_id: str):
    try:
        products = list(
            collection.find(
                {
                    "ProductID": {
                        "$gte": str(start_id),
                        "$lte": str(end_id)
                    }
                },
                {"_id": 0}
            ).sort("ProductID", 1).limit(10)
        )
        return _strip_mongo_id(products)
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/convert/{product_id}")
def convert(product_id: str):
    try:
        product = collection.find_one({"ProductID": str(product_id)}, {"_id": 0})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        product = _strip_mongo_id(product)

        usd_price = float(product["UnitPrice"])

        # realtime Exchangerate API call to get current USD to EUR exchange rate
        exchangerate_key = os.getenv("EXCHANGE_RATE_API_KEY", "").strip()
        if exchangerate_key:
            # if key specified, use the official endpoint that requires the API key
            url = f"https://v6.exchangerate-api.com/v6/{exchangerate_key}/latest/USD"
        else:
            # Fallback endpoint no key required
            url = "https://open.er-api.com/v6/latest/USD"

        exchange_response = requests.get(url, timeout=10)
        exchange_response.raise_for_status()
        exchange_data = exchange_response.json()

        rates = exchange_data.get("conversion_rates") or exchange_data.get("rates") or {}
        eur_rate = rates.get("EUR")
        if eur_rate is None:
            raise HTTPException(status_code=500, detail="Exchange API error: EUR rate not found")

        eur_price = round(usd_price * eur_rate, 2)

        return {
            "ProductID": product["ProductID"],
            "Name": product["Name"],
            "PriceUSD": usd_price,
            "ExchangeRateUSDtoEUR": eur_rate,
            "PriceEUR": eur_price
        }

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Exchange API error: {str(e)}")
    except ValueError:
        raise HTTPException(status_code=500, detail="Invalid UnitPrice stored in database")
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")