import os
import requests
from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pymongo.errors import PyMongoError

app = FastAPI()

# MongoDB connection
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
mongo_db_name = os.getenv("MONGO_DB", "inventory_db")

client = MongoClient(mongo_uri)
db = client[mongo_db_name]
collection = db["products"]


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
def get_single_product(product_id):
    try:
        product = collection.find_one({"ProductID": str(product_id)}, {"_id": 0})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/getAll")
def get_all():
    try:
        products = list(collection.find({}, {"_id": 0}))
        return products
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/addNew")
def add_new(
    ProductID,
    Name,
    UnitPrice,
    StockQuantity,
    Description
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
def delete_one(product_id):
    try:
        result = collection.delete_one({"ProductID": str(product_id)})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Product not found")

        return {"message": f"Product {product_id} deleted successfully"}

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/startsWith/{letter}")
def starts_with(letter):
    try:
        regex_pattern = f"^{letter}"
        products = list(
            collection.find(
                {"Name": {"$regex": regex_pattern, "$options": "i"}},
                {"_id": 0}
            )
        )
        return products
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/paginate/{start_id}/{end_id}")
def paginate(start_id, end_id):
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
        return products
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/convert/{product_id}")
def convert(product_id):
    try:
        product = collection.find_one({"ProductID": str(product_id)}, {"_id": 0})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        usd_price = float(product["UnitPrice"])

        exchange_response = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10)
        exchange_response.raise_for_status()
        exchange_data = exchange_response.json()

        eur_rate = exchange_data["rates"]["EUR"]
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