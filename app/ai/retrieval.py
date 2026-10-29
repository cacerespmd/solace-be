
import re

from openai import OpenAI
from sqlalchemy import select

from app.models import Product

from app.ai.knowledge import (
    get_collection,
    get_store_policy_collection,
)
from app.core.config import settings


MAX_DISTANCE = 0.75


def resolve_product_ids(query, db):
    """Resolve explicit catalog names, SKUs, or distinctive model references.

    Ambiguous references retain all candidates rather than picking an arbitrary
    product. Generic words such as 'webcam' must not select a product by themselves.
    """
    tokens = lambda value: re.findall(r"[a-z0-9]+", (value or "").lower())
    query_tokens = set(tokens(query))
    candidates = []
    products = db.scalars(select(Product)).all()
    for product in products:
        name_tokens = tokens(product.name)
        sku_tokens = tokens(product.sku)
        if not name_tokens:
            continue
        full_name = " " + " ".join(name_tokens) + " "
        question = " " + " ".join(tokens(query)) + " "
        sku_match = bool(sku_tokens) and (
            " " + " ".join(sku_tokens) + " " in question
        )
        overlap = query_tokens.intersection(name_tokens)
        model_match = any(
            any(c.isalpha() for c in token)
            and any(c.isdigit() for c in token)
            for token in overlap
        )
        if full_name in question or sku_match:
            candidates.append((2, len(name_tokens), product.id))
        elif model_match or (len(overlap) >= 2 and name_tokens[0] in overlap):
            candidates.append((1, len(overlap), product.id))
    if not candidates:
        return []
    best = max((priority, score) for priority, score, _ in candidates)
    return [pid for priority, score, pid in candidates if (priority, score) == best]


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
    product_ids=None,
):
    collection = get_collection()

    if collection.count() == 0:
        return []

    query_options = {}
    count = collection.count()
    if product_ids:
        where = {"product_id": {"$in": list(product_ids)}}
        count = len(collection.get(where=where, include=[])["ids"])
        if not count:
            # Never replace missing documentation with another product's terms.
            return []
        query_options["where"] = where

    query_embedding = create_query_embedding(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(limit, count),
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
        **query_options,
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
