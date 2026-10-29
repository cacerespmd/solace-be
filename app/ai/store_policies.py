
import json
from pathlib import Path

from openai import OpenAI

from app.ai.knowledge import get_store_policy_collection
from app.core.config import settings


POLICY_FILE = (
    Path(__file__).resolve().parent
    / "data"
    / "store_policies.json"
)


def load_store_policies():
    if not POLICY_FILE.is_file():
        raise FileNotFoundError(
            "Store policy file not found: {}".format(
                POLICY_FILE
            )
        )

    with POLICY_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data.get("policies"), list):
        raise ValueError(
            "Store policy file must contain a policies list"
        )

    if data.get("is_official") is not False:
        raise ValueError(
            "This demo indexer requires is_official=false"
        )

    return data


def index_store_policies():
    """
    Index demo store policies into a separate
    ChromaDB collection.
    """

    if not settings.OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY is not configured"
        )

    data = load_store_policies()
    policies = data["policies"]

    if not policies:
        raise ValueError(
            "No store policies available to index"
        )

    ids = []
    documents = []
    metadatas = []

    for policy in policies:
        policy_id = str(policy["id"]).strip()
        title = str(policy["title"]).strip()
        content = str(policy["content"]).strip()

        if not policy_id or not title or not content:
            raise ValueError(
                "Policy ID, title, and content are required"
            )

        ids.append("store_policy_{}".format(policy_id))

        documents.append(
            "Policy: {}\n\n{}".format(
                title,
                content,
            )
        )

        metadatas.append({
            "policy_id": policy_id,
            "title": title,
            "document_type": "demo_store_policy",
            "is_official": False,
            "store_name": data.get(
                "store_name",
                "SOLACE Demo Store",
            ),
            "version": str(data.get("version", "1.0")),
        })

    if len(set(ids)) != len(ids):
        raise ValueError(
            "Duplicate policy IDs found"
        )

    openai_client = OpenAI(
        api_key=settings.OPENAI_API_KEY
    )

    response = openai_client.embeddings.create(
        model=settings.OPENAI_EMBEDDING_MODEL,
        input=documents,
    )

    embeddings = [
        item.embedding
        for item in response.data
    ]

    collection = get_store_policy_collection()

    # Upsert makes repeated indexing safe.
    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    # Remove policies that no longer exist in JSON.
    current_ids = collection.get().get("ids", [])
    obsolete_ids = [
        item_id
        for item_id in current_ids
        if item_id not in set(ids)
    ]

    if obsolete_ids:
        collection.delete(ids=obsolete_ids)

    return {
        "status": "indexed",
        "store_name": data.get("store_name"),
        "is_official": False,
        "policies_indexed": len(ids),
        "collection": collection.name,
    }
