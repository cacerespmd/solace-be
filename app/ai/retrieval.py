
from openai import OpenAI

from app.ai.knowledge import (
    get_collection,
    get_store_policy_collection,
)
from app.core.config import settings


MAX_DISTANCE = 0.75


def create_query_embedding(query: str):
    client = OpenAI(
        api_key=settings.OPENAI_API_KEY
    )

    response = client.embeddings.create(
        model=settings.OPENAI_EMBEDDING_MODEL,
        input=query,
    )

    return response.data[0].embedding


# ==========================================
# PRODUCT DOCUMENT RETRIEVAL
# ==========================================

def search_product_knowledge(
    query: str,
    limit: int = 4,
):
    collection = get_collection()

    if collection.count() == 0:
        return []

    query_embedding = create_query_embedding(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(limit, collection.count()),
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    matches = []

    for content, metadata, distance in zip(
        documents,
        metadatas,
        distances,
    ):
        if distance > MAX_DISTANCE:
            continue

        matches.append({
            "content": content,
            "distance": distance,
            "product_id": metadata.get("product_id"),
            "product_name": metadata.get("product_name"),
            "product_description": metadata.get(
                "product_description",
                "",
            ),
            "document_id": metadata.get("document_id"),
            "document_title": metadata.get("document_title"),
            "source_url": metadata.get("source_url"),
        })

    return matches


# ==========================================
# STORE POLICY AND FAQ RETRIEVAL
# ==========================================

def search_store_knowledge(
    query: str,
    limit: int = 4,
):
    collection = get_store_policy_collection()

    if collection.count() == 0:
        return []

    query_embedding = create_query_embedding(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(limit, collection.count()),
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    matches = []

    for content, metadata, distance in zip(
        documents,
        metadatas,
        distances,
    ):
        if distance > MAX_DISTANCE:
            continue

        matches.append({
            "content": content,
            "distance": distance,
            "policy_id": metadata.get("policy_id"),
            "title": metadata.get("title"),
            "document_type": metadata.get(
                "document_type",
            ),
            "is_official": metadata.get(
                "is_official",
                False,
            ),
            "store_name": metadata.get(
                "store_name",
            ),
            "version": metadata.get(
                "version",
            ),
        })

    return matches
