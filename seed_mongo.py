import json
import os
from pymongo import MongoClient


def seed() -> None:
    mongo_uri = os.getenv("MONGO_URI")
    mongo_db_name = os.getenv("MONGO_DB", "inventory_db")

    if not mongo_uri:
        raise RuntimeError(
            "MONGO_URI is not set. Example: mongodb://admin:adminPassword123@localhost:27017/?authSource=admin"
        )

    client = MongoClient(mongo_uri)
    db = client[mongo_db_name]
    collection = db["products"]

    with open("data/products.json", "r", encoding="utf-8") as f:
        products = json.load(f)

    collection.delete_many({})
    collection.insert_many(products)

    print("MongoDB seeded successfully.")


if __name__ == "__main__":
    seed()