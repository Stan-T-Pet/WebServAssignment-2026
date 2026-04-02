import csv
import json
import os
from pathlib import Path

def convert() -> None:
    path = os.path.join(os.getcwd(), "data")

    csv_path = os.path.join(path, "products.csv")
    json_path = os.path.join(path, "products.json")

    csv_file_path = Path(csv_path)
    json_file_path = Path(json_path)


    # Create JSON file if it doesn't exist
    json_file_path.touch(exist_ok=True)

    try:
        with csv_file_path.open(mode="r", newline="", encoding="utf-8") as csv_file:
            csv_reader = csv.DictReader(csv_file)
            rows = list(csv_reader)

        with json_file_path.open(mode="w", encoding="utf-8") as json_file:
            json.dump(rows, json_file, indent=2, ensure_ascii=False)

        print(f"Conversion successful: {csv_file_path} -> {json_file_path}")
    except Exception as e:
        raise RuntimeError(f"Error during conversion: {e}")


if __name__ == "__main__":
    convert()


### references
# 1. https://docs.python.org/3/library/csv.html
# 2. How to: https://www.geeksforgeeks.org/python/convert-csv-to-json-using-python/