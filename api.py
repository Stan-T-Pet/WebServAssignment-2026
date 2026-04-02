from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import requests

app = FastAPI()


# MongoDB connection
client = MongoClient("mongodb://localhost:27017")
db = client["inventory_db"]
collection = db["products"]

# Home endpoint
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

##
# /getSingleProduct -
# This allows you to pass a single ID number into the endpoint and return the details of the single product in JSON format.
@app.get("/getSingleProduct/{product_id}")
def get_single_product(product_id):
    try:
        product = collection.find_one({"ProductID": str(product_id)}, {"_id": 0})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# /getAll - 
# This endpoint should return all inventory in JSON format from the database.
@app.get("/getAll")
def get_all():
    try:
        products = list(collection.find({}, {"_id": 0}))
        return products
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# /addNew - TODO - convert to pydantic model and use request body instead of query params

# This endpoint should take in all 5 attributes of a new item and insert them into the database as a new record.
@app.post("/addNew")
# using query params for simlicity, but in a real application
# would use a request body with a Pydantic model for validation.
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


# /deleteOne - 
# This endpoint should delete a product by the provided ID.
@app.delete("/deleteOne/{product_id}")
def delete_one(product_id):
    try:
        result = collection.delete_one({"ProductID": str(product_id)})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Product not found")

        return {"message": f"Product {product_id} deleted successfully"}

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# /startsWith - 
# This should allow the user to pass a letter to the URL, such as s, and return all products that start with s.
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


# /paginate - 
# This URL should pass in a product ID to start from and a product ID to end from. 
# The products should be returned in a batch of 10.
@app.get("/paginate/{start_id}/{end_id}")

#returns prods between start_id and end_is, sorted by ProductID
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


# /convert -
# All of the prices are currently in dollars in the sample data. 
# Implement a URL titled /convert which takes in the ID number of a product and returns the price in euros. 
# An online API should be used to get the current exchange rate.

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