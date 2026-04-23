# fix how you are loading the JSON file path, it should be relative to the project root.
import json
from pathlib import Path
from app.rag.pinecone_client import PineconeClient


def load_json(file_path: str):
    with open(file_path, "r") as f:
        return json.load(f)


def main():
    client = PineconeClient()

    # # Get project root dynamically
    # BASE_DIR = Path(__file__).resolve().parents[1]  
    # # app/

    # data_path = BASE_DIR / "data" / "properties.json"

    # properties = load_json(data_path)

    # Load your dataset
    properties = load_json("app/data/listings.json")

    print(f"Loaded {len(properties)} properties")

    # Ingest into Pinecone
    client.upsert_properties(properties)


if __name__ == "__main__":
    main()