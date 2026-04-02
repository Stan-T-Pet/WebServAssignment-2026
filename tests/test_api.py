from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import api

client = TestClient(api.app)


def test_home():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Inventory API is running"
    assert "/getAll" in data["endpoints"]


def test_get_single_product_found():
    fake_product = {
        "ProductID": "1001",
        "Name": "NVIDIA RTX 4090",
        "UnitPrice": "1599.99",
        "StockQuantity": "12",
        "Description": "High-end GPU with 24GB VRAM for 4K gaming."
    }

    with patch.object(api, "collection") as mock_collection:
        mock_collection.find_one.return_value = fake_product
        response = client.get("/getSingleProduct/1001")

    assert response.status_code == 200
    assert response.json()["ProductID"] == "1001"


def test_get_single_product_not_found():
    with patch.object(api, "collection") as mock_collection:
        mock_collection.find_one.return_value = None
        response = client.get("/getSingleProduct/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_get_all():
    fake_products = [
        {"ProductID": "1001", "Name": "A"},
        {"ProductID": "1002", "Name": "B"}
    ]

    with patch.object(api, "collection") as mock_collection:
        mock_collection.find.return_value = fake_products
        response = client.get("/getAll")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_add_new_success():
    with patch.object(api, "collection") as mock_collection:
        mock_collection.find_one.return_value = None
        mock_collection.insert_one.return_value = MagicMock()

        response = client.post(
            "/addNew",
            params={
                "ProductID": "9998",
                "Name": "Test Product",
                "UnitPrice": "10.50",
                "StockQuantity": "5",
                "Description": "Test Description"
            }
        )

    assert response.status_code == 200
    assert response.json()["message"] == "Product added successfully"


def test_add_new_duplicate():
    with patch.object(api, "collection") as mock_collection:
        mock_collection.find_one.return_value = {"ProductID": "9998"}

        response = client.post(
            "/addNew",
            params={
                "ProductID": "9998",
                "Name": "Test Product",
                "UnitPrice": "10.50",
                "StockQuantity": "5",
                "Description": "Test Description"
            }
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "ProductID already exists"


def test_delete_one_success():
    mock_result = MagicMock()
    mock_result.deleted_count = 1

    with patch.object(api, "collection") as mock_collection:
        mock_collection.delete_one.return_value = mock_result
        response = client.delete("/deleteOne/1001")

    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]


def test_delete_one_not_found():
    mock_result = MagicMock()
    mock_result.deleted_count = 0

    with patch.object(api, "collection") as mock_collection:
        mock_collection.delete_one.return_value = mock_result
        response = client.delete("/deleteOne/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_starts_with():
    fake_products = [
        {"ProductID": "1003", "Name": "Samsung 990 Pro 2TB"}
    ]

    with patch.object(api, "collection") as mock_collection:
        mock_collection.find.return_value = fake_products
        response = client.get("/startsWith/S")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_paginate():
    fake_products = [
        {"ProductID": "1001", "Name": "A"},
        {"ProductID": "1002", "Name": "B"}
    ]

    mock_cursor = MagicMock()
    mock_cursor.sort.return_value.limit.return_value = fake_products

    with patch.object(api, "collection") as mock_collection:
        mock_collection.find.return_value = mock_cursor
        response = client.get("/paginate/1001/1010")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_convert_success():
    fake_product = {
        "ProductID": "1001",
        "Name": "NVIDIA RTX 4090",
        "UnitPrice": "100.00",
        "StockQuantity": "12",
        "Description": "GPU"
    }

    fake_exchange = {
        "rates": {
            "EUR": 0.92
        }
    }

    with patch.object(api, "collection") as mock_collection, patch.object(api.requests, "get") as mock_get:
        mock_collection.find_one.return_value = fake_product

        mock_response = MagicMock()
        mock_response.json.return_value = fake_exchange
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        response = client.get("/convert/1001")

    assert response.status_code == 200
    assert response.json()["PriceEUR"] == 92.0