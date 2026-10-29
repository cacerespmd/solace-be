from types import SimpleNamespace
from unittest.mock import Mock

import chromadb
import pytest

from app.ai import retrieval


@pytest.mark.parametrize("question, expected", [
    ("What is the manufacturer warranty for Logitech C270 HD Webcam?", [1]),
    ("Warranty for C270?", [1]),
    ("Warranty for 4160953?", [3]),
    ("Thrustmaster TCA Sky Yoke warranty", [3]),
    ("What is the store warranty?", []),
    ("Do you sell a webcam?", []),
])
def test_resolve_product(question, expected):
    db = Mock()
    db.scalars.return_value.all.return_value = [
        SimpleNamespace(id=1, name="Logitech C270 HD Webcam", sku="LOG-C270"),
        SimpleNamespace(id=2, name="Sony 1000X Headphones", sku="SONY-1000X"),
        SimpleNamespace(id=3, name="Thrustmaster TCA Sky Yoke for PS5 (4160953)", sku="4160953"),
    ]
    assert retrieval.resolve_product_ids(question, db) == expected


@pytest.fixture
def collection(tmp_path, monkeypatch):
    client = chromadb.PersistentClient(path=str(tmp_path))
    collection = client.create_collection("warranty_test", metadata={"hnsw:space": "cosine"})
    collection.add(
        ids=["logitech", "sony"],
        documents=["Sample Logitech warranty: 24 months, parts and labor.",
                   "Sample Sony warranty: 12 months."],
        # Sony deliberately ranks higher in the unfiltered semantic search.
        embeddings=[[0.8, 0.2], [1.0, 0.0]],
        metadatas=[
            {"product_id": 1, "product_name": "Logitech C270 HD Webcam"},
            {"product_id": 2, "product_name": "Sony 1000X Headphones"},
        ],
    )
    monkeypatch.setattr(retrieval, "get_collection", lambda: collection)
    monkeypatch.setattr(retrieval, "create_query_embedding", lambda query: [1.0, 0.0])
    return collection


def test_product_filter_excludes_more_similar_sony_warranty(collection):
    matches = retrieval.search_product_knowledge("Logitech C270 warranty", product_ids=[1])
    assert len(matches) == 1
    assert matches[0]["product_id"] == 1
    assert "24 months" in matches[0]["content"]


def test_missing_product_documents_do_not_fall_back_to_sony(collection):
    assert retrieval.search_product_knowledge("Thrustmaster warranty", product_ids=[3]) == []


def test_general_semantic_search_remains_available(collection):
    matches = retrieval.search_product_knowledge("warranty")
    assert {match["product_id"] for match in matches} == {1, 2}
