import os
from typing import List, Dict, Any
import requests
from dotenv import load_dotenv
load_dotenv()
from pinecone import Pinecone, ServerlessSpec
from app.config.settings import (
    PINECONE_INDEX_NAME,
    EMBEDDING_MODEL,
    EMBEDDING_DIM,
    OLLAMA_EMBED_URL
)


class PineconeClient:
    def __init__(self):
        # Init clients
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

        # Ensure index exists
        self._ensure_index()

        # Connect index
        self.index = self.pc.Index(PINECONE_INDEX_NAME)

    # -------------------------------
    # INDEX SETUP
    # -------------------------------
    def _ensure_index(self):
        existing_indexes = self.pc.list_indexes().names()

        if PINECONE_INDEX_NAME not in existing_indexes:
            print(f"Creating index: {PINECONE_INDEX_NAME}")

            self.pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=EMBEDDING_DIM, # make sure dimentions are correct for your embedding model
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )

    # -------------------------------
    # EMBEDDING FUNCTION
    # -------------------------------
    def embed_text(self, text: str) -> list[float]:
        """Call Ollama's local embedding endpoint."""
        resp = requests.post(
            OLLAMA_EMBED_URL,
            json={"model": EMBEDDING_MODEL, "prompt": text},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if "embedding" in data:
            return data["embedding"]
        elif "data" in data:
            return data["data"][0]["embedding"]
        else:
            raise ValueError(f"Unexpected embedding response: {data}")
        # return resp.json()["embedding"]
    
    # -------------------------------
    # BUILD TEXT FROM PROPERTY JSON
    # -------------------------------
    def build_document_text(self, prop: Dict[str, Any]) -> str:
        return f"""
        {prop.get("title")}
        Located in {prop.get("city")} at {prop.get("address")}
        Price: {prop.get("price")}
        {prop.get("bedrooms")} bedrooms and {prop.get("bathrooms")} bathrooms
        Area: {prop.get("area_sqft")} sqft
        Type: {prop.get("property_type")}
        Description: {prop.get("description")}
        """

    # -------------------------------
    # UPSERT (INGEST)
    # -------------------------------
    def upsert_properties(self, properties: List[Dict[str, Any]]):
        vectors = []

        for prop in properties:
            text = self.build_document_text(prop)
            embedding = self.embed_text(text)

            vectors.append({
                "id": prop["id"],
                "values": embedding,
                "metadata": {
                    "title": prop.get("title"),
                    "city": prop.get("city"),
                    "price": prop.get("price"),
                    "bedrooms": prop.get("bedrooms"),
                    "bathrooms": prop.get("bathrooms"),
                    "area_sqft": prop.get("area_sqft"),
                    "property_type": prop.get("property_type"),
                    "address": prop.get("address"),
                    "description": prop.get("description")
                }
            })

        print(f"Ingesting {len(vectors)} properties...")
        self.index.upsert(vectors=vectors)
        print("✅ Ingestion complete")

    # -------------------------------
    # QUERY (RAG SEARCH)
    # -------------------------------
    def query(
        self,
        query_text: str,
        top_k: int = 5,
        filters: Dict[str, Any] = None
    ):
        embedding = self.embed_text(query_text)

        results = self.index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filters  # Pinecone filter syntax
        )

        return results["matches"]

    # -------------------------------
    # HELPER: FILTER FORMAT EXAMPLES
    # -------------------------------
    def example_filters(self):
        return {
            "city": {"$eq": "mumbai"},
            "price": {"$lt": 10000000},
            "bedrooms": {"$gte": 2}
        }


_client: PineconeClient | None = None


def get_client() -> PineconeClient:
    global _client
    if _client is None:
        _client = PineconeClient()
    return _client


def search_properties(
    query: str,
    city: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    bedrooms: int | None = None,
    property_type: str | None = None,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Semantic search + metadata filters against Pinecone."""
    filters: dict[str, Any] = {}

    if city:
        filters["city"] = {"$eq": city.strip().lower()}
    if property_type:
        filters["property_type"] = {"$eq": property_type.strip().lower()}
    if bedrooms is not None:
        filters["bedrooms"] = {"$eq": int(bedrooms)}
    if min_price is not None and max_price is not None:
        filters["price"] = {"$gte": float(min_price), "$lte": float(max_price)}
    elif min_price is not None:
        filters["price"] = {"$gte": float(min_price)}
    elif max_price is not None:
        filters["price"] = {"$lte": float(max_price)}

    results = get_client().query(
        query_text=query,
        top_k=top_k,
        filters=filters if filters else None,
    )

    properties = []
    for match in results:
        metadata = match.get("metadata", {}) if isinstance(match, dict) else getattr(match, "metadata", {}) or {}
        properties.append({
            "id": match.get("id") if isinstance(match, dict) else getattr(match, "id", None),
            "score": round(match.get("score"), 3) if isinstance(match, dict) and match.get("score") is not None else round(getattr(match, "score", 0), 3),
            "title": metadata.get("title", ""),
            "city": metadata.get("city", ""),
            "price": metadata.get("price"),
            "bedrooms": metadata.get("bedrooms"),
            "bathrooms": metadata.get("bathrooms"),
            "area_sqft": metadata.get("area_sqft"),
            "property_type": metadata.get("property_type", ""),
            "description": metadata.get("description", ""),
        })
    return properties